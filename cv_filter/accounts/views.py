import hashlib
import os
from pathlib import Path

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.utils import timezone
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from document_extraction.extract_data import CVTextExtractor
from .models import CVFile, CVParse, CVParseStatus, Candidate
from .logging_service import AuditLogService, CVAccessEventService
from .serializers import (
    AuditLogSerializer,
    CVAccessEventSerializer,
    CVUploadSerializer,
    CVFileListSerializer,
    CandidateBasicSerializer,
    CandidateCreateSerializer,
    LoginSerializer,
    OrganizationCreateSerializer,
    OrganizationSelectSerializer,
    OrganizationSerializer,
    RegisterSerializer,
    UserUpdateSerializer,
)

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

        timeout_seconds = request.data.get('timeout_seconds')
        save_to_file = request.data.get('save_to_file')
        try:
            timeout_seconds = int(timeout_seconds) if timeout_seconds else 30
        except (TypeError, ValueError):
            timeout_seconds = 30

        save_to_file_flag = True
        if isinstance(save_to_file, str):
            save_to_file_flag = save_to_file.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(save_to_file, bool):
            save_to_file_flag = save_to_file

        extraction = CVTextExtractor(
            timeout_seconds=timeout_seconds,
            save_to_file=save_to_file_flag,
        ).extract_text(str(Path('/app/uploads') / storage_path))

        parse_status = (
            CVParseStatus.SUCCEEDED if extraction.get('success') else CVParseStatus.FAILED
        )
        CVParse.objects.create(
            organization=organization,
            cv_file=cv_file,
            parse_status=parse_status,
            parser_name=extraction.get('method'),
            parser_version='',
            parsed_at=timezone.now(),
            text_content=extraction.get('text', ''),
            error_message=extraction.get('error'),
        )

        return Response(
            {
                **response_serializer.data,
                'success': extraction.get('success', False),
                'extracted_text': extraction.get('text', ''),
                'metadata': extraction.get('metadata', {}),
                'method': extraction.get('method'),
                'output_file': extraction.get('output_file'),
                'error': extraction.get('error'),
            },
            status=status.HTTP_201_CREATED,
        )


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


