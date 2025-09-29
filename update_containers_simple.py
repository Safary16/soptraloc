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

# Get today and tomorrow
today = timezone.now().date()
tomorrow = today + timedelta(days=1)

print(f"Today: {today}")
print(f"Tomorrow: {tomorrow}")

# Find containers to update
all_containers = Container.objects.all().order_by('id')[:10]
print(f"Found {all_containers.count()} containers to update")

updated_count = 0
for i, container in enumerate(all_containers):
    if i < 5:
        # First 5 for today
        container.scheduled_date = today
        container.scheduled_time = time(9, 0)
        container.status = 'PROGRAMADO'
        new_date = today
    else:
        # Next 5 for tomorrow
        container.scheduled_date = tomorrow
        container.scheduled_time = time(10, 0) 
        container.status = 'PROGRAMADO'
        new_date = tomorrow
    
    container.save()
    updated_count += 1
    print(f'Updated {container.container_number}: {new_date} {container.scheduled_time} - {container.status}')

print(f'\nSummary:')
print(f'Updated {updated_count} containers')
print(f'Today ({today}): {Container.objects.filter(scheduled_date=today).count()}')
print(f'Tomorrow ({tomorrow}): {Container.objects.filter(scheduled_date=tomorrow).count()}')
print(f'PROGRAMADO status: {Container.objects.filter(status="PROGRAMADO").count()}')