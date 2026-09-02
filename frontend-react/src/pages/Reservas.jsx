import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import FullscreenButton from '../components/FullscreenButton'
import { useStore } from '../store/useStore'
import { useRealTime } from '../store/useSocketStore'
import { getApiUrl } from '../utils/api'
const API_URL = getApiUrl()

const ESTADOS = {
  pendiente: { label: 'Pendiente', color: '#FF9800' },
  confirmada: { label: 'Confirmada', color: '#4CAF50' },
  completada: { label: 'Atendida', color: '#2196F3' },
  cancelada: { label: 'Cancelada', color: '#757575' },
  no_show: { label: 'No asistió', color: '#E53935' },
}

const HORAS = []
for (let h = 8; h < 24; h++) {
  HORAS.push(`${String(h).padStart(2, '0')}:00`)
  HORAS.push(`${String(h).padStart(2, '0')}:30`)
}

function formatFechaLocal(iso) {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

function hoyISO() {
  const d = new Date()
  const off = d.getTimezoneOffset()
  const local = new Date(d.getTime() - off * 60000)
  return local.toISOString().split('T')[0]
}

function sumarDias(iso, dias) {
  const [y, m, d] = iso.split('-').map(Number)
  const fecha = new Date(y, m - 1, d)
  fecha.setDate(fecha.getDate() + dias)
  const yy = fecha.getFullYear()
  const mm = String(fecha.getMonth() + 1).padStart(2, '0')
  const dd = String(fecha.getDate()).padStart(2, '0')
  return `${yy}-${mm}-${dd}`
}

function esHoy(iso) {
  return iso === hoyISO()
}

export default function Reservas() {
  const darkMode = useStore((state) => state.darkMode)
  const toggleDarkMode = useStore((state) => state.toggleDarkMode)
  const initDarkMode = useStore((state) => state.initDarkMode)
  const syncDarkMode = useStore((state) => state.syncDarkMode)
  const isMobile = useStore((state) => state.isMobile)
  const { initSocket, reservaActualizada } = useRealTime()

  const [fecha, setFecha] = useState(hoyISO())
  const [reservas, setReservas] = useState([])
  const [mesas, setMesas] = useState([])
  const [cargando, setCargando] = useState(true)
  const [modal, setModal] = useState(false)
  const [borrando, setBorrando] = useState(false)
  const [accionEstado, setAccionEstado] = useState(null)
  const [mensaje, setMensaje] = useState('')

  const loadReservas = useCallback(async (f) => {
    try {
      const res = await fetch(`${API_URL}/reservas?fecha=${f}`)
      const data = await res.json()
      if (data.success) setReservas(data.reservas || [])
    } catch (e) {
      console.error(e)
    }
  }, [])

  const loadMesas = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/mesas`)
      const data = await res.json()
      if (data.success) setMesas(data.mesas || [])
    } catch (e) {
      console.error(e)
    }
  }, [])

  useEffect(() => {
    initDarkMode()
    syncDarkMode()
    initSocket()
  }, [])

  useEffect(() => {
    setCargando(true)
    loadReservas(fecha).finally(() => setCargando(false))
    loadMesas()
  }, [fecha, loadReservas, loadMesas])

  useEffect(() => {
    if (reservaActualizada) {
      loadReservas(fecha)
      loadMesas()
    }
  }, [reservaActualizada, fecha, loadReservas, loadMesas])

  const notificarDatos = () => {
    loadMesas()
    if (window.socketExterno) window.socketExterno.emit?.('reserva_local', {})
  }

  const crear = async (payload) => {
    try {
      const res = await fetch(`${API_URL}/reservas/crear`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (!data.success) throw new Error(data.error || 'Error al crear la reserva')
      await loadReservas(fecha)
      loadMesas()
      return { ok: true }
    } catch (e) {
      return { ok: false, error: e.message }
    }
  }

  const editar = async (id, payload) => {
    try {
      const res = await fetch(`${API_URL}/reservas/${id}/editar`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (!data.success) throw new Error(data.error || 'Error al editar la reserva')
      await loadReservas(fecha)
      loadMesas()
      return { ok: true }
    } catch (e) {
      return { ok: false, error: e.message }
    }
  }

  const cambiarEstado = async (id, estado) => {
    setAccionEstado(null)
    try {
      const res = await fetch(`${API_URL}/reservas/${id}/estado`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ estado }),
      })
      const data = await res.json()
      if (!data.success) throw new Error(data.error || 'Error')
      await loadReservas(fecha)
      loadMesas()
      setMensaje('Estado actualizado')
      setTimeout(() => setMensaje(''), 2500)
    } catch (e) {
      setMensaje(e.message || 'Error')
      setTimeout(() => setMensaje(''), 2500)
    }
  }

  const eliminar = async (id) => {
    if (!window.confirm('¿Eliminar esta reserva?')) return
    setBorrando(id)
    try {
      const res = await fetch(`${API_URL}/reservas/${id}/eliminar`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
      })
      const data = await res.json()
      if (!data.success) throw new Error(data.error || 'Error')
      await loadReservas(fecha)
      loadMesas()
    } catch (e) {
      setMensaje(e.message || 'Error')
      setTimeout(() => setMensaje(''), 2500)
    } finally {
      setBorrando(null)
    }
  }

  const agrupadas = (() => {
    const mapa = {}
    reservas.forEach(r => {
      const bloque = r.hora.slice(0, 2) + ':00'
      if (!mapa[bloque]) mapa[bloque] = []
      mapa[bloque].push(r)
    })
    return Object.keys(mapa).sort().map(h => ({ hora: h, items: mapa[h] }))
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
      background: '#1a1a1a', color: 'white',
      borderBottom: '1px solid rgba(255,152,0,0.2)',
      boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
    },
    btn: {
      width: '36px', height: '36px', border: '1px solid rgba(255,255,255,0.12)',
      borderRadius: '8px', background: 'rgba(255,255,255,0.06)',
      color: 'rgba(255,255,255,0.8)', fontSize: '18px', cursor: 'pointer',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      textDecoration: 'none', transition: 'all 0.15s', fontFamily: 'inherit',
    },
    title: { fontSize: '22px', fontWeight: '800', letterSpacing: '0.5px' },
    body: { display: 'flex', height: 'calc(100vh - 64px)' },
    main: { flex: 1, overflow: 'auto', padding: '16px' },
  }

  return (
    <div style={{ ...s.container, overflowY: isMobile ? 'auto' : 'hidden', overflowX: 'hidden' }}>
      <header style={s.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Link to="/app/inicio" style={s.btn}><span className="material-icons">home</span></Link>
          <span className="material-icons" style={{ fontSize: '22px', color: '#9C27B0' }}>event</span>
          <span style={s.title}>Reservas</span>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {!isMobile && <FullscreenButton />}
          <button
            onClick={() => setModal({ modo: 'crear' })}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '0 14px', height: '36px', border: 'none', borderRadius: '8px',
              background: 'linear-gradient(135deg, #9C27B0, #7B1FA2)',
              color: 'white', fontSize: '12px', fontWeight: '700', cursor: 'pointer',
            }}
          >
            <span className="material-icons" style={{ fontSize: '16px' }}>add</span>
            {!isMobile && <span>Nueva reserva</span>}
          </button>
          <button onClick={toggleDarkMode} style={s.btn}><span className="material-icons">{darkMode ? 'dark_mode' : 'light_mode'}</span></button>
        </div>
      </header>

      <div style={{ ...s.body, height: isMobile ? undefined : 'calc(100vh - 64px)', minHeight: isMobile ? 'calc(100vh - 64px)' : undefined, paddingBottom: isMobile ? '60px' : '0' }}>
        <Sidebar activePath="/app/reservas" />

        <div style={s.main}>
          {/* Navegador de fecha */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            gap: '10px', flexWrap: 'wrap', marginBottom: '16px',
            padding: '14px 16px',
            background: darkMode ? '#1e1e1e' : 'white',
            borderRadius: '14px',
            border: `1px solid ${darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button onClick={() => setFecha(f => sumarDias(f, -1))} style={chipNav}>
                <span className="material-icons" style={{ fontSize: '18px' }}>chevron_left</span>
              </button>
              <input
                type="date"
                value={fecha}
                onChange={e => e.target.value && setFecha(e.target.value)}
                style={{
                  padding: '8px 10px', border: `1px solid ${darkMode ? '#444' : '#ddd'}`,
                  borderRadius: '8px', background: darkMode ? '#2a2a2a' : '#f5f5f5',
                  color: darkMode ? 'white' : '#333', fontSize: '13px', outline: 'none',
                }}
              />
              <button onClick={() => setFecha(f => sumarDias(f, 1))} style={chipNav}>
                <span className="material-icons" style={{ fontSize: '18px' }}>chevron_right</span>
              </button>
              {!esHoy(fecha) && (
                <button onClick={() => setFecha(hoyISO())} style={chipNav}>
                  <span style={{ fontSize: '12px', fontWeight: '700' }}>Hoy</span>
                </button>
              )}
            </div>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#9C27B0' }}>
              {esHoy(fecha) ? 'Hoy' : formatFechaLocal(fecha)} · {reservas.filter(r => ESTADOS[r.estado] && ['pendiente', 'confirmada'].includes(r.estado)).length} activas
            </div>
          </div>

          {mensaje && (
            <div style={{
              padding: '10px 14px', borderRadius: '10px', marginBottom: '12px',
              background: darkMode ? '#1e1e1e' : 'white', border: '1px solid #4CAF50',
              color: '#4CAF50', fontSize: '13px', fontWeight: '600', textAlign: 'center',
            }}>
              {mensaje}
            </div>
          )}

          {cargando ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: darkMode ? '#888' : '#999' }}>
              <div style={{ fontSize: '34px', marginBottom: '8px' }}>📅</div>
              Cargando reservas...
            </div>
          ) : agrupadas.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: darkMode ? '#888' : '#999' }}>
              <div style={{ fontSize: '34px', marginBottom: '8px' }}>🗓️</div>
              No hay reservas para este día
              <div style={{ fontSize: '13px', marginTop: '12px' }}>
                <button onClick={() => setModal({ modo: 'crear' })}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: '8px',
                    padding: '10px 18px', border: 'none', borderRadius: '10px',
                    background: 'linear-gradient(135deg, #9C27B0, #7B1FA2)',
                    color: 'white', fontSize: '13px', fontWeight: '700', cursor: 'pointer',
                    boxShadow: '0 4px 12px rgba(156,39,176,0.3)',
                  }}>
                  <span className="material-icons" style={{ fontSize: '18px' }}>add</span>
                  Crear primera reserva
                </button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {agrupadas.map(grupo => (
                <div key={grupo.hora}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                    <span style={{
                      fontSize: '13px', fontWeight: '800', color: '#9C27B0',
                      background: darkMode ? '#2a1e3d' : '#f3e5f5',
                      padding: '4px 12px', borderRadius: '8px',
                    }}>
                      {grupo.hora}
                    </span>
                    <div style={{ flex: 1, height: '1px', background: darkMode ? '#333' : '#e0e0e0' }} />
                  </div>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                    gap: '12px',
                  }}>
                    {grupo.items.sort((a, b) => a.hora.localeCompare(b.hora)).map(r => (
                      <ReservaCard
                        key={r.id}
                        reserva={r}
                        darkMode={darkMode}
                        onEditar={() => setModal({ modo: 'editar', reserva: r })}
                        onEstado={(estado) => setAccionEstado({ id: r.id, estado })}
                        onEliminar={() => eliminar(r.id)}
                        borrando={borrando === r.id}
                        accionEstado={accionEstado && accionEstado.id === r.id ? accionEstado : null}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {accionEstado && (
        <ModalAccion
          darkMode={darkMode}
          onClose={() => setAccionEstado(null)}
          onConfirm={() => cambiarEstado(accionEstado.id, accionEstado.estado)}
        />
      )}

      {modal && (
        <ModalReserva
          darkMode={darkMode}
          modo={modal.modo}
          reserva={modal.reserva || null}
          mesas={mesas}
          close={() => setModal(null)}
          onSave={async (payload) => {
            const id = modal.reserva?.id
            const res = id ? await editar(id, payload) : await crear({ ...payload, fecha })
            if (res.ok) { setModal(null); return { ok: true } }
            return res
          }}
        />
      )}
    </div>
  )
}

const chipNav = {
  width: '34px', height: '34px', border: `1px solid rgba(156,39,176,0.4)`,
  borderRadius: '8px', background: 'transparent', color: '#9C27B0',
  cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
  fontFamily: 'inherit', padding: '0 10px',
}

function ReservaCard({ reserva, darkMode, onEditar, onEstado, onEliminar, borrando, accionEstado }) {
  const est = ESTADOS[reserva.estado] || ESTADOS.pendiente
  const esFutura = reserva.es_hoy || !reserva.es_hoy

  const botonEstado = (estado, label, color) => (
    <button
      onClick={() => onEstado(estado)}
      style={{
        flex: 1, padding: '8px', border: `1px solid ${color}40`, borderRadius: '8px',
        background: `${color}18`, color, fontSize: '11px', fontWeight: '700', cursor: 'pointer',
        whiteSpace: 'nowrap',
      }}
    >
      {label}
    </button>
  )

  return (
    <div style={{
      borderRadius: '14px', overflow: 'hidden',
      background: darkMode ? '#1e1e1e' : 'white',
      border: `1px solid ${est.color}35`,
      borderLeft: `4px solid ${est.color}`,
      display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 14px' }}>
        <div style={{
          width: '46px', height: '46px', borderRadius: '12px', flexShrink: 0,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          background: `${est.color}18`, color: est.color,
        }}>
          <span style={{ fontSize: '13px', fontWeight: '800', lineHeight: 1 }}>{reserva.hora}</span>
          <span style={{ fontSize: '9px', opacity: 0.8 }}>{reserva.duracion_min}min</span>
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: '800', fontSize: '14px', wordBreak: 'break-word' }}>{reserva.cliente_nombre}</div>
          <div style={{ fontSize: '12px', color: darkMode ? '#aaa' : '#666', marginTop: '2px' }}>
            Mesa {reserva.mesa.numero} · {reserva.comensales} pers
            {reserva.cliente_telefono ? ` · ${reserva.cliente_telefono}` : ''}
          </div>
          {reserva.nota && (
            <div style={{ fontSize: '11px', color: darkMode ? '#888' : '#999', marginTop: '2px', fontStyle: 'italic' }}>
              {reserva.nota}
            </div>
          )}
        </div>
        <span style={{
          fontSize: '10px', fontWeight: '700', padding: '4px 8px', borderRadius: '8px',
          background: `${est.color}20`, color: est.color, whiteSpace: 'nowrap',
        }}>
          {est.label}
        </span>
      </div>

      {(reserva.estado === 'pendiente' || reserva.estado === 'confirmada') && (
        <div style={{ display: 'flex', gap: '6px', padding: '0 14px 12px', flexWrap: 'wrap' }}>
          {reserva.estado === 'pendiente'
            ? botonEstado('confirmada', '✔ Confirmar', '#4CAF50')
            : botonEstado('pendiente', '↩ Pendiente', '#FF9800')}
          {botonEstado('completada', 'Atender', '#2196F3')}
          {botonEstado('no_show', 'No asistió', '#E53935')}
          {botonEstado('cancelada', 'Cancelar', '#757575')}
          <button
            onClick={onEditar}
            title="Editar"
            style={{
              width: '34px', border: '1px solid rgba(156,39,176,0.4)', borderRadius: '8px',
              background: 'rgba(156,39,176,0.12)', color: '#9C27B0', cursor: 'pointer',
            }}
          >
            <span className="material-icons" style={{ fontSize: '15px' }}>edit</span>
          </button>
          <button
            onClick={onEliminar}
            disabled={borrando}
            title="Eliminar"
            style={{
              width: '34px', border: '1px solid rgba(229,57,53,0.4)', borderRadius: '8px',
              background: 'rgba(229,57,53,0.12)', color: '#E53935', cursor: borrando ? 'wait' : 'pointer',
            }}
          >
            <span className="material-icons" style={{ fontSize: '15px' }}>{borrando ? 'hourglass' : 'delete'}</span>
          </button>
        </div>
      )}
    </div>
  )
}

function ModalAccion({ darkMode, onClose, onConfirm }) {
  return (
    <div onClick={onClose} style={overlayStyle}>
      <div onClick={e => e.stopPropagation()} style={modalBox(darkMode)}>
        <h3 style={{ margin: '0 0 12px', color: '#9C27B0' }}>Confirmar cambio de estado</h3>
        <p style={{ fontSize: '13px', color: darkMode ? '#aaa' : '#666', margin: '0 0 18px' }}>
          ¿Seguro que querés cambiar el estado de esta reserva?
        </p>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={onClose} style={btnSecundario(darkMode)}>Cancelar</button>
          <button onClick={onConfirm} style={{
            flex: 1, padding: '10px', border: 'none', borderRadius: '10px',
            background: 'linear-gradient(135deg, #9C27B0, #7B1FA2)',
            color: 'white', fontSize: '14px', fontWeight: '700', cursor: 'pointer',
          }}>
            Confirmar
          </button>
        </div>
      </div>
    </div>
  )
}

function ModalReserva({ darkMode, modo, reserva, mesas, close, onSave }) {
  const [cliente, setCliente] = useState(reserva?.cliente_nombre || '')
  const [telefono, setTelefono] = useState(reserva?.cliente_telefono || '')
  const [mesaId, setMesaId] = useState(reserva?.mesa.id || undefined)
  const [hora, setHora] = useState(reserva?.hora || '12:00')
  const [comensales, setComensales] = useState(reserva?.comensales || 2)
  const [duracion, setDuracion] = useState(reserva?.duracion_min || 120)
  const [nota, setNota] = useState(reserva?.nota || '')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')

  const mesasActivas = mesas.filter(m => m.estado === 'disponible' || m.estado === 'reservada' || m.id === reserva?.mesa.id)

  const guardar = async () => {
    if (!cliente.trim()) return setError('Ingresá el nombre del cliente')
    if (!mesaId) return setError('Seleccioná una mesa')
    setCargando(true)
    setError('')
    const res = await onSave({
      mesa_id: mesaId,
      hora,
      duracion_min: duracion,
      cliente_nombre: cliente.trim(),
      cliente_telefono: telefono.trim(),
      comensales,
      nota,
    })
    setCargando(false)
    if (!res.ok) setError(res.error || 'Error al guardar')
  }

  return (
    <div onClick={close} style={overlayStyle}>
      <div onClick={e => e.stopPropagation()} style={{ ...modalBox(darkMode), maxWidth: '420px', maxHeight: '90vh', overflow: 'auto' }}>
        <h3 style={{ margin: '0 0 14px', color: '#9C27B0' }}>
          {modo === 'crear' ? 'Nueva reserva' : `Editar reserva de ${reserva?.cliente_nombre}`}
        </h3>

        <Campo label="Cliente *">
          <input value={cliente} onChange={e => setCliente(e.target.value)} placeholder="Nombre del cliente" style={inputStyle(darkMode)} />
        </Campo>

        <Campo label="Teléfono">
          <input value={telefono} onChange={e => setTelefono(e.target.value)} placeholder="Opcional" style={inputStyle(darkMode)} />
        </Campo>

        <Campo label="Mesa *">
          <select value={mesaId || ''} onChange={e => setMesaId(Number(e.target.value))} style={inputStyle(darkMode)}>
            <option value="">Seleccionar mesa...</option>
            {mesasActivas.sort((a, b) => a.numero - b.numero).map(m => {
              const conflicto = m.id !== reserva?.mesa.id && m.estado === 'reservada'
              return (
                <option key={m.id} value={m.id} disabled={conflicto}>
                  Mesa {m.numero} (cap. {m.capacidad}){conflicto ? ' — ocupada hoy' : ''}
                </option>
              )
            })}
          </select>
          <div style={{ fontSize: '10px', color: darkMode ? '#888' : '#999', marginTop: '4px' }}>
            Solo se ofrecen mesas libres o ya reservadas hoy.
          </div>
        </Campo>

        <div style={{ display: 'flex', gap: '10px' }}>
          <Campo label="Hora *">
            <select value={hora} onChange={e => setHora(e.target.value)} style={inputStyle(darkMode)}>
              {HORAS.map(h => <option key={h} value={h}>{h}</option>)}
            </select>
          </Campo>
          <Campo label="Duración (min)">
            <select value={duracion} onChange={e => setDuracion(Number(e.target.value))} style={inputStyle(darkMode)}>
              <option value={90}>90 min</option>
              <option value={120}>120 min</option>
              <option value={150}>150 min</option>
              <option value={180}>180 min</option>
            </select>
          </Campo>
        </div>

        <Campo label="Comensales">
          <input
            type="number" min={1} max={20} value={comensales}
            onChange={e => setComensales(Math.max(1, Number(e.target.value) || 1))}
            style={inputStyle(darkMode)}
          />
        </Campo>

        <Campo label="Nota">
          <textarea value={nota} onChange={e => setNota(e.target.value)} rows={2} placeholder="Opcional" style={inputStyle(darkMode)} />
        </Campo>

        {error && (
          <div style={{ padding: '10px 12px', borderRadius: '10px', marginBottom: '12px', background: 'rgba(229,57,53,0.12)', color: '#E53935', fontSize: '13px', fontWeight: '600' }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', gap: '10px', marginTop: '4px' }}>
          <button onClick={close} style={btnSecundario(darkMode)}>Cancelar</button>
          <button onClick={guardar} disabled={cargando} style={{
            flex: 1, padding: '10px', border: 'none', borderRadius: '10px',
            background: cargando ? '#8e24aa77' : 'linear-gradient(135deg, #9C27B0, #7B1FA2)',
            color: 'white', fontSize: '14px', fontWeight: '700', cursor: cargando ? 'wait' : 'pointer',
          }}>
            {cargando ? 'Guardando...' : modo === 'crear' ? 'Crear reserva' : 'Guardar cambios'}
          </button>
        </div>
      </div>
    </div>
  )
}

function Campo({ label, children }) {
  return (
    <div style={{ marginBottom: '12px' }}>
      <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: '#9C27B0', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        {label}
      </label>
      {children}
    </div>
  )
}

const overlayStyle = {
  position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
  background: 'rgba(0,0,0,0.6)', zIndex: 300,
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  backdropFilter: 'blur(4px)',
}

const modalBox = (darkMode) => ({
  background: darkMode ? '#1e1e1e' : 'white',
  borderRadius: '20px', padding: '24px', width: '90%', maxWidth: '380px',
  boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
})

const inputStyle = (darkMode) => ({
  width: '100%', boxSizing: 'border-box', padding: '9px 12px', border: `1px solid ${darkMode ? '#444' : '#ddd'}`,
  borderRadius: '10px', background: darkMode ? '#2a2a2a' : '#f5f5f5',
  color: darkMode ? 'white' : '#333', fontSize: '13px', outline: 'none', fontFamily: 'inherit',
  resize: 'vertical',
})

const btnSecundario = (darkMode) => ({
  padding: '10px 16px', border: `1px solid ${darkMode ? '#444' : '#ddd'}`, borderRadius: '10px',
  background: darkMode ? '#2a2a2a' : '#f0f2f5', color: darkMode ? '#ccc' : '#666',
  fontSize: '14px', fontWeight: '600', cursor: 'pointer', fontFamily: 'inherit',
})
