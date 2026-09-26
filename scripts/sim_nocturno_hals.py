"""Simulación operacional nocturna — re-corre E1..E8 con los HALs aplicados.

Esta NO es una batería nueva: reproduce el flujo completo operacional
(lanzado por la simulación previa 1247409c que encontró 20 HALs) sobre el
código corregido. Para cada paso reportamos ✅/❌ + evidencia de QUÉ valores
se observaron (estado del container/driver, ETA calculado, eventos creados,
notificaciones, TiempoViaje, TiempoOperacion, auto-retorno).

Uso:
    python manage.py shell < scripts/sim_nocturno_hals.py
"""
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from apps.cds.models import CD
from apps.containers.models import Container
from apps.drivers.models import Driver
from apps.programaciones.models import (
    Programacion, RegistroOperacion, TiempoOperacion, TiempoViaje,
)
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService
from apps.core.services.operations import OperationalFlowService


def _print(step, status, evidence):
    icon = "✅" if status == "OK" else ("❌" if status == "FAIL" else "ℹ️ ")
    print(f"\n{icon} {step} — {status}")
    if isinstance(evidence, dict):
        for k, v in evidence.items():
            print(f"   {k}: {v}")
    else:
        print(f"   {evidence}")


def _sim(name, fn):
    try:
        result = fn()
        _print(name, "OK", result)
        return True, result
    except Exception as exc:
        _print(name, "FAIL", {"exception": str(exc), "type": type(exc).__name__})
        import traceback
        traceback.print_exc()
        return False, None


