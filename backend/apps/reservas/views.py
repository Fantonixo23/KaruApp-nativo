import json
from datetime import datetime

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.usuarios.decorators import requiere_autenticacion
from apps.mesas.models import Mesa
from .models import Reserva


def _notificar(mesa):
    from pipperfood.socket_events import emit_mesa_update, emit_reserva_actualizada
    try:
        emit_mesa_update({'id': mesa.id, 'numero': mesa.numero, 'estado': mesa.estado})
        emit_reserva_actualizada()
    except Exception:
        pass


def _serializar(r, hoy=None):
    hoy = hoy or timezone.localtime().date()
    return {
        'id': r.id,
        'mesa': {
            'id': r.mesa.id,
            'numero': r.mesa.numero,
            'nombre': r.mesa.nombre,
            'area': r.mesa.area,
            'capacidad': r.mesa.capacidad,
            'estado': r.mesa.estado,
        },
        'fecha': r.fecha.isoformat(),
        'hora': r.hora.strftime('%H:%M'),
        'duracion_min': r.duracion_min,
        'cliente_nombre': r.cliente_nombre,
        'cliente_telefono': r.cliente_telefono or '',
        'comensales': r.comensales,
        'estado': r.estado,
        'nota': r.nota or '',
        'es_hoy': r.fecha == hoy,
    }


def _hay_conflicto(mesa, fecha, hora, duracion_min, excluir_id=None):
    """True si existe otra reserva activa para la misma mesa/fecha que
    se solape con el bloque [hora, hora+duracion_min]."""
    qs = Reserva.objects.filter(
        mesa=mesa,
        fecha=fecha,
        estado__in=Reserva.ESTADOS_ACTIVOS,
    )
    if excluir_id:
        qs = qs.exclude(pk=excluir_id)

    inicio = hora.hour * 60 + hora.minute
    fin = inicio + duracion_min
    for r in qs:
        inicio_r = r.hora.hour * 60 + r.hora.minute
        fin_r = inicio_r + r.duracion_min
        if inicio < fin_r and inicio_r < fin:
            return True
    return False


def _parse_fecha_hora(fecha_str, hora_str):
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    hora = datetime.strptime(hora_str, '%H:%M').time()
    return fecha, hora


@require_http_methods(["GET"])
def lista_reservas(request):
    """Lista reservas. Filtros: fecha=YYYY-MM-DD, estado, mesa_id."""
    fecha_str = request.GET.get('fecha')
    estado = request.GET.get('estado')
    mesa_id = request.GET.get('mesa_id')

    qs = Reserva.objects.select_related('mesa').all()
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            qs = qs.filter(fecha=fecha)
        except ValueError:
            pass
    if estado:
        qs = qs.filter(estado=estado)
    if mesa_id:
        qs = qs.filter(mesa_id=mesa_id)

    hoy = timezone.localtime().date()
    data = [_serializar(r, hoy) for r in qs]
    return JsonResponse({'success': True, 'reservas': data})


