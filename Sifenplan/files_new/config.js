require('dotenv').config();

function required(name, fallback = undefined) {
  const value = process.env[name] ?? fallback;
  return value;
}

module.exports = {
  port: parseInt(process.env.PORT || '4000', 10),
  serviceToken: required('SERVICE_TOKEN', ''),
  ambiente: required('SIFEN_AMBIENTE', 'test'), // 'test' | 'prod'
  certPath: required('CERT_PATH', ''),
  certPassword: required('CERT_PASSWORD', ''),
  csc: required('CSC', ''),
  cscId: required('CSC_ID', '1'),
  // Modo simulación: genera el XML real (valida tu mapeo de datos) pero NO
  // firma ni envía nada a la SET — no requiere .p12, RUC ni CSC reales.
  // Poner MOCK=false (o sacar la variable) cuando tengas certificado real.
  mock: required('MOCK', 'true') === 'true',
};
