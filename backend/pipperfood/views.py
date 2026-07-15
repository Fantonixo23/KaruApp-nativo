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
    """Obtiene las IPs locales del servidor"""
    hostname = socket.gethostname()
    ips = []
    try:
        import subprocess
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split('\n'):
            line = line.strip()
            if 'IPv4' in line and ':' in line:
                ip = line.split(':')[1].strip()
                if ip:
                    ips.append(ip)
    except Exception:
        pass
    if not ips:
        try:
            ips = [socket.gethostbyname(hostname)]
        except Exception:
            ips = ['127.0.0.1']
    urls = [f'http://{ip}:8000' for ip in ips]
    return JsonResponse({
        'ip': ips[0] if ips else '127.0.0.1',
        'ips': ips,
        'hostname': hostname,
        'urls': urls,
        'url_principal': urls[0] if urls else f'http://{hostname}:8000',
        'url_hostname': f'http://{hostname}:8000',
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

@require_http_methods(["GET"])
def qr_conexion(request):
    hostname = socket.gethostname()
    ips = []
    try:
        import subprocess
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split('\n'):
            line = line.strip()
            if 'IPv4' in line and ':' in line:
                ip = line.split(':')[1].strip()
                if ip:
                    ips.append(ip)
    except Exception:
        pass
    if not ips:
        try:
            ips = [socket.gethostbyname(hostname)]
        except Exception:
            ips = ['127.0.0.1']
    urls = [f'http://{ip}:8000' for ip in ips]
    url_principal = urls[0] if urls else f'http://{hostname}:8000'
    try:
        import qrcode
        from io import BytesIO
        import base64
        img = qrcode.make(url_principal)
        buf = BytesIO()
        img.save(buf, format='PNG')
        qr_b64 = base64.b64encode(buf.getvalue()).decode()
    except Exception:
        qr_b64 = None
    return JsonResponse({
        'hostname': hostname,
        'ips': ips,
        'urls': urls,
        'url_principal': url_principal,
        'qr_base64': qr_b64,
    })

@csrf_exempt
@require_http_methods(["POST"])
def activar_licencia(request):
    """Endpoint legacy - ahora la activación se maneja desde karuAPP"""
    return JsonResponse({
        'success': False,
        'error': 'La activación ahora se gestiona desde karuAPP Dashboard'
    })