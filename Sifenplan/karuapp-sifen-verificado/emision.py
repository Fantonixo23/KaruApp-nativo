"""
facturacion/services/emision.py
"""
from datetime import datetime
from django.db import transaction

from apps.facturacion.models import Configuracion, Timbrado, Factura
from . import sifen_client
from .mapper import pedido_a_data_sifen, pedidos_a_data_sifen


def emitir_para_factura(factura, pedidos, cfg=None, timbrado=None):
    """Pensada para llamarse DESDE cobrar_mesa, justo después de crear la
    Factura y de reservar el número en Timbrado — no reserva numeración de
    nuevo, reutiliza lo que ya hizo esa vista. Actualiza `factura` in-place
    y la devuelve. `pedidos` es el queryset/lista de Pedido cobrados juntos."""
    cfg = cfg or Configuracion.objects.first()
    if not cfg:
        raise ValueError("No hay Configuracion cargada")

    numero = factura.numero.split('-')[-1] if '-' in factura.numero else factura.numero
    data = pedidos_a_data_sifen(
        pedidos,
        establecimiento=factura.establecimiento or cfg.establecimiento,
        punto=factura.punto_expedicion or cfg.punto_expedicion,
        numero=numero,
        tipo_documento=1,
    )
    params = _armar_params(cfg)

    try:
        resultado = sifen_client.emitir_documento(id_=factura.id, params=params, data=data)
    except sifen_client.SifenServiceError as exc:
        # Sin conexión: la factura ya existe en tu base (como hoy), queda
        # pendiente_envio para que el job de reintentos la procese después.
        factura.estado = "pendiente_envio"
        factura.observacion_sifen = str(exc)
        factura.save(update_fields=["estado", "observacion_sifen"])
        return factura

    if resultado.get("ok"):
        factura.cdc = resultado["cdc"]
        factura.id_lote = resultado["idLote"]
        factura.xml_firmado = resultado["xmlFirmado"]
        factura.estado = "en_espera"
    else:
        factura.estado = "rechazada"
        factura.observacion_sifen = resultado.get("error", "Rechazado por la SET")

    factura.save()
    return factura


def _reservar_numero(timbrado):
    with transaction.atomic():
        t = Timbrado.objects.select_for_update().get(pk=timbrado.pk)
        if t.numero_actual >= t.numero_fin:
            raise ValueError(f"Timbrado {t.establecimiento}-{t.punto_expedicion} agotado")
        numero = t.numero_actual + 1
        t.numero_actual = numero
        t.save(update_fields=['numero_actual'])
        return f"{numero:07d}"


def _armar_params(cfg):
    return {
        "version": 150,
        "fechaFirmaDigital": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "ruc": cfg.ruc,
        "razonSocial": cfg.nombre_empresa,
        "nombreFantasia": cfg.nombre_fantasia or cfg.nombre_empresa,
        "timbradoNumero": cfg.timbrado_numero,
        "timbradoFecha": cfg.fecha_inicio.strftime("%Y-%m-%d") if cfg.fecha_inicio else None,
        "tipoContribuyente": cfg.tipo_contribuyente,
        "tipoRegimen": cfg.tipo_regimen,
        "actividadesEconomicas": cfg.actividades_economicas or [],
        "establecimientos": [{
            "codigo": cfg.establecimiento,
            "direccion": cfg.direccion or "",
            "numeroCasa": "0",
            "departamento": cfg.departamento,
            "departamentoDescripcion": cfg.departamento_descripcion,
            "distrito": cfg.distrito,
            "distritoDescripcion": cfg.distrito_descripcion,
            "ciudad": cfg.ciudad,
            "ciudadDescripcion": cfg.ciudad_descripcion,
            "telefono": cfg.telefono or "",
            "email": "",
            "denominacion": "Casa Matriz",
        }],
    }


def emitir_pedido(pedido):
    """Genera la Factura electrónica para un Pedido con estado='pagado'.
    Devuelve la instancia de Factura (aprobada, rechazada, o pendiente si no
    hubo conexión con el sifen-service)."""
    cfg = Configuracion.objects.first()
    if not cfg:
        raise ValueError("No hay Configuracion cargada")

    timbrado = Timbrado.objects.get(
        establecimiento=cfg.establecimiento,
        punto_expedicion=cfg.punto_expedicion,
        activo=True,
    )
    numero = _reservar_numero(timbrado)

    data = pedido_a_data_sifen(
        pedido,
        establecimiento=cfg.establecimiento,
        punto=cfg.punto_expedicion,
        numero=numero,
        tipo_documento=1,
    )
    params = _armar_params(cfg)

    factura = Factura.objects.create(
        numero=f"{cfg.establecimiento}-{cfg.punto_expedicion}-{numero}",
        pedido=pedido,
        ruc_cliente=data["cliente"]["ruc"] or "44444444-7",
        nombre_cliente=data["cliente"]["razonSocial"],
        total=pedido.total,
        estado="pendiente_envio",
        establecimiento=cfg.establecimiento,
        punto_expedicion=cfg.punto_expedicion,
    )

    try:
        resultado = sifen_client.emitir_documento(id_=factura.id, params=params, data=data)
    except sifen_client.SifenServiceError as exc:
        # Sin conexión al sifen-service o a la SET: queda pendiente_envio para
        # que un job de reintentos lo procese después (contingencia).
        factura.observacion_sifen = str(exc)
        factura.save(update_fields=["observacion_sifen"])
        return factura

    if resultado.get("ok"):
        factura.cdc = resultado["cdc"]
        factura.id_lote = resultado["idLote"]
        factura.xml_firmado = resultado["xmlFirmado"]
        factura.estado = "en_espera"
    else:
        factura.estado = "rechazada"
        factura.observacion_sifen = resultado.get("error", "Rechazado por la SET")

    factura.save()
    return factura


def confirmar_lote(factura):
    """Llamar desde el job de reintentos: consulta el resultado del lote
    asíncrono y actualiza el estado de la Factura a 'generada' o 'rechazada'."""
    if not factura.id_lote:
        return factura
    resultado = sifen_client.consultar_lote(id_=factura.id, id_lote=factura.id_lote)
    # TODO: parsear el código de resultado real de consultaLote (varía si
    # está aprobado, rechazado o todavía en proceso) y setear factura.estado
    # en consecuencia. Dejar como referencia hasta ver la respuesta real en test.
    return resultado
