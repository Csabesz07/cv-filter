from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from django.utils.text import slugify

from .models import CVFile, Candidate, Organization

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer to register a new user.
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        read_only_fields = ('id',)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer to validate login credentials.
    """

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'name', 'slug')
        read_only_fields = ('id',)


class OrganizationCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    slug = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        name = attrs.get('name', '').strip()
        slug = attrs.get('slug', '').strip()

        if not name:
            raise serializers.ValidationError({'name': 'Name is required.'})

        if not slug:
            slug = slugify(name)

        if not slug:
            raise serializers.ValidationError({'slug': 'Slug is required.'})

        if Organization.objects.filter(slug=slug).exists():
            raise serializers.ValidationError({'slug': 'Slug already exists.'})

        attrs['name'] = name
        attrs['slug'] = slug
        return attrs

    def create(self, validated_data):
        return Organization.objects.create(
            name=validated_data['name'],
            slug=validated_data['slug'],
        )


class UserUpdateSerializer(serializers.Serializer):
    """
    Serializer to update username and/or password for the current user.
    """

    username = serializers.CharField(required=False, allow_blank=False)
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)

    def validate_username(self, value):
        user = self.context.get('user')
        if not user:
            return value
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("Username is already taken.")
        return value

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        current_password = attrs.get('current_password')
        user = self.context.get('user')

        if new_password:
            if not current_password:
                raise serializers.ValidationError(
                    {"current_password": "Current password is required."}
                )
            if user and not user.check_password(current_password):
                raise serializers.ValidationError(
                    {"current_password": "Current password is incorrect."}
                )
            validate_password(new_password, user=user)

        if not attrs.get('username') and not new_password:
            raise serializers.ValidationError(
                "Provide a username or a new password to update."
            )

        return attrs

    def update(self, instance, validated_data):
        username = validated_data.get('username')
        new_password = validated_data.get('new_password')

        if username:
            instance.username = username
        if new_password:
            instance.set_password(new_password)

        instance.save()
        return instance


class CandidateBasicSerializer(serializers.ModelSerializer):
    """
    Minimal candidate information for CV upload response.
    """

    class Meta:
        model = Candidate
        fields = ('id', 'first_name', 'last_name', 'email')
        read_only_fields = fields


class CVUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for CV file uploads.
    Handles file validation, checksum calculation, and response.
    """

    file = serializers.FileField(write_only=True, required=True)
    candidate_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    candidate_email = serializers.EmailField(write_only=True, required=False, allow_null=True)
    candidate = CandidateBasicSerializer(read_only=True)

    class Meta:
        model = CVFile
        fields = (
            'id',
            'file',
            'candidate_id',
            'candidate_email',
            'candidate',
            'organization',
            'original_filename',
            'mime_type',
            'file_size_bytes',
            'checksum',
            'upload_status',
            'uploaded_at',
            'source_type',
        )
        read_only_fields = (
            'id',
            'candidate',
            'organization',
            'original_filename',
            'mime_type',
            'file_size_bytes',
            'checksum',
            'upload_status',
            'uploaded_at',
            'source_type',
        )

    def validate(self, data):
        """
        Validate file upload data.
        """
        file = data.get('file')
        candidate_id = data.get('candidate_id')
        candidate_email = data.get('candidate_email')

        # Validate that either candidate_id or candidate_email is provided
        if not candidate_id and not candidate_email:
            raise serializers.ValidationError(
                "Either 'candidate_id' or 'candidate_email' must be provided."
            )

        # Validate file type
        allowed_types = ('application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword')
        if file.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"Invalid file type: {file.content_type}. Allowed types: PDF, DOCX, DOC."
            )

        # Validate file size (25 MB max)
        max_size = 25 * 1024 * 1024  # 25 MB
        if file.size > max_size:
            raise serializers.ValidationError(
                f"File size exceeds 25 MB limit. Current size: {file.size / (1024 * 1024):.2f} MB."
            )

        return data

