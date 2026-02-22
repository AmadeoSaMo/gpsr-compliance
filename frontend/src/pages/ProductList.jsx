import { useState, useEffect } from 'react'
import { Plus, ShieldCheck, Loader2, PackageOpen, FileText } from 'lucide-react'
import { Link } from 'react-router-dom'
import { downloadTechnicalFilePdf, downloadLabelPdf, listProducts } from '../api/gpsr'

const STORAGE_KEY = 'gpsr_products'

const categoryLabel = {
    textile: '🧣 Textiles',
    jewellery: '💍 Joyería',
    candle: '🕯️ Velas',
    ceramic: '🏺 Cerámica',
    wood: '🪵 Madera',
    cosmetic: '🧴 Cosméticos',
    toy: '🧸 Juguetes',
    paper: '📄 Papel',
    other: '📦 Otro',
}

const statusBadge = (risks = []) => {
    const high = risks.filter(r => r.risk_level === 'high').length
    const medium = risks.filter(r => r.risk_level === 'medium').length
    if (high > 0) return <span className="badge badge-red">⚠ En Riesgo</span>
    if (medium > 0) return <span className="badge badge-amber">⏳ Pendiente</span>
    return <span className="badge badge-green">✓ Conforme</span>
}

// Mock fallback data shown when no products exist yet
const MOCK_PRODUCTS = [
    {
        id: 'mock-1', is_mock: true,
        product_name: 'Ejemplo: Bufanda de Lana Merino',
        category: 'textile', version_number: '1.0',
        batch_code: '2024-TEX-001', saved_at: null,
        risks: [{ risk_level: 'low' }],
        bom: [{ material_name: 'Lana merino' }],
        warnings: [],
    }
]

export default function ProductList() {
    const [products, setProducts] = useState([])
    const [generating, setGenerating] = useState(null)
    const [isMock, setIsMock] = useState(false)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        listProducts()
            .then(data => {
                if (data.length > 0) {
                    setProducts(data)
                    setIsMock(false)
                } else {
                    setProducts(MOCK_PRODUCTS)
                    setIsMock(true)
                }
            })
            .catch(() => {
                setProducts(MOCK_PRODUCTS)
                setIsMock(true)
            })
            .finally(() => setLoading(false))
    }, [])

    if (loading) return <div style={{ padding: 40, color: 'var(--text-muted)' }}>Cargando productos...</div>

    const handleDownloadPdf = async (p, index) => {
        setGenerating(index + '-pdf')
        try {
            await downloadTechnicalFilePdf(p)
        } catch (err) {
            alert(err.message || 'Error al generar el PDF de ' + p.product_name)
        }
        setGenerating(null)
    }

    const handleDownloadLabel = async (p, index) => {
        setGenerating(index + '-label')
        try {
            await downloadLabelPdf(p)
        } catch (err) {
            alert(err.message || 'Error al generar la etiqueta de ' + p.product_name)
        }
        setGenerating(null)
    }

    return (
        <>
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h2>Mis Productos</h2>
                    <p>Gestiona todas las familias de productos y sus versiones GPSR.</p>
                </div>
                <Link to="/wizard" className="btn btn-primary">
                    <Plus size={16} /> Nuevo Producto
                </Link>
            </div>

            {isMock && (
                <div className="check-item" style={{
                    background: 'var(--blue-dim)', borderColor: 'var(--blue)',
                    marginBottom: 20, alignItems: 'flex-start'
                }}>
                    <FileText size={16} style={{ color: 'var(--blue)', flexShrink: 0, marginTop: 2 }} />
                    <div style={{ fontSize: 13 }}>
                        <strong>Mostrando datos de ejemplo.</strong> Crea tu primer producto real usando el asistente{' '}
                        <Link to="/wizard" style={{ color: 'var(--blue)' }}>Nuevo Producto →</Link>
                    </div>
                </div>
            )}

            {products.length === 0 ? (
                <div className="card" style={{ padding: '60px 40px', textAlign: 'center' }}>
                    <PackageOpen size={56} style={{ opacity: 0.15, display: 'block', margin: '0 auto 20px' }} />
                    <h3 style={{ marginBottom: 8 }}>Sin productos todavía</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 24 }}>
                        Crea tu primer producto GPSR con el asistente en pocos minutos.
                    </p>
                    <Link to="/wizard" className="btn btn-primary">
                        <Plus size={16} /> Crear primer producto
                    </Link>
                </div>
            ) : (
                <div className="card">
                    <div className="card-title">
                        <ShieldCheck size={18} style={{ color: 'var(--blue)' }} />
                        Catálogo ({isMock ? '0' : products.length} productos reales{isMock ? ' — ejemplo' : ''})
                    </div>
                    <div className="table-wrap">
                        <table>
                            <thead>
                                <tr>
                                    <th>Producto</th>
                                    <th>Categoría</th>
                                    <th>Versión</th>
                                    <th>Lote</th>
                                    <th>Materiales</th>
                                    <th>Creado</th>
                                    <th>Estado</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {products.map((p, i) => (
                                    <tr key={p.id} style={{ opacity: p.is_mock ? 0.55 : 1 }}>
                                        <td style={{ fontWeight: 600 }}>
                                            {p.product_name}
                                            {p.is_mock && <span className="badge badge-blue" style={{ marginLeft: 6, fontSize: 10 }}>Ejemplo</span>}
                                        </td>
                                        <td style={{ color: 'var(--text-muted)' }}>
                                            {categoryLabel[p.category] || p.category}
                                        </td>
                                        <td>
                                            <span className="badge badge-blue">v{p.version_number}</span>
                                        </td>
                                        <td>
                                            <span style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--text-muted)' }}>
                                                {p.batch_code}
                                            </span>
                                        </td>
                                        <td style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                                            {p.bom?.length > 0
                                                ? <span>{p.bom.slice(0, 2).map(b => b.material_name).join(', ')}{p.bom.length > 2 ? ` +${p.bom.length - 2}` : ''}</span>
                                                : <span style={{ color: 'var(--text-dim)' }}>—</span>
                                            }
                                        </td>
                                        <td style={{ fontSize: 12, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                                            {p.saved_at ? new Date(p.saved_at).toLocaleDateString('es-ES') : '—'}
                                        </td>
                                        <td>{statusBadge(p.risks)}</td>
                                        <td>
                                            <div style={{ display: 'flex', gap: 6 }}>
                                                <Link
                                                    to="/wizard"
                                                    state={{ product: p }}
                                                    className="btn btn-sm btn-secondary"
                                                    title="Editar / ver detalles"
                                                >
                                                    ✏️ Editar
                                                </Link>
                                                <button
                                                    className="btn btn-sm btn-secondary"
                                                    onClick={() => handleDownloadPdf(p, i)}
                                                    disabled={generating !== null || p.is_mock}
                                                    title="Generar Expediente Técnico PDF"
                                                >
                                                    {generating === i + '-pdf'
                                                        ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
                                                        : '📄 PDF'
                                                    }
                                                </button>
                                                <button
                                                    className="btn btn-sm btn-secondary"
                                                    onClick={() => handleDownloadLabel(p, i)}
                                                    disabled={generating !== null || p.is_mock}
                                                    title="Generar etiqueta para imprimir"
                                                >
                                                    {generating === i + '-label' ? '⏳' : '🏷️'}
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-dim)' }}>
                        💡 Los productos reales aparecen aquí tras completar el Wizard y pulsar "Finalizar y Guardar".
                    </div>
                </div>
            )}

            <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
        </>
    )
}
