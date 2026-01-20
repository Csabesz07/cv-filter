import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from pgvector.django import VectorField


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not kwargs.get('update_fields'):
            self.updated_at = timezone.now()
        elif 'updated_at' not in kwargs['update_fields']:
            self.updated_at = timezone.now()
            kwargs['update_fields'] = list(kwargs['update_fields']) + ['updated_at']
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class Organization(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    slug = models.TextField(unique=True)

    class Meta:
        db_table = 'organizations'


class User(AbstractUser, TimeStampedModel):
    """
    Custom user model that stores a UUID as the primary key.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
    )
    full_name = models.TextField(default='')
    password_hash = models.TextField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta(AbstractUser.Meta):
        db_table = 'users'
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'email'],
                name='users_org_email_unique',
            ),
            models.UniqueConstraint(
                fields=['organization', 'id'],
                name='users_org_id_unique',
            ),
        ]


class Role(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'roles'


class UserRole(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='user_roles',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles',
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.RESTRICT,
        related_name='user_roles',
    )

    class Meta:
        db_table = 'user_roles'
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'user', 'role'],
                name='user_roles_org_user_role_unique',
            ),
            models.UniqueConstraint(
                fields=['organization', 'id'],
                name='user_roles_org_id_unique',
            ),
        ]


class CandidateStatus(models.TextChoices):
    NEW = 'new', 'new'
    IN_REVIEW = 'in_review', 'in_review'
    SHORTLISTED = 'shortlisted', 'shortlisted'
    REJECTED = 'rejected', 'rejected'
    HIRED = 'hired', 'hired'


class Candidate(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='candidates',
    )
    first_name = models.TextField()
    last_name = models.TextField()
    email = models.TextField()
    phone = models.TextField(null=True, blank=True)
    current_title = models.TextField(null=True, blank=True)
    current_company = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=CandidateStatus.choices,
        default=CandidateStatus.NEW,
    )
    source = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'candidates'
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'email'],
                name='candidates_org_email_unique',
            ),
            models.UniqueConstraint(
                fields=['organization', 'id'],
                name='candidates_org_id_unique',
            ),
        ]


class CVSourceType(models.TextChoices):
    UPLOAD = 'upload', 'upload'
    EMAIL = 'email', 'email'
    LINKEDIN = 'linkedin', 'linkedin'
    OTHER = 'other', 'other'


class CVUploadStatus(models.TextChoices):
    UPLOADED = 'uploaded', 'uploaded'
    FAILED = 'failed', 'failed'


class CVFile(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='cv_files',
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='cv_files',
    )
    source_type = models.CharField(
        max_length=20,
        choices=CVSourceType.choices,
        default=CVSourceType.UPLOAD,
    )
    storage_path = models.TextField()
    original_filename = models.TextField()
    mime_type = models.TextField(null=True, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    checksum = models.TextField(null=True, blank=True)
    upload_status = models.CharField(
        max_length=20,
        choices=CVUploadStatus.choices,
        default=CVUploadStatus.UPLOADED,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cv_files'
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'id'],
                name='cv_files_org_id_unique',
            ),
        ]


class CVParseStatus(models.TextChoices):
    PENDING = 'pending', 'pending'
    SUCCEEDED = 'succeeded', 'succeeded'
    FAILED = 'failed', 'failed'


class CVParse(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='cv_parses',
    )
    cv_file = models.ForeignKey(
        CVFile,
        on_delete=models.CASCADE,
        related_name='cv_parses',
    )
    parse_status = models.CharField(
        max_length=20,
        choices=CVParseStatus.choices,
        default=CVParseStatus.PENDING,
    )
    parser_name = models.TextField(null=True, blank=True)
    parser_version = models.TextField(null=True, blank=True)
    parsed_at = models.DateTimeField(null=True, blank=True)
    text_content = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'cv_parses'
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'id'],
                name='cv_parses_org_id_unique',
            ),
        ]


class CandidateStructuredData(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='candidate_structured_data',
    )
    cv_parse = models.ForeignKey(
        CVParse,
        on_delete=models.CASCADE,
        related_name='structured_data',
    )
    structured_json = models.JSONField(default=dict)
    headline = models.TextField(null=True, blank=True)
    primary_location = models.TextField(null=True, blank=True)
    top_skills = models.TextField(null=True, blank=True)
    experience_years = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'candidate_structured_data'
        constraints = [
            models.UniqueConstraint(
                fields=['cv_parse'],
                name='candidate_structured_data_cv_parse_unique',
            ),
            models.UniqueConstraint(
                fields=['organization', 'id'],
                name='candidate_structured_data_org_id_unique',
            ),
        ]


class SummaryStatus(models.TextChoices):
    PENDING = 'pending', 'pending'
    SUCCEEDED = 'succeeded', 'succeeded'
    FAILED = 'failed', 'failed'


class CandidateSummary(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='candidate_summaries',
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='summaries',
    )
    cv_parse = models.ForeignKey(
        CVParse,
        on_delete=models.SET_NULL,
        related_name='summaries',
        null=True,
        blank=True,
    )
    summary_status = models.CharField(
        max_length=20,
        choices=SummaryStatus.choices,
        default=SummaryStatus.PENDING,
    )
    language = models.TextField(default='hu')
    model_name = models.TextField(null=True, blank=True)
    model_version = models.TextField(null=True, blank=True)
    prompt_version = models.TextField(null=True, blank=True)
    summary_text = models.TextField(null=True, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'candidate_summaries'
        indexes = [
            models.Index(fields=['candidate'], name='cand_sum_cand_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'id'],
                name='candidate_summaries_org_id_unique',
            ),
        ]


class RankingRunStatus(models.TextChoices):
    PENDING = 'pending', 'pending'
    RUNNING = 'running', 'running'
    COMPLETED = 'completed', 'completed'
    FAILED = 'failed', 'failed'


class RankingRun(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='ranking_runs',
    )
    created_by_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='ranking_runs',
        null=True,
        blank=True,
    )
    criteria_json = models.JSONField()
    bias_config_json = models.JSONField(null=True, blank=True)
    model_name = models.TextField(null=True, blank=True)
    model_version = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=RankingRunStatus.choices,
        default=RankingRunStatus.PENDING,
    )
    notes = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ranking_runs'
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'id'],
                name='ranking_runs_org_id_unique',
            ),
        ]


class CandidateScore(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='candidate_scores',
    )
    ranking_run = models.ForeignKey(
        RankingRun,
        on_delete=models.CASCADE,
        related_name='candidate_scores',
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='candidate_scores',
    )
    score = models.DecimalField(max_digits=6, decimal_places=2)
    rank = models.IntegerField(null=True, blank=True)
    details_json = models.JSONField(null=True, blank=True)
    explanation = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'candidate_scores'
        constraints = [
            models.UniqueConstraint(
                fields=['ranking_run', 'candidate'],
                name='candidate_scores_run_candidate_unique',
            ),
            models.UniqueConstraint(
                fields=['organization', 'id'],
                name='candidate_scores_org_id_unique',
            ),
        ]


class SearchEntityType(models.TextChoices):
    CANDIDATE = 'candidate', 'candidate'
    CV_PARSE = 'cv_parse', 'cv_parse'
    OTHER = 'other', 'other'


class SearchIndexBackend(models.TextChoices):
    ELASTICSEARCH = 'elasticsearch', 'elasticsearch'
    OPENSEARCH = 'opensearch', 'opensearch'
    OTHER = 'other', 'other'


class SearchIndexStatus(models.TextChoices):
    PENDING = 'pending', 'pending'
    INDEXED = 'indexed', 'indexed'
    FAILED = 'failed', 'failed'


class SearchDocument(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='search_documents',
    )
    entity_type = models.CharField(max_length=20, choices=SearchEntityType.choices)
    entity_id = models.UUIDField()
    source_text = models.TextField(null=True, blank=True)
    embedding_json = models.JSONField(null=True, blank=True)
    embedding = VectorField(dimensions=384, null=True, blank=True)
    index_backend = models.CharField(
        max_length=20,
        choices=SearchIndexBackend.choices,
        default=SearchIndexBackend.ELASTICSEARCH,
    )
    index_status = models.CharField(
        max_length=20,
        choices=SearchIndexStatus.choices,
        default=SearchIndexStatus.PENDING,
    )
    indexed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'search_documents'
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'entity_type', 'entity_id'],
                name='search_documents_org_entity_unique',
            ),
            models.UniqueConstraint(
                fields=['organization', 'id'],
                name='search_documents_org_id_unique',
            ),
        ]


class CVAccessAction(models.TextChoices):
    VIEWED = 'viewed', 'viewed'
    FORWARDED = 'forwarded', 'forwarded'
    UPLOADED = 'uploaded', 'uploaded'
    PARSE_STARTED = 'parse_started', 'parse_started'
    PARSE_FINISHED = 'parse_finished', 'parse_finished'
    RANKED = 'ranked', 'ranked'
    SEARCHED = 'searched', 'searched'
    SUMMARY_GENERATED = 'summary_generated', 'summary_generated'


class CVAccessEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='cv_access_events',
    )
    actor_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='cv_access_events',
        null=True,
        blank=True,
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='cv_access_events',
    )
    cv_file = models.ForeignKey(
        CVFile,
        on_delete=models.SET_NULL,
        related_name='cv_access_events',
        null=True,
        blank=True,
    )
    cv_parse = models.ForeignKey(
        CVParse,
        on_delete=models.SET_NULL,
        related_name='cv_access_events',
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=30, choices=CVAccessAction.choices)
    channel = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cv_access_events'
        indexes = [
            models.Index(
                fields=['organization', 'created_at'],
                name='cv_access_org_created_idx',
            ),
            models.Index(
                fields=['candidate', 'created_at'],
                name='cv_access_cand_created_idx',
            ),
        ]


class AuditSeverity(models.TextChoices):
    LOG = 'log', 'log'
    DEBUG = 'debug', 'debug'
    VERBOSE = 'verbose', 'verbose'


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='audit_logs',
    )
    actor_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        null=True,
        blank=True,
    )
    severity = models.CharField(
        max_length=20,
        choices=AuditSeverity.choices,
        default=AuditSeverity.LOG,
    )
    event_type = models.TextField()
    entity_type = models.TextField()
    entity_id = models.UUIDField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(
                fields=['organization', 'created_at'],
                name='audit_logs_org_created_idx',
            ),
            models.Index(
                fields=['event_type', 'created_at'],
                name='audit_logs_event_created_idx',
            ),
        ]
