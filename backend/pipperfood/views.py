import socket
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .licencia import license_manager
from django.conf import settings


def info_empresa(request):
    """Obtiene información de la empresa"""
    from apps.facturacion.models import Configuracion
    try:
        config = Configuracion.objects.first()
        if config:
            return JsonResponse({
                'empresa': config.nombre_empresa,
                'ruc': config.ruc,
                'direccion': config.direccion,
                'telefono': config.telefono,
                'version': '1.0.0'
            })
    except Exception:
        pass
    return JsonResponse({
        'empresa': 'karuAPP',
        'ruc': '5418755-8',
        'version': '1.0.0'
    })


def verificar_suscripcion(request):
    """Verifica el estado de la suscripción"""
    lic = license_manager.verificar()
    estado = lic['estado']
    if estado == 'expirado':
        estado = 'bloqueada'
    return JsonResponse({
        'estado': estado,
        'dias_restantes': lic['dias_restantes'],
        'mensaje': lic['mensaje']
    })


def obtener_ip_local(request):
    """Obtiene la IP local del servidor"""
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return JsonResponse({
        'ip': ip_address,
        'hostname': hostname
    })


@csrf_exempt
@require_http_methods(["GET"])
def verificar_licencia(request):
    """Verifica el estado de la licencia (endpoint legacy)"""
    lic = license_manager.verificar()
    estado = lic['estado']
    if estado == 'expirado':
        estado = 'bloqueada'
    return JsonResponse({
        'success': estado != 'bloqueada',
        'licencia_valida': estado not in ('bloqueada', 'expirado'),
        'estado': estado,
        'dias_restantes': lic['dias_restantes'],
        'mensaje': lic['mensaje']
    })


@require_http_methods(["GET"])
def print_token(request):
    return JsonResponse({'success': True, 'token': settings.PRINT_API_TOKEN})

@csrf_exempt
@require_http_methods(["POST"])
def activar_licencia(request):
    """Endpoint legacy - ahora la activación se maneja desde karuAPP"""
    return JsonResponse({
        'success': False,
        'error': 'La activación ahora se gestiona desde karuAPP Dashboard'
    })