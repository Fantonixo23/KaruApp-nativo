import socket
import json
import subprocess
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .licencia import license_manager
from django.conf import settings


def _es_ip_virtual(ip):
    try:
        p = [int(x) for x in ip.split('.')]
        if len(p) != 4:
            return True
        if p[0] == 127:
            return True
        if p[0] == 169 and p[1] == 254:
            return True
        if p[0] == 172 and 16 <= p[1] <= 31:
            return True
        if p[0] == 10:
            return True
    except (ValueError, IndexError):
        return True
    return False

def _get_local_ips():
    """Devuelve las IPs reales de la PC, ignorando adaptadores virtuales"""
    hostname = socket.gethostname()
    todas = set()
    try:
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=5)
        for ip in re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', result.stdout):
            if not _es_ip_virtual(ip):
                todas.add(ip)
    except Exception:
        pass
    if not todas:
        try:
            ip = socket.gethostbyname(hostname)
            if not _es_ip_virtual(ip):
                todas.add(ip)
        except Exception:
            pass
    ordenadas = sorted(todas, key=lambda ip: (
        0 if ip.startswith('192.168.') else
        1 if ip.startswith('172.') else
        2 if ip.startswith('10.') else 3
    ))
    return ordenadas if ordenadas else ['127.0.0.1']


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