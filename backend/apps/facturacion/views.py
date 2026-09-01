import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from apps.usuarios.decorators import requiere_autenticacion, requiere_rol
from .models import Configuracion, Timbrado, Factura, MetodoPago
from apps.pedidos.models import Pedido
from .services import sifen_client

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@requiere_autenticacion
def get_config(request):
    """Obtiene la configuraciÃ³n"""
    config = Configuracion.objects.first()
    if not config:
        config = Configuracion.objects.create(
            nombre_empresa='Mi Restaurant',
            ruc='44444444-7',
            direccion='Sin direcciÃ³n',
            telefono='0000000000',
            tasa_iva=10,
            timbrado_numero='001-001-0000001',
            establecimiento='001',
            punto_expedicion='001',
            estado='activo'
        )
    return JsonResponse({
        'success': True,
        'config': {
            'id': config.id,
            'nombre_empresa': config.nombre_empresa,
            'ruc': config.ruc,
            'direccion': config.direccion,
            'telefono': config.telefono,
            'tasa_iva': str(config.tasa_iva),
            'timbrado_numero': config.timbrado_numero or '001-001-0000001',
            'establecimiento': config.establecimiento or '001',
            'punto_expedicion': config.punto_expedicion or '001',
            'estado': config.estado,
            'fecha_inicio': config.fecha_inicio.isoformat() if config.fecha_inicio else None,
            'fecha_vencimiento': config.fecha_vencimiento.isoformat() if config.fecha_vencimiento else None,
            'tamano_papel': config.tamano_papel or '58mm',
            # --- SIFEN ---
            'nombre_fantasia': config.nombre_fantasia or '',
            'tipo_contribuyente': config.tipo_contribuyente,
            'tipo_regimen': config.tipo_regimen,
            'actividades_economicas': config.actividades_economicas or [],
            'departamento': config.departamento,
            'departamento_descripcion': config.departamento_descripcion or '',
            'distrito': config.distrito,
            'distrito_descripcion': config.distrito_descripcion or '',
            'ciudad': config.ciudad,
            'ciudad_descripcion': config.ciudad_descripcion or '',
            'ambiente_sifen': config.ambiente_sifen or 'test',
            'certificado_nombre': (config.ruta_certificado.rsplit('\\', 1)[-1].rsplit('/', 1)[-1]
                                   if config.ruta_certificado else ''),
            'csc_configurado': bool(config.csc),
            'csc_id': config.csc_id or '1',
        }
    })


