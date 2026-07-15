import { useStore } from '../store/useStore'
import { MOBILE_HIDDEN_MODULES } from '../constants'
import { Link } from 'react-router-dom'

const ALL_ITEMS = [
  { path: '/app/mesas', icon: 'table_restaurant', label: 'Mesas', modulo: 'mesas' },
  { path: '/app/cocina', icon: 'restaurant', label: 'Cocina', modulo: 'cocina' },
  { path: '/app/caja', icon: 'point_of_sale', label: 'Caja', modulo: 'caja' },
  { path: '/app/delivery', icon: 'delivery_dining', label: 'Delivery', modulo: 'delivery' },
  { path: '/app/informes', icon: 'analytics', label: 'Informes', modulo: 'informes' },
  { path: '/app/productos', icon: 'inventory_2', label: 'Productos', modulo: 'productos' },
  { path: '/app/inventario', icon: 'inventory', label: 'Inventario', modulo: 'inventario' },
  { path: '/app/configuracion', icon: 'settings', label: 'Config', modulo: 'configuracion' },
]

const RED = '#D32F2F'

export default function Sidebar({ activePath }) {
  const isMobile = useStore((state) => state.isMobile)
  const visibleItems = ALL_ITEMS.filter(item => !isMobile || !MOBILE_HIDDEN_MODULES.includes(item.modulo))

  return (
    <div style={{
      background: '#1a1a1a',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '12px 0',
      gap: '6px',
      width: '90px',
      flexShrink: 0,
      height: '100vh',
      position: 'sticky',
      top: 0,
      overflowY: 'auto',
    }}>
      <Link to="/app/inicio" style={{
        width: '70px', height: '60px', display: 'flex',
        flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        border: 'none', background: RED, color: 'white',
        fontSize: '9px', fontWeight: '700', borderRadius: '10px', textDecoration: 'none',
        marginBottom: '4px',
      }}>
        <span className="material-icons" style={{ fontSize: '24px' }}>home</span>
        <span style={{ marginTop: '3px' }}>Inicio</span>
      </Link>

      <div style={{ width: '80%', height: '1px', background: 'rgba(255,255,255,0.08)', margin: '2px 0 4px' }} />

      {visibleItems.map((item, index) => (
        <Link
          key={index}
          to={item.path}
          style={{
            width: '70px',
            height: '60px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            border: 'none',
            background: activePath === item.path ? RED : 'transparent',
            color: activePath === item.path ? 'white' : '#bbb',
            fontSize: '9px',
            fontWeight: '700',
            borderRadius: '10px',
            textDecoration: 'none',
            transition: 'all 0.2s',
          }}
        >
          <span className="material-icons" style={{ fontSize: '24px' }}>
            {item.icon}
          </span>
          <span style={{ marginTop: '3px' }}>{item.label}</span>
        </Link>
      ))}
    </div>
  )
}