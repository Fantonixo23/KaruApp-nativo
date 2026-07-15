from django.urls import path
from .views import (
    info_empresa,
    verificar_suscripcion,
    obtener_ip_local,
    verificar_licencia as verificar_licencia_viejo,
    activar_licencia,
    print_token,
)
from .licencia import verificar_licencia_api
from apps.facturacion.signing import qz_sign, qz_cert

urlpatterns = [
    path('info', info_empresa, name='info'),
    path('verificar-suscripcion', verificar_suscripcion, name='verificar_suscripcion'),
    path('obtener-ip', obtener_ip_local, name='obtener_ip'),
    path('verificar-licencia', verificar_licencia_api, name='verificar_licencia'),
    path('activar-licencia', activar_licencia, name='activar_licencia'),
    path('print-token', print_token, name='print_token'),
    path('print-cert', qz_cert, name='qz_cert'),
    path('print-sign', qz_sign, name='qz_sign'),
]