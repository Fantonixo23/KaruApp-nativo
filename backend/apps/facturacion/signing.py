import os
import base64
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

CERT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'print_service', 'certs')
PRIVATE_KEY_PATH = os.path.join(CERT_DIR, 'qz-private-key.pem')
CERT_PATH = os.path.join(CERT_DIR, 'qz-certificate.pem')


def _sign_data(data_str):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    with open(PRIVATE_KEY_PATH, 'rb') as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    signature = private_key.sign(
        data_str.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode('utf-8')


def qz_cert(request):
    try:
        with open(CERT_PATH, 'rb') as f:
            return HttpResponse(f.read(), content_type='text/plain')
    except FileNotFoundError:
        return HttpResponse('Certificado no encontrado', status=500)


@csrf_exempt
@require_http_methods(["POST"])
def qz_sign(request):
    try:
        data = json.loads(request.body)
        to_sign = data.get('data', '')
        if not to_sign:
            return JsonResponse({'success': False, 'error': 'Falta data'}, status=400)
        signature = _sign_data(to_sign)
        return JsonResponse({'success': True, 'signature': signature})
    except FileNotFoundError:
        return JsonResponse({'success': False, 'error': 'Certificados no generados. Ejecute generar_certificados_qz.py'}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
