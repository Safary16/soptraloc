#!/usr/bin/env python
import os
import sys
import django
from datetime import date, time, timedelta

# Setup Django
sys.path.insert(0, '/workspaces/soptraloc/soptraloc_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from apps.containers.models import Container

# Get containers scheduled for September 11
containers_sep11 = Container.objects.filter(scheduled_date='2025-09-11')
print(f'Containers scheduled for 2025-09-11: {containers_sep11.count()}')

if containers_sep11.count() == 0:
    print('No containers found for 2025-09-11, checking all scheduled dates...')
    all_scheduled = Container.objects.exclude(scheduled_date__isnull=True).values_list('scheduled_date', flat=True).distinct()
    print(f'Scheduled dates found: {list(all_scheduled)}')
    
    # Try with a different date that might exist
    containers_sep11 = Container.objects.filter(scheduled_date__month=9, scheduled_date__day=11)
    print(f'Containers scheduled for day 11 of any September: {containers_sep11.count()}')

# Update dates: some for today, some for tomorrow  
today = timezone.now().date()
tomorrow = today + timedelta(days=1)

# Update containers
containers = list(containers_sep11[:10])  # Limit to first 10 for testing
half = len(containers) // 2

updated_count = 0
for i, container in enumerate(containers):
    if i < half:
        container.scheduled_date = today
        container.scheduled_time = time(9, 0)  # 9:00 AM
        new_date = today
    else:
        container.scheduled_date = tomorrow
        container.scheduled_time = time(10, 0)  # 10:00 AM
        new_date = tomorrow
    
    container.save()
    updated_count += 1
    print(f'Updated {container.container_number}: {new_date} {container.scheduled_time}')

print(f'Updated {updated_count} containers')
print(f'Today ({today}): {Container.objects.filter(scheduled_date=today).count()}')
print(f'Tomorrow ({tomorrow}): {Container.objects.filter(scheduled_date=tomorrow).count()}')