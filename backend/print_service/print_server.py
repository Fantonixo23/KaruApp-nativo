import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from printer_utils import listar_impresoras, detectar_impresora_termica, imprimir_texto
from escpos_builder import build_comanda, build_cuenta, build_factura, build_test_page, get_chars_per_line

HOST = '0.0.0.0'
PORT = 5123
TOKEN = os.environ.get('PRINT_API_TOKEN')
MAX_RETRIES = 3
RETRY_DELAY = 1
if not TOKEN:
    raise RuntimeError('PRINT_API_TOKEN no configurada. Defínala como variable de entorno.')


class PrintHandler(BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def _json(self, data, status=200):
        self.send_response(status)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _text(self, text, status=200):
        self.send_response(status)
        self._cors()
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(text.encode('utf-8'))

    def _check_auth(self):
        auth = self.headers.get('Authorization', '')
        expected = f'Bearer {TOKEN}'
        if auth != expected:
            self._json({'success': False, 'error': 'No autorizado'}, 401)
            return False
        return True

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self._json({'status': 'ok', 'servicio': 'karu-print'})

        elif self.path == '/printers':
            try:
                impresoras = listar_impresoras()
                self._json({'success': True, 'impresoras': impresoras})
            except Exception as e:
                self._json({'success': False, 'error': str(e)}, 500)

        else:
            self._json({'error': 'not found'}, 404)

    def do_POST(self):
        if not self._check_auth():
            return

        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            body = {}

        try:
            if self.path == '/print/comanda':
                return self._print_comanda(body)
            elif self.path == '/print/cuenta':
                return self._print_cuenta(body)
            elif self.path == '/print/factura':
                return self._print_factura(body)
            elif self.path == '/print/test':
                return self._print_test(body)
            else:
                self._json({'error': 'not found'}, 404)
        except Exception as e:
            import traceback
            print(f'[PrintServer ERROR] {e}')
            traceback.print_exc()
            self._json({'success': False, 'error': str(e)}, 500)

    def _get_printer(self, body):
        printer = body.get('impresora', '')
        if not printer:
            printer = detectar_impresora_termica()
        if not printer:
            raise Exception('No se encontr ninguna impresora. Configrela en Ajustes.')
        return printer

    def _get_size(self, body):
        size = body.get('tamano', 'normal')
        if isinstance(size, dict):
            if size.get('type') == 'custom':
                return size
            return 'normal'
        return size if size in ('pequeno', 'normal', 'grande') else 'normal'

    def _print_with_retry(self, printer, escpos):
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                imprimir_texto(printer, escpos)
                return
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))
        raise last_error

    def _print_comanda(self, body):
        printer = self._get_printer(body)
        size = self._get_size(body)
        pedido = body.get('pedido', {})
        negocio = body.get('negocio', {})
        escpos = build_comanda(pedido, negocio, size)
        self._print_with_retry(printer, escpos)
        self._json({'success': True, 'impresora': printer, 'tamano': size})

    def _print_cuenta(self, body):
        printer = self._get_printer(body)
        size = self._get_size(body)
        pedidos = body.get('pedidos', [])
        negocio = body.get('negocio', {})
        mesa = body.get('mesa', '')
        mesero_nombre = body.get('mesero_nombre', '')
        escpos = build_cuenta(pedidos, negocio, size, mesa, mesero_nombre)
        self._print_with_retry(printer, escpos)
        self._json({'success': True, 'impresora': printer, 'tamano': size})

    def _print_factura(self, body):
        printer = self._get_printer(body)
        size = self._get_size(body)
        pedido = body.get('pedido', {})
        negocio = body.get('negocio', {})
        cliente = body.get('cliente', {})
        factura = body.get('factura') or {}
        detalle_pagos = body.get('detalle_pagos', pedido.get('detalle_pagos', []))
        qr_base64 = body.get('qr_base64') or factura.get('qr_base64', '') or pedido.get('qr_base64', '')
        pedido['cdc'] = factura.get('cdc', '') or pedido.get('cdc', '')
        pedido['kude'] = factura.get('kude', '') or pedido.get('kude', '')
        pedido['detalle_pagos'] = detalle_pagos
        pedido['vuelto'] = body.get('vuelto', pedido.get('vuelto', 0))
        pedido['propina'] = body.get('propina', pedido.get('propina', 0))
        pedido['monto_recibido'] = body.get('monto_recibido', pedido.get('monto_recibido', 0))
        escpos = build_factura(pedido, negocio, cliente, size, qr_base64)
        self._print_with_retry(printer, escpos)
        self._json({'success': True, 'impresora': printer, 'tamano': size})

    def _print_test(self, body):
        printer = self._get_printer(body)
        size = self._get_size(body)
        escpos = build_test_page(printer, size)
        self._print_with_retry(printer, escpos)
        self._json({'success': True, 'impresora': printer, 'tamano': size})

    def log_message(self, format, *args):
        print(f'[PrintServer] {args[0]} {args[1]} {args[2]}')


if __name__ == '__main__':
    print(f' karuAPP Print Service iniciado en http://{HOST}:{PORT}')
    print(f' Endpoints:')
    print(f'   GET  /health    - Estado del servicio')
    print(f'   GET  /printers  - Listar impresoras')
    print(f'   POST /print/comanda - Imprimir comanda')
    print(f'   POST /print/cuenta  - Imprimir cuenta mesa')
    print(f'   POST /print/factura - Imprimir factura')
    print(f'   POST /print/test    - Pagina de prueba')
    server = HTTPServer((HOST, PORT), PrintHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n Servicio detenido')
        server.server_close()
