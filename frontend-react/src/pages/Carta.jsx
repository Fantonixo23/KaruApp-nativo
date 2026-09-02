import { useState, useEffect, useRef, useCallback } from "react"
import { getApiUrl, getMediaUrl } from "../utils/api"
import { useRealTime } from "../store/useSocketStore"

const API_URL = getApiUrl()
const MEDIA_URL = getMediaUrl()

function formatGs(n) {
  return "Gs. " + Number(n).toLocaleString("es-PY")
}

function resolveImg(url) {
  if (!url) return null
  if (url.startsWith("http")) return url
  // ya viene con /media/... del backend, solo agregar el host
  return MEDIA_URL + url
}

export default function Carta() {
  const [categorias, setCategorias] = useState([])
  const [empresa, setEmpresa] = useState({ nombre: "Menu" })
  const [cargando, setCargando] = useState(true)
  const [categoriaActiva, setCategoriaActiva] = useState(null)
  const [busqueda, setBusqueda] = useState("")
  const [productoModal, setProductoModal] = useState(null)
  const seccionesRef = useRef({})
  const { initSocket, cartaActualizada } = useRealTime()

  const cargar = useCallback(() => {
    fetch(`${API_URL}/carta`)
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          setCategorias(data.categorias)
          setEmpresa(data.empresa || { nombre: "Menu" })
          setCategoriaActiva(prev => prev ?? (data.categorias.length > 0 ? data.categorias[0].id : null))
        }
      })
      .catch(() => {})
      .finally(() => setCargando(false))
  }, [])

  useEffect(() => {
    initSocket()
    cargar()
  }, [cargar])

  useEffect(() => {
    if (cartaActualizada) cargar()
  }, [cartaActualizada, cargar])

  const irACategoria = (id) => {
    setCategoriaActiva(id)
    const el = seccionesRef.current[id]
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" })
  }

  useEffect(() => {
    const handler = () => {
      const ids = Object.keys(seccionesRef.current).map(Number).sort((a, b) => a - b)
      for (let i = ids.length - 1; i >= 0; i--) {
        const el = seccionesRef.current[ids[i]]
        if (!el) continue
        const rect = el.getBoundingClientRect()
        if (rect.top <= 130) { setCategoriaActiva(ids[i]); break }
      }
    }
    window.addEventListener("scroll", handler, { passive: true })
    return () => window.removeEventListener("scroll", handler)
  }, [categorias])

  const categoriasFiltradas = busqueda.trim()
    ? categorias.map(cat => ({
        ...cat,
productos: cat.productos.filter(p =>
          p.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
          (p.descripcion || "").toLowerCase().includes(busqueda.toLowerCase()) ||
          (p.ingredientes || "").toLowerCase().includes(busqueda.toLowerCase()) ||
          (p.notas || "").toLowerCase().includes(busqueda.toLowerCase())
        )
      })).filter(cat => cat.productos.length > 0)
    : categorias

  if (cargando) return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#0f0f0f" }}>
      <div style={{ textAlign: "center", color: "#fff" }}>
        <div style={{ fontSize: 40, marginBottom: 8 }}>🍽️</div>
        <div style={{ color: "rgba(255,255,255,0.45)", fontSize: 14 }}>Cargando menu...</div>
      </div>
    </div>
  )

  return (
    <div style={{ minHeight: "100vh", background: "#0f0f0f", color: "#fff", fontFamily: "system-ui, -apple-system, sans-serif" }}>
      <style>{`
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { display: none; }
        .prod-card:active { transform: scale(0.97); }
      `}</style>

      {/* ── Header sticky ── */}
      <div style={{
        position: "sticky", top: 0, zIndex: 100,
        background: "rgba(15,15,15,0.97)", backdropFilter: "blur(14px)",
        borderBottom: "1px solid rgba(255,255,255,0.07)",
        padding: "12px 16px 0",
      }}>
        {/* Nombre negocio */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: "rgba(244,67,54,0.15)",
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, flexShrink: 0
          }}>🍴</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16, lineHeight: 1.2 }}>{empresa.nombre}</div>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)" }}>Menu digital</div>
          </div>
        </div>

        {/* Buscador */}
        <div style={{ position: "relative", marginBottom: 10 }}>
          <span className="material-icons" style={{
            position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)",
            fontSize: 18, color: "rgba(255,255,255,0.3)", pointerEvents: "none"
          }}>search</span>
          <input
            value={busqueda}
            onChange={e => setBusqueda(e.target.value)}
            placeholder="Buscar en el menu..."
            style={{
              width: "100%", padding: "9px 36px",
              background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 10, color: "#fff", fontSize: 14, outline: "none"
            }}
          />
          {busqueda && (
            <button onClick={() => setBusqueda("")} style={{
              position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)",
              background: "none", border: "none", color: "rgba(255,255,255,0.4)",
              cursor: "pointer", padding: 0, display: "flex"
            }}>
              <span className="material-icons" style={{ fontSize: 18 }}>close</span>
            </button>
          )}
        </div>

        {/* Chips de categorías */}
        {!busqueda && (
          <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 10, scrollbarWidth: "none" }}>
            {categorias.map(cat => (
              <button key={cat.id} onClick={() => irACategoria(cat.id)} style={{
                flexShrink: 0, padding: "6px 16px", borderRadius: 20,
                border: categoriaActiva === cat.id ? "1.5px solid #F44336" : "1px solid rgba(255,255,255,0.12)",
                background: categoriaActiva === cat.id ? "rgba(244,67,54,0.15)" : "rgba(255,255,255,0.05)",
                color: categoriaActiva === cat.id ? "#F44336" : "rgba(255,255,255,0.55)",
                fontSize: 13, fontWeight: categoriaActiva === cat.id ? 700 : 400,
                cursor: "pointer", whiteSpace: "nowrap", transition: "all 0.15s"
              }}>{cat.nombre}</button>
            ))}
          </div>
        )}
      </div>

      {/* ── Contenido ── */}
      <div style={{ padding: "16px 14px 80px" }}>
        {categoriasFiltradas.length === 0 && (
          <div style={{ textAlign: "center", padding: "60px 20px", color: "rgba(255,255,255,0.3)" }}>
            <div style={{ fontSize: 40, marginBottom: 8 }}>🔍</div>
            <div style={{ fontSize: 15 }}>No encontramos "{busqueda}"</div>
          </div>
        )}

        {categoriasFiltradas.map(cat => (
          <div key={cat.id} ref={el => seccionesRef.current[cat.id] = el}
            style={{ marginBottom: 28, scrollMarginTop: 140 }}>

            {/* Titulo categoria */}
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <span className="material-icons" style={{ fontSize: 20, color: "#F44336" }}>
                {cat.icono || "category"}
              </span>
              <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>{cat.nombre}</h2>
              <div style={{ flex: 1, height: 1, background: "rgba(255,255,255,0.07)" }} />
            </div>

            {/* Grilla 2 columnas */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, 1fr)",
              gap: 12
            }}>
              {cat.productos.map(prod => (
                <ProductoCard key={prod.id} producto={prod} onClick={() => setProductoModal(prod)} />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div style={{
        position: "fixed", bottom: 0, left: 0, right: 0,
        background: "rgba(15,15,15,0.97)", backdropFilter: "blur(12px)",
        borderTop: "1px solid rgba(255,255,255,0.06)",
        padding: "10px 16px", textAlign: "center",
        fontSize: 11, color: "rgba(255,255,255,0.2)"
      }}>
        Menu digital · Precios incluyen impuestos
      </div>

      {/* Modal de detalle */}
      {productoModal && (
        <ProductoModal producto={productoModal} onClose={() => setProductoModal(null)} />
      )}
    </div>
  )
}

/* ── Card de producto (grilla) ─────────────────────────── */
function ProductoCard({ producto, onClick }) {
  const img = resolveImg(producto.imagen)
  const [imgError, setImgError] = useState(false)

  return (
    <button className="prod-card" onClick={onClick} style={{
      background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
      borderRadius: 14, overflow: "hidden", cursor: "pointer",
      textAlign: "left", color: "#fff", padding: 0,
      display: "flex", flexDirection: "column",
      transition: "transform 0.12s",
    }}>
      {/* Imagen */}
      <div style={{
        width: "100%", height: 110,
        background: "rgba(244,67,54,0.07)",
        display: "flex", alignItems: "center", justifyContent: "center",
        overflow: "hidden", flexShrink: 0
      }}>
        {img && !imgError ? (
          <img
            src={img}
            alt={producto.nombre}
            onError={() => setImgError(true)}
            style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
          />
        ) : (
          <span style={{ fontSize: 36 }}>🍽️</span>
        )}
      </div>

      {/* Info */}
      <div style={{ padding: "10px 10px 12px", flex: 1, display: "flex", flexDirection: "column", gap: 4 }}>
        <div style={{ fontWeight: 600, fontSize: 13, lineHeight: 1.3 }}>{producto.nombre}</div>
        {producto.descripcion && (
          <div style={{
            fontSize: 11, color: "rgba(255,255,255,0.4)", lineHeight: 1.4,
            overflow: "hidden", textOverflow: "ellipsis",
            display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical"
          }}>{producto.descripcion}</div>
        )}
        <div style={{ fontSize: 14, fontWeight: 700, color: "#4CAF50", marginTop: "auto", paddingTop: 4 }}>
          {formatGs(producto.precio)}
        </div>
        {producto.variantes?.length > 0 && (
          <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)" }}>
            {producto.variantes.length} opcion{producto.variantes.length > 1 ? "es" : ""}
          </div>
        )}
      </div>
    </button>
  )
}

function Seccion({ icono, titulo, texto }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
        <span style={{ fontSize: 14 }}>{icono}</span>
        <span style={{ fontSize: 11, fontWeight: 700, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: "0.8px" }}>
          {titulo}
        </span>
      </div>
      <p style={{ margin: 0, color: "rgba(255,255,255,0.65)", fontSize: 13.5, lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
        {texto}
      </p>
    </div>
  )
}
function ProductoModal({ producto, onClose }) {
  const img = resolveImg(producto.imagen)
  const [imgError, setImgError] = useState(false)

  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.78)",
      zIndex: 999, display: "flex", alignItems: "flex-end", backdropFilter: "blur(4px)",
    }}>
      <style>{`@keyframes slideUp { from { transform:translateY(100%) } to { transform:translateY(0) } }`}</style>
      <div onClick={e => e.stopPropagation()} style={{
        width: "100%", maxWidth: 500, margin: "0 auto",
        background: "#1c1c1c", borderRadius: "22px 22px 0 0",
        overflow: "hidden", animation: "slideUp 0.22s ease-out",
        maxHeight: "90vh", overflowY: "auto"
      }}>
        {/* Imagen grande */}
        <div style={{
          width: "100%", aspectRatio: "16/9",
          background: "rgba(244,67,54,0.08)",
          display: "flex", alignItems: "center", justifyContent: "center",
          overflow: "hidden"
        }}>
          {img && !imgError ? (
            <img src={img} alt={producto.nombre}
              onError={() => setImgError(true)}
              style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
          ) : (
            <span style={{ fontSize: 64 }}>🍽️</span>
          )}
        </div>

        {/* Info */}
        <div style={{ padding: "20px 20px 36px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
            <h3 style={{ margin: 0, fontSize: 22, fontWeight: 700, flex: 1, lineHeight: 1.3 }}>{producto.nombre}</h3>
            <button onClick={onClose} style={{
              background: "rgba(255,255,255,0.08)", border: "none", color: "#fff",
              borderRadius: "50%", width: 34, height: 34, cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginLeft: 10
            }}>
              <span className="material-icons" style={{ fontSize: 18 }}>close</span>
            </button>
          </div>

{producto.descripcion && (
            <p style={{ color: "rgba(255,255,255,0.55)", fontSize: 14, lineHeight: 1.65, margin: "0 0 16px" }}>
              {producto.descripcion}
            </p>
          )}

          {producto.ingredientes && <Seccion icono="🥗" titulo="Ingredientes" texto={producto.ingredientes} />}
          {producto.notas && <Seccion icono="📌" titulo="Notas" texto={producto.notas} />}

          {((producto.ingredientes) || (producto.notas)) && (
            <div style={{ height: 1, background: "rgba(255,255,255,0.08)", margin: "0 0 16px" }} />
          )}

          <div style={{ fontSize: 28, fontWeight: 800, color: "#4CAF50", marginBottom: 18 }}>
            {formatGs(producto.precio)}
          </div>

          {/* Variantes */}
          {producto.variantes?.length > 0 && (
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.4)", marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.8px" }}>
                Opciones disponibles
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {producto.variantes.map((v, i) => (
                  <div key={i} style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                    background: "rgba(255,255,255,0.05)", borderRadius: 10, padding: "10px 14px",
                    border: "1px solid rgba(255,255,255,0.08)"
                  }}>
                    <span style={{ fontSize: 14 }}>{v.nombre || v.name || String(v)}</span>
{(v.precio || v.price) && (
                      <span style={{ color: "#4CAF50", fontWeight: 700, fontSize: 14 }}>
                        {formatGs(v.precio || v.price)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
