"""
Audit logging and access tracking service.
Provides unified interface for logging user activities and system events.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    AuditLog,
    AuditSeverity,
    CVAccessEvent,
    CVAccessAction,
    Organization,
    Candidate,
    CVFile,
    CVParse,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class AuditLogService:
    """
    Service for creating and managing audit logs.
    Supports 3 severity levels: LOG, DEBUG, VERBOSE
    """

    @staticmethod
    def log(
        organization: Organization,
        event_type: str,
        entity_type: str,
        description: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        actor_user: Any = None,  # User model instance
        metadata: Optional[Dict[str, Any]] = None,
        severity: str = AuditSeverity.LOG,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            organization: Organization the event belongs to
            event_type: Type of event (e.g., 'user.login', 'cv.upload')
            entity_type: Type of entity affected (e.g., 'user', 'cv_file')
            description: Human-readable description
            entity_id: UUID of the affected entity
            actor_user: User who performed the action
            metadata: Additional structured data
            severity: Log severity level (LOG, DEBUG, VERBOSE)

        Returns:
            Created AuditLog instance
        """
        try:
            audit_log = AuditLog.objects.create(
                organization=organization,
                actor_user=actor_user,
                severity=severity,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description or f"{event_type} on {entity_type}",
                metadata=metadata or {},
            )

            # Also log to Python logging system
            log_message = (
                f"[{severity}] {event_type} | "
                f"org={organization.slug} | "
                f"user={actor_user.username if actor_user else 'system'} | "
                f"entity={entity_type}:{entity_id}"
            )

            if severity == AuditSeverity.VERBOSE:
                logger.debug(log_message)
            elif severity == AuditSeverity.DEBUG:
                logger.info(log_message)
            else:  # LOG
                logger.info(log_message)

            return audit_log

        except Exception as e:
            logger.exception(f"Failed to create audit log: {str(e)}")
            raise

    @staticmethod
    def log_user_action(
        organization: Organization,
        user: Any,  # User model instance
        action: str,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Convenience method for logging user actions with LOG severity.
        """
        return AuditLogService.log(
            organization=organization,
            event_type=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user=user,
            description=description,
            metadata=metadata,
            severity=AuditSeverity.LOG,
        )

    @staticmethod
    def debug(
        organization: Organization,
        event_type: str,
        entity_type: str,
        description: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        actor_user: Any = None,  # User model instance
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Create a DEBUG level audit log entry.
        Used for detailed operational information.
        """
        return AuditLogService.log(
            organization=organization,
            event_type=event_type,
            entity_type=entity_type,
            description=description,
            entity_id=entity_id,
            actor_user=actor_user,
            metadata=metadata,
            severity=AuditSeverity.DEBUG,
        )

    @staticmethod
    def verbose(
        organization: Organization,
        event_type: str,
        entity_type: str,
        description: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        actor_user: Any = None,  # User model instance
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Create a VERBOSE level audit log entry.
        Used for very detailed diagnostic information.
        """
        return AuditLogService.log(
            organization=organization,
            event_type=event_type,
            entity_type=entity_type,
            description=description,
            entity_id=entity_id,
            actor_user=actor_user,
            metadata=metadata,
            severity=AuditSeverity.VERBOSE,
        )

    @staticmethod
    def query_logs(
        organization: Organization,
        event_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        actor_user: Any = None,  # User model instance
        severity: Optional[str] = None,
        limit: int = 100,
    ):
        """
        Query audit logs with filters.

        Args:
            organization: Organization to filter by
            event_type: Optional event type filter
            entity_type: Optional entity type filter
            actor_user: Optional user filter
            severity: Optional severity filter
            limit: Maximum number of results

        Returns:
            QuerySet of AuditLog objects
        """
        queryset = AuditLog.objects.filter(organization=organization)

        if event_type:
            queryset = queryset.filter(event_type=event_type)

        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)

        if actor_user:
            queryset = queryset.filter(actor_user=actor_user)

        if severity:
            queryset = queryset.filter(severity=severity)

        return queryset.order_by('-created_at')[:limit]


class CVAccessEventService:
    """
    Service for tracking CV access and processing events.
    Provides detailed activity tracking for compliance.
    """

    @staticmethod
    def log_event(
        organization: Organization,
        action: str,
        candidate: Candidate,
        actor_user: Any = None,  # User model instance
        cv_file: Optional[CVFile] = None,
        cv_parse: Optional[CVParse] = None,
        channel: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CVAccessEvent:
        """
        Log a CV access event.

        Args:
            organization: Organization
            action: Action type (from CVAccessAction enum)
            candidate: Candidate being accessed
            actor_user: User performing the action
            cv_file: Related CV file (if applicable)
            cv_parse: Related CV parse (if applicable)
            channel: Channel through which action occurred (e.g., 'web', 'api')
            metadata: Additional data

        Returns:
            Created CVAccessEvent instance
        """
        try:
            event = CVAccessEvent.objects.create(
                organization=organization,
                actor_user=actor_user,
                candidate=candidate,
                cv_file=cv_file,
                cv_parse=cv_parse,
                action=action,
                channel=channel or 'api',
                metadata=metadata or {},
            )

            # Also create audit log for important events
            important_actions = [
                CVAccessAction.UPLOADED,
                CVAccessAction.VIEWED,
                CVAccessAction.RANKED,
                CVAccessAction.PARSE_STARTED,
                CVAccessAction.PARSE_FINISHED,
                CVAccessAction.SEARCHED,
                CVAccessAction.SUMMARY_GENERATED,
            ]
            
            if action in important_actions:
                AuditLogService.log(
                    organization=organization,
                    event_type=f"cv.{action.lower()}",
                    entity_type='cv_file' if cv_file else 'candidate',
                    entity_id=cv_file.id if cv_file else candidate.id,
                    actor_user=actor_user,
                    description=f"CV {action.lower().replace('_', ' ')} for {candidate.first_name} {candidate.last_name}",
                    metadata={
                        'cv_file_id': str(cv_file.id) if cv_file else None,
                        'cv_parse_id': str(cv_parse.id) if cv_parse else None,
                        'candidate_name': f"{candidate.first_name} {candidate.last_name}",
                        'filename': cv_file.original_filename if cv_file else None,
                        'action': action,
                    },
                    severity=AuditSeverity.LOG,
                )

            return event

        except Exception as e:
            logger.exception(f"Failed to create CV access event: {str(e)}")
            raise

    @staticmethod
    def log_cv_upload(
        organization: Organization,
        candidate: Candidate,
        cv_file: CVFile,
        actor_user: Any,  # User model instance
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CVAccessEvent:
        """Log CV upload event."""
        return CVAccessEventService.log_event(
            organization=organization,
            action=CVAccessAction.UPLOADED,
            candidate=candidate,
            cv_file=cv_file,
            actor_user=actor_user,
            channel='api',
            metadata=metadata,
        )

    @staticmethod
    def log_cv_view(
        organization: Organization,
        candidate: Candidate,
        cv_file: CVFile,
        actor_user: Any,  # User model instance
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CVAccessEvent:
        """Log CV view event."""
        return CVAccessEventService.log_event(
            organization=organization,
            action=CVAccessAction.VIEWED,
            candidate=candidate,
            cv_file=cv_file,
            actor_user=actor_user,
            channel='web',
            metadata=metadata,
        )

    @staticmethod
    def log_parse_started(
        organization: Organization,
        candidate: Candidate,
        cv_file: CVFile,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CVAccessEvent:
        """Log CV parse start event."""
        return CVAccessEventService.log_event(
            organization=organization,
            action=CVAccessAction.PARSE_STARTED,
            candidate=candidate,
            cv_file=cv_file,
            actor_user=None,  # System action
            channel='system',
            metadata=metadata,
        )

    @staticmethod
    def log_parse_finished(
        organization: Organization,
        candidate: Candidate,
        cv_file: CVFile,
        cv_parse: CVParse,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CVAccessEvent:
        """Log CV parse completion event."""
        return CVAccessEventService.log_event(
            organization=organization,
            action=CVAccessAction.PARSE_FINISHED,
            candidate=candidate,
            cv_file=cv_file,
            cv_parse=cv_parse,
            actor_user=None,  # System action
            channel='system',
            metadata=metadata,
        )

    @staticmethod
    def log_ranking(
        organization: Organization,
        candidate: Candidate,
        actor_user: Any,  # User model instance
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CVAccessEvent:
        """Log candidate ranking event."""
        return CVAccessEventService.log_event(
            organization=organization,
            action=CVAccessAction.RANKED,
            candidate=candidate,
            actor_user=actor_user,
            channel='api',
            metadata=metadata,
        )

    @staticmethod
    def query_events(
        organization: Organization,
        candidate: Optional[Candidate] = None,
        actor_user: Any = None,  # User model instance
        action: Optional[str] = None,
        limit: int = 100,
    ):
        """
        Query CV access events with filters.

        Args:
            organization: Organization to filter by
            candidate: Optional candidate filter
            actor_user: Optional user filter
            action: Optional action filter
            limit: Maximum number of results

        Returns:
            QuerySet of CVAccessEvent objects
        """
        queryset = CVAccessEvent.objects.filter(organization=organization)

        if candidate:
            queryset = queryset.filter(candidate=candidate)

        if actor_user:
            queryset = queryset.filter(actor_user=actor_user)

        if action:
            queryset = queryset.filter(action=action)

        return queryset.order_by('-created_at')[:limit]
