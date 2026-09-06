# Cómo aplicar esto a tu proyecto real

Estos archivos salieron de correr TU proyecto real (backend/) en una copia de
prueba: migré una base descartable, creé un Pedido real, y `emitir_para_factura`
guardó una Factura con CDC válido de 44 dígitos contra el sifen-service en
modo simulación. Funcionó de punta a punta.

## Reemplazar (son el archivo completo, no un patch)
- `apps/facturacion/models.py` → reemplaza tu `backend/apps/facturacion/models.py`
- `apps/pedidos/views.py` → reemplaza tu `backend/apps/pedidos/views.py`
  (el único cambio real está en `cobrar_mesa`, línea ~1105, el resto del
  archivo queda idéntico al tuyo)
- `pipperfood/settings.py` → reemplaza tu `backend/pipperfood/settings.py`
  (los únicos agregados son SIFEN_SERVICE_URL y SIFEN_SERVICE_TOKEN al final)

## Copiar (son archivos nuevos)
- `apps/facturacion/services/` (carpeta completa) → a
  `backend/apps/facturacion/services/`
- `apps/facturacion/0012_configuracion_actividades_economicas_and_more.py` →
  a `backend/apps/facturacion/migrations/` (respetá el nombre del archivo)

## Después de copiar todo

```bash
cd backend
python manage.py migrate
```

No hace falta correr `makemigrations` de nuevo — la migración 0012 ya está
generada y probada.

## Para probar en tu máquina, en modo simulación (sin certificado)

1. Levantá `sifen-service` (el otro zip que te pasé) con `MOCK=true`.
2. En tu `.env` de Django (o variables de entorno), poné:
   ```
   SIFEN_SERVICE_URL=http://127.0.0.1:4000
   SIFEN_SERVICE_TOKEN=el-mismo-token-que-en-sifen-service/.env
   ```
3. Cargá `Configuracion` con datos de prueba (RUC inventado tipo
   `80012345-6`, `fecha_inicio` con una fecha real, `establecimiento`/
   `punto_expedicion` en `001`), y un `Timbrado` activo.
4. Cobrá una mesa con la casilla "generar factura" tildada. Debería quedar
   la `Factura` en estado `en_espera` con un CDC de 44 dígitos.

## Un detalle real que encontré al probarlo

`Configuracion.fecha_inicio` tiene que tener una fecha válida — si queda
vacío, la SET (o el mock) rechaza el documento porque no puede armar
`timbradoFecha`. No es un bug del código, es un dato que hay que cargar sí o
sí en el panel de configuración antes de emitir cualquier cosa.
