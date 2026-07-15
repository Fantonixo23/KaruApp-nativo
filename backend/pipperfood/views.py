import socket
import json
import subprocess
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .licencia import license_manager
from django.conf import settings


def _get_local_ips():
    """Devuelve las IPs reales de la PC, ignorando adaptadores virtuales (Docker, Hyper-V, etc)"""
    hostname = socket.gethostname()
    ips_reales = []
    try:
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=5)
        lines = result.stdout.split('\n')
        current_has_gateway = False
        current_ip = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('Ethernet adapter') or stripped.startswith('Wireless LAN adapter') or stripped.startswith('Unknown adapter'):
                if current_ip and current_has_gateway:
                    ips_reales.append(current_ip)
                current_ip = None
                current_has_gateway = False
                continue
            ip_match = re.search(r'IPv4[^:]*:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', stripped)
            if ip_match:
                current_ip = ip_match.group(1)
                continue
            gw_match = re.search(r'Default Gateway[^:]*:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', stripped)
            if gw_match:
                current_has_gateway = True
        if current_ip and current_has_gateway:
            ips_reales.append(current_ip)
    except Exception:
        pass
    if not ips_reales:
        try:
            ips_reales = [socket.gethostbyname(hostname)]
        except Exception:
            ips_reales = ['127.0.0.1']
        ips_reales = [ip for ip in ips_reales if not ip.startswith('127.')]
    final = []
    for ip in ips_reales:
        partes = ip.split('.')
        if len(partes) == 4:
            try:
                primero = int(partes[0])
                segundo = int(partes[1])
                if primero == 172 and 17 <= segundo <= 31:
                    continue
            except ValueError:
                pass
        final.append(ip)
    return final if final else ['127.0.0.1']


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
    ips = _get_local_ips()
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
    ips = _get_local_ips()
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