"""
facturacion/services/mapper.py

Traduce un Pedido (con estado='pagado') al 'data' que espera xmlgen.
Basado en los campos reales de apps/pedidos/models.py y apps/productos/models.py.
"""
import random
from decimal import Decimal
from apps.productos.models import Producto


def _item_a_sifen(item_json):
    """item_json es uno de los dicts que ya guarda Pedido.items, ej:
    {'producto_id': 12, 'producto_nombre': 'Milanesa', 'cantidad': 2,
     'precio': '35000', 'variante': None, 'nota': ''}
    Se busca el Producto para tomar su tasa de IVA real (no la del pedido)."""
    producto = Producto.objects.filter(pk=item_json.get('producto_id')).first()
    iva_tipo_map = {0: 3, 5: 2, 10: 1}  # SIFEN: 1=Gravado 10%, 2=Gravado 5%, 3=Exento
    iva_pct = producto.iva if producto else 10
    if iva_pct not in (0, 5, 10):
        # Salvavidas: si quedó cargado un 15% u otro valor no válido para SIFEN,
        # no mandamos basura a la SET — mejor fallar temprano y visible.
        raise ValueError(
            f"Producto '{item_json.get('producto_nombre')}' tiene IVA {iva_pct}%, "
            f"no soportado por SIFEN (solo 0, 5 o 10%). Corregí el producto antes de facturar."
        )

    cantidad = Decimal(str(item_json.get('cantidad', 1)))
    precio = Decimal(str(item_json.get('precio', 0)))
    # precio unitario informado ya incluye IVA (así lo maneja tu POS); xmlgen
    # espera precioUnitario "gravado" según ivaTipo — ver Manual Técnico 3.6
    # para el detalle de cómo se descompone base/IVA a partir del precio final.

    return {
        "codigo": str(item_json.get('producto_id', '')),
        "descripcion": item_json.get('producto_nombre', 'Producto'),
        "observacion": item_json.get('nota', '') or '',
        "unidadMedida": 77,  # 77 = unidad
        "cantidad": float(cantidad),
        "precioUnitario": float(precio),
        "cambio": 0,
        "descuento": 0,
        "anticipo": 0,
        "pais": "PRY",
        "paisDescripcion": "Paraguay",
        "ivaTipo": iva_tipo_map[iva_pct],
        "ivaBase": 100,
        "iva": iva_pct,
    }


def _condicion_pago(pedido, total_cobrado):
    # tipo: 1 = contado. Tu Pedido no maneja crédito, así que siempre contado.
    metodo_a_tipo_entrega = {
        'efectivo': 1,
        'tarjeta': 3,
        'transferencia': 4,
        'qr': 4,
        'mixto': 1,  # si es mixto, se listan detalle_pagos abajo
    }
    entregas = []
    if pedido.detalle_pagos:
        for pago in pedido.detalle_pagos:
            entregas.append({
                "tipo": metodo_a_tipo_entrega.get(pago.get('metodo'), 1),
                "monto": str(int(Decimal(str(pago.get('monto_pyg', pago.get('monto', 0)))))),
                "moneda": "PYG",
                "cambio": 0,
            })
    else:
        entregas.append({
            "tipo": metodo_a_tipo_entrega.get(pedido.metodo_pago, 1),
            "monto": str(int(total_cobrado)),
            "moneda": "PYG",
            "cambio": 0,
        })
    return {"tipo": 1, "entregas": entregas}


def pedidos_a_data_sifen(pedidos, establecimiento, punto, numero, tipo_documento=1):
    """pedidos: iterable/queryset de Pedido ya marcados 'pagado' (una mesa puede
    cobrarse con varios pedidos juntos en una sola factura). Todos comparten
    cliente_tipo/cliente_ruc/cliente_nombre/detalle_pagos porque cobrar_mesa
    los setea igual a todos en el mismo cobro."""
    pedidos = list(pedidos)
    primero = pedidos[0]

    items = []
    propina_total = 0
    total_cobrado = 0
    for p in pedidos:
        items.extend(_item_a_sifen(it) for it in (p.items or []))
        propina_total += float(p.propina or 0)
        total_cobrado += float(p.total or 0)

    if not items:
        raise ValueError("La mesa no tiene items, no se puede facturar")

    return _armar_data(
        primero, items, propina_total, total_cobrado, establecimiento, punto, numero, tipo_documento
    )


