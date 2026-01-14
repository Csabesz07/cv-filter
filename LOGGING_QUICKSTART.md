"""
Quick Start Guide: Audit Logging & Transparency
================================================

This guide shows how to use the audit logging system in the CV Filter application.

## 1. Configuration

Set the logging level in environment variables or settings.py:

```bash
# .env file
AUDIT_LOG_LEVEL=LOG      # Production: only important actions
AUDIT_LOG_LEVEL=DEBUG    # Development: all API calls
AUDIT_LOG_LEVEL=VERBOSE  # Debugging: everything with full details
```

## 2. Automatic Logging

The system automatically logs:

✓ All HTTP requests (based on log level)
✓ CV uploads
✓ Ranking runs
✓ User actions

No code changes needed - middleware handles it automatically!

## 3. Manual Logging

Use the service when you need explicit logging:

```python
from accounts.logging_service import AuditLogService

# Log user action
AuditLogService.log_user_action(
    organization=request.user.organization,
    user=request.user,
    action='custom.action',
    entity_type='custom_entity',
    entity_id=entity.id,
    description='User performed custom action'
)

# Debug logging (development)
AuditLogService.debug(
    organization=org,
    event_type='api.debug',
    entity_type='endpoint',
    description='Debugging API endpoint'
)

# Verbose logging (troubleshooting)
AuditLogService.verbose(
    organization=org,
    event_type='system.trace',
    entity_type='background_job',
    metadata={'full': 'details', 'here': True}
)
```

## 4. CV Access Logging

Track CV-specific events:

```python
from accounts.logging_service import CVAccessEventService

# Log CV view
CVAccessEventService.log_cv_view(
    organization=org,
    candidate=candidate,
    cv_file=cv_file,
    actor_user=request.user
)

# Log ranking
CVAccessEventService.log_ranking(
    organization=org,
    candidate=candidate,
    actor_user=request.user,
    metadata={'ranking_score': 95.5}
)
```

## 5. Query Logs via API

### Get Audit Logs

```bash
# All logs for your organization
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/audit/logs/

# Filter by event type
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/audit/logs/?event_type=cv_access.uploaded"

# Filter by severity
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/audit/logs/?severity=debug&limit=50"
```

### Get CV Access Events

```bash
# All CV access events
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/audit/events/

# For specific candidate
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/audit/events/?candidate_id=<UUID>"

# Filter by action
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/audit/events/?action=viewed"
```

## 6. Understanding Log Levels

### LOG (Production)
- Only important actions: POST, PUT, DELETE, PATCH
- Only API endpoints
- Minimal performance impact
- **Use for production**

Example logs:
- User login/logout
- CV uploads
- Ranking runs
- Data modifications

### DEBUG (Development)
- All API calls including GET
- More detailed information
- Moderate performance impact
- **Use for development/testing**

Example logs:
- All LOG events
- API queries
- Search requests
- Data retrievals

### VERBOSE (Troubleshooting)
- EVERY HTTP request
- Full request/response details
- Request body included (sensitive data redacted)
- Significant performance impact
- **Use only for debugging**

Example logs:
- All DEBUG events
- Static file requests
- Full query parameters
- Response status codes
- Request duration

## 7. Security Features

✓ **Sensitive data redaction**: Passwords, tokens automatically hidden
✓ **Organization isolation**: Can only see your own logs
✓ **Read-only API**: Cannot modify past logs
✓ **Rate limiting**: Max 1000 results per query

## 8. Common Use Cases

### Compliance Audit
```python
# Get all CV views in the last month
logs = AuditLogService.query_logs(
    organization=org,
    event_type='cv_access.viewed',
    limit=1000
)
```

### Debug User Issue
```bash
# Set VERBOSE logging temporarily
AUDIT_LOG_LEVEL=VERBOSE

# Reproduce issue
# Check logs via API
curl http://localhost:8000/api/audit/logs/?limit=100

# Review full request details
```

### Track Specific Candidate
```bash
# Get all events for candidate
curl "http://localhost:8000/api/audit/events/?candidate_id=$CANDIDATE_ID"
```

## 9. Best Practices

1. **Production**: Use LOG level
2. **Development**: Use DEBUG level  
3. **Troubleshooting**: Temporarily use VERBOSE, then switch back
4. **Manual logging**: Add for critical business events
5. **Metadata**: Include relevant context in metadata field
6. **Review regularly**: Set up monitoring/alerts on logs

## 10. Performance Considerations

- LOG level: Minimal impact (~5ms per request)
- DEBUG level: Low impact (~10ms per request)
- VERBOSE level: Moderate impact (~20-50ms per request)

Database indexes ensure fast queries even with millions of logs.

## Examples in Production

### Example 1: CV Upload Tracking
```python
# In views.py - automatically logged by CVUploadView
cv_file = CVFile.objects.create(...)

CVAccessEventService.log_cv_upload(
    organization=org,
    candidate=candidate,
    cv_file=cv_file,
    actor_user=request.user,
    metadata={'file_size': file.size}
)
```

### Example 2: Ranking Run Audit
```python
# In ranking/views.py - automatically logged
run = service.start_and_execute_run(...)

AuditLogService.log(
    organization=org,
    event_type='ranking.created',
    entity_type='ranking_run',
    entity_id=run.id,
    actor_user=request.user,
    metadata={'criteria_count': len(criteria)}
)
```

### Example 3: Query User Activity
```bash
# Get all actions by specific user (via API)
curl "http://localhost:8000/api/audit/logs/" | \
  jq '.results[] | select(.actor_username=="johndoe")'
```

## Support

For issues or questions about audit logging:
1. Check logs directory: `cv_filter/logs/debug.log`
2. Review middleware: `accounts/middleware.py`
3. Check service: `accounts/logging_service.py`
4. Verify settings: `cv_filter/settings.py` -> AUDIT_LOG_LEVEL
