import os
import sys
sys.path.insert(0, '/app/cv_filter')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_filter.settings')

import django
django.setup()

from accounts.models import User, AuditLog

admin = User.objects.get(username='admin')
org = admin.organization

print("=== ALL EVENT TYPES ===")
all_events = AuditLog.objects.filter(organization=org).values_list('event_type', flat=True).distinct()
for event in sorted(all_events):
    count = AuditLog.objects.filter(organization=org, event_type=event).count()
    print(f"  {event}: {count}")

print("\n=== BUSINESS EVENTS (excluding http.*) ===")
business_events = AuditLog.objects.filter(organization=org).exclude(event_type__startswith='http.')
print(f"Total: {business_events.count()}")

if business_events.count() == 0:
    print("\n⚠️ No business events found. Only http.* events exist.")
    print("Creating sample events for testing...")
    
    from accounts.logging_service import AuditLogService
    import uuid
    
    # Create sample ranking event with valid UUID
    run_id = uuid.uuid4()
    AuditLogService.log(
        organization=org,
        event_type='ranking.run.started',
        entity_type='ranking_run',
        entity_id=run_id,
        description='Started ranking for Senior Python Developer role',
        metadata={'role': 'Senior Python Developer', 'candidate_count': 5, 'criteria': ['skills', 'experience']}
    )
    
    # Create sample CV event
    AuditLogService.log(
        organization=org,
        event_type='cv.uploaded',
        entity_type='cv_file',
        entity_id=uuid.uuid4(),
        description='Uploaded CV for John Doe',
        metadata={'filename': 'john_doe.pdf', 'size_bytes': 245678}
    )
    
    print("✅ Created 2 sample events")
else:
    print("\nSample events:")
    for log in business_events.order_by('-created_at')[:5]:
        print(f"  [{log.severity}] {log.event_type} - {log.description}")