class UserMeView(APIView):
    """
    API endpoint to get/update the current user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'user': RegisterSerializer(request.user).data})

    def patch(self, request):
        serializer = UserUpdateSerializer(
            data=request.data, context={'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.update(request.user, serializer.validated_data)
        return Response({'user': RegisterSerializer(user).data})


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


class RankingEventListView(APIView):
    """
    API endpoint to query ranking-specific audit events.
    Provides detailed tracking of ranking runs and their outcomes.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get ranking events with optional filters.

        Query parameters:
        - run_id: Filter by ranking run UUID
        - event_type: Filter by event type (started, completed, failed, etc.)
        - limit: Number of results (default 100, max 1000)
        """
        org = request.user.organization
        if not org:
            return Response(
                {"detail": "User has no organization"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get query parameters
        run_id = request.query_params.get('run_id')
        event_type = request.query_params.get('event_type')
        limit = min(int(request.query_params.get('limit', 100)), 1000)

        # Build filter for ranking events
        # All ranking events start with 'ranking.'
        from accounts.models import AuditLog
        
        queryset = AuditLog.objects.filter(
            organization=org,
            event_type__startswith='ranking.'
        )

        # Filter by run_id if provided
        if run_id:
            queryset = queryset.filter(entity_id=run_id)

        # Filter by specific event type
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        # Order and limit
        queryset = queryset.order_by('-created_at')[:limit]

        # Serialize and return
        serializer = AuditLogSerializer(queryset, many=True)
        
        # Calculate statistics if filtering by run_id
        stats = None
        if run_id and serializer.data:
            stats = self._calculate_run_stats(serializer.data)

        return Response({
            'count': len(serializer.data),
            'results': serializer.data,
            'statistics': stats,
        })

    def _calculate_run_stats(self, events: list) -> dict:
        """Calculate statistics from ranking run events."""
        stats = {
            'total_events': len(events),
            'event_types': {},
            'has_completion': False,
            'has_failure': False,
        }

        for event in events:
            event_type = event.get('event_type', '')
            stats['event_types'][event_type] = stats['event_types'].get(event_type, 0) + 1

            if 'completed' in event_type:
                stats['has_completion'] = True
                # Extract performance metrics from metadata
                metadata = event.get('metadata', {})
                stats['candidates_evaluated'] = metadata.get('candidates_evaluated')
                stats['scores_created'] = metadata.get('scores_created')
                stats['total_duration_seconds'] = metadata.get('total_duration_seconds')
                stats['score_statistics'] = metadata.get('score_statistics')

            if 'failed' in event_type:
                stats['has_failure'] = True
                metadata = event.get('metadata', {})
                stats['error'] = metadata.get('error')
                stats['error_type'] = metadata.get('error_type')

        return stats


class OrganizationListCreateView(APIView):
    """
    API endpoint to list or create organizations.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        organizations = OrganizationSerializer(
            self._get_organizations(), many=True
        )
        return Response({'results': organizations.data})

    def post(self, request):
        if request.user.organization:
            return Response(
                {'detail': 'User already belongs to an organization.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrganizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = serializer.save()

        request.user.organization = organization
        request.user.save(update_fields=['organization'])

        return Response(
            {'organization': OrganizationSerializer(organization).data},
            status=status.HTTP_201_CREATED,
        )

    def _get_organizations(self):
        return self._organization_queryset()

    def _organization_queryset(self):
        from accounts.models import Organization
        return Organization.objects.all().order_by('name')


class OrganizationSelectView(APIView):
    """
    API endpoint to assign the current user to an organization.
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = OrganizationSelectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = serializer.validated_data['organization_id']
        request.user.organization = organization
        request.user.save(update_fields=['organization'])
        return Response({'organization': OrganizationSerializer(organization).data})


class CandidateListCreateView(APIView):
    """
    API endpoint to list or create candidates within the user's organization.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = request.user.organization
        if not organization:
            return Response(
                {'detail': 'User has no organization.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = Candidate.objects.filter(organization=organization).order_by(
            'first_name', 'last_name'
        )
        serializer = CandidateBasicSerializer(queryset, many=True)
        return Response({'results': serializer.data})

    def post(self, request):
        organization = request.user.organization
        if not organization:
            return Response(
                {'detail': 'User has no organization.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CandidateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        candidate = serializer.save(organization=organization)
        return Response(
            {'candidate': CandidateCreateSerializer(candidate).data},
            status=status.HTTP_201_CREATED,
        )


class CVFileListDeleteView(APIView):
    """
    API endpoint to list uploaded CV files and delete a file.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = request.user.organization
        if not organization:
            return Response(
                {'detail': 'User has no organization.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = CVFile.objects.filter(organization=organization).select_related(
            'candidate'
        )
        serializer = CVFileListSerializer(queryset, many=True)
        return Response({'results': serializer.data})

    def delete(self, request, cv_file_id):
        organization = request.user.organization
        if not organization:
            return Response(
                {'detail': 'User has no organization.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            cv_file = CVFile.objects.get(id=cv_file_id, organization=organization)
        except CVFile.DoesNotExist:
            return Response({'detail': 'CV file not found.'}, status=status.HTTP_404_NOT_FOUND)

        storage_path = Path('/app/uploads') / cv_file.storage_path
        extracted_path = storage_path.with_name(
            f"{storage_path.stem}_extracted.txt"
        )

        cv_file.cv_parses.all().delete()
        cv_file.delete()

        try:
            if storage_path.exists():
                storage_path.unlink()
            if extracted_path.exists():
                extracted_path.unlink()
        except OSError:
            pass

        return Response(status=status.HTTP_204_NO_CONTENT)
