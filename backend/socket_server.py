#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pipperfood.settings')

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Inicializar Django
django.setup()

from django.core.asgi import get_asgi_application
from socketio import ASGIApp, AsyncServer
import uvicorn

# Importar las rutas de Django
django_app = get_asgi_application()

# Crear servidor Socket.IO
sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
)

# App ASGI que combina Django + Socket.IO
app = ASGIApp(sio, django_app)

@sio.event
async def connect(sid, environ):
    print(f'Cliente conectado: {sid}')
    await sio.emit('connected', {'message': 'Conectado al servidor', 'sid': sid})

@sio.event
async def disconnect(sid):
    print(f'Cliente desconectado: {sid}')

@sio.event
async def message(sid, data):
    print(f'Mensaje de {sid}: {data}')
    await sio.emit('message', data)

# Importar y configurar el módulo de eventos
import pipperfood.socket_events as socket_events
socket_events.sio = sio

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)