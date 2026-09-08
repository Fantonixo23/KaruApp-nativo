import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from apps.usuarios.decorators import requiere_autenticacion, requiere_rol
from .models import (
    CajaSession, MovimientoCaja, CorteCaja,
    MONEDAS_SOPORTADAS, TasaCambio, convertir_a_pyg,
    obtener_tasas_cambio, tasa_de,
)


def _get_session_abierta():
    return CajaSession.objects.filter(estado='abierta').first()


def _procesar_arqueo(denominaciones):
    """Cuenta el físico por moneda y lo convierte a Gs con la tasa vigente.
    Devuelve (por_moneda, total_gs, tasas_usadas)."""
    por_moneda = {}
    tasas = obtener_tasas_cambio()
    for d in denominaciones or []:
        moneda = d.get('moneda', 'PYG')
        valor = float(d.get('valor', 0) or 0)
        cantidad = float(d.get('cantidad', 0) or 0)
        por_moneda[moneda] = por_moneda.get(moneda, 0) + valor * cantidad
    total_gs = 0
    tasas_usadas = {}
    for moneda, monto in por_moneda.items():
        tasa = tasas.get(moneda, 0)
        tasas_usadas[moneda] = tasa
        total_gs += monto * tasa
    return por_moneda, round(total_gs), tasas_usadas


