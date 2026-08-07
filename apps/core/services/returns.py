"""Flujo transaccional de retiro y retorno de contenedores vacíos."""
from django.db import transaction

from apps.cds.models import CD
from apps.containers.models import Container


class EmptyReturnService:
    @classmethod
    @transaction.atomic
    def start(cls, container, *, destination_type, destination_cd=None, depot_name=None, user=None):
        locked = Container.objects.select_for_update().select_related('cd_entrega').get(pk=container.pk)
        if locked.estado not in {'vacio', 'en_ccti'}:
            raise ValueError('El contenedor debe estar vacío y disponible para iniciar retorno.')
        if destination_type not in {'deposito', 'ccti'}:
            raise ValueError('Destino debe ser depósito o CCTI.')
        if destination_type == 'ccti':
            if not destination_cd or destination_cd.tipo != 'ccti' or not destination_cd.activo:
                raise ValueError('Debe seleccionar un CCTI activo.')
            destination_cd = CD.objects.select_for_update().get(pk=destination_cd.pk)
            if not destination_cd.puede_recibir_vacios:
                raise ValueError('El CCTI destino no tiene capacidad disponible.')
        elif not (depot_name or locked.deposito_devolucion):
            raise ValueError('Debe indicar el depósito de devolución.')

        # Retirar del inventario físico de origen una sola vez.
        if locked.vacio_contabilizado and locked.cd_entrega_id:
            origin = CD.objects.select_for_update().get(pk=locked.cd_entrega_id)
            origin.retirar_vacio()
            locked.vacio_contabilizado = False

        locked.retorno_destino_tipo = destination_type
        locked.retorno_destino_cd = destination_cd if destination_type == 'ccti' else None
        if destination_type == 'deposito':
            locked.deposito_devolucion = depot_name or locked.deposito_devolucion
        locked.save(update_fields=[
            'vacio_contabilizado', 'retorno_destino_tipo', 'retorno_destino_cd',
            'deposito_devolucion', 'updated_at',
        ])
        locked.cambiar_estado('vacio_en_ruta', user)
        return locked

    @classmethod
    @transaction.atomic
    def complete(cls, container, *, user=None):
        locked = Container.objects.select_for_update().get(pk=container.pk)
        if locked.estado != 'vacio_en_ruta':
            raise ValueError('El contenedor debe estar en retorno.')
        if locked.retorno_destino_tipo == 'ccti':
            destination = CD.objects.select_for_update().get(pk=locked.retorno_destino_cd_id)
            if not destination.recibir_vacio():
                raise ValueError('El CCTI destino quedó sin capacidad disponible.')
            locked.cd_entrega = destination
            locked.vacio_contabilizado = True
            locked.save(update_fields=['cd_entrega', 'vacio_contabilizado', 'updated_at'])
            locked.cambiar_estado('en_ccti', user)
        elif locked.retorno_destino_tipo == 'deposito':
            locked.cambiar_estado('devuelto', user)
        else:
            raise ValueError('El retorno no tiene destino configurado.')
        return locked
