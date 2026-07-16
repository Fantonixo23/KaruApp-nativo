import { Routes, Route, Navigate } from 'react-router-dom'
import Inicio from './pages/Inicio'
import NuevaVenta from './pages/NuevaVenta'
import Cocina from './pages/Cocina'
import Caja from './pages/Caja'
import Delivery from './pages/Delivery'
import Informes from './pages/Informes'
import Productos from './pages/Productos'
import Inventario from './pages/Inventario'
import Configuracion from './pages/Configuracion'
import SifenConfig from './pages/SifenConfig'
import { Config, Mesero, ParaLlevar, Admin } from './pages/Placeholders'
import { FullscreenProvider } from './hooks/useFullscreen.jsx'
import { useMediaQuery } from './hooks/useMediaQuery'
import LicenseBanner from './components/LicenseBanner'

export default function App() {
  useMediaQuery()
  return (
    <FullscreenProvider>
      <LicenseBanner />
      <Routes>
        <Route path="/" element={<Navigate to="/app/inicio" replace />} />
        <Route path="/app/inicio" element={<Inicio />} />
        <Route path="/app/mesas" element={<NuevaVenta />} />
        <Route path="/app/cocina" element={<Cocina />} />
        <Route path="/app/caja" element={<Caja />} />
        <Route path="/app/delivery" element={<Delivery />} />
        <Route path="/app/informes" element={<Informes />} />
        <Route path="/app/productos" element={<Productos />} />
        <Route path="/app/inventario" element={<Inventario />} />
        <Route path="/app/configuracion" element={<Configuracion />} />
        <Route path="/app/sifen" element={<SifenConfig />} />
        <Route path="/app/config" element={<Config />} />
        <Route path="/app/mesero" element={<Mesero />} />
        <Route path="/app/para-llevar" element={<ParaLlevar />} />
        <Route path="/app/admin" element={<Admin />} />
      </Routes>
    </FullscreenProvider>
  )
}