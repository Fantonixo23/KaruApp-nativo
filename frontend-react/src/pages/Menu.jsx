import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import FullscreenButton from '../components/FullscreenButton'
import { useStore } from '../store/useStore'
import { formatGuarani } from '../utils/currency'
import { getApiUrl, getMediaUrl } from '../utils/api'
const API_URL = getApiUrl()
const MEDIA_URL = getMediaUrl()

function resolveImg(url) {
  if (!url) return null
  if (url.startsWith('http')) return url
  return MEDIA_URL + url
}

export default function Menu() {
  const darkMode = useStore((state) => state.darkMode)
  const toggleDarkMode = useStore((state) => state.toggleDarkMode)
  const initDarkMode = useStore((state) => state.initDarkMode)
  const syncDarkMode = useStore((state) => state.syncDarkMode)
  const isMobile = useStore((state) => state.isMobile)

  const [productos, setProductos] = useState([])
  const [categorias, setCategorias] = useState([])
  const [categoria, setCategoria] = useState('todas')
  const [visibilidad, setVisibilidad] = useState('todas')
  const [busqueda, setBusqueda] = useState('')
  const [cargando, setCargando] = useState(true)
  const [guardandoId, setGuardandoId] = useState(null)
  const [guardadoIds, setGuardadoIds] = useState({})
  const [errores, setErrores] = useState({})
  const [qrModal, setQrModal] = useState(false)
  const [qrData, setQrData] = useState({ url: '', qr_base64: '' })

  useEffect(() => {
    initDarkMode()
    syncDarkMode()
    cargarDatos()
  }, [])

  const cargarDatos = async () => {
    try {
      setCargando(true)
      const [prodRes, catRes] = await Promise.all([
        fetch(`${API_URL}/productos`),
        fetch(`${API_URL}/categorias`),
      ])
      const prodData = await prodRes.json()
      const catData = await catRes.json()
      if (prodData.success) setProductos(prodData.productos || [])
      if (catData.success) setCategorias(catData.categorias || [])
    } catch (e) {
      console.error(e)
    } finally {
      setCargando(false)
    }
  }

  const cambiarCampo = (id, campo, valor) => {
    setProductos(ps => ps.map(p => (p.id === id ? { ...p, [campo]: valor } : p)))
    setGuardadoIds(g => ({ ...g, [id]: false }))
    setErrores(e => ({ ...e, [id]: '' }))
  }

  const toggleDisponible = (id) => {
    const p = productos.find(x => x.id === id)
    if (!p) return
    setProductos(ps => ps.map(x => (x.id === id ? { ...x, disponible: !x.disponible } : x)))
    guardar(id, !p.disponible)
  }

  const guardar = async (id, disponibleSobreescrito) => {
    const p = productos.find(x => x.id === id)
    if (!p) return
    const disponible = disponibleSobreescrito !== undefined ? disponibleSobreescrito : p.disponible
    setGuardandoId(id)
    setErrores(e => ({ ...e, [id]: '' }))
    try {
      const res = await fetch(`${API_URL}/productos/${id}/carta`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          descripcion: p.descripcion || '',
          ingredientes: p.ingredientes || '',
          notas: p.notas || '',
          disponible,
        }),
      })
      const data = await res.json()
      if (data.success) {
        setGuardadoIds(g => ({ ...g, [id]: true }))
        setTimeout(() => setGuardadoIds(g => ({ ...g, [id]: false })), 2500)
      } else {
        setErrores(e => ({ ...e, [id]: data.error || 'Error al guardar' }))
      }
    } catch (e) {
      setErrores(err => ({ ...err, [id]: 'Error de conexión' }))
    } finally {
      setGuardandoId(null)
    }
  }

  const abrirQr = async () => {
    setQrModal(true)
    setQrData({ url: '', qr_base64: '' })
    try {
      const res = await fetch(`${API_URL}/qr-carta`)
      const data = await res.json()
      if (data) setQrData(data)
    } catch (e) {
      console.error(e)
    }
  }

  const productosFiltrados = (() => {
    let lista = categoria === 'todas' ? productos : productos.filter(p => p.categoria_id === categoria)
    if (visibilidad === 'visibles') lista = lista.filter(p => p.disponible)
    if (visibilidad === 'ocultos') lista = lista.filter(p => !p.disponible)
    if (busqueda.trim()) {
      const q = busqueda.toLowerCase()
      lista = lista.filter(p =>
        p.nombre?.toLowerCase().includes(q) ||
        (p.descripcion || '').toLowerCase().includes(q) ||
        (p.ingredientes || '').toLowerCase().includes(q) ||
        (p.notas || '').toLowerCase().includes(q)
      )
    }
    return lista
  })()

  const grupos = (() => {
    const sinCategoria = productosFiltrados.filter(p => !p.categoria_id)
    const conCategoria = categorias
      .filter(c => productosFiltrados.some(p => p.categoria_id === c.id))
      .map(c => ({ ...c, productos: productosFiltrados.filter(p => p.categoria_id === c.id) }))
    if (sinCategoria.length > 0) conCategoria.push({ id: 0, nombre: 'Otros', icono: 'restaurant_menu', productos: sinCategoria })
    return conCategoria
  })()

  const s = {
    container: {
      minHeight: '100vh',
      background: darkMode ? '#121212' : '#f0f2f5',
      color: darkMode ? '#fff' : '#1a1a1a',
      overflow: 'hidden',
    },
    header: {
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '10px 20px',
      background: '#1a1a1a',
      color: 'white',
      borderBottom: '1px solid rgba(255,152,0,0.2)',
      boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
    },
    btn: {
      width: '36px', height: '36px', border: '1px solid rgba(255,255,255,0.12)',
      borderRadius: '8px', background: 'rgba(255,255,255,0.06)',
      color: 'rgba(255,255,255,0.8)', fontSize: '18px', cursor: 'pointer',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      textDecoration: 'none', transition: 'all 0.15s',
    },
    btnCarta: {
      display: 'flex', alignItems: 'center', gap: '6px',
      padding: '0 12px', height: '36px',
      border: '1px solid rgba(76,175,80,0.5)',
      borderRadius: '8px', background: 'rgba(76,175,80,0.15)',
      color: '#4CAF50', fontSize: '12px', fontWeight: '700',
      cursor: 'pointer', textDecoration: 'none', transition: 'all 0.15s',
    },
    btnQr: {
      display: 'flex', alignItems: 'center', gap: '6px',
      padding: '0 12px', height: '36px',
      border: '1px solid rgba(255,152,0,0.5)',
      borderRadius: '8px', background: 'rgba(255,152,0,0.15)',
      color: '#FF9800', fontSize: '12px', fontWeight: '700',
      cursor: 'pointer', transition: 'all 0.15s', fontFamily: 'inherit',
    },
    title: { fontSize: '22px', fontWeight: '800', letterSpacing: '0.5px' },
    body: {
      display: 'flex', height: 'calc(100vh - 64px)',
    },
    main: {
      flex: 1, overflow: 'auto', padding: '16px',
    },
    chip: (active) => ({
      padding: '6px 14px', border: 'none', borderRadius: '8px',
      cursor: 'pointer', whiteSpace: 'nowrap', fontSize: '12px', fontWeight: '600',
      background: active ? '#FF9800' : darkMode ? '#2a2a2a' : '#e8e8e8',
      color: active ? 'white' : darkMode ? '#ccc' : '#666',
    }),
    input: {
      width: '100%', padding: '8px 12px', border: `1px solid ${darkMode ? '#444' : '#ddd'}`,
      borderRadius: '8px', background: darkMode ? '#333' : '#f5f5f5',
      color: darkMode ? 'white' : '#333', fontSize: '13px', outline: 'none',
      boxSizing: 'border-box',
    },
    textarea: {
      width: '100%', resize: 'vertical', minHeight: '52px',
      padding: '8px 10px', borderRadius: '10px',
      background: darkMode ? '#2a2a2a' : '#f5f5f5',
      border: `1px solid ${darkMode ? '#444' : '#ddd'}`,
      color: darkMode ? '#fff' : '#333',
      fontSize: '12.5px', lineHeight: '1.5', outline: 'none',
      boxSizing: 'border-box', fontFamily: 'inherit',
    },
  }

  return (
    <div style={{ ...s.container, overflowY: isMobile ? 'auto' : 'hidden', overflowX: 'hidden' }}>
      <header style={s.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Link to="/app/inicio" style={s.btn}><span className="material-icons">home</span></Link>
          <span className="material-icons" style={{ fontSize: '22px', color: '#FF9800' }}>restaurant_menu</span>
          <span style={s.title}>Carta</span>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button onClick={abrirQr} style={s.btnQr}>
            <span className="material-icons" style={{ fontSize: '16px' }}>qr_code_scanner</span>
            {!isMobile && <span>Escanear QR</span>}
          </button>
          <a href="/carta" target="_blank" rel="noopener noreferrer" style={s.btnCarta}>
            <span style={{ fontSize: '15px' }}>🍽️</span>
            {!isMobile && <span>Ver carta</span>}
          </a>
          {!isMobile && <FullscreenButton />}
          <button onClick={toggleDarkMode} style={s.btn}><span className="material-icons">{darkMode ? 'dark_mode' : 'light_mode'}</span></button>
        </div>
      </header>

      <div style={{ ...s.body, height: isMobile ? undefined : 'calc(100vh - 64px)', minHeight: isMobile ? 'calc(100vh - 64px)' : undefined, paddingBottom: isMobile ? '60px' : '0' }}>
        <Sidebar activePath="/app/menu" />

        <div style={s.main}>
          <div style={{ marginBottom: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <input
              value={busqueda}
              onChange={e => setBusqueda(e.target.value)}
              placeholder="🔍 Buscar producto, ingrediente o nota..."
              style={s.input}
            />
            <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
              <button onClick={() => setCategoria('todas')} style={s.chip(categoria === 'todas')}>Todas</button>
              {categorias.map(c => (
                <button key={c.id} onClick={() => setCategoria(c.id)} style={s.chip(categoria === c.id)}>{c.nombre}</button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              <button onClick={() => setVisibilidad('todas')} style={s.chip(visibilidad === 'todas')}>Todas</button>
              <button onClick={() => setVisibilidad('visibles')} style={s.chip(visibilidad === 'visibles')}>✅ Visibles</button>
              <button onClick={() => setVisibilidad('ocultos')} style={s.chip(visibilidad === 'ocultos')}>🙈 Ocultos</button>
            </div>
          </div>

          {cargando ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: darkMode ? '#888' : '#999' }}>
              <div style={{ fontSize: '34px', marginBottom: '8px' }}>🍽️</div>
              Cargando carta...
            </div>
          ) : grupos.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: darkMode ? '#888' : '#999' }}>
              <div style={{ fontSize: '34px', marginBottom: '8px' }}>🔍</div>
              No hay productos que coincidan
            </div>
          ) : (
            grupos.map(grupo => (
              <div key={grupo.id} style={{ marginBottom: '22px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                  <span className="material-icons" style={{ fontSize: '18px', color: '#FF9800' }}>
                    {grupo.icono || 'category'}
                  </span>
                  <h3 style={{ margin: 0, fontSize: '15px', fontWeight: '700' }}>{grupo.nombre}</h3>
                  <span style={{ fontSize: '11px', color: darkMode ? '#777' : '#aaa' }}>
                    ({grupo.productos.filter(p => p.disponible).length} visibles · {grupo.productos.filter(p => !p.disponible).length} ocultos)
                  </span>
                </div>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
                  gap: '12px',
                }}>
                  {grupo.productos.map(p => (
                    <ProductoCarta
                      key={p.id}
                      producto={p}
                      darkMode={darkMode}
                      guardando={guardandoId === p.id}
                      guardado={!!guardadoIds[p.id]}
                      error={errores[p.id]}
                      onChange={cambiarCampo}
                      onToggle={toggleDisponible}
                      onGuardar={guardar}
                    />
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {qrModal && (
        <div onClick={() => setQrModal(false)} style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.6)', zIndex: 300,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backdropFilter: 'blur(4px)',
        }}>
          <div onClick={e => e.stopPropagation()} style={{
            background: darkMode ? '#1e1e1e' : 'white',
            borderRadius: '20px', padding: '30px', maxWidth: '360px', width: '90%',
            textAlign: 'center', boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
          }}>
            <h3 style={{ margin: '0 0 4px', color: darkMode ? '#fff' : '#1a1a1a' }}>Escaneá la carta</h3>
            <p style={{ fontSize: '12px', color: darkMode ? 'rgba(255,255,255,0.5)' : '#888', margin: '0 0 16px' }}>
              Abrí la cámara de tu celular y apuntá al código
            </p>
            {qrData.qr_base64 ? (
              <img src={`data:image/png;base64,${qrData.qr_base64}`} alt="QR Carta"
                style={{ width: '200px', height: '200px', borderRadius: '12px', marginBottom: '16px' }} />
            ) : (
              <div style={{
                height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                marginBottom: '16px', color: darkMode ? '#888' : '#aaa', fontSize: '13px',
              }}>
                Generando QR...
              </div>
            )}
            <div style={{
              background: darkMode ? '#2a2a2a' : '#f5f5f5',
              borderRadius: '10px', padding: '12px', textAlign: 'left',
              fontSize: '13px',
            }}>
              <div style={{ color: darkMode ? '#aaa' : '#666', marginBottom: '4px' }}>O ingresá esta URL:</div>
              <code style={{
                display: 'block', padding: '8px', borderRadius: '6px',
                background: darkMode ? '#333' : '#e8e8e8',
                color: '#4CAF50', fontWeight: '700', fontSize: '13px',
                wordBreak: 'break-all',
              }}>{qrData.url || 'Cargando...'}</code>
            </div>
            <button onClick={() => setQrModal(false)} style={{
              marginTop: '16px', width: '100%', padding: '10px', border: 'none', borderRadius: '10px',
              background: 'linear-gradient(135deg, #FF9800, #F57C00)',
              color: 'white', fontSize: '14px', fontWeight: '700', cursor: 'pointer',
            }}>
              Cerrar
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function ProductoCarta({ producto, darkMode, guardando, guardado, error, onChange, onToggle, onGuardar }) {
  const img = resolveImg(producto.imagen)
  const [imgError, setImgError] = useState(false)
  const max = 500

  const campo = (label, icono, valor, placeholder) => (
    <div style={{ marginBottom: '10px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '4px' }}>
        <span style={{ fontSize: '13px' }}>{icono}</span>
        <span style={{ fontSize: '11px', fontWeight: '700', color: darkMode ? '#aaa' : '#666', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {label}
        </span>
        <span style={{ marginLeft: 'auto', fontSize: '10px', color: darkMode ? '#666' : '#bbb' }}>
          {valor.length}/{max}
        </span>
      </div>
      <textarea
        value={valor}
        onChange={e => onChange(producto.id, label === 'Descripción' ? 'descripcion' : label === 'Ingredientes' ? 'ingredientes' : 'notas', e.target.value)}
        rows={label === 'Descripción' ? 3 : 2}
        maxLength={max}
        placeholder={placeholder}
        style={{
          width: '100%', resize: 'vertical', minHeight: '52px', boxSizing: 'border-box',
          padding: '8px 10px', borderRadius: '10px',
          background: darkMode ? '#2a2a2a' : '#f5f5f5',
          border: `1px solid ${darkMode ? '#444' : '#ddd'}`,
          color: darkMode ? '#fff' : '#333',
          fontSize: '12.5px', lineHeight: '1.5', outline: 'none', fontFamily: 'inherit',
        }}
      />
    </div>
  )

  return (
    <div style={{
      borderRadius: '14px', overflow: 'hidden',
      background: darkMode ? '#1e1e1e' : 'white',
      border: `1px solid ${darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'}`,
      opacity: producto.disponible ? 1 : 0.72,
      display: 'flex', flexDirection: 'column',
    }}>
      {/* Encabezado de la tarjeta */}
      <div style={{ display: 'flex', gap: '12px', padding: '12px 14px 8px' }}>
        <div style={{
          width: '58px', height: '58px', borderRadius: '12px', flexShrink: 0,
          background: darkMode ? '#2a2a2a' : '#f0f2f5',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '24px', overflow: 'hidden',
        }}>
          {img && !imgError ? (
            <img src={img} alt={producto.nombre} onError={() => setImgError(true)}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            <span>🍽️</span>
          )}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: '700', fontSize: '14px', lineHeight: 1.3, wordBreak: 'break-word' }}>{producto.nombre}</div>
          <div style={{ fontSize: '13px', fontWeight: '800', color: '#4CAF50', marginTop: '2px' }}>
            {formatGuarani(producto.precio)}
          </div>
        </div>
        <button
          onClick={() => onToggle(producto.id)}
          title={producto.disponible ? 'Se muestra en la carta' : 'Oculto de la carta'}
          style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: '0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px', fontFamily: 'inherit' }}
        >
          <div style={{
            width: '40px', height: '22px', borderRadius: '11px',
            background: producto.disponible ? '#4CAF50' : darkMode ? '#555' : '#ccc',
            position: 'relative', transition: 'background 0.15s', flexShrink: 0,
          }}>
            <div style={{
              position: 'absolute', top: '3px', left: producto.disponible ? '21px' : '3px',
              width: '16px', height: '16px', background: 'white', borderRadius: '50%',
              transition: 'left 0.15s', boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
            }} />
          </div>
          <span style={{
            fontSize: '10px', fontWeight: '700',
            color: producto.disponible ? '#4CAF50' : (darkMode ? '#777' : '#999'),
            whiteSpace: 'nowrap',
          }}>
            {producto.disponible ? 'Visible' : 'Oculto'}
          </span>
        </button>
      </div>

      {/* Campos editables */}
      <div style={{ padding: '4px 14px 0' }}>
        {campo('Descripción', '📝', producto.descripcion || '',
          'Ej: Un rico plato tradicional paraguayo hecho con harina de maíz y queso paraguay...')}
        {campo('Ingredientes', '🥗', producto.ingredientes || '',
          'Ej: Harina de maíz, queso paraguay, cebolla, orégano...')}
        {campo('Notas', '📌', producto.notas || '',
          'Ej: Recomendado con una gaseosa bien fría. Acompaña con salsa...')}
      </div>

      {/* Pie de la tarjeta */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '10px',
        padding: '0 14px 12px', marginTop: 'auto', flexWrap: 'wrap',
      }}>
        <span style={{ fontSize: '10px', color: darkMode ? '#666' : '#999' }}>
          {producto.disponible ? 'Aparece en la carta 📋' : 'Oculto en la carta 📋'}
        </span>
        {error && <span style={{ fontSize: '11px', color: '#E53935' }}>⚠️ {error}</span>}
        <button
          onClick={() => onGuardar(producto.id)}
          disabled={guardando}
          style={{
            marginLeft: 'auto', padding: '8px 18px', border: 'none', borderRadius: '9px',
            cursor: guardando ? 'wait' : 'pointer',
            background: guardado ? 'linear-gradient(135deg, #4CAF50, #388E3C)' : 'linear-gradient(135deg, #FF9800, #F57C00)',
            color: 'white', fontSize: '12px', fontWeight: '700',
            display: 'flex', alignItems: 'center', gap: '5px',
          }}
        >
          {guardando ? 'Guardando...' : guardado ? <><span>✓</span> Guardado</> : 'Guardar'}
        </button>
      </div>
    </div>
  )
}