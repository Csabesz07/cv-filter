import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_filter.settings')
django.setup()

from accounts.models import AuditLog
from django.db.models import Count

print("=" * 80)
print("AUDIT LOG ANALYSIS")
print("=" * 80)

total = AuditLog.objects.count()
print(f"\n📊 Total audit logs: {total}")

print("\n📋 Event types (top 10):")
events = AuditLog.objects.values('event_type').annotate(count=Count('id')).order_by('-count')[:10]
for event in events:
    print(f"  - {event['event_type']}: {event['count']}")

print("\n⚠️ Ranking events:")
ranking_events = AuditLog.objects.filter(event_type__startswith='ranking.').count()
print(f"  Total: {ranking_events}")

ranking_types = AuditLog.objects.filter(event_type__startswith='ranking.').values('event_type').annotate(count=Count('id')).order_by('-count')
for event in ranking_types:
    print(f"  - {event['event_type']}: {event['count']}")

print("\n🔍 Recent 5 events:")
recent = AuditLog.objects.order_by('-created_at')[:5]
for log in recent:
    print(f"  [{log.created_at.strftime('%Y-%m-%d %H:%M')}] {log.event_type} - {log.description[:60]}")

print("\n" + "=" * 80)
