import { useState, useEffect } from 'react'
import { Tag, Download, PackageOpen, Plus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { downloadLabelPdf, listProducts } from '../api/gpsr'

const STORAGE_KEY = 'gpsr_products'

const categoryLabel = {
    textile: '🧣 Textiles', jewellery: '💍 Joyería', candle: '🕯️ Velas',
    ceramic: '🏺 Cerámica', wood: '🪵 Madera', cosmetic: '🧴 Cosméticos',
    toy: '🧸 Juguetes', paper: '📄 Papel', other: '📦 Otro',
}

const SIZE_LABELS = {
    brother_62x100: 'Brother QL 62×100mm',
    brother_38x90: 'Brother QL 38×90mm',
    dymo_89x36: 'Dymo 89×36mm',
    zebra_100x150: 'Zebra 100×150mm',
    a6_148x105: 'A6 148×105mm',
}

export default function Labels() {
    const [products, setProducts] = useState([])
    const [generating, setGenerating] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        listProducts()
            .then(setProducts)
            .catch(() => setProducts([]))
            .finally(() => setLoading(false))
    }, [])

    const handleLabel = async (p) => {
        setGenerating(p.id)
        try {
            await downloadLabelPdf(p)
        } catch (err) {
            alert(err.message || 'Error al generar la etiqueta')
        }
        setGenerating(null)
    }

    if (loading) return <div style={{ padding: 40, color: 'var(--text-muted)' }}>Cargando etiquetas...</div>

    if (products.length === 0) {
        return (
            <>
                <div className="page-header">
                    <h2>Etiquetas Generadas</h2>
                    <p>Reimprime o descarga etiquetas físicas de tus productos GPSR.</p>
                </div>
                <div className="card" style={{ padding: '60px 40px', textAlign: 'center' }}>
                    <Tag size={56} style={{ opacity: 0.15, display: 'block', margin: '0 auto 20px' }} />
                    <h3 style={{ marginBottom: 8 }}>Sin productos guardados todavía</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 24 }}>
                        Crea y finaliza un producto desde el asistente para ver aquí sus etiquetas disponibles.
                    </p>
                    <Link to="/wizard" className="btn btn-primary">
                        <Plus size={16} /> Crear primer producto
                    </Link>
                </div>
            </>
        )
    }

    return (
        <>
            <div className="page-header">
                <h2>Etiquetas Generadas</h2>
                <p>Reimprime o descarga etiquetas físicas de tus productos GPSR (Art. 19).</p>
            </div>

            <div className="check-item" style={{ background: 'var(--blue-dim)', borderColor: 'var(--blue)', marginBottom: 20 }}>
                <Tag size={16} style={{ color: 'var(--blue)', flexShrink: 0 }} />
                <div style={{ fontSize: 13 }}>
                    <strong>Art. 19 GPSR — Etiquetado obligatorio:</strong> La etiqueta debe incluir tu nombre o marca,
                    dirección postal UE, email de contacto, número de lote y advertencias de seguridad en el idioma del país de venta.
                </div>
            </div>

            <div className="card">
                <div className="card-title">
                    <Tag size={18} style={{ color: 'var(--blue)' }} />
                    Etiquetas disponibles ({products.length} productos)
                </div>

                <div style={{ display: 'grid', gap: 12 }}>
                    {products.map((p) => (
                        <div key={p.id} style={{
                            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                            padding: '14px 18px',
                            background: 'var(--bg)', border: '1px solid var(--border)',
                            borderRadius: 'var(--radius-sm)'
                        }}>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontWeight: 600, marginBottom: 2 }}>{p.product_name}</div>
                                <div style={{ fontSize: 12, color: 'var(--text-muted)', display: 'flex', gap: 12 }}>
                                    <span>{categoryLabel[p.category] || p.category}</span>
                                    <span>Lote: <code style={{ fontSize: 11 }}>{p.batch_code}</code></span>
                                    <span>Tamaño: {SIZE_LABELS[p.label_size_key] || p.label_size_key}</span>
                                    {p.warnings?.length > 0 && (
                                        <span>{p.warnings.length} advertencia{p.warnings.length > 1 ? 's' : ''}</span>
                                    )}
                                </div>
                            </div>
                            <button
                                className="btn btn-sm btn-primary"
                                onClick={() => handleLabel(p)}
                                disabled={generating !== null}
                                style={{ flexShrink: 0, marginLeft: 16 }}
                            >
                                {generating === p.id
                                    ? '⏳ Generando...'
                                    : <><Download size={13} /> Imprimir Etiqueta</>
                                }
                            </button>
                        </div>
                    ))}
                </div>

                <div style={{ marginTop: 16, fontSize: 12, color: 'var(--text-dim)' }}>
                    💡 El tamaño de la etiqueta se configura en el Paso 4 del asistente de creación de producto.
                    Puedes editar el producto desde "Mis Productos" para cambiar el formato.
                </div>
            </div>
        </>
    )
}
