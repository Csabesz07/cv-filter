import hashlib
import os
from pathlib import Path

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CVFile, Candidate
from .serializers import (
    CVUploadSerializer,
    LoginSerializer,
    RegisterSerializer,
    AuditLogSerializer,
    CVAccessEventSerializer,
)
from .logging_service import AuditLogService, CVAccessEventService

User = get_user_model()


class RegisterView(APIView):
    """
    API endpoint to register a user and return JWT tokens.
    """

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'user': RegisterSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    API endpoint to log in and return JWT tokens.
    """

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if not user:
            return Response(
                {'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED
            )
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'user': RegisterSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        )


class LoginPageView(TemplateView):
    template_name = 'accounts/login.html'


class RegisterPageView(TemplateView):
    template_name = 'accounts/register.html'


class CVUploadView(APIView):
    """
    API endpoint to upload a CV file for a candidate.
    Handles file validation, storage, and database record creation.
    """

    permission_classes = [IsAuthenticated]

    def _get_file_checksum(self, file):
        """
        Calculate SHA256 checksum of uploaded file.
        """
        hash_sha256 = hashlib.sha256()
        for chunk in file.chunks(8192):
            hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _get_organization(self):
        """
        Get the organization for the authenticated user.
        """
        user = self.request.user
        if not user.organization:
            raise ValueError("User is not associated with any organization.")
        return user.organization

    def _get_candidate(self, organization, candidate_id=None, candidate_email=None):
        """
        Find candidate by ID or email within the organization.
        """
        try:
            if candidate_id:
                return Candidate.objects.get(id=candidate_id, organization=organization)
            elif candidate_email:
                return Candidate.objects.get(email=candidate_email, organization=organization)
        except Candidate.DoesNotExist:
            raise ValueError(f"Candidate not found in organization {organization.id}.")

    def _save_uploaded_file(self, file, organization, candidate):
        """
        Save uploaded file to disk.
        Returns the storage path relative to uploads directory.
        """
        uploads_dir = Path('/app/uploads') / str(organization.id) / str(candidate.id)
        uploads_dir.mkdir(parents=True, exist_ok=True)

        # Use original filename
        file_path = uploads_dir / file.name
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Return relative path for storage in DB
        return str(file_path.relative_to('/app/uploads'))

    @transaction.atomic
    def post(self, request):
        """
        Handle CV file upload with validation and idempotent behavior.
        """
        try:
            # Get organization from authenticated user
            organization = self._get_organization()
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

        # Extract candidate lookup parameters
        candidate_id = request.data.get('candidate_id')
        candidate_email = request.data.get('candidate_email')

        # Get candidate
        try:
            candidate = self._get_candidate(organization, candidate_id, candidate_email)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        # Validate serializer
        serializer = CVUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get uploaded file
        file = serializer.validated_data['file']

        # Calculate checksum
        checksum = self._get_file_checksum(file)

        # Check for duplicate (same checksum)
        existing_cv = CVFile.objects.filter(
            organization=organization,
            candidate=candidate,
            checksum=checksum,
        ).first()

        if existing_cv:
            # Idempotent: return existing record with 200 OK
            response_serializer = CVUploadSerializer(existing_cv)
            return Response(
                {
                    **response_serializer.data,
                    'message': 'File already uploaded with this checksum.',
                },
                status=status.HTTP_200_OK,
            )

        # Save file to disk
        try:
            storage_path = self._save_uploaded_file(file, organization, candidate)
        except IOError as e:
            return Response(
                {'error': f'Failed to save file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Create CVFile record in database
        cv_file = CVFile.objects.create(
            organization=organization,
            candidate=candidate,
            storage_path=storage_path,
            original_filename=file.name,
            mime_type=file.content_type,
            file_size_bytes=file.size,
            checksum=checksum,
            upload_status='uploaded',
            source_type='upload',
        )

        # Log CV upload event
        CVAccessEventService.log_cv_upload(
            organization=organization,
            candidate=candidate,
            cv_file=cv_file,
            actor_user=request.user,
            metadata={
                'file_size': file.size,
                'mime_type': file.content_type,
            },
        )

        # Return response
        response_serializer = CVUploadSerializer(cv_file)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class AuditLogListView(APIView):
    """
    API endpoint to query audit logs for the organization.
    Supports filtering by event type, entity type, severity, etc.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get audit logs with optional filters.

        Query parameters:
        - event_type: Filter by event type
        - entity_type: Filter by entity type
        - severity: Filter by severity (log, debug, verbose)
        - limit: Number of results (default 100, max 1000)
        """
        org = request.user.organization
        if not org:
            return Response(
                {"detail": "User has no organization"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get query parameters
        event_type = request.query_params.get('event_type')
        entity_type = request.query_params.get('entity_type')
        severity = request.query_params.get('severity')
        limit = min(int(request.query_params.get('limit', 100)), 1000)

        # Query logs
        logs = AuditLogService.query_logs(
            organization=org,
            event_type=event_type,
            entity_type=entity_type,
            severity=severity,
            limit=limit,
        )

        # Serialize and return
        serializer = AuditLogSerializer(logs, many=True)
        return Response({
            'count': len(serializer.data),
            'results': serializer.data,
        })


class CVAccessEventListView(APIView):
    """
    API endpoint to query CV access events for the organization.
    Supports filtering by candidate, action, etc.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get CV access events with optional filters.

        Query parameters:
        - candidate_id: Filter by candidate UUID
        - action: Filter by action type
        - limit: Number of results (default 100, max 1000)
        """
        org = request.user.organization
        if not org:
            return Response(
                {"detail": "User has no organization"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get query parameters
        candidate_id = request.query_params.get('candidate_id')
        action = request.query_params.get('action')
        limit = min(int(request.query_params.get('limit', 100)), 1000)

        # Get candidate if filtering
        candidate = None
        if candidate_id:
            try:
                candidate = Candidate.objects.get(id=candidate_id, organization=org)
            except Candidate.DoesNotExist:
                return Response(
                    {"detail": "Candidate not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Query events
        events = CVAccessEventService.query_events(
            organization=org,
            candidate=candidate,
            action=action,
            limit=limit,
        )

        # Serialize and return
        serializer = CVAccessEventSerializer(events, many=True)
        return Response({
            'count': len(serializer.data),
            'results': serializer.data,
        })
