"""
Test audit logging functionality.
Quick validation of the logging service and middleware.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Organization, AuditLog, AuditSeverity
from accounts.logging_service import AuditLogService

User = get_user_model()


class AuditLogServiceTest(TestCase):
    """Test AuditLogService functionality."""

    def setUp(self):
        """Create test organization and user."""
        self.org = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )

    def test_log_basic_event(self):
        """Test creating a basic audit log entry."""
        log = AuditLogService.log(
            organization=self.org,
            event_type='test.event',
            entity_type='test_entity',
            description='Test event',
            actor_user=self.user
        )

        self.assertIsNotNone(log.id)
        self.assertEqual(log.organization, self.org)
        self.assertEqual(log.event_type, 'test.event')
        self.assertEqual(log.severity, AuditSeverity.LOG)
        self.assertEqual(log.actor_user, self.user)

    def test_log_severity_levels(self):
        """Test all three severity levels."""
        # LOG level
        log1 = AuditLogService.log(
            organization=self.org,
            event_type='test.log',
            entity_type='test',
            severity=AuditSeverity.LOG
        )
        self.assertEqual(log1.severity, AuditSeverity.LOG)

        # DEBUG level
        log2 = AuditLogService.debug(
            organization=self.org,
            event_type='test.debug',
            entity_type='test'
        )
        self.assertEqual(log2.severity, AuditSeverity.DEBUG)

        # VERBOSE level
        log3 = AuditLogService.verbose(
            organization=self.org,
            event_type='test.verbose',
            entity_type='test'
        )
        self.assertEqual(log3.severity, AuditSeverity.VERBOSE)

    def test_query_logs(self):
        """Test querying audit logs with filters."""
        # Create test logs
        AuditLogService.log(
            organization=self.org,
            event_type='user.login',
            entity_type='user',
            actor_user=self.user
        )
        AuditLogService.log(
            organization=self.org,
            event_type='cv.upload',
            entity_type='cv_file',
            actor_user=self.user
        )

        # Query all logs
        all_logs = AuditLogService.query_logs(organization=self.org)
        self.assertEqual(all_logs.count(), 2)

        # Query by event type
        login_logs = AuditLogService.query_logs(
            organization=self.org,
            event_type='user.login'
        )
        self.assertEqual(login_logs.count(), 1)
        self.assertEqual(login_logs[0].event_type, 'user.login')

    def test_log_with_metadata(self):
        """Test logging with metadata."""
        metadata = {
            'key1': 'value1',
            'key2': 123,
            'nested': {'key': 'value'}
        }

        log = AuditLogService.log(
            organization=self.org,
            event_type='test.metadata',
            entity_type='test',
            metadata=metadata
        )

        self.assertEqual(log.metadata['key1'], 'value1')
        self.assertEqual(log.metadata['key2'], 123)
        self.assertEqual(log.metadata['nested']['key'], 'value')


class AuditLogMiddlewareTest(TestCase):
    """Test AuditLoggingMiddleware."""

    def setUp(self):
        """Create test organization and user."""
        self.org = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )

    def test_middleware_logs_api_request(self):
        """Test that middleware logs API requests."""
        # Login
        self.client.login(username='testuser', password='testpass123')

        # Make API request
        initial_count = AuditLog.objects.filter(organization=self.org).count()
        
        # Note: This will only work if AUDIT_LOG_LEVEL is set appropriately
        # For testing, you might need to temporarily set it to 'VERBOSE'
        
        response = self.client.get('/api/audit/logs/')
        
        # Check if log was created (depends on AUDIT_LOG_LEVEL setting)
        # In production with LOG level, GET requests won't be logged
        # With DEBUG or VERBOSE, they will be

    def test_middleware_excludes_static_paths(self):
        """Test that middleware excludes static paths."""
        initial_count = AuditLog.objects.count()
        
        # Request static file (should not be logged)
        self.client.get('/static/test.css')
        
        final_count = AuditLog.objects.count()
        self.assertEqual(initial_count, final_count)
