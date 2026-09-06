# sifen-service

Microservicio Node local que firma y envía los documentos electrónicos de KaruApp
a la SET (Paraguay). Django nunca genera ni firma XML directamente — le manda a
este servicio los datos por HTTP y recibe el resultado (ver
`apps/facturacion/services/sifen_client.py`).

Usa librerías npm ya hechas y mantenidas para Paraguay (autor `marcosjara`,
MIT), en vez de generar/firmar el XML a mano:

- `facturacionelectronicapy-xmlgen` — arma el XML del Documento Electrónico.
- `facturacionelectronicapy-xmlsign` — lo firma con tu certificado `.p12`.
- `facturacionelectronicapy-qrgen` — agrega el código QR (usa tu CSC).
- `facturacionelectronicapy-setapi` — lo envía a la SET por SOAP y consulta resultados.

## Instalación

Requiere Node.js instalado (LTS, 18 o superior).

```bash
cd sifen-service
npm install
copy .env.example .env
```

Editar `.env` con tus datos reales:

- `SERVICE_TOKEN`: una cadena larga y aleatoria (debe coincidir con
  `SIFEN_SERVICE_TOKEN` en el `settings.py` de Django).
- `MOCK`: **dejalo en `true`** mientras no tengas certificado ni RUC de
  facturador. Genera el XML real (valida tu mapeo de datos) pero salta la
  firma y el envío a la SET, devolviendo una aprobación simulada. Pasalo a
  `false` recién cuando tengas certificado real y estés homologado.
- `SIFEN_AMBIENTE`: `test` mientras no estés homologado, `prod` después.
- `CERT_PATH` / `CERT_PASSWORD`: ruta al `.p12` de tu certificado y su clave
  (solo hace falta con `MOCK=false`).
- `CSC` / `CSC_ID`: te los da la SET al habilitarte como facturador electrónico
  (solo hace falta con `MOCK=false`).

## Arrancar

En Windows, doble clic a `iniciar_sifen_service.bat` (instala dependencias la
primera vez y después arranca el servicio). Manual:

```bash
npm start
```

Por defecto escucha en `http://127.0.0.1:4000`. Probar que está vivo:

```bash
curl http://127.0.0.1:4000/health
```

## Endpoints (los que ya espera `sifen_client.py` de Django)

| Método | Ruta | Uso |
|---|---|---|
| POST | `/documentos/emitir` | Generar, firmar, agregar QR y enviar un DE |
| GET  | `/lotes/:idLote` | Consultar resultado de un lote enviado |
| POST | `/documentos/cancelar` | Cancelar un documento ya aprobado |
| POST | `/documentos/inutilizar` | Inutilizar un rango de numeración no usado |
| GET  | `/ruc/:ruc` | Consultar un RUC en la SET |
| GET  | `/cdc/:cdc` | Consultar un documento por su CDC |

## Pendiente real (no adivinado, hay que probarlo contra el ambiente de test)

- **Formato de respuesta de `recibeLote`/`consultaLote`**: el código en
  `src/sifen.js` asume campos (`dCodRes`, `dMsgRes`, `dProtConsLote`) según la
  nomenclatura típica de la SET, pero **no están verificados contra una
  respuesta real** — hay que ajustarlos la primera vez que se pruebe en
  homologación. Está señalado con comentarios `// TODO` en el código.
- **Inutilización de numeración**: el método de `xmlgen` para este evento no
  se confirmó contra la documentación del paquete. Revisar el README de
  `facturacionelectronicapy-xmlgen` antes de usar `/documentos/inutilizar`.
- **`params`/`data`** que llegan desde Django no incluyen todavía el bloque
  completo que exige `generateXMLDE` (por ejemplo, forma de pago detallada,
  actividades económicas del emisor) — puede hacer falta revisar el README de
  `facturacionelectronicapy-xmlgen` y completar campos en
  `apps/facturacion/services/mapper.py` y `emision.py` la primera vez que se
  pruebe una emisión real.