@csrf_exempt
@require_http_methods(["PUT"])
@requiere_rol('administrador')
def update_config(request):
    """Actualiza la configuraciÃ³n"""
    try:
        data = json.loads(request.body)
        config = Configuracion.objects.first()
        
        if not config:
            config = Configuracion.objects.create(
                nombre_empresa=data.get('nombre_empresa', 'Mi Restaurant'),
                ruc=data.get('ruc', '5418755-8')
            )
        else:
            config.nombre_empresa = data.get('nombre_empresa', config.nombre_empresa)
            config.ruc = data.get('ruc', config.ruc)
            config.direccion = data.get('direccion', config.direccion)
            config.telefono = data.get('telefono', config.telefono)
            config.tasa_iva = data.get('tasa_iva', config.tasa_iva)
            config.timbrado_numero = data.get('timbrado_numero', config.timbrado_numero)
            config.establecimiento = data.get('establecimiento', config.establecimiento)
            config.punto_expedicion = data.get('punto_expedicion', config.punto_expedicion)
            config.tamano_papel = data.get('tamano_papel', config.tamano_papel)
            # --- SIFEN ---
            config.nombre_fantasia = data.get('nombre_fantasia', config.nombre_fantasia)
            if data.get('tipo_contribuyente') is not None:
                config.tipo_contribuyente = data.get('tipo_contribuyente')
            if data.get('tipo_regimen') is not None:
                config.tipo_regimen = data.get('tipo_regimen')
            if 'actividades_economicas' in data:
                config.actividades_economicas = data.get('actividades_economicas') or []
            if data.get('departamento') is not None:
                config.departamento = data.get('departamento')
                config.departamento_descripcion = data.get('departamento_descripcion', config.departamento_descripcion)
                config.distrito = data.get('distrito')
                config.distrito_descripcion = data.get('distrito_descripcion', config.distrito_descripcion)
                config.ciudad = data.get('ciudad')
                config.ciudad_descripcion = data.get('ciudad_descripcion', config.ciudad_descripcion)
            if data.get('ambiente_sifen') in ('test', 'prod'):
                config.ambiente_sifen = data.get('ambiente_sifen')
            if data.get('csc'):
                config.csc = data.get('csc')
            if data.get('csc_id'):
                config.csc_id = str(data.get('csc_id'))
            if data.get('fecha_inicio'):
                from datetime import datetime as _dt
                try:
                    config.fecha_inicio = _dt.strptime(str(data.get('fecha_inicio'))[:10], '%Y-%m-%d').date()
                except ValueError:
                    pass
            config.save()

        # Reflejar en el .env del microservicio lo que cambia la configuración
        # (ambiente y CSC se usan al firmar / generar el QR en sifen-service).
        sifen_client.actualizar_config_sifen(
            ambiente=data.get('ambiente_sifen') if data.get('ambiente_sifen') in ('test', 'prod') else None,
            csc=data.get('csc') or None,
            cscId=data.get('csc_id') or None,
        )

        return JsonResponse({
            'success': True,
            'config': {
                'nombre_empresa': config.nombre_empresa,
                'ruc': config.ruc,
                'direccion': config.direccion,
                'telefono': config.telefono,
                'timbrado_numero': config.timbrado_numero,
                'establecimiento': config.establecimiento,
                'punto_expedicion': config.punto_expedicion,
                'tipo_contribuyente': config.tipo_contribuyente,
                'tipo_regimen': config.tipo_regimen,
                'ambiente_sifen': config.ambiente_sifen,
                'fecha_inicio': config.fecha_inicio.isoformat() if config.fecha_inicio else None,
                'csc_configurado': bool(config.csc),
                'certificado_nombre': (config.ruta_certificado.rsplit('\\', 1)[-1].rsplit('/', 1)[-1]
                                       if config.ruta_certificado else ''),
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@requiere_autenticacion
def lista_timbrados(request):
    """Lista timbrados"""
    timbrados = Timbrado.objects.all().order_by('-id')
    data = [{
        'id': t.id,
        'establecimiento': t.establecimiento,
        'punto_expedicion': t.punto_expedicion,
        'numero_inicio': t.numero_inicio,
        'numero_fin': t.numero_fin,
        'numero_actual': t.numero_actual,
        'fecha_vencimiento': t.fecha_vencimiento.isoformat() if t.fecha_vencimiento else None,
        'activo': t.activo
    } for t in timbrados]
    return JsonResponse({'success': True, 'timbrados': data})


@csrf_exempt
@require_http_methods(["POST"])
@requiere_rol('administrador')
def crear_timbrado(request):
    """Crea un timbrado"""
    try:
        data = json.loads(request.body)
        timbrado = Timbrado.objects.create(
            establecimiento=data.get('establecimiento', '001'),
            punto_expedicion=data.get('punto_expedicion', '001'),
            numero_inicio=data.get('numero_inicio'),
            numero_fin=data.get('numero_fin'),
            numero_actual=data.get('numero_inicio', 1) - 1,
            fecha_vencimiento=data.get('fecha_vencimiento')
        )
        return JsonResponse({
            'success': True,
            'timbrado': {'id': timbrado.id}
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@requiere_autenticacion
def generar_factura(request):
    """Genera una factura numerada por timbrado"""
    try:
        data = json.loads(request.body)
        pedido_id = data.get('pedido_id')
        ruc_cliente = data.get('ruc_cliente', '44444444-7')
        nombre_cliente = data.get('nombre_cliente', 'CONSUMIDOR FINAL')
        
        config = Configuracion.objects.first()
        if not config:
            return JsonResponse({
                'success': False,
                'error': 'Configure la empresa primero'
            }, status=400)
        
        pedido = Pedido.objects.get(pk=pedido_id)

        # Consumir número secuencial del timbrado (se revertirá si falla)
        timbrado = Timbrado.objects.filter(activo=True).first()
        if not timbrado:
            numero = str(1).zfill(7)
        else:
            timbrado.numero_actual += 1
            timbrado.save()
            numero = str(timbrado.numero_actual).zfill(7)

        try:
            factura = Factura.objects.create(
                numero=numero,
                pedido=pedido,
                ruc_cliente=ruc_cliente,
                nombre_cliente=nombre_cliente,
                estado='generada',
                total=pedido.total,
            )
        except Exception:
            if timbrado:
                timbrado.numero_actual -= 1
                timbrado.save()
            raise
        
        return JsonResponse({
            'success': True,
            'factura': {
                'numero': factura.numero,
                'total': str(factura.total),
            }
        })
    except Pedido.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pedido no encontrado'}, status=404)
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'trace': traceback.format_exc()
        }, status=500)


@require_http_methods(["GET"])
@requiere_autenticacion
def lista_facturas(request):
    """Lista facturas"""
    facturas = Factura.objects.all().order_by('-created_at')[:50]
    data = [{
        'id': f.id,
        'numero': f.numero,
        'ruc_cliente': f.ruc_cliente,
        'nombre_cliente': f.nombre_cliente,
        'estado': f.estado,
        'total': str(f.total),
        'created_at': f.created_at.isoformat() if f.created_at else None
    } for f in facturas]
    return JsonResponse({'success': True, 'facturas': data})


# ========== MÃ‰TODOS DE PAGO ==========

@require_http_methods(["GET"])
@requiere_autenticacion
def lista_metodos_pago(request):
    """Lista todos los mÃ©todos de pago"""
    if not MetodoPago.objects.exists():
        defaults = [
            {'nombre': 'efectivo', 'etiqueta': 'Efectivo', 'icono': 'payments', 'color': '#4CAF50', 'orden': 1},
            {'nombre': 'tarjeta', 'etiqueta': 'DÃ©bito/CrÃ©dito', 'icono': 'credit_card', 'color': '#9C27B0', 'orden': 2},
            {'nombre': 'transferencia', 'etiqueta': 'Transferencia', 'icono': 'account_balance', 'color': '#2196F3', 'orden': 3},
            {'nombre': 'qr', 'etiqueta': 'QR', 'icono': 'qr_code', 'color': '#00BCD4', 'orden': 4},
        ]
        for d in defaults:
            MetodoPago.objects.create(**d)
    metodos = MetodoPago.objects.all().order_by('orden')
    data = [{
        'id': m.id,
        'nombre': m.nombre,
        'etiqueta': m.etiqueta,
        'icono': m.icono,
        'color': m.color,
        'activo': m.activo,
        'orden': m.orden
    } for m in metodos]
    return JsonResponse({'success': True, 'metodos': data})


@csrf_exempt
@require_http_methods(["POST"])
@requiere_rol('administrador')
def crear_metodo_pago(request):
    """Crea un nuevo mÃ©todo de pago"""
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre', '').strip().lower().replace(' ', '_')
        if not nombre:
            return JsonResponse({'success': False, 'error': 'El nombre es requerido'}, status=400)
        if MetodoPago.objects.filter(nombre=nombre).exists():
            return JsonResponse({'success': False, 'error': 'Ya existe un mÃ©todo con ese nombre'}, status=400)
        metodo = MetodoPago.objects.create(
            nombre=nombre,
            etiqueta=data.get('etiqueta', nombre),
            icono=data.get('icono', 'payments'),
            color=data.get('color', '#4CAF50'),
            activo=data.get('activo', True),
            orden=data.get('orden', 0)
        )
        return JsonResponse({
            'success': True,
            'metodo': {
                'id': metodo.id,
                'nombre': metodo.nombre,
                'etiqueta': metodo.etiqueta,
                'icono': metodo.icono,
                'color': metodo.color,
                'activo': metodo.activo,
                'orden': metodo.orden
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
@requiere_rol('administrador')
def actualizar_metodo_pago(request, pk):
    """Actualiza un mÃ©todo de pago"""
    try:
        data = json.loads(request.body)
        try:
            metodo = MetodoPago.objects.get(pk=pk)
        except MetodoPago.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'MÃ©todo no encontrado'}, status=404)

        if 'nombre' in data:
            nombre = data['nombre'].strip().lower().replace(' ', '_')
            if nombre != metodo.nombre and MetodoPago.objects.filter(nombre=nombre).exists():
                return JsonResponse({'success': False, 'error': 'Ya existe un mÃ©todo con ese nombre'}, status=400)
            metodo.nombre = nombre
        if 'etiqueta' in data:
            metodo.etiqueta = data['etiqueta']
        if 'icono' in data:
            metodo.icono = data['icono']
        if 'color' in data:
            metodo.color = data['color']
        if 'activo' in data:
            metodo.activo = data['activo']
        if 'orden' in data:
            metodo.orden = data['orden']
        metodo.save()

        return JsonResponse({
            'success': True,
            'metodo': {
                'id': metodo.id,
                'nombre': metodo.nombre,
                'etiqueta': metodo.etiqueta,
                'icono': metodo.icono,
                'color': metodo.color,
                'activo': metodo.activo,
                'orden': metodo.orden
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@requiere_rol('administrador')
def eliminar_metodo_pago(request, pk):
    """Elimina un mÃ©todo de pago"""
    try:
        metodo = MetodoPago.objects.get(pk=pk)
        metodo.delete()
        return JsonResponse({'success': True})
    except MetodoPago.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'MÃ©todo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
@requiere_autenticacion
def buscar_cliente_ruc(request):
    """Busca contribuyentes usando la API de TuRuc (consulta DNIT)"""
    q = request.GET.get('q', '').strip()
    if len(q) < 3:
        return JsonResponse({'success': True, 'resultados': []})
    try:
        url = f'https://turuc.com.py/api/contribuyente/search?search={urllib.parse.quote(q)}&page=0'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode())
        contribuyentes = data.get('data', {}).get('contribuyentes', [])
        resultados = [{'ruc': c['ruc'], 'nombre': c['razonSocial']} for c in contribuyentes]
        return JsonResponse({'success': True, 'resultados': resultados})
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return JsonResponse({'success': False, 'error': 'Servicio de consulta RUC temporalmente no disponible. Intente más tarde.'}, status=503)
        return JsonResponse({'success': False, 'error': f'Error del servicio RUC ({e.code})'}, status=502)
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Error al consultar RUC. Verifique su conexión a internet.'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@requiere_autenticacion
def sifen_status(request):
    """Devuelve el estado de la facturación electrónica SIFEN.

    - sifen_disponible: si el microservicio sifen-service responde.
    - certificado_configurado / csc_configurado: desde el .env del microservicio
      (que es lo que realmente se usa al firmar), combinado con Configuracion.
    - ambiente: el ambiente real activo en el microservicio.
    """
    try:
        config = Configuracion.objects.first()

        estado_ms = sifen_client.obtener_config_sifen()
        sifen_disponible = estado_ms is not None
        if estado_ms:
            cert_configurado = bool(estado_ms.get('certConfigurado'))
            csc_configurado = bool(estado_ms.get('cscConfigurado'))
            ambiente = estado_ms.get('ambiente', 'desconocido')
        else:
            cert_configurado = bool(config and config.ruta_certificado)
            csc_configurado = bool(config and config.csc)
            ambiente = getattr(config, 'ambiente_sifen', 'test') if config else 'test'

        return JsonResponse({
            'success': True,
            'sifen_habilitado': bool(config and config.estado in ('activo', 'demo', 'test')),
            'sifen_disponible': sifen_disponible,
            'certificado_configurado': cert_configurado,
            'csc_configurado': csc_configurado,
            'ambiente': ambiente,
            'empresa': config.nombre_empresa if config else None,
        })
    except Exception as e:
        logger.exception('Error en sifen_status')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT", "POST"])
@requiere_autenticacion
def sifen_certificado_subir(request):
    """Guarda el certificado .p12 subido por el usuario, actualiza
    Configuracion.ruta_certificado y escribe CERT_PATH/CERT_PASSWORD/CSC
    en el .env del microservicio (que es lo que se usa al firmar)."""
    try:
        config = Configuracion.objects.first()
        if not config:
            config = Configuracion.objects.create(
                nombre_empresa='Mi Restaurant', ruc='44444444-7',
                establecimiento='001', punto_expedicion='001',
            )

        certificado = request.FILES.get('certificado')
        pin = request.POST.get('pin', '')
        csc = request.POST.get('csc', '')

        ruta = config.ruta_certificado or ''
        if certificado:
            cert_dir = Path(settings.MEDIA_ROOT) / 'certificados'
            cert_dir.mkdir(parents=True, exist_ok=True)
            nombre = f'certificado_{config.id or 1}.p12'
            ruta = str(cert_dir / nombre)
            with open(ruta, 'wb+') as dest:
                for chunk in certificado.chunks():
                    dest.write(chunk)

        config.ruta_certificado = ruta
        if csc:
            config.csc = csc
        config.save()

        # Reflejar en el microservicio lo que realmente se usa al firmar.
        sifen_client.actualizar_config_sifen(
            certPath=ruta or None,
            certPassword=pin or None,
            csc=csc or None,
        )

        return JsonResponse({
            'success': True,
            'ruta_certificado': config.ruta_certificado,
            'certificado_configurado': bool(ruta),
            'csc_configurado': bool(config.csc),
        })
    except Exception as e:
        logger.exception('Error en sifen_certificado_subir')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)