@csrf_exempt
@require_http_methods(["POST"])
@requiere_autenticacion
def crear_reserva(request):
    """Crea una reserva y sincroniza el estado de la mesa."""
    try:
        data = json.loads(request.body)
        mesa_id = data.get('mesa_id')
        fecha_str = data.get('fecha')
        hora_str = data.get('hora')

        if not mesa_id or not fecha_str or not hora_str:
            return JsonResponse({
                'success': False,
                'error': 'Mesa, fecha y hora son requeridos'
            }, status=400)

        try:
            mesa = Mesa.objects.get(pk=mesa_id)
        except Mesa.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Mesa no encontrada'}, status=404)

        try:
            fecha, hora = _parse_fecha_hora(fecha_str, hora_str)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Fecha o hora inválidas'}, status=400)

        if fecha < timezone.localtime().date():
            return JsonResponse({
                'success': False,
                'error': 'La fecha no puede ser anterior a hoy'
            }, status=400)

        duracion = int(data.get('duracion_min', 120) or 120)
        nombre = (data.get('cliente_nombre') or '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre del cliente es requerido'
            }, status=400)

        if _hay_conflicto(mesa, fecha, hora, duracion):
            return JsonResponse({
                'success': False,
                'error': 'La mesa ya está reservada en ese horario'
            }, status=400)

        reserva = Reserva.objects.create(
            mesa=mesa,
            fecha=fecha,
            hora=hora,
            duracion_min=duracion,
            cliente_nombre=nombre,
            cliente_telefono=(data.get('cliente_telefono') or '').strip(),
            comensales=int(data.get('comensales', 2) or 2),
            nota=(data.get('nota') or '').strip(),
            estado=data.get('estado', 'pendiente'),
        )

        mesa.sincronizar_estado()
        _notificar(mesa)

        return JsonResponse({'success': True, 'reserva': _serializar(reserva)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
@requiere_autenticacion
def modificar_reserva(request, pk):
    """Modifica una reserva (re-valida choques y re-sincroniza la mesa)."""
    try:
        data = json.loads(request.body)
        try:
            reserva = Reserva.objects.select_related('mesa').get(pk=pk)
        except Reserva.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Reserva no encontrada'}, status=404)

        mesa = reserva.mesa
        fecha = reserva.fecha
        hora = reserva.hora
        duracion = reserva.duracion_min

        if data.get('mesa_id'):
            try:
                mesa = Mesa.objects.get(pk=data.get('mesa_id'))
            except Mesa.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Mesa no encontrada'}, status=404)

        if data.get('fecha') and data.get('hora'):
            try:
                fecha, hora = _parse_fecha_hora(data['fecha'], data['hora'])
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Fecha o hora inválidas'}, status=400)

        if 'duracion_min' in data:
            duracion = int(data.get('duracion_min', 120) or 120)

        if fecha < timezone.localtime().date():
            return JsonResponse({
                'success': False,
                'error': 'La fecha no puede ser anterior a hoy'
            }, status=400)

        nombre = (data.get('cliente_nombre') or reserva.cliente_nombre).strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre del cliente es requerido'
            }, status=400)

        if _hay_conflicto(mesa, fecha, hora, duracion, excluir_id=reserva.pk):
            return JsonResponse({
                'success': False,
                'error': 'La mesa ya está reservada en ese horario'
            }, status=400)

        if 'estado' in data and data['estado'] in [e[0] for e in Reserva.ESTADOS]:
            reserva.estado = data['estado']

        reserva.mesa = mesa
        reserva.fecha = fecha
        reserva.hora = hora
        reserva.duracion_min = duracion
        reserva.cliente_nombre = nombre
        if 'cliente_telefono' in data:
            reserva.cliente_telefono = (data.get('cliente_telefono') or '').strip()
        if 'comensales' in data:
            reserva.comensales = int(data.get('comensales', 2) or 2)
        if 'nota' in data:
            reserva.nota = (data.get('nota') or '').strip()
        reserva.save()

        mesa.sincronizar_estado()
        _notificar(mesa)

        return JsonResponse({'success': True, 'reserva': _serializar(reserva)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@requiere_autenticacion
def cambiar_estado_reserva(request, pk):
    """Cambia el estado de una reserva (confirmar/cancelar/atender/no asistió)."""
    try:
        data = json.loads(request.body)
        nuevo = data.get('estado')
        validos = [e[0] for e in Reserva.ESTADOS]
        if nuevo not in validos:
            return JsonResponse({'success': False, 'error': 'Estado no válido'}, status=400)

        try:
            reserva = Reserva.objects.select_related('mesa').get(pk=pk)
        except Reserva.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Reserva no encontrada'}, status=404)

        reserva.estado = nuevo
        reserva.save()

        mesa = reserva.mesa
        mesa.sincronizar_estado()
        _notificar(mesa)

        return JsonResponse({'success': True, 'reserva': _serializar(reserva)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@requiere_autenticacion
def eliminar_reserva(request, pk):
    """Elimina una reserva y re-sincroniza la mesa."""
    try:
        reserva = Reserva.objects.select_related('mesa').get(pk=pk)
        mesa = reserva.mesa
        reserva.delete()
        mesa.sincronizar_estado()
        _notificar(mesa)
        return JsonResponse({'success': True})
    except Reserva.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Reserva no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)