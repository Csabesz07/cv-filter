"""
Middleware for automatic audit logging of HTTP requests.
Tracks user activities and API calls for transparency and compliance.
"""

import json
import logging
import time
from typing import Optional

from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from .logging_service import AuditLogService
from .models import AuditSeverity

logger = logging.getLogger(__name__)
User = get_user_model()


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware that automatically logs HTTP requests to the audit log.
    Supports 3 logging levels based on configuration:
    - LOG: Important actions (POST, PUT, DELETE, PATCH)
    - DEBUG: All API calls including GET
    - VERBOSE: All requests with full details
    """

    # Actions that should always be logged at LOG level
    IMPORTANT_ACTIONS = ['POST', 'PUT', 'DELETE', 'PATCH']

    # Paths that should be excluded from logging
    EXCLUDED_PATHS = [
        '/admin/jsi18n/',
        '/static/',
        '/favicon.ico',
    ]

    # Sensitive fields to redact from logs
    SENSITIVE_FIELDS = ['password', 'password_hash', 'token', 'access', 'refresh']

    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def process_request(self, request: HttpRequest):
        """Store request start time."""
        request._audit_start_time = time.time()
        return None

    def process_response(self, request: HttpRequest, response: HttpResponse):
        """
        Log the request after processing.
        """
        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return response

        # Get logging level from settings
        from django.conf import settings
        log_level = getattr(settings, 'AUDIT_LOG_LEVEL', 'LOG')

        # Determine if we should log this request
        should_log = self._should_log_request(request, log_level)

        if should_log:
            try:
                self._create_audit_log(request, response, log_level)
            except Exception as e:
                # Never let logging break the application
                logger.exception(f"Failed to create audit log: {str(e)}")

        return response

    def _should_log_request(self, request: HttpRequest, log_level: str) -> bool:
        """
        Determine if request should be logged based on level.

        Args:
            request: HTTP request
            log_level: Current logging level (LOG, DEBUG, VERBOSE)

        Returns:
            True if request should be logged
        """
        # VERBOSE logs everything
        if log_level == 'VERBOSE':
            return True

        # DEBUG logs all API calls
        if log_level == 'DEBUG':
            return request.path.startswith('/api/')

        # LOG level logs important actions only
        if log_level == 'LOG':
            return (
                request.method in self.IMPORTANT_ACTIONS
                and request.path.startswith('/api/')
            )

        return False

    def _create_audit_log(
        self, request: HttpRequest, response: HttpResponse, log_level: str
    ):
        """
        Create audit log entry for the request.

        Args:
            request: HTTP request
            response: HTTP response
            log_level: Logging level
        """
        # Get user and organization
        user = request.user if request.user.is_authenticated else None
        organization = user.organization if user and hasattr(user, 'organization') else None

        # Skip if no organization
        if not organization:
            return

        # Calculate request duration
        duration_ms = None
        if hasattr(request, '_audit_start_time'):
            duration_ms = int((time.time() - request._audit_start_time) * 1000)

        # Determine event type
        event_type = f"http.{request.method.lower()}"

        # Extract entity information from path
        entity_type = self._extract_entity_type(request.path)

        # Build metadata
        metadata = {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': duration_ms,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
        }

        # Add request data for VERBOSE level
        if log_level == 'VERBOSE':
            metadata['query_params'] = dict(request.GET)
            metadata['request_body'] = self._get_safe_request_body(request)

        # Add response data for failed requests
        if response.status_code >= 400:
            metadata['error'] = True

        # Determine description
        description = f"{request.method} {request.path} - {response.status_code}"

        # Map log level to severity
        severity = self._map_log_level_to_severity(log_level)

        # Create audit log
        AuditLogService.log(
            organization=organization,
            event_type=event_type,
            entity_type=entity_type,
            description=description,
            actor_user=user,
            metadata=metadata,
            severity=severity,
        )

    def _extract_entity_type(self, path: str) -> str:
        """
        Extract entity type from request path.

        Args:
            path: Request path

        Returns:
            Entity type string
        """
        # Map common path patterns to entity types
        if '/cv/' in path or '/upload/' in path:
            return 'cv_file'
        elif '/ranking/' in path:
            return 'ranking'
        elif '/candidate/' in path:
            return 'candidate'
        elif '/user/' in path or '/auth/' in path:
            return 'user'
        else:
            return 'http_request'

    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Get client IP address from request.

        Args:
            request: HTTP request

        Returns:
            IP address string
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def _get_safe_request_body(self, request: HttpRequest) -> Optional[dict]:
        """
        Get request body with sensitive data redacted.

        Args:
            request: HTTP request

        Returns:
            Safe request body or None
        """
        try:
            # Only process JSON bodies
            content_type = request.META.get('CONTENT_TYPE', '')
            if 'application/json' not in content_type:
                return None

            # Parse body
            if hasattr(request, 'body') and request.body:
                body = json.loads(request.body)

                # Redact sensitive fields
                if isinstance(body, dict):
                    return self._redact_sensitive_data(body)

                return body

        except Exception:
            return None

        return None

    def _redact_sensitive_data(self, data: dict) -> dict:
        """
        Redact sensitive fields from dictionary.

        Args:
            data: Dictionary to redact

        Returns:
            Redacted dictionary
        """
        redacted = {}
        for key, value in data.items():
            if key.lower() in self.SENSITIVE_FIELDS:
                redacted[key] = '***REDACTED***'
            elif isinstance(value, dict):
                redacted[key] = self._redact_sensitive_data(value)
            else:
                redacted[key] = value
        return redacted

    def _map_log_level_to_severity(self, log_level: str) -> str:
        """
        Map configuration log level to AuditSeverity.

        Args:
            log_level: Configuration log level

        Returns:
            AuditSeverity value
        """
        mapping = {
            'VERBOSE': AuditSeverity.VERBOSE,
            'DEBUG': AuditSeverity.DEBUG,
            'LOG': AuditSeverity.LOG,
        }
        return mapping.get(log_level, AuditSeverity.LOG)