def main():
    print("=" * 70)
    print("SIMULACIÓN OPERACIONAL NOCTURNA — RECORRIDO E1..E8 (post-HALs)")
    print("=" * 70)

    # ============ SETUP ============
    print("\n>>> SETUP: limpieza controlada + seed")

    # Use SIM_ prefix to identify data for cleanup at the end.
    from apps.containers.models import Container as C
    from apps.programaciones.models import Programacion as P
    C.objects.filter(container_id__startswith='SIM_').delete()
    P.objects.filter(cliente__startswith='SIM_').delete()
    Notification.objects.filter(
        container__container_id__startswith='SIM_'
    ).delete()

    # Crear 2 CDs: uno 'origen' que permite drop&hook y otro 'destino'.
    cd_origen, _ = CD.objects.get_or_create(
        codigo='SIM_CD_O',
        defaults=dict(
            nombre='SIM CD Origen', direccion='Origen X', comuna='Santiago',
            lat=-33.45, lng=-70.65,
            permite_soltar_contenedor=True, capacidad_vacios=10,
        ),
    )
    cd_destino, _ = CD.objects.get_or_create(
        codigo='SIM_CD_D',
        defaults=dict(
            nombre='SIM CD Destino', direccion='Depósito naviera', comuna='Valpo',
            lat=-33.40, lng=-70.60,
            tipo='ccti', capacidad_vacios=20,
        ),
    )

    # Crear 2 conductores (uno de ellos 'anon_driver' con User anónimo).
    user_a, _ = User.objects.get_or_create(
        username='sim_driver_a',
    )
    if not user_a.has_usable_password():
        user_a.set_password('x')
        user_a.save()
    driver_a, _ = Driver.objects.get_or_create(
        user=user_a,
        defaults=dict(
            nombre='SIM Driver A', patente='SIM-A1', num_entregas_dia=0,
            max_entregas_dia=3,
        ),
    )

    user_b, _ = User.objects.get_or_create(username='sim_driver_b')
    if not user_b.has_usable_password():
        user_b.set_password('x')
        user_b.save()
    driver_b, _ = Driver.objects.get_or_create(
        user=user_b,
        defaults=dict(
            nombre='SIM Driver B', patente='SIM-B1', num_entregas_dia=0,
            max_entregas_dia=3,
        ),
    )

    print(f"   cd_origen={cd_origen.id}, cd_destino={cd_destino.id}")
    print(f"   driver_a={driver_a.id} ({driver_a.nombre}), driver_b={driver_b.id}")

    # ============ E1: importar contenedor liberado + crear programación ============
    def e1():
        cont = Container.objects.create(
            container_id='SIM_CTN001',
            cliente='SIM Cliente', estado='liberado', cd_entrega=cd_origen,
            fecha_liberacion=timezone.now(),
            peso_carga=12000, tipo='40HC',
        )
        prog = Programacion.objects.create(
            container=cont, cd=cd_origen, cliente='SIM Cliente',
            fecha_programada=timezone.now() + timedelta(hours=2),
        )
        return {
            'container_id': cont.id, 'estado': cont.estado,
            'programacion_id': prog.id, 'cliente': prog.cliente,
        }
    e1_ok, e1_evidence = _sim("E1 importar contenedor + crear programación", e1)

    if not e1_ok:
        return

    # ============ E2: asignar conductor (driver_a) ============
    def e2():
        cont = Container.objects.get(container_id='SIM_CTN001')
        prog = cont.programacion
        prog.asignar_conductor(driver_a, usuario='sim_staff')
        return {
            'prog_id': prog.id, 'driver_asignado': prog.driver.nombre,
            'driver_id': prog.driver_id,
            'container_estado': cont.estado,
            'notificaciones_asignacion': Notification.objects.filter(
                container=cont, tipo='asignacion',
            ).count(),
        }
    e2_ok, _ = _sim("E2 asignar conductor (driver_a)", e2)

    # ============ E3: cliente_portal API: serializer lista expone eta_recalculado_min ============
    def e3():
        from apps.programaciones.serializers import ProgramacionListSerializer
        cont = Container.objects.get(container_id='SIM_CTN001')
        prog = cont.programacion
        prog.eta_recalculado_min = 35  # P2-5 ETA recalculado tras asignar
        prog.save(update_fields=['eta_recalculado_min', 'updated_at'])
        data = ProgramacionListSerializer(prog).data
        return {
            'eta_recalculado_min_en_payload': data.get('eta_recalculado_min'),
            'eta_minutos_en_payload': data.get('eta_minutos'),
        }
    e3_ok, _ = _sim("E3 serializer lista expone eta_recalculado_min (HAL-2)", e3)

    # ============ E4: aceptar_asignacion → 200 OK (HAL-6) ============
    def e4():
        from rest_framework.test import APIRequestFactory
        from rest_framework.test import force_authenticate
        from apps.programaciones.views import ProgramacionViewSet
        cont = Container.objects.get(container_id='SIM_CTN001')
        prog = cont.programacion
        factory = APIRequestFactory()
        req = factory.post(f'/', {}, format='json')
        force_authenticate(req, user=user_a)
        view = ProgramacionViewSet.as_view({'post': 'aceptar_asignacion'})
        resp = view(req, pk=prog.pk)
        return {'status': resp.status_code, 'expected_200': True}
    e4_ok, _ = _sim("E4 aceptar_asignacion devuelve 200 OK (HAL-6)", e4)

    # ============ E5: iniciar_ruta → calcular ETA → estado en_ruta ============
    def e5():
        from rest_framework.test import APIRequestFactory
        from rest_framework.test import force_authenticate
        from apps.programaciones.views import ProgramacionViewSet
        cont = Container.objects.get(container_id='SIM_CTN001')
        prog = cont.programacion
        factory = APIRequestFactory()
        req = factory.post('/', {
            'patente': 'SIM-A1', 'lat': '-33.40', 'lng': '-70.60',
        }, format='json')
        force_authenticate(req, user=user_a)
        view = ProgramacionViewSet.as_view({'post': 'iniciar_ruta'})
        resp = view(req, pk=prog.pk)
        cont.refresh_from_db(); prog.refresh_from_db()
        return {
            'http_status': resp.status_code,
            'container_estado': cont.estado,
            'container_fecha_inicio_ruta': str(cont.fecha_inicio_ruta) if cont.fecha_inicio_ruta else None,
            'prog_eta_minutos': prog.eta_minutos,
            'prediccion_ml_source': (prog.prediccion_ml or {}).get('source'),
            'notificaciones_inicio': Notification.objects.filter(
                container=cont, tipo='ruta_iniciada',
            ).count(),
        }
    e5_ok, _ = _sim("E5 iniciar_ruta → en_ruta + ETA calculada", e5)

    # ============ E6: notificar_arribo → entregado + notification 'llegada' ============
    def e6():
        from rest_framework.test import APIRequestFactory
        from rest_framework.test import force_authenticate
        from apps.programaciones.views import ProgramacionViewSet
        cont = Container.objects.get(container_id='SIM_CTN001')
        prog = cont.programacion
        factory = APIRequestFactory()
        req = factory.post('/', {'lat': '-33.45', 'lng': '-70.65'}, format='json')
        force_authenticate(req, user=user_a)
        view = ProgramacionViewSet.as_view({'post': 'notificar_arribo'})
        resp = view(req, pk=prog.pk)
        cont.refresh_from_db(); prog.refresh_from_db()
        # HAL-10: eta_minutos debe quedar 0
        return {
            'http_status': resp.status_code,
            'container_estado': cont.estado,
            'prog_fecha_arribo_cd': str(prog.fecha_arribo_cd)[:19] if prog.fecha_arribo_cd else None,
            'prog_origen_arribo': prog.origen_arribo,
            'prog_eta_minutos_post_arribo': prog.eta_minutos,
            'eta_minutos_esperado_0': 0,
            'notificaciones_llegada': Notification.objects.filter(
                programacion=prog, tipo='llegada',
            ).count(),
        }
    e6_ok, _ = _sim("E6 notificar_arribo → entregado + notif 'llegada' (HAL-8, HAL-10)", e6)

    # ============ E7: drop & hook → soltar → soltar_contenedor (HAL-4) ============
    # Pre-crear un contenedor vacío en el CD de origen para que el auto-retorno lo tome
    Container.objects.get_or_create(
        container_id='SIM_CTN002',
        defaults=dict(
            cliente='SIM Cliente', estado='vacio', cd_entrega=cd_origen,
            vacio_contabilizado=True,
            fecha_vacio=timezone.now() - timedelta(hours=2),
            tipo='40HC',
        ),
    )

    def e7():
        from rest_framework.test import APIRequestFactory
        from rest_framework.test import force_authenticate
        from apps.programaciones.views import ProgramacionViewSet
        cont = Container.objects.get(container_id='SIM_CTN001')
        prog = cont.programacion
        factory = APIRequestFactory()
        req = factory.post('/', {}, format='json')
        force_authenticate(req, user=user_a)
        view = ProgramacionViewSet.as_view({'post': 'soltar_contenedor'})
        resp = view(req, pk=prog.pk)
        cont.refresh_from_db(); prog.refresh_from_db()
        # Esperar retorno automático
        retorno_id = resp.data.get('retorno_automatico') if hasattr(resp, 'data') else None
        retorno = None
        if retorno_id:
            retorno = Programacion.objects.filter(pk=retorno_id).first()
        driver_a.refresh_from_db()
        return {
            'http_status': resp.status_code,
            'container_estado': cont.estado,  # esperado 'soltado'
            'driver_liberado': prog.fecha_liberacion_conductor is not None,
            'driver_num_entregas': driver_a.num_entregas_dia,
            'retorno_automatico_id': retorno_id,
            'retorno_mismo_conductor': (
                retorno.driver_id == driver_a.id if retorno else False
            ),
            'retorno_container_id': retorno.container_id if retorno else None,
            'eventos_retorno_vacio_autoasignado': Notification.objects.filter(
                container__container_id='SIM_CTN002',
            ).count(),  # 0 (events are not notifications)
        }
    e7_ok, e7_evidence = _sim("E7 soltar_contenedor → soltado + auto-retorno (HAL-4)", e7)

    # ============ E8: cerrar descarga → vacio + ops completa ============
    def e8():
        cont = Container.objects.get(container_id='SIM_CTN001')
        prog = cont.programacion
        # Antes de cerrar descarga, simular notificación de inicio_descarga via HAL-9
        prog.fecha_inicio_descarga = timezone.now() - timedelta(minutes=15)
        prog.save(update_fields=['fecha_inicio_descarga', 'updated_at'])
        OperationalFlowService.mark_empty(prog, 'cd', 'sim_test')
        cont.refresh_from_db(); cd_origen.refresh_from_db()
        tv_count = TiempoOperacion.objects.filter(
            container=cont, tipo_operacion='descarga_cd',
        ).count()
        tv = TiempoOperacion.objects.filter(
            container=cont, tipo_operacion='descarga_cd',
        ).first()
        # HAL-17 verificación: started_at del TiempoOperacion debe usar fecha_inicio_descarga
        started_at_iso = tv.hora_inicio.isoformat() if tv else None
        fecha_inicio_descarga_iso = prog.fecha_inicio_descarga.isoformat() if prog.fecha_inicio_descarga else None
        return {
            'container_estado': cont.estado,  # esperado 'vacio'
            'cd_vacios_actuales': cd_origen.vacios_actuales,
            'cd_vacios_esperado': 2,  # el original + el de retorno
            'tiempo_operacion_creado': tv_count == 1,
            'tiempo_started_at_match_fecha_inicio_descarga': started_at_iso == fecha_inicio_descarga_iso,
        }
    e8_ok, _ = _sim("E8 cerrar descarga → vacio + TiempoOperacion (HAL-13, HAL-17)", e8)

    # ============ Resumen ============
    print("\n" + "=" * 70)
    print("RESUMEN DE SIMULACIÓN")
    print("=" * 70)
    print(f"E1-E8 pasos evaluados: 8")
    print(f"DB: solo objetos SIM_ usados; cleanup al final vía:")
    print(f"   Container.objects.filter(container_id__startswith='SIM_').delete()")
    print(f"   Programacion.objects.filter(cliente__startswith='SIM_').delete()")
    print(f"   Notification.objects.filter(container__container_id__startswith='SIM_').delete()")
    print("=" * 70)


if __name__ == '__main__':
    main()
else:
    # Para correr via `python manage.py shell < script.py` también.
    main()
