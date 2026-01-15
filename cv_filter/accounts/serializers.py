from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from django.utils.text import slugify

from .models import CVFile, Candidate, Organization, AuditLog, CVAccessEvent

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


class OrganizationSelectSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()

    def validate_organization_id(self, value):
        try:
            organization = Organization.objects.get(id=value)
        except Organization.DoesNotExist:
            raise serializers.ValidationError("Organization not found.")
        return organization


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


class CandidateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ('id', 'first_name', 'last_name', 'email')
        read_only_fields = ('id',)


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


class CVFileListSerializer(serializers.ModelSerializer):
    candidate = CandidateBasicSerializer(read_only=True)
    extracted_text = serializers.SerializerMethodField()
    parsed_at = serializers.SerializerMethodField()

    class Meta:
        model = CVFile
        fields = (
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
            'extracted_text',
            'parsed_at',
        )

    def get_extracted_text(self, obj):
        latest = obj.cv_parses.order_by('-created_at').first()
        return latest.text_content if latest and latest.text_content else ''

    def get_parsed_at(self, obj):
        latest = obj.cv_parses.order_by('-created_at').first()
        return latest.parsed_at if latest else None


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for audit logs.
    Provides read-only access to audit log entries.
    """

    actor_username = serializers.CharField(source='actor_user.username', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            'id',
            'organization',
            'organization_name',
            'actor_user',
            'actor_username',
            'severity',
            'event_type',
            'entity_type',
            'entity_id',
            'description',
            'metadata',
            'created_at',
        )
        read_only_fields = fields


class CVAccessEventSerializer(serializers.ModelSerializer):
    """
    Serializer for CV access events.
    Provides read-only access to CV access tracking.
    """

    actor_username = serializers.CharField(source='actor_user.username', read_only=True)
    candidate_name = serializers.SerializerMethodField()

    class Meta:
        model = CVAccessEvent
        fields = (
            'id',
            'organization',
            'actor_user',
            'actor_username',
            'candidate',
            'candidate_name',
            'cv_file',
            'cv_parse',
            'action',
            'channel',
            'metadata',
            'created_at',
        )
        read_only_fields = fields

    def get_candidate_name(self, obj):
        """Get full candidate name."""
        return f"{obj.candidate.first_name} {obj.candidate.last_name}"


class NLQParseRequestSerializer(serializers.Serializer):
    query = serializers.CharField()
    language = serializers.CharField(required=False, default="hu")


class NLQFiltersSerializer(serializers.Serializer):
    must_have_skills = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    nice_to_have_skills = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    min_years_experience = serializers.FloatField(required=False, allow_null=True)
    location = serializers.CharField(required=False, allow_blank=True, default="")
    remote = serializers.BooleanField(required=False, allow_null=True)
    keywords = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    sort = serializers.DictField(required=False, default=dict)


class NLQParseResponseSerializer(serializers.Serializer):
    filters = NLQFiltersSerializer()
    raw = serializers.DictField(required=False, default=dict)


class CandidateSearchRequestSerializer(serializers.Serializer):
    must_have_skills = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    nice_to_have_skills = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    min_years_experience = serializers.FloatField(required=False, allow_null=True)
    location = serializers.CharField(required=False, allow_blank=True, default="")
    remote = serializers.BooleanField(required=False, allow_null=True)
    keywords = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    sort = serializers.CharField(required=False, default="score_desc")


class CandidateSearchResultSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.CharField()
    status = serializers.CharField()
    headline = serializers.CharField(allow_blank=True, required=False)
    primary_location = serializers.CharField(allow_blank=True, required=False)
    experience_years = serializers.FloatField(required=False, allow_null=True)
    top_skills = serializers.CharField(allow_blank=True, required=False)
    score = serializers.FloatField()
    score_explanation = serializers.CharField()


class CandidateSummaryRequestSerializer(serializers.Serializer):
    language = serializers.CharField(required=False, default="hu")
    job_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class CandidateSummaryResponseSerializer(serializers.Serializer):
    summary = serializers.CharField()
    highlights = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    risks = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    fit_score_explanation = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
