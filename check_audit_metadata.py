import os
import sys
import json
sys.path.insert(0, '/app/cv_filter')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_filter.settings')

import django
django.setup()

from accounts.models import AuditLog

# Get all business events (excluding http.*)
logs = AuditLog.objects.exclude(event_type__startswith='http.').order_by('-created_at')
print(f'Found {logs.count()} business audit events\n')

for i, log in enumerate(logs[:10]):
    print(f'Event {i+1}:')
    print(f'  Event Type: {log.event_type}')
    print(f'  Created at: {log.created_at}')
    print(f'  Description: {log.description}')
    print(f'  Metadata: {json.dumps(log.metadata, indent=4, default=str)}')
    print()
