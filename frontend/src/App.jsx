import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ProductWizard from './pages/ProductWizard'
import ProductList from './pages/ProductList'
import Documents from './pages/Documents'
import Labels from './pages/Labels'
import Incidents from './pages/Incidents'
import Settings from './pages/Settings'
import {
  LayoutDashboard, ShieldCheck, PackagePlus, FileText,
  Tag, AlertTriangle, Settings as SettingsIcon
} from 'lucide-react'

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>🛡️ GPSR Comply</h1>
        <span>Reglamento UE 2023/988</span>
      </div>
      <nav className="sidebar-nav">
        <div className="nav-section-title">Principal</div>
        <NavLink to="/" end className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
          <LayoutDashboard size={16} /> Dashboard
        </NavLink>
        <NavLink to="/products" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
          <ShieldCheck size={16} /> Mis Productos
        </NavLink>
        <NavLink to="/wizard" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
          <PackagePlus size={16} /> Nuevo Producto
        </NavLink>

        <div className="nav-section-title" style={{ marginTop: 24 }}>Documentación</div>
        <NavLink to="/documents" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
          <FileText size={16} /> Expedientes
        </NavLink>
        <NavLink to="/labels" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
          <Tag size={16} /> Etiquetas
        </NavLink>
        <NavLink to="/incidents" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
          <AlertTriangle size={16} /> Incidencias
        </NavLink>

        <div className="nav-section-title" style={{ marginTop: 24 }}>Sistema</div>
        <NavLink to="/settings" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
          <SettingsIcon size={16} /> Configuración
        </NavLink>
      </nav>
    </aside>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/products" element={<ProductList />} />
            <Route path="/wizard" element={<ProductWizard />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/labels" element={<Labels />} />
            <Route path="/incidents" element={<Incidents />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
