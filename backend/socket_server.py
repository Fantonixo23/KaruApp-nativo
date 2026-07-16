#!/usr/bin/env python
import os
import sys
import logging
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(str(LOG_DIR / 'django.log'), encoding='utf-8'),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger('karuapp')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pipperfood.settings')

sys.path.insert(0, str(BASE_DIR))

import django
django.setup()

from django.core.asgi import get_asgi_application
from socketio import ASGIApp, AsyncServer
import uvicorn

django_app = get_asgi_application()

sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
)

app = ASGIApp(sio, django_app)

@sio.event
async def connect(sid, environ):
    logger.info(f'Cliente conectado: {sid}')

@sio.event
async def disconnect(sid):
    logger.info(f'Cliente desconectado: {sid}')

@sio.event
async def message(sid, data):
    logger.info(f'Mensaje de {sid}: {data}')

import pipperfood.socket_events as socket_events
socket_events.sio = sio

if __name__ == '__main__':
    logger.info('Iniciando servidor Django + Socket.IO en puerto 8000')
    uvicorn.run(app, host='0.0.0.0', port=8000, log_config={
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s [%(levelname)s] %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'file': {
                'class': 'logging.FileHandler',
                'filename': str(LOG_DIR / 'uvicorn.log'),
                'formatter': 'default',
                'encoding': 'utf-8',
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
        },
        'root': {
            'level': 'INFO',
            'handlers': ['file', 'console'],
        },
    })