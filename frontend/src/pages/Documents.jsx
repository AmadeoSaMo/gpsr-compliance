import { useState, useEffect } from 'react'
import { FileText, Download, Trash2, PackageOpen, Plus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { downloadTechnicalFilePdf, downloadLabelPdf, downloadAmazonImage, listProducts, deleteProduct } from '../api/gpsr'

const categoryLabel = {
    textile: '🧣 Textiles', jewellery: '💍 Joyería', candle: '🕯️ Velas',
    ceramic: '🏺 Cerámica', wood: '🪵 Madera', cosmetic: '🧴 Cosméticos',
    toy: '🧸 Juguetes', paper: '📄 Papel', other: '📦 Otro',
}

export default function Documents() {
    const [products, setProducts] = useState([])
    const [loading, setLoading] = useState(true)
    const [generating, setGenerating] = useState(null)

    useEffect(() => {
        listProducts()
            .then(setProducts)
            .catch(() => setProducts([]))
            .finally(() => setLoading(false))
    }, [])

    const handleDelete = async (id) => {
        if (!confirm('¿Eliminar este producto? Esta acción no se puede deshacer.')) return
        try {
            await deleteProduct(id)
            setProducts(prev => prev.filter(p => p.id !== id))
        } catch (err) {
            alert('Error al eliminar: ' + (err.response?.data?.detail || err.message))
        }
    }

    const handlePdf = async (p) => {
        setGenerating(p.id + '-pdf')
        try { await downloadTechnicalFilePdf(p) }
        catch (err) { alert(err.message || 'Error al generar el expediente') }
        setGenerating(null)
    }

    const handleLabel = async (p) => {
        setGenerating(p.id + '-label')
        try { await downloadLabelPdf(p) }
        catch (err) { alert(err.message || 'Error al generar la etiqueta') }
        setGenerating(null)
    }

    const handleAmazon = async (p) => {
        setGenerating(p.id + '-amazon')
        try { await downloadAmazonImage(p.id) }
        catch (err) { alert(err.message || 'Error al generar la imagen para Amazon') }
        setGenerating(null)
    }

    if (loading) return <div style={{ padding: 40, color: 'var(--text-muted)' }}>Cargando expedientes...</div>

    return (
        <>
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h2>Expedientes Técnicos</h2>
                    <p>Historial de todos los expedientes GPSR generados y guardados.</p>
                </div>
                <Link to="/wizard" className="btn btn-primary">
                    <Plus size={16} /> Nuevo Producto
                </Link>
            </div>

            {products.length === 0 ? (
                <div className="card" style={{ padding: '60px 40px', textAlign: 'center' }}>
                    <PackageOpen size={56} style={{ opacity: 0.15, display: 'block', margin: '0 auto 20px' }} />
                    <h3 style={{ marginBottom: 8 }}>Todavía no hay expedientes generados</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 24 }}>
                        Usa el asistente para crear tu primer producto y generar su Expediente Técnico GPSR.
                    </p>
                    <Link to="/wizard" className="btn btn-primary">
                        <Plus size={16} /> Crear primer producto
                    </Link>
                </div>
            ) : (
                <div className="card">
                    <div className="card-title">
                        <FileText size={18} style={{ color: 'var(--blue)' }} />
                        Expedientes guardados ({products.length})
                    </div>
                    <div className="table-wrap">
                        <table>
                            <thead>
                                <tr>
                                    <th>Producto</th>
                                    <th>Categoría</th>
                                    <th>Lote</th>
                                    <th>Versión</th>
                                    <th>Creado</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {products.map((p) => (
                                    <tr key={p.id}>
                                        <td style={{ fontWeight: 600 }}>{p.product_name}</td>
                                        <td style={{ color: 'var(--text-muted)' }}>{categoryLabel[p.category] || p.category}</td>
                                        <td>
                                            <span style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--text-muted)' }}>
                                                {p.batch_code}
                                            </span>
                                        </td>
                                        <td><span className="badge badge-blue">v{p.version_number}</span></td>
                                        <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                            {p.saved_at ? new Date(p.saved_at).toLocaleDateString('es-ES') : '—'}
                                        </td>
                                        <td>
                                            <div style={{ display: 'flex', gap: 6 }}>
                                                <button className="btn btn-sm btn-primary"
                                                    onClick={() => handlePdf(p)} disabled={generating !== null}>
                                                    {generating === p.id + '-pdf' ? '⏳' : <><Download size={12} /> Expediente</>}
                                                </button>
                                                <button className="btn btn-sm btn-secondary"
                                                    onClick={() => handleLabel(p)} disabled={generating !== null}>
                                                    {generating === p.id + '-label' ? '⏳' : '🏷️ Etiqueta'}
                                                </button>
                                                <button className="btn btn-sm btn-secondary"
                                                    onClick={() => handleAmazon(p)} disabled={generating !== null}
                                                    title="Generar Imagen Art. 19 para Amazon"
                                                    style={{ color: 'var(--blue)' }}>
                                                    {generating === p.id + '-amazon' ? '⏳' : '📦 Amazon'}
                                                </button>
                                                <button className="btn btn-sm btn-secondary"
                                                    onClick={() => handleDelete(p.id)}
                                                    style={{ color: 'var(--red)' }} title="Eliminar">
                                                    <Trash2 size={12} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <div style={{ marginTop: 16, fontSize: 12, color: 'var(--text-dim)' }}>
                        ℹ️ Los expedientes técnicos deben conservarse durante <strong>10 años</strong> según el Art. 9 del GPSR.
                    </div>
                </div>
            )}
        </>
    )
}
