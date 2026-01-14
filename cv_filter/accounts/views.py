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
    OrganizationCreateSerializer,
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

        # Return response
        response_serializer = CVUploadSerializer(cv_file)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


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


class OrganizationCreateView(APIView):
    """
    API endpoint to create an organization for the current user.
    """

    permission_classes = [IsAuthenticated]

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
