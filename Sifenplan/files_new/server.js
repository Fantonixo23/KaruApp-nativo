const express = require('express');
const config = require('./config');
const sifen = require('./sifen');

const app = express();
app.use(express.json({ limit: '5mb' }));

// Autenticación simple por token compartido con Django (SIFEN_SERVICE_TOKEN)
app.use((req, res, next) => {
  if (!config.serviceToken) return next(); // sin token configurado = sin auth (solo para pruebas locales)
  const header = req.headers['authorization'] || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : null;
  if (token !== config.serviceToken) {
    return res.status(401).json({ error: 'Token inválido o ausente' });
  }
  next();
});

function handleError(res, err) {
  console.error(err);
  res.status(500).json({ error: err?.message || 'Error interno del sifen-service' });
}

app.post('/documentos/emitir', async (req, res) => {
  const { id, params, data } = req.body || {};
  if (!params || !data) {
    return res.status(400).json({ error: 'Faltan params o data' });
  }
  try {
    const resultado = await sifen.emitirDocumento(id, params, data);
    res.json(resultado);
  } catch (err) {
    handleError(res, err);
  }
});

app.get('/lotes/:idLote', async (req, res) => {
  const { idLote } = req.params;
  const { id } = req.query;
  try {
    const resultado = await sifen.consultarLote(id, idLote);
    res.json(resultado);
  } catch (err) {
    handleError(res, err);
  }
});

app.post('/documentos/cancelar', async (req, res) => {
  const { id, params, data } = req.body || {};
  try {
    const resultado = await sifen.cancelarDocumento(id, params, data);
    res.json(resultado);
  } catch (err) {
    handleError(res, err);
  }
});

app.post('/documentos/inutilizar', async (req, res) => {
  const { id, params, data } = req.body || {};
  try {
    const resultado = await sifen.inutilizarNumeracion(id, params, data);
    res.json(resultado);
  } catch (err) {
    handleError(res, err);
  }
});

app.get('/ruc/:ruc', async (req, res) => {
  const { ruc } = req.params;
  const { id } = req.query;
  try {
    const resultado = await sifen.consultarRuc(id, ruc);
    res.json(resultado);
  } catch (err) {
    handleError(res, err);
  }
});

app.get('/cdc/:cdc', async (req, res) => {
  const { cdc } = req.params;
  const { id } = req.query;
  try {
    const resultado = await sifen.consultarCdc(id, cdc);
    res.json(resultado);
  } catch (err) {
    handleError(res, err);
  }
});

app.get('/health', (req, res) => {
  res.json({ ok: true, ambiente: config.ambiente });
});

app.listen(config.port, () => {
  console.log(`sifen-service escuchando en http://127.0.0.1:${config.port} (ambiente: ${config.ambiente})`);
});