def pedido_a_data_sifen(pedido, establecimiento, punto, numero, tipo_documento=1):
    """Variante para un solo Pedido (delivery, venta suelta, etc)."""
    items = [_item_a_sifen(it) for it in (pedido.items or [])]
    if not items:
        raise ValueError(f"Pedido {pedido.id} no tiene items, no se puede facturar")
    return _armar_data(
        pedido, items, float(pedido.propina or 0), float(pedido.total or 0),
        establecimiento, punto, numero, tipo_documento
    )


def _armar_data(pedido, items, propina_total, total_cobrado, establecimiento, punto, numero, tipo_documento):
    tiene_ruc = pedido.cliente_tipo == 'factura' and pedido.cliente_ruc
    items = list(items)

    data = {
        "tipoDocumento": tipo_documento,
        "establecimiento": establecimiento,
        "punto": punto,
        "numero": numero,
        # Requerido por la librería (probado contra la versión real instalada):
        # 9 dígitos, elegido al armar el documento, va tal cual en el CDC.
        "codigoSeguridadAleatorio": str(random.randint(0, 999999999)).zfill(9),
        "descripcion": f"Venta KaruApp #{pedido.numero_orden}",
        "observacion": "",
        "fecha": pedido.updated_at.strftime("%Y-%m-%dT%H:%M:%S"),
        "tipoEmision": 1,
        "tipoTransaccion": 1,
        "tipoImpuesto": 1,
        "moneda": "PYG",
        "condicionAnticipo": 1,
        "condicionTipoCambio": 1,
        "descuentoGlobal": 0,
        "anticipoGlobal": 0,
        "cambio": 0,
        "cliente": {
            "contribuyente": bool(tiene_ruc),
            "ruc": pedido.cliente_ruc if tiene_ruc else None,
            "razonSocial": pedido.cliente_nombre or "Consumidor Final",
            "tipoOperacion": 1 if tiene_ruc else 2,
            "pais": "PRY",
            "paisDescripcion": "Paraguay",
            "documentoTipo": 1,
            "documentoNumero": pedido.cliente_ruc.split('-')[0] if not tiene_ruc else "",
        },
        "usuario": {
            "documentoTipo": 1,
            # OJO: tu modelo Usuario no guarda número de documento (CI) hoy.
            # Poné acá el CI real del mesero/cajero, o agregá el campo a Usuario.
            "documentoNumero": "0",
            "nombre": pedido.mesero.nombre if pedido.mesero else "Sistema",
            "cargo": pedido.mesero.get_rol_display() if pedido.mesero else "",
        },
        "condicion": _condicion_pago(pedido, total_cobrado),
        "items": items,
        # Requerido por la librería para Factura (tipoDocumento=1):
        # 1 = Operación presencial (el caso normal en un restaurante).
        "factura": {"presencia": 1},
    }

    if propina_total > 0:
        # La propina no es parte del precio del producto ni lleva IVA
        # discriminado igual — se agrega como línea aparte exenta.
        data["items"].append({
            "codigo": "PROPINA",
            "descripcion": "Propina voluntaria",
            "unidadMedida": 77,
            "cantidad": 1,
            "precioUnitario": propina_total,
            "cambio": 0,
            "descuento": 0,
            "anticipo": 0,
            "pais": "PRY",
            "paisDescripcion": "Paraguay",
            "ivaTipo": 3,  # exento
            "ivaBase": 100,
            "iva": 0,
        })

    return data
