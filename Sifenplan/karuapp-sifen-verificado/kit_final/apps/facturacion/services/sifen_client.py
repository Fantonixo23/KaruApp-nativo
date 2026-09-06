"""
Cliente HTTP hacia el microservicio sifen-service (Node), que corre local
en el mismo servidor on-premise. Django nunca genera ni firma el XML: le
manda a este servicio los datos de la venta y recibe el resultado.
"""
import requests
from django.conf import settings

SIFEN_SERVICE_URL = getattr(settings, "SIFEN_SERVICE_URL", "http://127.0.0.1:4000")
SIFEN_SERVICE_TOKEN = getattr(settings, "SIFEN_SERVICE_TOKEN", "")
TIMEOUT = 30  # segundos. La SET puede tardar; no conviene un timeout corto.


class SifenServiceError(Exception):
    """El sifen-service no respondió o devolvió un error inesperado."""


def _headers():
    headers = {"Content-Type": "application/json"}
    if SIFEN_SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {SIFEN_SERVICE_TOKEN}"
    return headers


def _post(path, payload):
    try:
        resp = requests.post(
            f"{SIFEN_SERVICE_URL}{path}", json=payload, headers=_headers(), timeout=TIMEOUT
        )
    except requests.RequestException as exc:
        # Acá cae, por ejemplo, "no hay internet" o "el servicio no está corriendo".
        # Quien llame a esto debe encolar el documento para reintento (ver Fase 5 del plan).
        raise SifenServiceError(f"No se pudo contactar al sifen-service: {exc}") from exc
    if resp.status_code >= 500:
        raise SifenServiceError(resp.json().get("error", "Error del sifen-service"))
    return resp.json()


def _get(path, params):
    try:
        resp = requests.get(
            f"{SIFEN_SERVICE_URL}{path}", params=params, headers=_headers(), timeout=TIMEOUT
        )
    except requests.RequestException as exc:
        raise SifenServiceError(f"No se pudo contactar al sifen-service: {exc}") from exc
    if resp.status_code >= 500:
        raise SifenServiceError(resp.json().get("error", "Error del sifen-service"))
    return resp.json()


def emitir_documento(id_, params, data):
    """params/data: ver estructura completa en el README de facturacionelectronicapy-xmlgen.
    Devuelve dict con: ok, cdc, idLote, datetime, xmlFirmado (si ok=True)
    o ok=False, error (si la SET lo rechazó al encolar)."""
    return _post("/documentos/emitir", {"id": id_, "params": params, "data": data})


def consultar_lote(id_, id_lote):
    return _get(f"/lotes/{id_lote}", {"id": id_})


def cancelar_documento(id_, params, data):
    return _post("/documentos/cancelar", {"id": id_, "params": params, "data": data})


def inutilizar_numeracion(id_, params, data):
    return _post("/documentos/inutilizar", {"id": id_, "params": params, "data": data})


def consultar_ruc(id_, ruc):
    return _get(f"/ruc/{ruc}", {"id": id_})


def consultar_cdc(id_, cdc):
    return _get(f"/cdc/{cdc}", {"id": id_})