@csrf_exempt
@require_http_methods(["POST"])
@requiere_autenticacion
def apertura(request):
    """Abrir caja: fondo inicial y opcionalmente usuario"""
    try:
        data = json.loads(request.body)
        fondo = float(data.get('fondo_inicial', 0))
        notas = data.get('notas', '')
        usuario_id = data.get('usuario_id')

        if _get_session_abierta():
            return JsonResponse({
                'success': False,
                'error': 'Ya hay una sesión de caja abierta. Ciérrela primero.'
            }, status=400)

        from apps.usuarios.models import Usuario
        usuario = Usuario.objects.filter(pk=usuario_id).first() if usuario_id else None

        session = CajaSession.objects.create(
            usuario=usuario,
            fondo_inicial=fondo,
            notas_apertura=notas,
            estado='abierta'
        )

        return JsonResponse({
            'success': True,
            'session': {
                'id': session.id,
                'usuario': usuario.nombre if usuario else 'Sin asignar',
                'fondo_inicial': float(session.fondo_inicial),
                'apertura_en': session.apertura_en.isoformat(),
                'estado': session.estado,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
@requiere_autenticacion
def sesion_actual(request):
    """Devuelve la sesión activa con todos los totales calculados"""
    session = _get_session_abierta()
    if not session:
        return JsonResponse({
            'success': True,
            'session': None,
            'message': 'No hay sesión de caja abierta'
        })

    movs = session.movimientos.filter(tipo='venta')
    total_pedidos = movs.count()
    total_ventas = float(sum(float(m.monto_pyg) for m in movs) or 0)
    propinas = float(sum(float(m.propina) for m in movs) or 0)
    propinas_efectivo = float(sum(float(m.propina) for m in movs.filter(metodo_pago='efectivo')) or 0)

    movs_extra = session.movimientos.filter(tipo='ingreso_extra')
    total_ingresos_extra = float(sum(float(m.monto_pyg) for m in movs_extra) or 0)
    movs_retiros = session.movimientos.filter(tipo='retiro')
    total_retiros = float(sum(float(m.monto_pyg) for m in movs_retiros) or 0)

    ventas_efectivo = session.total_ventas_efectivo()
    ventas_tarjeta = session.total_ventas_tarjeta()
    ventas_transferencia = session.total_ventas_transferencia()
    ventas_qr = session.total_ventas_qr()

    efectivo_esperado = float(session.fondo_inicial) + ventas_efectivo + total_ingresos_extra - total_retiros
    total_general = ventas_efectivo + ventas_tarjeta + ventas_transferencia + ventas_qr

    return JsonResponse({
        'success': True,
        'session': {
            'id': session.id,
            'usuario': session.usuario.nombre if session.usuario else 'Sin asignar',
            'usuario_id': session.usuario_id,
            'fondo_inicial': float(session.fondo_inicial),
            'apertura_en': session.apertura_en.isoformat(),
            'estado': session.estado,
            'totales': {
                'total_pedidos': total_pedidos,
                'total_ventas': total_ventas,
                'ventas_efectivo': ventas_efectivo,
                'ventas_tarjeta': ventas_tarjeta,
                'ventas_transferencia': ventas_transferencia,
                'ventas_qr': ventas_qr,
                'total_general': total_general,
                'propinas': propinas,
                'propinas_efectivo': propinas_efectivo,
                'ingresos_extra': total_ingresos_extra,
                'retiros': total_retiros,
                'efectivo_esperado': efectivo_esperado,
            }
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
@requiere_autenticacion
def movimiento(request):
    """Registra un ingreso extra o retiro durante el turno"""
    try:
        session = _get_session_abierta()
        if not session:
            return JsonResponse({
                'success': False, 'error': 'No hay sesión de caja abierta'
            }, status=400)

        data = json.loads(request.body)
        tipo = data.get('tipo', 'ingreso_extra')
        if tipo not in ('ingreso_extra', 'retiro'):
            return JsonResponse({'success': False, 'error': 'Tipo inválido'}, status=400)

        monto = float(data.get('monto', 0))
        if monto <= 0:
            return JsonResponse({'success': False, 'error': 'El monto debe ser mayor a 0'}, status=400)

        if tipo == 'retiro':
            disponible = session.efectivo_esperado()
            if monto > disponible:
                return JsonResponse({
                    'success': False,
                    'error': f'No puede retirar más de lo que hay en la caja. Disponible: {int(disponible):,} Gs'
                }, status=400)

        motivo = data.get('motivo', '')
        if not motivo:
            return JsonResponse({'success': False, 'error': 'Debe ingresar un motivo'}, status=400)

        usuario_id = data.get('usuario_id')
        from apps.usuarios.models import Usuario
        usuario = Usuario.objects.filter(pk=usuario_id).first() if usuario_id else None

        mov = MovimientoCaja.objects.create(
            session=session,
            tipo=tipo,
            metodo_pago='efectivo',
            monto=monto,
            moneda='PYG',
            monto_pyg=monto,
            motivo=motivo,
            usuario=usuario,
        )

        return JsonResponse({
            'success': True,
            'movimiento': {
                'id': mov.id,
                'tipo': mov.tipo,
                'monto_pyg': float(mov.monto_pyg),
                'motivo': mov.motivo,
                'created_at': mov.created_at.isoformat(),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
@requiere_autenticacion
def movimientos_lista(request):
    """Lista todos los movimientos de la sesión actual"""
    session = _get_session_abierta()
    if not session:
        return JsonResponse({'success': True, 'movimientos': []})

    movs = MovimientoCaja.objects.filter(session=session).select_related('pedido')
    data = [{
        'id': m.id,
        'tipo': m.tipo,
        'metodo_pago': m.metodo_pago,
        'monto': float(m.monto),
        'moneda': m.moneda,
        'monto_pyg': float(m.monto_pyg),
        'tasa_usada': float(m.tasa_usada) if m.tasa_usada else 0,
        'propina': float(m.propina),
        'vuelto': float(m.vuelto),
        'motivo': m.motivo,
        'pedido_numero': m.pedido.numero_orden if m.pedido else None,
        'pedido_mesa': m.pedido.mesa.numero if m.pedido and m.pedido.mesa else None,
        'detalle_pagos': m.detalle_pagos,
        'created_at': m.created_at.isoformat(),
    } for m in movs]

    return JsonResponse({'success': True, 'movimientos': data})


@require_http_methods(["GET"])
@requiere_autenticacion
def tasas_cambio(request):
    """Devuelve las tasas del día para todas las monedas soportadas."""
    tasas = {t.moneda: float(t.tasa) for t in TasaCambio.objects.all()}
    data = [
        {
            'moneda': m['codigo'],
            'nombre': m['nombre'],
            'simbolo': m['simbolo'],
            'tasa': tasas.get(m['codigo'], 0),
        }
        for m in MONEDAS_SOPORTADAS
    ]
    return JsonResponse({'success': True, 'tasas': data})


@csrf_exempt
@require_http_methods(["POST"])
@requiere_autenticacion
def tasas_cambio_actualizar(request):
    """Actualiza las tasas del día. Body: {'BRL': 900, 'USD': 7500, 'ARS': 8}"""
    try:
        data = json.loads(request.body)
        actualizadas = []
        for moneda_info in MONEDAS_SOPORTADAS:
            codigo = moneda_info['codigo']
            if codigo == 'PYG':
                continue
            valor = data.get(codigo)
            if valor is None:
                continue
            try:
                tasa = float(valor)
            except (TypeError, ValueError):
                return JsonResponse({
                    'success': False,
                    'error': f'Tasa inválida para {codigo}'
                }, status=400)
            if tasa <= 0:
                return JsonResponse({
                    'success': False,
                    'error': f'La tasa de {codigo} debe ser mayor a 0'
                }, status=400)
            obj, _ = TasaCambio.objects.update_or_create(
                moneda=codigo,
                defaults={
                    'nombre': moneda_info['nombre'],
                    'simbolo': moneda_info['simbolo'],
                    'tasa': tasa,
                }
            )
            actualizadas.append({'moneda': codigo, 'tasa': float(obj.tasa)})
        if not actualizadas:
            return JsonResponse({
                'success': False,
                'error': 'No se recibió ninguna tasa para actualizar'
            }, status=400)
        return JsonResponse({'success': True, 'tasas': actualizadas})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@requiere_autenticacion
def arqueo(request):
    """Registra conteo físico de billetes/monedas (sin cerrar caja - Reporte X).
    Las denominaciones incluyen moneda: [{moneda, valor, cantidad}, ...]"""
    try:
        session = _get_session_abierta()
        if not session:
            return JsonResponse({
                'success': False, 'error': 'No hay sesión de caja abierta'
            }, status=400)

        data = json.loads(request.body)
        denominaciones = data.get('denominaciones', [])

        por_moneda, total_contado, tasas_usadas = _procesar_arqueo(denominaciones)

        efectivo_esperado = session.efectivo_esperado()
        diferencia = total_contado - efectivo_esperado

        return JsonResponse({
            'success': True,
            'arqueo': {
                'denominaciones': denominaciones,
                'totales_por_moneda': por_moneda,
                'tasas_aplicadas': tasas_usadas,
                'total_contado': total_contado,
                'total_esperado': efectivo_esperado,
                'diferencia': diferencia,
                'tipo_diferencia': 'sobrante' if diferencia > 0 else ('faltante' if diferencia < 0 else ''),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@requiere_rol('administrador')
def cierre(request):
    """Cierre definitivo de caja (Corte Z) con arqueo final"""
    try:
        session = _get_session_abierta()
        if not session:
            return JsonResponse({'success': False, 'error': 'No hay sesión de caja abierta'}, status=400)

        from apps.pedidos.models import Pedido
        pendientes = Pedido.objects.exclude(estado__in=['pagado', 'cancelado']).exists()
        if pendientes:
            return JsonResponse({
                'success': False,
                'error': 'No se puede cerrar caja con pedidos pendientes. Debe pagar o cancelar todos los pedidos primero.'
            }, status=400)

        data = json.loads(request.body)
        denominaciones = data.get('denominaciones', [])
        observaciones = data.get('observaciones', '')
        usuario_id = data.get('usuario_id')

        # Arqueo multi-moneda: cuenta cada moneda por separado y convierte a Gs
        # con la tasa vigente en el momento del cierre.
        por_moneda, total_contado, tasas_usadas = _procesar_arqueo(denominaciones)
        efectivo_esperado = session.efectivo_esperado()
        diferencia = total_contado - efectivo_esperado

        from apps.usuarios.models import Usuario
        usuario_cierre = Usuario.objects.filter(pk=usuario_id).first() if usuario_id else None

        ventas_efectivo = session.total_ventas_efectivo()
        ventas_tarjeta = session.total_ventas_tarjeta()
        ventas_transferencia = session.total_ventas_transferencia()
        ventas_qr = session.total_ventas_qr()
        total_ingresos = session.total_ingresos_extra()
        total_retiros_monto = session.total_retiros()
        total_ventas = session.total_ventas()
        total_propinas_monto = sum(
            float(m.propina or 0) for m in session.movimientos.filter(tipo='venta')
        )

        corte = CorteCaja.objects.create(
            session=session,
            usuario_cierre=usuario_cierre,
            fondo_inicial=session.fondo_inicial,
            total_ventas_efectivo=ventas_efectivo,
            total_ventas_tarjeta=ventas_tarjeta,
            total_ventas_transferencia=ventas_transferencia,
            total_ventas_qr=ventas_qr,
            total_ingresos_extra=total_ingresos,
            total_retiros=total_retiros_monto,
            total_propinas=total_propinas_monto,
            total_ventas=total_ventas,
            denominaciones=denominaciones,
            totales_por_moneda=por_moneda,
            tasas_aplicadas=tasas_usadas,
            total_contado_efectivo=total_contado,
            total_esperado=efectivo_esperado,
            diferencia=diferencia,
            tipo_diferencia='sobrante' if diferencia > 0 else ('faltante' if diferencia < 0 else ''),
            observaciones=observaciones,
        )

        session.cerrar()

        return JsonResponse({
            'success': True,
            'corte': {
                'id': corte.id,
                'fondo_inicial': float(corte.fondo_inicial),
                'total_ventas_efectivo': float(corte.total_ventas_efectivo),
                'total_ventas_tarjeta': float(corte.total_ventas_tarjeta),
                'total_ventas_transferencia': float(corte.total_ventas_transferencia),
                'total_ventas_qr': float(corte.total_ventas_qr),
                'total_ingresos_extra': float(corte.total_ingresos_extra),
                'total_retiros': float(corte.total_retiros),
                'total_propinas': float(corte.total_propinas),
                'total_ventas': float(corte.total_ventas),
                'denominaciones': denominaciones,
                'totales_por_moneda': por_moneda,
                'tasas_aplicadas': tasas_usadas,
                'total_contado_efectivo': total_contado,
                'total_esperado': efectivo_esperado,
                'diferencia': diferencia,
                'tipo_diferencia': corte.tipo_diferencia,
                'observaciones': observaciones,
                'created_at': corte.created_at.isoformat(),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
@requiere_autenticacion
def cortes_lista(request):
    """Lista todos los cortes de caja anteriores"""
    cortes = CorteCaja.objects.all().order_by('-created_at')[:30]
    data = [{
        'id': c.id,
        'session_id': c.session_id,
        'usuario_cierre': c.usuario_cierre.nombre if c.usuario_cierre else '?',
        'fondo_inicial': float(c.fondo_inicial),
        'total_ventas': float(c.total_ventas),
        'totales_por_moneda': c.totales_por_moneda,
        'tasas_aplicadas': c.tasas_aplicadas,
        'total_contado_efectivo': float(c.total_contado_efectivo),
        'diferencia': float(c.diferencia),
        'tipo_diferencia': c.tipo_diferencia,
        'observaciones': c.observaciones,
        'created_at': c.created_at.isoformat(),
    } for c in cortes]
    return JsonResponse({'success': True, 'cortes': data})
