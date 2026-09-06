import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import FullscreenButton from '../components/FullscreenButton'
import { useStore } from '../store/useStore'

const createPlaceholder = (title, activeRoute, icon) => {
  return function() {
    const darkMode = useStore((state) => state.darkMode)
    const toggleDarkMode = useStore((state) => state.toggleDarkMode)
    const initDarkMode = useStore((state) => state.initDarkMode)
    const syncDarkMode = useStore((state) => state.syncDarkMode)
    const isMobile = useStore((state) => state.isMobile)

    useEffect(() => {
      initDarkMode()
      syncDarkMode()
    }, [])

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
      btn: {
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
    }

    return (
      <div style={{ ...s.container(darkMode), display: 'flex', flexDirection: 'column' }}>
        <header style={{ ...s.header, flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Link to="/app/inicio" style={s.btn}><span className="material-icons">home</span></Link>
            <img src="/logo.png" alt="karuAPP" style={{ width: '28px', height: '28px', borderRadius: '6px' }} />
            <span style={s.title}>{title}</span>
          </div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            {!isMobile && <FullscreenButton />}
            <button onClick={toggleDarkMode} style={s.btn}>
              <span className="material-icons">{darkMode ? 'light_mode' : 'dark_mode'}</span>
            </button>
          </div>
        </header>

        <div style={{ display: 'flex', flex: 1, minHeight: 0, paddingBottom: isMobile ? '60px' : '0' }}>
          <Sidebar activePath={activeRoute} />
          <div style={{ padding: isMobile ? '12px' : '20px', flex: 1, overflow: 'auto' }}>
            <div style={{ textAlign: 'center', padding: '60px', color: darkMode ? '#666' : '#888' }}>
              <span className="material-icons" style={{ fontSize: '60px', color: darkMode ? '#ccc' : '#333' }}>{icon}</span>
              <p style={{ marginTop: '16px', color: darkMode ? '#666' : '#888' }}>Página en construcción</p>
            </div>
          </div>
        </div>
      </div>
    )
  }
}

export const Productos = createPlaceholder('Productos', '/app/productos', 'inventory_2')
export const Inventario = createPlaceholder('Inventario', '/app/inventario', 'inventory')
export const Config = createPlaceholder('Configuracion', '/app/config', 'settings')
export const Mesero = createPlaceholder('Vista Mesero', '/app/mesero', 'table_restaurant')
export const ParaLlevar = createPlaceholder('Para Llevar', '/app/para-llevar', 'takeout_dining')
export const Admin = createPlaceholder('Admin', '/app/admin', 'admin_panel_settings')
export const Autoservicio = createPlaceholder('Autoservicio', '/app/autoservi', 'dining')
