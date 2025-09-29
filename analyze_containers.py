#!/usr/bin/env python3

import os
import sys
import django

# Configurar Django
sys.path.append('/workspaces/soptraloc/soptraloc_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.containers.models import Container

def analyze_containers():
    print('=' * 50)
    print('ANÁLISIS EXHAUSTIVO DE CONTENEDORES')
    print('=' * 50)
    
    total = Container.objects.count()
    print(f'📦 Total contenedores: {total}')
    
    if total == 0:
        print('❌ NO HAY CONTENEDORES EN LA BASE DE DATOS')
        return
    
    print('\n📊 DISTRIBUCIÓN POR ESTADO:')
    print('-' * 30)
    states = ['PROGRAMADO', 'EN_PROCESO', 'EN_TRANSITO', 'LIBERADO', 'DESCARGADO', 'EN_SECUENCIA']
    for state in states:
        count = Container.objects.filter(status=state).count()
        print(f'  {state}: {count}')
    
    print('\n🔄 CONTENEDORES ACTIVOS/INACTIVOS:')
    print('-' * 35)
    activos = Container.objects.filter(is_active=True).count()
    inactivos = Container.objects.filter(is_active=False).count()
    print(f'  ✅ Activos: {activos}')
    print(f'  ❌ Inactivos: {inactivos}')
    
    print('\n📋 PRIMEROS 10 CONTENEDORES:')
    print('-' * 30)
    for i, c in enumerate(Container.objects.all()[:10], 1):
        status_icon = '✅' if c.is_active else '❌'
        print(f'  {i:2d}. {c.container_number} - Estado: {c.status} - Activo: {status_icon}')
    
    print('\n🔍 ANÁLISIS DE FILTROS EN VIEWS:')
    print('-' * 35)
    # Simular los filtros que usa la vista
    queryset_dashboard = Container.objects.filter(is_active=True)
    print(f'  📊 Dashboard (is_active=True): {queryset_dashboard.count()}')
    
    programados = Container.objects.filter(status='PROGRAMADO')
    print(f'  📅 Programados: {programados.count()}')
    
    print('\n🗂️ TODOS LOS ESTADOS ÚNICOS EN DB:')
    print('-' * 35)
    unique_states = Container.objects.values_list('status', flat=True).distinct()
    for state in unique_states:
        count = Container.objects.filter(status=state).count()
        print(f'  {state}: {count}')
    
    print('\n🏢 DISTRIBUCIÓN POR EMPRESA:')
    print('-' * 30)
    companies = Container.objects.values_list('owner_company__name', flat=True).distinct()
    for company in companies:
        if company:
            count = Container.objects.filter(owner_company__name=company).count()
            print(f'  {company}: {count}')
        else:
            count = Container.objects.filter(owner_company__isnull=True).count()
            print(f'  Sin empresa: {count}')

if __name__ == '__main__':
    analyze_containers()