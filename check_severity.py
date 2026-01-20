import os
import sys
sys.path.insert(0, '/app/cv_filter')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_filter.settings')

import django
django.setup()

from accounts.models import User, AuditLog
from django.db.models import Count

admin = User.objects.get(username='admin')
logs = AuditLog.objects.filter(organization=admin.organization)

print("Severity distribution:")
severities = logs.values('severity').annotate(count=Count('id')).order_by('-count')
for s in severities:
    print(f"  {s['severity']}: {s['count']}")

print("\nSample events with severity:")
samples = logs.order_by('-created_at')[:10]
for log in samples:
    print(f"  [{log.severity}] {log.event_type}")
