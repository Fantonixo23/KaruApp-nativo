const path = require('path');
const dotenv = require('dotenv');

const ENV_PATH = path.join(__dirname, '.env');

function required(name, fallback = undefined) {
  const value = process.env[name] ?? fallback;
  return value;
}

// El objeto exportado se lee dinámicamente desde process.env. Inicializamos
// en el arranque y `reload()` re-ejecuta dotenv para que los cambios hechos
// desde Django (pantalla de configuración SIFEN) surtan efecto sin reiniciar.
const config = {
  get port() { return parseInt(process.env.PORT || '4000', 10); },
  get serviceToken() { return required('SERVICE_TOKEN', ''); },
  get ambiente() { return required('SIFEN_AMBIENTE', 'test'); },
  get certPath() { return required('CERT_PATH', ''); },
  get certPassword() { return required('CERT_PASSWORD', ''); },
  get csc() { return required('CSC', ''); },
  get cscId() { return required('CSC_ID', '1'); },
  get mock() { return required('MOCK', 'true') === 'true'; },
  reload() {
    dotenv.config({ override: true, path: ENV_PATH });
  },
};

dotenv.config({ override: true, path: ENV_PATH });

module.exports = config;
