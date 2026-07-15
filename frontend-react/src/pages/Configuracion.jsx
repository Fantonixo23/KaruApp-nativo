import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useStore } from '../store/useStore'
import Sidebar from '../components/Sidebar'
import { formatGuarani } from '../utils/currency'
import { getApiUrl } from '../utils/api'

const API_URL = getApiUrl()

const ICONOS_DISPONIBLES = [
  'payments', 'credit_card', 'account_balance', 'qr_code', 'qr_code_scanner',
  'wallet', 'money', 'receipt', 'currency_exchange', 'paid',
  'smartphone', 'phone_iphone', 'tap_and_play', 'contactless',
  'check_circle', 'done_all', 'shopping_cart', 'point_of_sale'
]

export default function Configuracion() {
  const darkMode = useStore((state) => state.darkMode)
  const toggleDarkMode = useStore((state) => state.toggleDarkMode)
  const initDarkMode = useStore((state) => state.initDarkMode)
  const syncDarkMode = useStore((state) => state.syncDarkMode)

  useEffect(() => { initDarkMode(); syncDarkMode() }, [])

  const [datos, setDatos] = useState({
    nombre_empresa: '',
    ruc: '',
    direccion: '',
    telefono: '',
    timbrado_numero: '',
    establecimiento: '001',
    punto_expedicion: '001'
  })
  const [guardando, setGuardando] = useState(false)
  const [mensaje, setMensaje] = useState('')

  const [metodos, setMetodos] = useState([])
  const [metodoForm, setMetodoForm] = useState({ nombre: '', etiqueta: '', icono: 'payments', color: '#4CAF50', activo: true, orden: 0 })
  const [editMetodoId, setEditMetodoId] = useState(null)
  const [showMetodoModal, setShowMetodoModal] = useState(false)
  const [metodoMsg, setMetodoMsg] = useState('')

  const [logoPreview, setLogoPreview] = useState(() => localStorage.getItem('pipper_logo_base64') || '')
  const logoInputRef = useRef(null)
  const [printerName, setPrinterName] = useState(() => localStorage.getItem('pipper_printer_name') || localStorage.getItem('qz_printer_name') || '')
  const [paperSize, setPaperSize] = useState(() => localStorage.getItem('pipper_paper_size') || '58mm')

  useEffect(() => {
    cargarDatos()
    cargarMetodos()
  }, [])

  const cargarMetodos = async () => {
    try {
      const res = await fetch(`${API_URL}/facturacion/metodos-pago`)
      const data = await res.json()
      if (data.success) setMetodos(data.metodos || [])
    } catch {}
  }

  const abrirMetodoModal = (metodo = null) => {
    if (metodo) {
      setMetodoForm({
        nombre: metodo.nombre,
        etiqueta: metodo.etiqueta,
        icono: metodo.icono,
        color: metodo.color,
        activo: metodo.activo,
        orden: metodo.orden
      })
      setEditMetodoId(metodo.id)
    } else {
      setMetodoForm({ nombre: '', etiqueta: '', icono: 'payments', color: '#4CAF50', activo: true, orden: metodos.length + 1 })
      setEditMetodoId(null)
    }
    setMetodoMsg('')
    setShowMetodoModal(true)
  }

  const guardarMetodo = async () => {
    if (!metodoForm.nombre || !metodoForm.etiqueta) {
      setMetodoMsg('Nombre y etiqueta son requeridos')
      return
    }
    try {
      const url = editMetodoId
        ? `${API_URL}/facturacion/metodos-pago/${editMetodoId}/editar`
        : `${API_URL}/facturacion/metodos-pago/crear`
      const res = await fetch(url, {
        method: editMetodoId ? 'PUT' : 'POST',
        body: JSON.stringify(metodoForm)
      })
      const data = await res.json()
      if (data.success) {
        setShowMetodoModal(false)
        setMetodoMsg('')
        cargarMetodos()
      } else {
        setMetodoMsg(data.error || 'Error al guardar')
      }
    } catch {
      setMetodoMsg('Error de conexión')
    }
  }

  const eliminarMetodo = async (id) => {
    if (!confirm('¿Eliminar este método de pago?')) return
    try {
      const res = await fetch(`${API_URL}/facturacion/metodos-pago/${id}/eliminar`, { method: 'DELETE' })
      const data = await res.json()
      if (data.success) {
        cargarMetodos()
      }
    } catch {}
  }

  const cargarDatos = async () => {
    try {
      const res = await fetch(`${API_URL}/facturacion/config`)
      const data = await res.json()
      if (data.success && data.config) {
        setDatos({
          nombre_empresa: data.config.nombre_empresa || '',
          ruc: data.config.ruc || '',
          direccion: data.config.direccion || '',
          telefono: data.config.telefono || '',
          timbrado_numero: data.config.timbrado_numero || '001-001-0000001',
          establecimiento: data.config.establecimiento || '001',
          punto_expedicion: data.config.punto_expedicion || '001',
          tamano_papel: data.config.tamano_papel || '58mm'
        })
        if (data.config.tamano_papel) {
          setPaperSize(data.config.tamano_papel)
          localStorage.setItem('pipper_paper_size', data.config.tamano_papel)
        }
      }
    } catch (e) {
      console.error('Error:', e)
    }
  }

  const guardar = async () => {
    if (!datos.nombre_empresa || !datos.ruc) {
      setMensaje('Complete los campos requeridos')
      return
    }
    
    setGuardando(true)
    setMensaje('')
    
    try {
      const res = await fetch(`${API_URL}/facturacion/config/actualizar`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...datos, tamano_papel: paperSize })
      })
      const data = await res.json()
      
      if (data.success) {
        setMensaje('✅ Datos guardados correctamente')
      } else {
        setMensaje(data.error || 'Error al guardar')
      }
    } catch (e) {
      setMensaje('Error de conexión')
    }
    
    setGuardando(false)
  }

  return (
    <div style={{ ...s.container(darkMode), display: 'flex', flexDirection: 'column' }}>
      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .animate { animation: fadeIn 0.3s ease-out; }
        .cfg-input, .cfg-select, .cfg-textarea {
          width: 100%; padding: 11px 14px; font-size: 14px; border-radius: 10px;
          border: 1px solid ${darkMode ? 'rgba(255,255,255,0.15)' : '#d0d0d0'};
          background: ${darkMode ? '#2a2a2a' : '#f8f8f8'};
          color: ${darkMode ? 'white' : '#1a1a1a'};
          outline: none; box-sizing: border-box; transition: border 0.15s;
        }
        .cfg-input:focus, .cfg-select:focus, .cfg-textarea:focus { border-color: #FF9800; }
      `}</style>
      
      <header style={{ ...s.header, flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Link to="/app/inicio" style={s.btnHeader}><span className="material-icons">home</span></Link>
          <img src="/logo.png" alt="karuAPP" style={{ width: '28px', height: '28px', borderRadius: '6px' }} />
          <span style={s.title}>Configuración</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button onClick={toggleDarkMode} style={s.btnHeader}><span className="material-icons">{darkMode ? 'dark_mode' : 'light_mode'}</span></button>
        </div>
      </header>

      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <Sidebar activePath="/app/configuracion" />
        <div style={{ flex: 1, overflow: 'auto' }}>
          <div style={s.content}>
        <div style={s.card(darkMode)} className="animate">
          <h2 style={s.cardTitle(darkMode)}>Datos de la Empresa</h2>
          <p style={s.subtitle(darkMode)}>Estos datos aparecen en los tickets y facturas</p>
          
          <div style={s.field}>
            <label style={s.label(darkMode)}>Nombre del Restaurante *</label>
            <input 
              type="text"
              value={datos.nombre_empresa}
              onChange={(e) => setDatos({...datos, nombre_empresa: e.target.value})}
              placeholder="Mi Restaurante"
              style={s.input(darkMode)}
            />
          </div>
          
          <div style={s.field}>
            <label style={s.label(darkMode)}>RUC *</label>
            <input 
              type="text"
              value={datos.ruc}
              onChange={(e) => setDatos({...datos, ruc: e.target.value})}
              placeholder="80012345-7"
              style={s.input(darkMode)}
            />
          </div>
          
          <div style={s.field}>
            <label style={s.label(darkMode)}>Dirección</label>
            <input 
              type="text"
              value={datos.direccion}
              onChange={(e) => setDatos({...datos, direccion: e.target.value})}
              placeholder="Ciudad, Paraguay"
              style={s.input(darkMode)}
            />
          </div>
          
          <div style={s.field}>
            <label style={s.label(darkMode)}>Teléfono</label>
            <input 
              type="text"
              value={datos.telefono}
              onChange={(e) => setDatos({...datos, telefono: e.target.value})}
              placeholder="021-123456"
              style={s.input(darkMode)}
            />
          </div>
        </div>

        <div style={s.card(darkMode)} className="animate">
          <h2 style={s.cardTitle(darkMode)}>📋 Datos de Facturación</h2>
          <p style={s.subtitle(darkMode)}>Configuración del timbrado SET</p>
          
          <div style={s.field}>
            <label style={s.label(darkMode)}>Número de Timbrado</label>
            <input 
              type="text"
              value={datos.timbrado_numero}
              onChange={(e) => setDatos({...datos, timbrado_numero: e.target.value})}
              placeholder="001-001-0000001"
              style={s.input(darkMode)}
            />
          </div>
          
          <div style={{ display: 'flex', gap: '10px' }}>
            <div style={{...s.field, flex: 1}}>
              <label style={s.label(darkMode)}>Establecimiento</label>
              <input 
                type="text"
                value={datos.establecimiento}
                onChange={(e) => setDatos({...datos, establecimiento: e.target.value})}
                placeholder="001"
                style={s.input(darkMode)}
              />
            </div>
            <div style={{...s.field, flex: 1}}>
              <label style={s.label(darkMode)}>Punto Expedición</label>
              <input 
                type="text"
                value={datos.punto_expedicion}
                onChange={(e) => setDatos({...datos, punto_expedicion: e.target.value})}
                placeholder="001"
                style={s.input(darkMode)}
              />
            </div>
          </div>
        </div>

        {/* MÉTODOS DE PAGO */}
        <div style={s.card(darkMode)} className="animate">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <h2 style={s.cardTitle(darkMode)}>💳 Métodos de Pago</h2>
            <button onClick={() => abrirMetodoModal(null)} style={{
              padding: '8px 16px', border: 'none', borderRadius: '8px',
              background: '#4CAF50', color: 'white', fontWeight: '700', fontSize: '13px', cursor: 'pointer'
            }}>+ Agregar</button>
          </div>
          <p style={s.subtitle(darkMode)}>Estos métodos aparecen al cobrar en Caja</p>

          {metodos.length === 0 ? (
            <p style={{ color: '#999', fontSize: '13px', textAlign: 'center', padding: '20px' }}>No hay métodos de pago configurados</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {metodos.map((m) => (
                <div key={m.id} style={{
                  display: 'flex', alignItems: 'center', gap: '12px',
                  padding: '10px 14px', borderRadius: '10px',
                  background: '#f9f9f9', border: '1px solid #eee',
                  opacity: m.activo ? 1 : 0.5
                }}>
                  <span className="material-icons" style={{ color: m.color, fontSize: '24px' }}>{m.icono}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: '700', fontSize: '14px', color: '#333' }}>{m.etiqueta}</div>
                    <div style={{ fontSize: '11px', color: '#999' }}>/{m.nombre} · Orden {m.orden}</div>
                  </div>
                  <button onClick={() => abrirMetodoModal(m)} style={{
                    padding: '6px 10px', border: '2px solid #ddd', borderRadius: '8px',
                    background: 'white', cursor: 'pointer', fontSize: '12px', color: '#666'
                  }}>✏️</button>
                  <button onClick={() => eliminarMetodo(m.id)} style={{
                    padding: '6px 10px', border: '2px solid #E53935', borderRadius: '8px',
                    background: 'white', cursor: 'pointer', fontSize: '12px', color: '#E53935'
                  }}>🗑️</button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* CONFIGURACIÓN DE IMPRESIÓN TÉRMICA */}
        <div style={s.card(darkMode)} className="animate">
          <h2 style={s.cardTitle(darkMode)}>🖨️ Impresión Térmica</h2>
          <p style={s.subtitle(darkMode)}>Configuración de la impresora térmica para tickets y comandas</p>

          <div style={s.field}>
            <label style={s.label(darkMode)}>Impresora</label>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <input
                type="text"
                value={printerName}
                onChange={(e) => {
                  setPrinterName(e.target.value)
                  localStorage.setItem('pipper_printer_name', e.target.value)
                }}
                placeholder="Nombre exacto (dejar vacío = predeterminada)"
                style={{ ...s.input(darkMode), flex: 1 }}
              />
              <button
                onClick={async () => {
                  try {
                    const token = await (await fetch(`${API_URL}/print-token`)).json()
                    const res = await fetch('http://localhost:5123/printers', {
                      headers: { 'Authorization': 'Bearer ' + (token.token || 'pipper-print-token-default') }
                    })
                    const data = await res.json()
                    if (data.success && data.impresoras.length > 0) {
                      alert('Impresoras disponibles:\n' + data.impresoras.join('\n'))
                    } else {
                      alert('No se encontraron impresoras.\nAsegúrate de que el Servicio de Impresión esté iniciado (iniciar.bat)')
                    }
                  } catch (e) {
                    alert('Error: ' + e.message + '\n\nAsegúrate de que el Servicio de Impresión esté iniciado (iniciar.bat)')
                  }
                }}
                style={{
                  padding: '10px 14px', border: 'none', borderRadius: '10px',
                  background: '#FF9800', color: 'white', fontWeight: '700', fontSize: '12px', cursor: 'pointer', whiteSpace: 'nowrap'
                }}
              >
                🔍 Buscar
              </button>
            </div>
          </div>

          <div style={s.field}>
            <label style={s.label(darkMode)}>Tamaño del papel</label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => {
                  setPaperSize('58mm')
                  localStorage.setItem('pipper_paper_size', '58mm')
                }}
                style={{
                  flex: 1, padding: '10px', border: 'none', borderRadius: '10px',
                  background: paperSize === '58mm' ? '#FF9800' : (darkMode ? '#333' : '#e0e0e0'),
                  color: paperSize === '58mm' ? 'white' : (darkMode ? '#ccc' : '#333'),
                  fontWeight: '700', fontSize: '13px', cursor: 'pointer',
                  transition: 'all 0.15s'
                }}
              >
                📄 58mm (2″)
              </button>
              <button
                onClick={() => {
                  setPaperSize('80mm')
                  localStorage.setItem('pipper_paper_size', '80mm')
                }}
                style={{
                  flex: 1, padding: '10px', border: 'none', borderRadius: '10px',
                  background: paperSize === '80mm' ? '#FF9800' : (darkMode ? '#333' : '#e0e0e0'),
                  color: paperSize === '80mm' ? 'white' : (darkMode ? '#ccc' : '#333'),
                  fontWeight: '700', fontSize: '13px', cursor: 'pointer',
                  transition: 'all 0.15s'
                }}
              >
                📄 80mm (3″)
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <button
              onClick={async () => {
                try {
                  const { printDeliveryTicket } = await import('../utils/qzPrint')
                  const pedidoPrueba = {
                    numero_orden: 'TEST',
                    nombre_cliente: 'Cliente de Prueba',
                    telefono_cliente: '0981 123 456',
                    direccion: 'Calle Prueba 123',
                    created_at: new Date().toISOString(),
                    items: [
                      { producto_nombre: 'Hamburguesa Simple', cantidad: 2, precio: 25000 },
                      { producto_nombre: 'Coca Cola 500ml', cantidad: 1, precio: 8000 },
                    ],
                    total: 58000,
                  }
                  const empresaPrueba = { nombre: datos.nombre_empresa || 'Mi Restaurante' }
                  await printDeliveryTicket(pedidoPrueba, empresaPrueba)
                  alert('✅ Impresión de prueba enviada correctamente')
                } catch (e) {
                  alert('Error: ' + e.message)
                }
              }}
              style={{
                flex: 1, padding: '10px', border: 'none', borderRadius: '10px',
                background: '#4CAF50', color: 'white', fontWeight: '700', fontSize: '12px', cursor: 'pointer'
              }}
            >
              🖨️ Probar Impresión
            </button>
          </div>
        </div>



        {/* MODAL MÉTODO DE PAGO */}
        {showMetodoModal && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.8)', zIndex: 300,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            backdropFilter: 'blur(10px)'
          }}>
            <div style={{
              background: 'white', borderRadius: '20px', width: '92%', maxWidth: '450px',
              maxHeight: '85vh', overflow: 'auto', padding: '24px'
            }}>
              <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: '700', color: '#333' }}>
                {editMetodoId ? '✏️ Editar Método' : '➕ Nuevo Método de Pago'}
              </h3>

              {metodoMsg && (
                <p style={{ color: '#E53935', fontSize: '12px', marginBottom: '12px', background: 'rgba(229,57,53,0.1)', padding: '8px', borderRadius: '8px' }}>
                  {metodoMsg}
                </p>
              )}

              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '13px', fontWeight: '600', color: '#333' }}>Nombre (clave)</label>
                <input type="text" value={metodoForm.nombre} onChange={e => setMetodoForm({ ...metodoForm, nombre: e.target.value })}
                  placeholder="efectivo, qr, etc." style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '2px solid #ddd', fontSize: '14px', boxSizing: 'border-box' }} />
              </div>

              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '13px', fontWeight: '600', color: '#333' }}>Etiqueta (visible)</label>
                <input type="text" value={metodoForm.etiqueta} onChange={e => setMetodoForm({ ...metodoForm, etiqueta: e.target.value })}
                  placeholder="Efectivo, QR, etc." style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '2px solid #ddd', fontSize: '14px', boxSizing: 'border-box' }} />
              </div>

              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '13px', fontWeight: '600', color: '#333' }}>Icono</label>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {ICONOS_DISPONIBLES.map(ic => (
                    <button key={ic} onClick={() => setMetodoForm({ ...metodoForm, icono: ic })} style={{
                      padding: '8px', borderRadius: '8px',
                      border: `2px solid ${metodoForm.icono === ic ? '#FF9800' : '#ddd'}`,
                      background: metodoForm.icono === ic ? 'rgba(255,152,0,0.1)' : 'white',
                      cursor: 'pointer'
                    }}>
                      <span className="material-icons" style={{ fontSize: '20px', color: metodoForm.icono === ic ? '#FF9800' : '#666' }}>{ic}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '13px', fontWeight: '600', color: '#333' }}>Color</label>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <input type="color" value={metodoForm.color} onChange={e => setMetodoForm({ ...metodoForm, color: e.target.value })}
                    style={{ width: '48px', height: '40px', border: 'none', borderRadius: '8px', cursor: 'pointer', padding: 0 }} />
                  <input type="text" value={metodoForm.color} onChange={e => setMetodoForm({ ...metodoForm, color: e.target.value })}
                    style={{ flex: 1, padding: '10px 12px', borderRadius: '8px', border: '2px solid #ddd', fontSize: '14px', fontFamily: 'monospace' }} />
                  <div style={{
                    width: '36px', height: '36px', borderRadius: '8px',
                    background: metodoForm.color,
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <span className="material-icons" style={{ color: 'white', fontSize: '18px' }}>{metodoForm.icono}</span>
                  </div>
                </div>
              </div>

              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '13px', fontWeight: '600', color: '#333' }}>Orden</label>
                <input type="number" value={metodoForm.orden} onChange={e => setMetodoForm({ ...metodoForm, orden: Number(e.target.value) })}
                  min={0} max={99} style={{ width: '80px', padding: '10px 12px', borderRadius: '8px', border: '2px solid #ddd', fontSize: '14px' }} />
              </div>

              <div style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input type="checkbox" checked={metodoForm.activo} onChange={e => setMetodoForm({ ...metodoForm, activo: e.target.checked })}
                  id="metodo-activo" style={{ width: '18px', height: '18px' }} />
                <label htmlFor="metodo-activo" style={{ fontSize: '13px', fontWeight: '600', color: '#333' }}>Activo</label>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button onClick={() => setShowMetodoModal(false)} style={{
                  flex: 1, padding: '12px', border: 'none', borderRadius: '10px',
                  background: '#ccc', color: '#333', fontWeight: '600', cursor: 'pointer'
                }}>Cancelar</button>
                <button onClick={guardarMetodo} style={{
                  flex: 1, padding: '12px', border: 'none', borderRadius: '10px',
                  background: 'linear-gradient(135deg, #FF9800, #F57C00)', color: 'white',
                  fontWeight: '700', cursor: 'pointer'
                }}>{editMetodoId ? '💾 Guardar' : '➕ Crear'}</button>
              </div>
            </div>
          </div>
        )}

        {mensaje && (
          <div style={{
            ...s.mensaje,
            background: mensaje.includes('✅') ? '#d4edda' : '#f8d7da',
            color: mensaje.includes('✅') ? '#155724' : '#721c24'
          }}>
            {mensaje}
          </div>
        )}

        <button 
          onClick={guardar}
          disabled={guardando}
          style={{
            ...s.btn,
            opacity: guardando ? 0.7 : 1
          }}
        >
          {guardando ? 'Guardando...' : '💾 Guardar Cambios'}
        </button>

        <div style={s.info}>
          <p>📌 Los cambios se aplican inmediatamente a los tickets.</p>
        </div>
        </div>
      </div>
      </div>
    </div>
  )
}

const s = {
  container: (dm) => ({
    minHeight: '100vh',
    background: dm ? '#121212' : '#f0f2f5',
    color: dm ? '#fff' : '#1a1a1a',
    overflow: 'hidden',
  }),
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '10px 20px',
    background: '#1a1a1a',
    color: 'white',
    borderBottom: '1px solid rgba(255,152,0,0.2)',
    boxShadow: '0 1px 4px rgba(0,0,0,0.3)'
  },
  btnHeader: {
    width: '36px',
    height: '36px',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: '8px',
    background: 'rgba(255,255,255,0.06)',
    color: 'rgba(255,255,255,0.8)',
    fontSize: '18px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    textDecoration: 'none',
    transition: 'all 0.15s'
  },
  title: { fontSize: '22px', fontWeight: '800', letterSpacing: '0.5px' },
  content: {
    padding: '20px',
    maxWidth: '600px',
    margin: '0 auto'
  },
  card: (dm) => ({
    borderRadius: '14px',
    padding: '20px',
    marginBottom: '20px',
    border: `1px solid ${dm ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'}`,
    background: dm ? '#1e1e1e' : 'white',
    boxShadow: dm ? 'none' : '0 1px 4px rgba(0,0,0,0.04)',
  }),
  cardTitle: (dm) => ({
    margin: '0 0 5px 0',
    fontSize: '16px',
    fontWeight: '700',
    color: dm ? '#fff' : '#1a1a1a'
  }),
  subtitle: (dm) => ({
    margin: '0 0 20px 0',
    fontSize: '13px',
    color: dm ? 'rgba(255,255,255,0.5)' : '#888'
  }),
  field: {
    marginBottom: '15px'
  },
  label: (dm) => ({
    display: 'block',
    marginBottom: '5px',
    fontSize: '13px',
    fontWeight: '600',
    color: dm ? '#ccc' : '#555'
  }),
  mensaje: {
    padding: '12px',
    borderRadius: '10px',
    marginBottom: '15px',
    textAlign: 'center',
    fontWeight: '600',
    fontSize: '13px'
  },
  btn: {
    width: '100%',
    padding: '12px',
    border: 'none',
    borderRadius: '10px',
    background: 'linear-gradient(135deg, #4CAF50, #388E3C)',
    color: 'white',
    fontSize: '14px',
    fontWeight: '700',
    cursor: 'pointer'
  },
  input: (dm) => ({
    width: '100%',
    padding: '11px 14px',
    fontSize: '14px',
    borderRadius: '10px',
    border: `1px solid ${dm ? 'rgba(255,255,255,0.15)' : '#d0d0d0'}`,
    background: dm ? '#2a2a2a' : '#f8f8f8',
    color: dm ? 'white' : '#1a1a1a',
    outline: 'none',
    boxSizing: 'border-box',
    transition: 'border 0.15s',
  }),
}