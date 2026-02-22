import { useState, useEffect } from 'react'
import { AlertTriangle, Plus, ShieldAlert, CheckCircle, Trash2, PackageOpen } from 'lucide-react'

const STORAGE_KEY = 'gpsr_incidents'
const PRODUCTS_KEY = 'gpsr_products'

const SEVERITY_LEVELS = [
    { value: 'minor', label: '🟡 Leve — No requiere actuación inmediata', serious: false },
    { value: 'moderate', label: '🟠 Moderado — Seguimiento recomendado', serious: false },
    { value: 'serious', label: '🔴 Grave — Notificación obligatoria (Art. 20 GPSR)', serious: true },
    { value: 'recall', label: '⛔ Retirada de mercado — Acción inmediata', serious: true },
]

export default function Incidents() {
    const [incidents, setIncidents] = useState([])
    const [products, setProducts] = useState([])
    const [showForm, setShowForm] = useState(false)
    const [saved, setSaved] = useState(false)

    const [form, setForm] = useState({
        product_id: '',
        product_name: '',
        description: '',
        severity: 'minor',
        is_serious: false,
        authority_notified: false,
        resolution: '',
        reported_at: new Date().toISOString().split('T')[0],
    })

    useEffect(() => {
        const stored = localStorage.getItem(STORAGE_KEY)
        if (stored) { try { setIncidents(JSON.parse(stored)) } catch { } }
        const prods = localStorage.getItem(PRODUCTS_KEY)
        if (prods) { try { setProducts(JSON.parse(prods)) } catch { } }
    }, [])

    const setF = (field, value) => {
        setSaved(false)
        setForm(prev => {
            const next = { ...prev, [field]: value }
            if (field === 'severity') {
                const lvl = SEVERITY_LEVELS.find(s => s.value === value)
                next.is_serious = lvl?.serious ?? false
            }
            if (field === 'product_id') {
                const prod = products.find(p => p.id === value)
                next.product_name = prod?.product_name || value
            }
            return next
        })
    }

    const handleSave = () => {
        const incident = {
            id: `inc-${Date.now()}`,
            ...form,
            created_at: new Date().toISOString()
        }
        const updated = [incident, ...incidents]
        setIncidents(updated)
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
        setShowForm(false)
        setSaved(false)
        setForm({
            product_id: '', product_name: '',
            description: '', severity: 'minor', is_serious: false,
            authority_notified: false, resolution: '',
            reported_at: new Date().toISOString().split('T')[0],
        })
    }

    const handleDelete = (id) => {
        if (!confirm('¿Eliminar este registro de incidencia?')) return
        const updated = incidents.filter(i => i.id !== id)
        setIncidents(updated)
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    }

    const sevBadge = (sev) => {
        const colors = {
            minor: '#ca8a04',
            moderate: '#ea580c',
            serious: '#dc2626',
            recall: '#7c3aed',
        }
        const labels = { minor: 'Leve', moderate: 'Moderado', serious: 'Grave', recall: 'Retirada' }
        const bg = colors[sev] || 'var(--text-muted)'
        return (
            <span className="badge" style={{ background: bg + '22', color: bg }}>
                {labels[sev] || sev}
            </span>
        )
    }

    const seriousCount = incidents.filter(i => i.is_serious).length

    return (
        <>
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h2>Registro de Incidencias</h2>
                    <p>Documentación de quejas, accidentes y retiradas según el Art. 20 del GPSR.</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowForm(v => !v)}>
                    <Plus size={16} /> Registrar Incidencia
                </button>
            </div>

            {/* Alerta si hay incidencias graves */}
            {seriousCount > 0 && (
                <div className="check-item" style={{
                    background: 'rgba(220,38,38,0.08)', borderColor: 'var(--red)',
                    marginBottom: 20, alignItems: 'flex-start'
                }}>
                    <ShieldAlert size={18} style={{ color: 'var(--red)', flexShrink: 0, marginTop: 2 }} />
                    <div>
                        <strong style={{ color: 'var(--red)' }}>
                            {seriousCount} incidencia{seriousCount > 1 ? 's' : ''} grave{seriousCount > 1 ? 's' : ''} registrada{seriousCount > 1 ? 's' : ''}
                        </strong>
                        <div style={{ fontSize: 13, marginTop: 2 }}>
                            Las incidencias graves deben notificarse a través del{' '}
                            <a href="https://ec.europa.eu/safety-gate-alerts/screen/webReport" target="_blank" rel="noreferrer"
                                style={{ color: 'var(--red)' }}>Safety Business Gateway</a>{' '}
                            en un plazo de 2 días hábiles (Art. 20.4 GPSR).
                        </div>
                    </div>
                </div>
            )}

            {/* Formulario de nueva incidencia */}
            {showForm && (
                <div className="card" style={{ marginBottom: 20 }}>
                    <div className="card-title">
                        <Plus size={16} style={{ color: 'var(--blue)' }} /> Nueva Incidencia
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Producto afectado</label>
                            {products.length > 0 ? (
                                <select className="form-select" value={form.product_id} onChange={e => setF('product_id', e.target.value)}>
                                    <option value="">— Selecciona producto —</option>
                                    {products.map(p => <option key={p.id} value={p.id}>{p.product_name} ({p.batch_code})</option>)}
                                </select>
                            ) : (
                                <input
                                    className="form-input"
                                    value={form.product_name}
                                    onChange={e => setF('product_name', e.target.value)}
                                    placeholder="Nombre del producto afectado"
                                />
                            )}
                        </div>
                        <div className="form-group">
                            <label className="form-label">Fecha del incidente</label>
                            <input
                                className="form-input"
                                type="date"
                                value={form.reported_at}
                                onChange={e => setF('reported_at', e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Gravedad <span>*</span></label>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
                            {SEVERITY_LEVELS.map(lvl => (
                                <label key={lvl.value} style={{
                                    display: 'flex', gap: 10, alignItems: 'center',
                                    padding: '10px 14px',
                                    background: form.severity === lvl.value ? 'var(--blue-dim)' : 'var(--bg)',
                                    border: `1.5px solid ${form.severity === lvl.value ? 'var(--blue)' : 'var(--border)'}`,
                                    borderRadius: 'var(--radius-sm)', cursor: 'pointer', transition: 'all 0.15s',
                                    fontSize: 13
                                }}>
                                    <input type="radio" name="severity" value={lvl.value} checked={form.severity === lvl.value}
                                        onChange={() => setF('severity', lvl.value)} style={{ accentColor: 'var(--blue)' }} />
                                    {lvl.label}
                                    {lvl.serious && <span className="badge badge-red" style={{ marginLeft: 'auto' }}>Notificación obligatoria</span>}
                                </label>
                            ))}
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Descripción del incidente <span>*</span></label>
                        <textarea
                            className="form-textarea"
                            value={form.description}
                            onChange={e => setF('description', e.target.value)}
                            placeholder="Describe qué ocurrió, cómo se detectó y las personas involucradas..."
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Resolución / Medidas tomadas</label>
                        <textarea
                            className="form-textarea"
                            style={{ minHeight: 80 }}
                            value={form.resolution}
                            onChange={e => setF('resolution', e.target.value)}
                            placeholder="Describe las acciones correctivas tomadas..."
                        />
                    </div>

                    {form.is_serious && (
                        <label style={{
                            display: 'flex', gap: 10, alignItems: 'flex-start',
                            padding: '12px 16px', marginBottom: 16,
                            background: 'rgba(220,38,38,0.08)', border: '1.5px solid var(--red)',
                            borderRadius: 'var(--radius-sm)', cursor: 'pointer', fontSize: 13
                        }}>
                            <input type="checkbox" checked={form.authority_notified}
                                onChange={e => setF('authority_notified', e.target.checked)}
                                style={{ accentColor: 'var(--red)', marginTop: 2 }} />
                            <span>He notificado esta incidencia grave a las autoridades de vigilancia del mercado a través del{' '}
                                <a href="https://ec.europa.eu/safety-gate-alerts/screen/webReport" target="_blank" rel="noreferrer"
                                    style={{ color: 'var(--red)' }}>Safety Business Gateway</a>
                            </span>
                        </label>
                    )}

                    <div style={{ display: 'flex', gap: 10 }}>
                        <button
                            className="btn btn-primary"
                            onClick={handleSave}
                            disabled={!form.description || (!form.product_id && !form.product_name)}
                        >
                            <CheckCircle size={15} /> Guardar Incidencia
                        </button>
                        <button className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancelar</button>
                    </div>
                </div>
            )}

            {/* Historial */}
            {incidents.length === 0 ? (
                <div className="card" style={{ padding: '60px 40px', textAlign: 'center' }}>
                    <PackageOpen size={48} style={{ opacity: 0.15, margin: '0 auto 20px', display: 'block' }} />
                    <h3 style={{ marginBottom: 8 }}>Sin incidencias registradas</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>
                        El GPSR exige registrar cualquier queja de seguridad aunque no sea grave.
                        Registra incidencias incluso menores para demostrar diligencia debida.
                    </p>
                </div>
            ) : (
                <div className="card">
                    <div className="card-title">
                        <AlertTriangle size={18} style={{ color: 'var(--amber)' }} />
                        Historial de incidencias ({incidents.length})
                    </div>
                    <div className="table-wrap">
                        <table>
                            <thead>
                                <tr>
                                    <th>Fecha</th>
                                    <th>Producto</th>
                                    <th>Gravedad</th>
                                    <th>Descripción</th>
                                    <th>Autoridad Notificada</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {incidents.map(inc => (
                                    <tr key={inc.id}>
                                        <td style={{ fontSize: 13, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                                            {new Date(inc.reported_at).toLocaleDateString('es-ES')}
                                        </td>
                                        <td style={{ fontWeight: 500 }}>{inc.product_name || '—'}</td>
                                        <td>{sevBadge(inc.severity)}</td>
                                        <td style={{ fontSize: 13, maxWidth: 300 }}>
                                            <span style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                                                {inc.description}
                                            </span>
                                        </td>
                                        <td>
                                            {inc.is_serious
                                                ? inc.authority_notified
                                                    ? <span className="badge badge-green">✓ Notificado</span>
                                                    : <span className="badge badge-red">⚠ Pendiente</span>
                                                : <span style={{ color: 'var(--text-dim)', fontSize: 12 }}>N/A</span>
                                            }
                                        </td>
                                        <td>
                                            <button
                                                className="btn btn-sm btn-secondary"
                                                onClick={() => handleDelete(inc.id)}
                                                style={{ color: 'var(--red)' }}
                                            >
                                                <Trash2 size={12} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </>
    )
}
