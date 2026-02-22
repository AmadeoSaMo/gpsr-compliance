import { useState, useEffect } from 'react'
import { ShieldCheck, AlertTriangle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { listProducts } from '../api/gpsr'

const STORAGE_KEY = 'gpsr_products'

const categoryLabel = {
    textile: '🧣 Textiles', jewellery: '💍 Joyería', candle: '🕯️ Velas',
    ceramic: '🏺 Cerámica', wood: '🪵 Madera', cosmetic: '🧴 Cosméticos',
    toy: '🧸 Juguetes', paper: '📄 Papel', other: '📦 Otro',
}

// Derive compliance status + score from stored risk data
function deriveStatus(p) {
    const risks = p.risks || []
    const high = risks.filter(r => r.risk_level === 'high').length
    const medium = risks.filter(r => r.risk_level === 'medium').length
    if (high > 0) return { status: 'at_risk', score: Math.max(20, 55 - high * 15) }
    if (medium > 0) return { status: 'pending', score: Math.min(79, 65 + (risks.length - medium) * 5) }
    return { status: 'compliant', score: Math.min(99, 88 + Math.floor(Math.random() * 10)) }
}

const MOCK = [
    { id: 'm1', product_name: 'Bufanda de Lana Merino', category: 'textile', version_number: '1.2', batch_code: '2024-TEX-001', risks: [], is_mock: true },
    { id: 'm2', product_name: 'Vela de Cera de Abeja', category: 'candle', version_number: '1.0', batch_code: '2024-CAN-001', risks: [{ risk_level: 'medium' }], is_mock: true },
    { id: 'm3', product_name: 'Pulsera de Plata', category: 'jewellery', version_number: '2.1', batch_code: '2024-JEW-003', risks: [], is_mock: true },
    { id: 'm4', product_name: 'Cerámica Decorativa', category: 'ceramic', version_number: '1.0', batch_code: '2024-CER-001', risks: [{ risk_level: 'high' }, { risk_level: 'medium' }], is_mock: true },
]

const statusBadge = (s) => {
    if (s === 'compliant') return <span className="badge badge-green">✓ Conforme</span>
    if (s === 'pending') return <span className="badge badge-amber">⏳ Pendiente</span>
    return <span className="badge badge-red">⚠ En Riesgo</span>
}

export default function Dashboard() {
    const [products, setProducts] = useState([])
    const [isMock, setIsMock] = useState(false)

    useEffect(() => {
        listProducts()
            .then(data => {
                if (data.length > 0) {
                    setProducts(data)
                    setIsMock(false)
                } else {
                    setProducts(MOCK)
                    setIsMock(true)
                }
            })
            .catch(() => {
                setProducts(MOCK)
                setIsMock(true)
            })
    }, [])

    const enriched = products.map(p => ({ ...p, ...deriveStatus(p) }))
    const compliant = enriched.filter(p => p.status === 'compliant').length
    const pending = enriched.filter(p => p.status === 'pending').length
    const atRisk = enriched.filter(p => p.status === 'at_risk').length
    const avgScore = enriched.length > 0
        ? Math.round(enriched.reduce((a, p) => a + p.score, 0) / enriched.length)
        : 0

    const pendingActions = enriched.filter(p => p.status !== 'compliant').flatMap(p => {
        const items = []
        if ((p.risks || []).some(r => r.risk_level === 'high'))
            items.push({ product: p.product_name, msg: 'Riesgo ALTO sin mitigar — verificar medidas correctoras.' })
        if ((p.risks || []).some(r => r.risk_level === 'medium'))
            items.push({ product: p.product_name, msg: 'Análisis de riesgos incompleto — revisar gravedad.' })
        if (!p.warnings || p.warnings.length === 0)
            items.push({ product: p.product_name, msg: 'Advertencias de seguridad para la etiqueta no confirmadas.' })
        return items
    }).slice(0, 5) // max 5

    return (
        <>
            <div className="page-header">
                <h2>Dashboard de Cumplimiento</h2>
                <p>
                    Resumen del estado actual de cumplimiento GPSR de tus productos.
                    {isMock && <span style={{ marginLeft: 8, fontSize: 12, color: 'var(--text-dim)' }}>(datos de ejemplo)</span>}
                </p>
            </div>

            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-label">Puntuación Global</div>
                    <div className="stat-value" style={{ color: avgScore > 75 ? 'var(--green)' : 'var(--amber)' }}>{avgScore}%</div>
                    <div className="stat-sub">Media de todos los productos</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Conformes</div>
                    <div className="stat-value" style={{ color: 'var(--green)' }}>{compliant}</div>
                    <div className="stat-sub">de {products.length} productos</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Pendientes</div>
                    <div className="stat-value" style={{ color: 'var(--amber)' }}>{pending}</div>
                    <div className="stat-sub">documentación incompleta</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">En Riesgo</div>
                    <div className="stat-value" style={{ color: 'var(--red)' }}>{atRisk}</div>
                    <div className="stat-sub">acción requerida</div>
                </div>
            </div>

            <div className="card">
                <div className="card-title">
                    <ShieldCheck size={18} style={{ color: 'var(--blue)' }} />
                    Estado de Productos
                </div>
                <div className="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Producto</th>
                                <th>Categoría</th>
                                <th>Versión</th>
                                <th>Puntuación</th>
                                <th>Estado</th>
                                <th>Acción</th>
                            </tr>
                        </thead>
                        <tbody>
                            {enriched.map((p) => (
                                <tr key={p.id} style={{ opacity: p.is_mock ? 0.6 : 1 }}>
                                    <td style={{ fontWeight: 500 }}>
                                        {p.product_name}
                                        {p.is_mock && <span className="badge badge-blue" style={{ marginLeft: 6, fontSize: 10 }}>Ejemplo</span>}
                                    </td>
                                    <td style={{ color: 'var(--text-muted)' }}>{categoryLabel[p.category] || p.category}</td>
                                    <td><span className="badge badge-blue">v{p.version_number}</span></td>
                                    <td>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                            <div style={{ flex: 1, height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
                                                <div style={{
                                                    width: `${p.score}%`, height: '100%', borderRadius: 3,
                                                    background: p.score > 75 ? 'var(--green)' : p.score > 50 ? 'var(--amber)' : 'var(--red)'
                                                }} />
                                            </div>
                                            <span style={{ fontSize: 13, color: 'var(--text-muted)', minWidth: 32 }}>{p.score}%</span>
                                        </div>
                                    </td>
                                    <td>{statusBadge(p.status)}</td>
                                    <td>
                                        <Link to="/wizard" state={{ product: p }} className="btn btn-sm btn-secondary">
                                            {p.is_mock ? 'Ejemplo' : 'Ver →'}
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {pendingActions.length > 0 && (
                <div className="card">
                    <div className="card-title">
                        <AlertTriangle size={18} style={{ color: 'var(--amber)' }} />
                        Tareas Pendientes
                    </div>
                    <div className="checks-list">
                        {pendingActions.map((a, i) => (
                            <div key={i} className="check-item">
                                <AlertTriangle size={16} className="check-icon" />
                                <div><strong>{a.product}</strong> — {a.msg}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {isMock && (
                <div className="card" style={{ marginTop: 16, display: 'flex', alignItems: 'center', gap: 16, padding: '20px 24px' }}>
                    <div style={{ flex: 1, fontSize: 14 }}>
                        <strong>¿Listo para empezar?</strong>
                        <span style={{ color: 'var(--text-muted)', marginLeft: 8 }}>
                            Añade tu primer producto real y genera tu Expediente Técnico GPSR.
                        </span>
                    </div>
                    <Link to="/wizard" className="btn btn-primary" style={{ flexShrink: 0 }}>
                        Crear mi primer producto →
                    </Link>
                </div>
            )}
        </>
    )
}
