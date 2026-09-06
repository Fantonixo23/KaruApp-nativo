const xmlgen = require('facturacionelectronicapy-xmlgen').default;
const xmlsign = require('facturacionelectronicapy-xmlsign').default;
const qrgen = require('facturacionelectronicapy-qrgen').default;
const setApi = require('facturacionelectronicapy-setapi').default;
const config = require('./config');

/** Extrae el CDC (44 dígitos) del atributo Id del nodo <DE> del XML generado. */
function extraerCDC(xml) {
  const match = xml.match(/Id="(\d{44})"/);
  return match ? match[1] : null;
}

/**
 * Genera, firma, agrega QR y envía un Documento Electrónico a la SET.
 * `id` es un identificador de correlación (usamos el id de Factura de Django).
 * `params`/`data` vienen tal cual arma facturacion/services/emision.py del lado Django.
 */
async function emitirDocumento(id, params, data) {
  // 1) Generar el XML del DE a partir de params/data — esto SIEMPRE es real,
  // con o sin modo simulación, porque no necesita certificado. Es la parte
  // que de verdad valida que tu mapeo Django -> SIFEN está bien armado.
  const xml = await xmlgen.generateXMLDE(params, data);
  const cdc = extraerCDC(xml);

  if (config.mock) {
    // MODO SIMULACIÓN: no firma ni envía nada a la SET. Sirve para probar
    // todo el circuito (Django -> sifen-service -> Django -> UI) sin
    // certificado, RUC ni CSC reales. El xml generado es real; la
    // "aprobación" de acá abajo es inventada.
    console.log(`[MOCK] Documento ${id} generado (sin firmar ni enviar). CDC: ${cdc}`);
    return {
      ok: true,
      cdc,
      idLote: `MOCK-${Date.now()}`,
      xmlFirmado: xml, // sin firmar de verdad, es el XML plano
      datetime: new Date().toISOString(),
      mock: true,
    };
  }

  // 2) Firmar el XML con el certificado .p12
  const xmlFirmado = await xmlsign.signXML(xml, config.certPath, config.certPassword);

  // 3) Insertar el código QR (requiere CSC/CSC_ID de la SET)
  const xmlConQR = await qrgen.generateQR(xmlFirmado, config.cscId, config.csc, config.ambiente);

  // 4) Enviar a la SET como lote (respuesta asíncrona: idLote a confirmar después)
  const respuestaLote = await setApi.recibeLote(id, [xmlConQR], config.ambiente, config.certPath, config.certPassword);

  // NOTA: la forma exacta de `respuestaLote` (nombres de campos de aceptado/rechazado
  // al encolar) hay que confirmarla contra una respuesta real del ambiente de test —
  // esto es lo mismo que el TODO que ya señalaba emision.py del lado Django.
  // Devolvemos la respuesta cruda además de los campos que sabemos con certeza
  // (cdc, xmlFirmado) para no perder información mientras se termina de mapear.
  const idLote = respuestaLote?.dProtConsLote || respuestaLote?.idLote || respuestaLote?.id || null;
  const rechazado = respuestaLote?.dCodRes && String(respuestaLote.dCodRes) !== '0300'; // 0300 = "Lote recibido con éxito" (verificar contra doc real)

  if (rechazado) {
    return {
      ok: false,
      error: respuestaLote?.dMsgRes || 'Rechazado al encolar en la SET',
      raw: respuestaLote,
    };
  }

  return {
    ok: true,
    cdc,
    idLote,
    xmlFirmado: xmlConQR,
    datetime: new Date().toISOString(),
    raw: respuestaLote,
  };
}

async function consultarLote(id, idLote) {
  if (config.mock) {
    console.log(`[MOCK] Consulta de lote ${idLote} (documento ${id}) -> aprobado simulado`);
    return { dCodRes: '0362', dMsgRes: 'Aprobado (simulado)', mock: true };
  }
  return setApi.consultaLote(id, idLote, config.ambiente, config.certPath, config.certPassword);
}

async function cancelarDocumento(id, params, data) {
  const xml = await xmlgen.generateXMLEventoCancelacion(id, params, data);
  if (config.mock) {
    console.log(`[MOCK] Cancelación simulada para documento ${id}`);
    return { ok: true, mock: true };
  }
  const xmlFirmado = await xmlsign.signXMLEvento(xml, config.certPath, config.certPassword);
  return setApi.evento(id, xmlFirmado, config.ambiente, config.certPath, config.certPassword);
}

async function inutilizarNumeracion(id, params, data) {
  const xml = await xmlgen.generateXMLEventoInutilizacion(id, params, data);
  if (config.mock) {
    console.log(`[MOCK] Inutilización simulada para documento ${id}`);
    return { ok: true, mock: true };
  }
  const xmlFirmado = await xmlsign.signXMLEvento(xml, config.certPath, config.certPassword);
  return setApi.evento(id, xmlFirmado, config.ambiente, config.certPath, config.certPassword);
}

async function consultarRuc(id, ruc) {
  if (config.mock) {
    console.log(`[MOCK] Consulta RUC ${ruc} simulada`);
    return { dCodRes: '0502', dMsgRes: 'RUC Existente (simulado)', mock: true };
  }
  return setApi.consultaRUC(id, ruc, config.ambiente, config.certPath, config.certPassword);
}

async function consultarCdc(id, cdc) {
  if (config.mock) {
    console.log(`[MOCK] Consulta CDC ${cdc} simulada`);
    return { encontrado: true, mock: true };
  }
  return setApi.consulta(id, cdc, config.ambiente, config.certPath, config.certPassword);
}

module.exports = {
  emitirDocumento,
  consultarLote,
  cancelarDocumento,
  inutilizarNumeracion,
  consultarRuc,
  consultarCdc,
};
