import logging

logger = logging.getLogger(__name__)

sio = None

def _emit_event(event_name, data):
    if not sio:
        return
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    async def _emit():
        await sio.emit(event_name, data)
    try:
        loop.run_until_complete(_emit())
    except Exception as e:
        logger.warning(f'Error emitiendo evento socket {event_name}: {e}')

def emit_mesa_update(mesa):
    _emit_event('mesa_update', {'type': 'mesa_update', 'mesa': mesa})

def emit_pedido_update(pedido):
    _emit_event('pedido_update', {'type': 'pedido_update', 'pedido': pedido})

def emit_nuevo_pedido_cocina(pedido):
    _emit_event('nuevo_pedido_cocina', {'type': 'nuevo_pedido_cocina', 'pedido': pedido})

def emit_pedido_modificado(pedido):
    _emit_event('pedido_modificado', {'type': 'pedido_modificado', 'pedido': pedido})

def emit_cobro(cobro):
    _emit_event('cobro', {'type': 'cobro', 'cobro': cobro})