import { useState, useEffect } from 'react'
import { ChevronRight, ChevronLeft, Plus, X, Loader2, AlertTriangle, CheckCircle, FileText, Tag, Download, Printer } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { analyzeRisk, downloadTechnicalFilePdf, downloadLabelPdf, createProduct, updateProduct, listProducts, listResponsiblePersons, api } from '../api/gpsr'

const STEPS = [
    { id: 1, label: 'Producto' },
    { id: 2, label: 'Materiales' },
    { id: 3, label: 'Riesgos' },
    { id: 4, label: 'Etiquetado' },
    { id: 5, label: 'Revisar' },
]

const CATEGORIES = [
    { value: 'textile', label: '🧣 Textiles (ropa, bufandas, bolsas)' },
    { value: 'jewellery', label: '💍 Joyería y bisutería' },
    { value: 'candle', label: '🕯️ Velas y aromaterapia' },
    { value: 'ceramic', label: '🏺 Cerámica y alfarería' },
    { value: 'wood', label: '🪵 Madera y carpintería' },
    { value: 'cosmetic', label: '🧴 Cosméticos y jabones' },
    { value: 'toy', label: '🧸 Juguetes' },
    { value: 'paper', label: '📄 Papel y capetas' },
    { value: 'other', label: '📦 Otro' },
]

const StatusBadge = ({ risks = [] }) => {
    const high = risks.filter(r => r.risk_level === 'high').length
    const medium = risks.filter(r => r.risk_level === 'medium').length

    if (high > 0) return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
            <span className="badge badge-red">⚠ En Riesgo</span>
            <span style={{ fontSize: 10, color: 'var(--red)', marginTop: 4 }}>Requiere medidas inmediatas</span>
        </div>
    )
    if (medium > 0) return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
            <span className="badge badge-amber">⏳ Pendiente</span>
            <span style={{ fontSize: 10, color: 'var(--amber)', marginTop: 4 }}>Faltan medidas preventivas</span>
        </div>
    )
    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
            <span className="badge badge-green">✓ Conforme</span>
            <span style={{ fontSize: 10, color: 'var(--green)', marginTop: 4 }}>Listo para la venta</span>
        </div>
    )
}

function StepIndicator({ current }) {
    return (
        <div className="wizard-steps">
            {STEPS.map((step, i) => {
                const done = step.id < current
                const active = step.id === current
                return (
                    <div key={step.id} style={{ display: 'flex', alignItems: 'center', flex: i < STEPS.length - 1 ? 1 : 'none' }}>
                        <div className={`wizard-step${active ? ' active' : ''}${done ? ' done' : ''}`}>
                            <div className="step-circle">{done ? '✓' : step.id}</div>
                            <span style={{ whiteSpace: 'nowrap' }}>{step.label}</span>
                        </div>
                        {i < STEPS.length - 1 && <div className={`step-line${done ? ' done' : ''}`} />}
                    </div>
                )
            })}
        </div>
    )
}

function TagInput({ tags, onChange, placeholder }) {
    const [input, setInput] = useState('')
    const add = () => {
        const v = input.trim()
        if (v && !tags.includes(v)) onChange([...tags, v])
        setInput('')
    }
    const remove = (t) => onChange(tags.filter(x => x !== t))
    return (
        <div className="tags-input">
            {tags.map(t => (
                <span key={t} className="tag">
                    {t}
                    <button onClick={() => remove(t)}><X size={12} /></button>
                </span>
            ))}
            <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); add() } }}
                placeholder={placeholder || 'Escribe y pulsa Enter...'}
            />
        </div>
    )
}

const riskColor = (level) => ({ low: 'var(--green)', medium: 'var(--amber)', high: 'var(--red)' }[level] || 'var(--text-muted)')
const riskClass = (level) => ({ low: 'low', medium: 'medium', high: 'high' }[level] || '')

/** Converts old display strings like 'Textiles' to internal keys like 'textile'. */
const mapCategory = (catStr) => {
    if (!catStr) return ''
    if (catStr.includes('Textil')) return 'textile'
    if (catStr.includes('Vela')) return 'candle'
    if (catStr.includes('Joyer')) return 'jewellery'
    if (catStr.includes('Cerám')) return 'ceramic'
    if (catStr.includes('Madera') || catStr === 'wood') return 'wood'
    if (catStr.includes('Cosm') || catStr === 'cosmetic') return 'cosmetic'
    if (catStr.includes('Cerám') || catStr === 'ceramic') return 'ceramic'
    if (catStr.includes('Jugue') || catStr === 'toy') return 'toy'
    // If it's already a key (no spaces, no capitals mixed), return as-is
    if (!catStr.includes(' ')) return catStr
    return 'other'
}

export default function ProductWizard() {
    const location = useLocation()
    const navigate = useNavigate()
    const initialProduct = location.state?.product || null
    const initialCategory = location.state?.family || initialProduct?.category || ''

    // The API returns product_name; old localStorage used name — handle both
    const p = initialProduct || {}
    const resolvedName = p.product_name || p.name || ''
    // category comes directly from the API as a value key (e.g. 'textile')
    // The old mock data passed a display string like 'Textiles' — mapCategory handles that
    const resolvedCategory = p.category && !p.category.includes(' ')
        ? p.category              // already a key from the API
        : mapCategory(initialCategory)  // legacy string → key

    const [step, setStep] = useState(1)
    const [loading, setLoading] = useState(false)
    const [riskError, setRiskError] = useState('')    // error message for risk analysis
    const [generating, setGenerating] = useState('')  // 'pdf' | 'label' | ''
    const [generated, setGenerated] = useState([])    // list of completed doc types
    const [saved, setSaved] = useState(false)         // product saved to store

    // Step 1: Product Info
    const [productName, setProductName] = useState(resolvedName)
    const [category, setCategory] = useState(resolvedCategory)
    const [versionNumber, setVersionNumber] = useState(p.version_number || '1.0')
    const [description, setDescription] = useState(p.description || '')
    const [intendedUse, setIntendedUse] = useState(p.intended_use || '')
    const [foreseeableMisuse, setForeseeableMisuse] = useState(p.foreseeable_misuse || '')

    // Step 2: Materials — BOM items can be objects {material_name} or plain strings
    const [materials, setMaterials] = useState(
        p.bom?.map(b => typeof b === 'string' ? b : b.material_name).filter(Boolean) || []
    )
    const [mandatoryChecks, setMandatoryChecks] = useState([])

    // Step 3: Risks
    const [risks, setRisks] = useState(p.risks || [])
    const [mitigations, setMitigations] = useState(
        Object.fromEntries((p.risks || []).map((r, i) => [i, r.mitigation || '']))
    )
    // Add-risk form state
    const [showAddRisk, setShowAddRisk] = useState(false)
    const [newRisk, setNewRisk] = useState({ hazard_type: 'chemical', hazard_description: '', probability: 2, severity: 2 })

    // Step 4: Label & manufacturer
    const [batchCode, setBatchCode] = useState(
        p.batch_code || `${new Date().getFullYear()}-TEX-001`
    )
    const [manufacturerName, setManufacturerName] = useState(p.manufacturer_name || '')
    const [manufacturerEmail, setManufacturerEmail] = useState(p.manufacturer_email || '')
    const [manufacturerAddress, setManufacturerAddress] = useState(p.manufacturer_address || '')
    const [logoData, setLogoData] = useState(p.logo_data || '')
    const [suggestedWarnings, setSuggestedWarnings] = useState(
        (p.warnings || []).map(w => ({ text: w, source: 'saved', accepted: true }))
    )
    const [labelSizeKey, setLabelSizeKey] = useState(p.label_size_key || 'brother_62x100')
    const [labelSizes, setLabelSizes] = useState([])

    useEffect(() => {
        api.get('/documents/label/sizes')
            .then(r => setLabelSizes(r.data.sizes))
            .catch(() => setLabelSizes([
                { key: 'brother_62x100', label: 'Brother QL — 62×100mm (grande)', width_mm: 62, height_mm: 100 },
                { key: 'brother_38x90', label: 'Brother QL — 38×90mm (estándar)', width_mm: 38, height_mm: 90 },
                { key: 'dymo_89x36', label: 'Dymo LabelWriter — 89×36mm', width_mm: 89, height_mm: 36 },
                { key: 'zebra_100x150', label: 'Zebra — 100×150mm', width_mm: 100, height_mm: 150 },
                { key: 'a6_148x105', label: 'A6 — 148×105mm', width_mm: 148, height_mm: 105 },
            ]))
    }, [])

    // Auto-fill manufacturer from Settings when creating a NEW product
    // (Skip if editing: the product already has these fields)
    useEffect(() => {
        if (initialProduct) return   // editing mode — keep existing values
        if (manufacturerName) return // already filled (shouldn’t happen, but guard)
        listResponsiblePersons()
            .then(list => {
                if (list.length === 0) return
                const rp = list[0]
                setManufacturerName(rp.name || '')
                setManufacturerEmail(rp.email || '')
                setManufacturerAddress(
                    [rp.address, rp.country].filter(Boolean).join(', ')
                )
                setLogoData(rp.logo_data || '')
            })
            .catch(() => {/* silently ignore if API unavailable */ })
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    const fetchRiskAnalysis = async () => {
        if (!category || materials.length === 0) return
        setLoading(true)
        setRiskError('')
        try {
            const data = await analyzeRisk(category, materials)
            setRisks(data.risk_suggestions)
            setMandatoryChecks(data.mandatory_checks)
            // Pre-fill mitigation suggestions from the engine
            const prefilled = {}
            data.risk_suggestions.forEach((r, i) => {
                prefilled[i] = r.mitigation_suggestion || ''
            })
            setMitigations(prefilled)
            // Pre-load suggested warnings as checkbox list
            if (data.suggested_warnings?.length > 0) {
                setSuggestedWarnings(data.suggested_warnings)
            }
        } catch (err) {
            setRiskError(
                'No se pudo conectar con el motor de riesgos. ' +
                (err?.response?.data?.detail || err?.message || 'Verifica que el servidor esté activo.') +
                ' Puedes añadir los riesgos manualmente a continuación.'
            )
        }
        setLoading(false)
    }

    /** Build the payload shared by technical file and label endpoints */
    const buildPayload = () => ({
        product_name: productName,
        category,
        version_number: versionNumber || '1.0',
        batch_code: batchCode,
        manufacturer_name: manufacturerName || 'Fabricante',
        manufacturer_email: manufacturerEmail || 'contacto@ejemplo.com',
        manufacturer_address: manufacturerAddress || 'Dirección no especificada',
        description,
        intended_use: intendedUse,
        foreseeable_misuse: foreseeableMisuse || null,
        bom: materials.map(m => ({ material_name: m })),
        risks: risks.map((r, i) => ({ ...r, mitigation: mitigations[i] || null })),
        mandatory_checks: mandatoryChecks,
        warnings: suggestedWarnings.filter(w => w.accepted).map(w => w.text),
        label_size_key: labelSizeKey,
        logo_data: logoData,
    })

    const handleDownloadPdf = async () => {
        setGenerating('pdf')
        try {
            await downloadTechnicalFilePdf(buildPayload())
            setGenerated(g => [...new Set([...g, 'pdf'])])
        } catch (e) { console.error(e) }
        setGenerating('')
    }

    const handleDownloadLabel = async () => {
        setGenerating('label')
        try {
            await downloadLabelPdf(buildPayload())
            setGenerated(g => [...new Set([...g, 'label'])])
        } catch (e) { console.error(e) }
        setGenerating('')
    }

    const updateRisk = (i, field, val) => {
        const updated = [...risks]
        updated[i] = { ...updated[i], [field]: Number(val) }
        const score = updated[i].probability * updated[i].severity
        updated[i].risk_score = score
        updated[i].risk_level = score <= 4 ? 'low' : score <= 12 ? 'medium' : 'high'
        setRisks(updated)
    }

    const deleteRisk = (i) => {
        const updatedRisks = risks.filter((_, idx) => idx !== i)
        // Rebuild mitigations with re-indexed keys
        const updatedMitigations = {}
        updatedRisks.forEach((_, idx) => {
            const oldIdx = idx < i ? idx : idx + 1
            updatedMitigations[idx] = mitigations[oldIdx] || ''
        })
        setRisks(updatedRisks)
        setMitigations(updatedMitigations)
    }

    const addRiskManually = () => {
        if (!newRisk.hazard_description.trim()) return
        const score = newRisk.probability * newRisk.severity
        const level = score <= 4 ? 'low' : score <= 12 ? 'medium' : 'high'
        const entry = { ...newRisk, risk_score: score, risk_level: level }
        setRisks(prev => [...prev, entry])
        setMitigations(prev => ({ ...prev, [risks.length]: '' }))
        setNewRisk({ hazard_type: 'chemical', hazard_description: '', probability: 2, severity: 2 })
        setShowAddRisk(false)
    }

    const next = async () => {
        if (step === 2) await fetchRiskAnalysis()
        if (step === 1) setBatchCode(`${new Date().getFullYear()}-${category.toUpperCase().slice(0, 3)}-001`)
        setStep(s => Math.min(s + 1, 5))
        window.scrollTo({ top: 0, behavior: 'smooth' })
    }
    const prev = () => setStep(s => Math.max(s - 1, 1))

    const handleFinalize = async () => {
        setLoading(true)
        try {
            const payload = buildPayload()
            const apiPayload = {
                ...payload,
                bom: payload.bom.map(b => typeof b === 'string' ? { material_name: b } : b),
            }

            if (initialProduct && versionNumber === initialProduct.version_number) {
                // Editing mode — update existing record
                await updateProduct(initialProduct.id, apiPayload)
            } else {
                try {
                    await createProduct(apiPayload)
                } catch (createErr) {
                    // If duplicate (400), try to find the existing record and update it
                    if (createErr?.response?.status === 400) {
                        const all = await listProducts()
                        const existing = all.find(
                            p => p.product_name === payload.product_name &&
                                p.version_number === payload.version_number
                        )
                        if (existing) {
                            await updateProduct(existing.id, apiPayload)
                        } else {
                            throw createErr
                        }
                    } else {
                        throw createErr
                    }
                }
            }

            setSaved(true)
            window.scrollTo({ top: 0, behavior: 'smooth' })
        } catch (err) {
            alert('Error al guardar el producto: ' + (err.response?.data?.detail || err.message))
        } finally {
            setLoading(false)
        }
    }

    const canNext = () => {
        if (step === 1) return productName && category && description
        if (step === 2) return materials.length > 0
        return true
    }

    return (
        <div className="wizard-container">
            <div className="page-header">
                <h2>{initialProduct ? `Editar: ${resolvedName}` : 'Nuevo Producto'}</h2>
                <p>{initialProduct ? 'Modifica los datos del producto y guarda los cambios.' : 'Completa el Wizard para generar tu Expediente Técnico GPSR'}</p>
            </div>

            <StepIndicator current={step} />

            {/* STEP 1: Product Info */}
            {step === 1 && (
                <div className="card">
                    <div className="card-title">📦 Información del Producto</div>
                    <div className="form-group">
                        <label className="form-label">Nombre del Producto <span>*</span></label>
                        <input className="form-input" value={productName} onChange={e => setProductName(e.target.value)} placeholder="ej. Bufanda de Lana Merino Azul" />
                    </div>
                    <div className="form-row">
                        <div className="form-group" style={{ flex: 2 }}>
                            <label className="form-label">Categoría GPSR <span>*</span></label>
                            <select className="form-select" value={category} onChange={e => setCategory(e.target.value)}>
                                <option value="">Selecciona la categoría...</option>
                                {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                            </select>
                        </div>
                        <div className="form-group" style={{ flex: 1 }}>
                            <label className="form-label">Versión <span>*</span></label>
                            <input className="form-input" value={versionNumber} onChange={e => setVersionNumber(e.target.value)} placeholder="v1.0" />
                        </div>
                    </div>
                    <div className="form-hint" style={{ marginTop: -12, marginBottom: 20 }}>
                        La categoría determina los checks obligatorios. Incrementa la versión si estás haciendo cambios en un producto ya existente.
                    </div>
                    <div className="form-group">
                        <label className="form-label">Descripción del Producto <span>*</span></label>
                        <textarea className="form-textarea" value={description} onChange={e => setDescription(e.target.value)} placeholder="Describe el producto, sus características físicas, tamaño, colores disponibles..." />
                    </div>
                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Uso Previsto</label>
                            <textarea className="form-textarea" style={{ minHeight: 80 }} value={intendedUse} onChange={e => setIntendedUse(e.target.value)} placeholder="¿Para qué se usa el producto?" />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Mal Uso Previsible</label>
                            <textarea className="form-textarea" style={{ minHeight: 80 }} value={foreseeableMisuse} onChange={e => setForeseeableMisuse(e.target.value)} placeholder="¿Qué uso incorrecto podría hacer un usuario?" />
                        </div>
                    </div>
                    {category === 'toy' && (
                        <div className="check-item" style={{ background: 'var(--amber-dim)', borderColor: 'var(--amber)', marginTop: 8 }}>
                            <AlertTriangle size={16} style={{ color: 'var(--amber)', flexShrink: 0, marginTop: 2 }} />
                            <div style={{ fontSize: 13 }}>⚠️ <strong>Juguetes:</strong> Requieren Marcado CE y cumplir la Directiva 2009/48/CE adicional al GPSR.</div>
                        </div>
                    )}
                    {category === 'cosmetic' && (
                        <div className="check-item" style={{ background: 'var(--purple-dim)', borderColor: 'var(--purple)', marginTop: 8 }}>
                            <AlertTriangle size={16} style={{ color: 'var(--purple)', flexShrink: 0, marginTop: 2 }} />
                            <div style={{ fontSize: 13 }}>⚠️ <strong>Cosméticos:</strong> Requieren notificación adicional en el portal <strong>CPNP</strong> y Safety Assessment.</div>
                        </div>
                    )}
                </div>
            )}

            {/* STEP 2: Materials */}
            {step === 2 && (
                <div className="card">
                    <div className="card-title">🧪 Materiales y BOM</div>
                    <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 20 }}>
                        Añade todos los materiales que componen tu producto. El sistema detectará riesgos automáticamente en el siguiente paso.
                    </p>
                    <div className="form-group">
                        <label className="form-label">Materiales <span>*</span></label>
                        <TagInput tags={materials} onChange={setMaterials} placeholder="ej. lana, botones, tinte — pulsa Enter" />
                        <div className="form-hint">Escribe cada material y pulsa Enter. Sé específico: "lana merino" es mejor que "lana".</div>
                    </div>
                    {materials.length > 0 && (
                        <div style={{ marginTop: 16 }}>
                            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>Vista previa BOM ({materials.length} materiales)</div>
                            <div className="table-wrap">
                                <table>
                                    <thead><tr><th>#</th><th>Material</th><th>Proveedor</th><th>Certificado</th></tr></thead>
                                    <tbody>
                                        {materials.map((m, i) => (
                                            <tr key={i}>
                                                <td style={{ color: 'var(--text-dim)' }}>{i + 1}</td>
                                                <td style={{ fontWeight: 500 }}>{m}</td>
                                                <td><input className="form-input" style={{ padding: '6px 10px', fontSize: 13 }} placeholder="Nombre proveedor" /></td>
                                                <td><button className="btn btn-sm btn-secondary">+ Adjuntar</button></td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* STEP 3: Risk Analysis */}
            {step === 3 && (
                <div className="card">
                    <div className="card-title">⚠️ Análisis de Riesgos</div>
                    {loading ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, color: 'var(--text-muted)', padding: '24px 0' }}>
                            <Loader2 size={20} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
                            Analizando materiales con el motor de riesgos GPSR...
                        </div>
                    ) : (
                        <>
                            {/* Error banner */}
                            {riskError && (
                                <div style={{
                                    background: 'var(--amber-dim, #fff8e6)', border: '1.5px solid var(--amber)',
                                    borderRadius: 'var(--radius-sm)', padding: '12px 16px',
                                    marginBottom: 20, display: 'flex', gap: 10, alignItems: 'flex-start'
                                }}>
                                    <AlertTriangle size={16} style={{ color: 'var(--amber)', flexShrink: 0, marginTop: 2 }} />
                                    <div style={{ flex: 1, fontSize: 13, color: 'var(--text)' }}>
                                        {riskError}
                                        <button
                                            className="btn btn-secondary btn-sm"
                                            style={{ marginTop: 8, display: 'block' }}
                                            onClick={fetchRiskAnalysis}
                                        >
                                            🔄 Reintentar
                                        </button>
                                    </div>
                                </div>
                            )}

                            {mandatoryChecks.length > 0 && (
                                <div style={{ marginBottom: 24 }}>
                                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--amber)', marginBottom: 10 }}>⚡ Checks obligatorios para tu categoría:</div>
                                    <div className="checks-list">
                                        {mandatoryChecks.map((c, i) => (
                                            <div key={i} className="check-item">
                                                <AlertTriangle size={14} style={{ color: 'var(--amber)', flexShrink: 0, marginTop: 2 }} />
                                                <span style={{ fontSize: 13 }}>{c}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>
                                Riesgos detectados ({risks.length}) — Ajusta la probabilidad y gravedad:
                            </div>
                            <div className="risk-list">
                                {risks.map((r, i) => (
                                    <div key={i} className={`risk-item ${riskClass(r.risk_level)}`}>
                                        <div className="risk-item-header">
                                            <span className="risk-item-title" style={{ textTransform: 'capitalize' }}>{r.hazard_type.replace('_', ' ')}</span>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                <span className="badge" style={{ background: riskColor(r.risk_level) + '22', color: riskColor(r.risk_level) }}>
                                                    {r.risk_level?.toUpperCase()} — Score: {r.risk_score}
                                                </span>
                                                <button
                                                    title="Eliminar riesgo"
                                                    onClick={() => deleteRisk(i)}
                                                    style={{
                                                        background: 'none', border: 'none', cursor: 'pointer',
                                                        color: 'var(--text-dim)', padding: '2px 4px', borderRadius: 4,
                                                        display: 'flex', alignItems: 'center',
                                                        transition: 'color 0.15s'
                                                    }}
                                                    onMouseEnter={e => e.currentTarget.style.color = 'var(--red)'}
                                                    onMouseLeave={e => e.currentTarget.style.color = 'var(--text-dim)'}
                                                >
                                                    <X size={14} />
                                                </button>
                                            </div>
                                        </div>
                                        <div className="risk-item-desc">{r.hazard_description}</div>
                                        <div className="risk-sliders">
                                            <div className="slider-group">
                                                <label><span>Probabilidad</span><strong style={{ color: 'var(--text)' }}>{r.probability}/5</strong></label>
                                                <input type="range" min={1} max={5} value={r.probability} onChange={e => updateRisk(i, 'probability', e.target.value)} />
                                            </div>
                                            <div className="slider-group">
                                                <label><span>Gravedad</span><strong style={{ color: 'var(--text)' }}>{r.severity}/5</strong></label>
                                                <input type="range" min={1} max={5} value={r.severity} onChange={e => updateRisk(i, 'severity', e.target.value)} />
                                            </div>
                                        </div>
                                        <div style={{ marginTop: 10 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
                                                <label className="form-label" style={{ margin: 0 }}>Medida de Mitigación</label>
                                                {mitigations[i] && (
                                                    <span style={{
                                                        fontSize: 10, padding: '2px 7px',
                                                        background: 'var(--blue-dim)', color: 'var(--blue)',
                                                        borderRadius: 20, fontWeight: 600, letterSpacing: '0.3px'
                                                    }}>✦ Sugerencia IA — editable</span>
                                                )}
                                            </div>
                                            <textarea
                                                className="form-textarea"
                                                style={{ fontSize: 13, minHeight: 72 }}
                                                value={mitigations[i] || ''}
                                                onChange={e => setMitigations(m => ({ ...m, [i]: e.target.value }))}
                                                placeholder="Describe cómo eliminas o reduces este riesgo..."
                                            />
                                        </div>
                                    </div>
                                ))}

                                {/* Add risk form */}
                                {showAddRisk ? (
                                    <div style={{
                                        border: '1.5px dashed var(--border)', borderRadius: 'var(--radius-sm)',
                                        padding: 16, display: 'flex', flexDirection: 'column', gap: 10
                                    }}>
                                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>➕ Nuevo riesgo manual</div>
                                        <div className="form-row">
                                            <div className="form-group" style={{ flex: 1 }}>
                                                <label className="form-label">Tipo de peligro</label>
                                                <select className="form-select"
                                                    value={newRisk.hazard_type}
                                                    onChange={e => setNewRisk(r => ({ ...r, hazard_type: e.target.value }))}
                                                >
                                                    <option value="chemical">Chemical (Químico)</option>
                                                    <option value="thermal">Thermal (Térmico)</option>
                                                    <option value="physical">Physical (Físico)</option>
                                                    <option value="mechanical">Mechanical (Mecánico)</option>
                                                    <option value="other">Otro</option>
                                                </select>
                                            </div>
                                            <div className="form-group" style={{ flex: 1 }}>
                                                <label className="form-label">Probabilidad: {newRisk.probability}/5</label>
                                                <input type="range" min={1} max={5} value={newRisk.probability}
                                                    onChange={e => setNewRisk(r => ({ ...r, probability: Number(e.target.value) }))} />
                                            </div>
                                            <div className="form-group" style={{ flex: 1 }}>
                                                <label className="form-label">Gravedad: {newRisk.severity}/5</label>
                                                <input type="range" min={1} max={5} value={newRisk.severity}
                                                    onChange={e => setNewRisk(r => ({ ...r, severity: Number(e.target.value) }))} />
                                            </div>
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Descripción del peligro *</label>
                                            <textarea className="form-textarea" style={{ minHeight: 60, fontSize: 13 }}
                                                value={newRisk.hazard_description}
                                                onChange={e => setNewRisk(r => ({ ...r, hazard_description: e.target.value }))}
                                                placeholder="Describe el peligro detectado..."
                                            />
                                        </div>
                                        <div style={{ display: 'flex', gap: 8 }}>
                                            <button className="btn btn-primary btn-sm" onClick={addRiskManually}
                                                disabled={!newRisk.hazard_description.trim()}>
                                                <Plus size={13} /> Añadir
                                            </button>
                                            <button className="btn btn-secondary btn-sm" onClick={() => setShowAddRisk(false)}>
                                                Cancelar
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <button className="btn btn-secondary" style={{ alignSelf: 'flex-start' }}
                                        onClick={() => setShowAddRisk(true)}>
                                        <Plus size={14} /> Añadir riesgo manualmente
                                    </button>
                                )}
                            </div>
                        </>
                    )}
                </div>
            )}

            {/* STEP 4: Labelling */}
            {step === 4 && (
                <div className="card">
                    <div className="card-title">🏷️ Etiquetado y Trazabilidad</div>
                    <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 20 }}>
                        Según el Art. 19 GPSR, el etiquetado obligatorio debe incluir tu identificación, un número de lote y las advertencias de seguridad.
                    </p>
                    <div className="form-group">
                        <label className="form-label">Código de Lote (autogenerado)</label>
                        <input className="form-input" value={batchCode} onChange={e => setBatchCode(e.target.value)} />
                        <div className="form-hint">Puedes modificarlo. Se incluirá en la etiqueta y en el Expediente Técnico.</div>
                    </div>
                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Nombre / Marca <span>*</span></label>
                            <input className="form-input" value={manufacturerName} onChange={e => setManufacturerName(e.target.value)} placeholder="Tu nombre o nombre comercial" />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Email Obligatorio (GPSR) <span>*</span></label>
                            <input className="form-input" type="email" value={manufacturerEmail} onChange={e => setManufacturerEmail(e.target.value)} placeholder="contacto@tuemail.com" />
                        </div>
                    </div>
                    <div className="form-group">
                        <label className="form-label">Dirección Postal <span>*</span></label>
                        <input className="form-input" value={manufacturerAddress} onChange={e => setManufacturerAddress(e.target.value)} placeholder="Calle, Nº, CP, Ciudad, País UE" />
                    </div>

                    {manufacturerName && !initialProduct && (
                        <div className="check-item" style={{ background: 'var(--blue-dim)', borderColor: 'var(--blue)', marginBottom: 16 }}>
                            <CheckCircle size={15} style={{ color: 'var(--blue)', flexShrink: 0 }} />
                            <div style={{ fontSize: 13 }}>
                                Datos obtenidos automáticamente de <strong>Ajustes → Persona Responsable</strong>.
                                Puedes modificarlos aquí o{' '}
                                <a href="/settings" style={{ color: 'var(--blue)' }}>cambiar los predeterminados</a>.
                            </div>
                        </div>
                    )}
                    {!manufacturerName && !initialProduct && (
                        <div className="check-item" style={{ background: 'var(--amber-dim, #fff8e6)', borderColor: 'var(--amber)', marginBottom: 16 }}>
                            <AlertTriangle size={15} style={{ color: 'var(--amber)', flexShrink: 0 }} />
                            <div style={{ fontSize: 13 }}>
                                Sin datos de Persona Responsable. Rellena los campos manualmente o{' '}
                                <a href="/settings" style={{ color: 'var(--amber)' }}>configúralos en Ajustes</a> para que aparezcan aquí automáticamente.
                            </div>
                        </div>
                    )}

                    {/* Label size selector */}
                    <div className="form-group">
                        <label className="form-label"><Printer size={13} style={{ marginRight: 5, verticalAlign: 'middle' }} />Tamaño de Etiqueta (según tu etiquetadora)</label>
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
                            gap: 8, marginTop: 8
                        }}>
                            {labelSizes.map(s => {
                                const maxDim = Math.max(s.width_mm, s.height_mm)
                                const previewW = Math.round((s.width_mm / maxDim) * 80)
                                const previewH = Math.round((s.height_mm / maxDim) * 55)
                                const isSelected = labelSizeKey === s.key
                                return (
                                    <button
                                        key={s.key}
                                        type="button"
                                        onClick={() => setLabelSizeKey(s.key)}
                                        style={{
                                            display: 'flex', flexDirection: 'column', alignItems: 'center',
                                            gap: 8, padding: '10px 6px',
                                            background: isSelected ? 'var(--blue-dim)' : 'var(--bg)',
                                            border: `1.5px solid ${isSelected ? 'var(--blue)' : 'var(--border)'}`,
                                            borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                                            transition: 'all 0.15s'
                                        }}
                                    >
                                        {/* Mini visual representation of the label */}
                                        <div style={{
                                            width: previewW, height: previewH, minWidth: 20, minHeight: 14,
                                            background: isSelected ? 'var(--blue)' : 'var(--border)',
                                            borderRadius: 2, opacity: 0.7
                                        }} />
                                        <span style={{
                                            fontSize: 11, textAlign: 'center', lineHeight: 1.3,
                                            color: isSelected ? 'var(--blue)' : 'var(--text-muted)',
                                            fontWeight: isSelected ? 600 : 400
                                        }}>
                                            {s.width_mm}×{s.height_mm} mm
                                        </span>
                                        <span style={{
                                            fontSize: 10, color: isSelected ? 'var(--blue)' : 'var(--text-dim)',
                                            textAlign: 'center', lineHeight: 1.2
                                        }}>
                                            {s.label.split(' — ')[0]}
                                        </span>
                                    </button>
                                )
                            })}
                        </div>
                        {labelSizes.find(s => s.key === labelSizeKey) && (
                            <div className="form-hint" style={{ marginTop: 8 }}>
                                Seleccionado: <strong>{labelSizes.find(s => s.key === labelSizeKey)?.label}</strong>
                            </div>
                        )}
                    </div>

                    <hr className="divider" />

                    {/* Warnings — checkbox list from engine suggestions */}
                    <div className="form-group">
                        <label className="form-label">Advertencias de Seguridad</label>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
                            Generadas a partir de tu análisis de riesgos. Confirma las que aplican a tu producto. Puedes añadir advertencias personalizadas.
                        </p>
                        {suggestedWarnings.length === 0 && (
                            <div style={{ fontSize: 13, color: 'var(--text-dim)', fontStyle: 'italic', padding: '8px 0' }}>
                                Vuelve al Paso 3 y analiza los materiales para generar advertencias automáticas.
                            </div>
                        )}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {suggestedWarnings.map((w, i) => (
                                <label key={i} style={{
                                    display: 'flex', gap: 10, alignItems: 'flex-start',
                                    padding: '10px 12px',
                                    background: w.accepted ? 'var(--green-dim)' : 'var(--bg)',
                                    border: `1.5px solid ${w.accepted ? 'var(--green)' : 'var(--border)'}`,
                                    borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                                    transition: 'all 0.15s'
                                }}>
                                    <input
                                        type="checkbox"
                                        checked={w.accepted}
                                        style={{ marginTop: 2, accentColor: 'var(--green)', flexShrink: 0 }}
                                        onChange={e => {
                                            const updated = [...suggestedWarnings]
                                            updated[i] = { ...updated[i], accepted: e.target.checked }
                                            setSuggestedWarnings(updated)
                                        }}
                                    />
                                    <div style={{ flex: 1 }}>
                                        <span style={{ fontSize: 13, lineHeight: 1.4 }}>{w.text}</span>
                                        <span style={{
                                            display: 'inline-block', marginLeft: 8, fontSize: 10,
                                            color: 'var(--text-dim)', fontStyle: 'italic'
                                        }}>— {w.source}</span>
                                    </div>
                                </label>
                            ))}
                        </div>

                        {/* Add custom warning */}
                        <div style={{ marginTop: 10 }}>
                            <TagInput
                                tags={[]}
                                onChange={newTags => {
                                    const extra = newTags.map(t => ({ text: t, source: 'personalizada', accepted: true }))
                                    setSuggestedWarnings(prev => [...prev, ...extra])
                                }}
                                placeholder="Añadir advertencia personalizada — pulsa Enter"
                            />
                        </div>
                    </div>
                    <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
                        <div className="check-item" style={{ flex: 1 }}>
                            <CheckCircle size={14} style={{ color: 'var(--green)', flexShrink: 0, marginTop: 2 }} />
                            <span style={{ fontSize: 13 }}>Solo se incluirán en la etiqueta las advertencias <strong>marcadas con ✓</strong>.</span>
                        </div>
                    </div>
                </div>
            )}

            {/* STEP 5: Review */}
            {step === 5 && (
                <div className="card">
                    <div className="card-title"><CheckCircle size={18} style={{ color: 'var(--green)' }} /> Resumen y Generación</div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
                        <div style={{ background: 'var(--bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', padding: 16 }}>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Producto</div>
                            <div style={{ fontWeight: 600 }}>{productName || '—'}</div>
                            <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{CATEGORIES.find(c => c.value === category)?.label}</div>
                        </div>
                        <div style={{ background: 'var(--bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', padding: 16 }}>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Materiales</div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                                {materials.map(m => <span key={m} className="badge badge-blue">{m}</span>)}
                            </div>
                        </div>
                        <div style={{ background: 'var(--bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', padding: 16 }}>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Riesgos detectados</div>
                            <div style={{ display: 'flex', gap: 8 }}>
                                {['high', 'medium', 'low'].map(l => {
                                    const count = risks.filter(r => r.risk_level === l).length
                                    return count > 0 ? <span key={l} className={`badge badge-${l === 'high' ? 'red' : l === 'medium' ? 'amber' : 'green'}`}>{count} {l}</span> : null
                                })}
                            </div>
                        </div>
                        <div style={{ background: 'var(--bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', padding: 16 }}>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Lote</div>
                            <div style={{ fontWeight: 600, fontFamily: 'monospace' }}>{batchCode}</div>
                        </div>
                    </div>

                    <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Generar documentación:</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>

                        {/* Expediente Técnico */}
                        <button
                            className="btn btn-primary btn-lg"
                            onClick={handleDownloadPdf}
                            disabled={!!generating}
                        >
                            {generating === 'pdf'
                                ? <><Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> Generando PDF...</>
                                : generated.includes('pdf')
                                    ? <><Download size={18} /> Expediente Técnico Generado ✓</>
                                    : <><FileText size={18} /> Generar Expediente Técnico PDF</>}
                        </button>

                        <div style={{ display: 'flex', gap: 10 }}>
                            {/* Etiqueta física */}
                            <button
                                className={`btn btn-secondary${generated.includes('label') ? ' btn-success' : ''}`}
                                style={{ flex: 1 }}
                                onClick={handleDownloadLabel}
                                disabled={!!generating}
                            >
                                {generating === 'label'
                                    ? <><Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> Generando...</>
                                    : generated.includes('label')
                                        ? <><Tag size={14} /> Etiqueta Generada ✓</>
                                        : <><Tag size={14} /> Generar Etiqueta para Imprimir</>}
                            </button>
                            {/* Amazon pack - próximamente */}
                            <button className="btn btn-secondary" style={{ flex: 1 }} disabled>
                                📦 Pack Amazon (próximamente)
                            </button>
                        </div>
                    </div>

                    {/* Success banner after saving */}
                    {saved && (
                        <div style={{
                            background: 'var(--green-dim)', border: '1.5px solid var(--green)',
                            borderRadius: 'var(--radius-sm)', padding: '16px 20px',
                            marginBottom: 20, display: 'flex', gap: 12, alignItems: 'flex-start'
                        }}>
                            <CheckCircle size={20} style={{ color: 'var(--green)', flexShrink: 0, marginTop: 1 }} />
                            <div>
                                <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--green)', marginBottom: 4 }}>
                                    ✅ Producto guardado correctamente
                                </div>
                                <div style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.5 }}>
                                    <strong>{productName}</strong> — Lote <code>{batchCode}</code><br />
                                    {risks.length} riesgos analizados · {suggestedWarnings.filter(w => w.accepted).length} advertencias confirmadas
                                </div>
                                <div style={{ marginTop: 10, display: 'flex', gap: 8 }}>
                                    <button className="btn btn-primary btn-sm" onClick={handleDownloadPdf} disabled={!!generating}>
                                        {generating === 'pdf' ? <Loader2 size={13} className="spin" /> : <FileText size={13} />}
                                        Descargar Expediente Técnico
                                    </button>
                                    <button className="btn btn-secondary btn-sm" onClick={handleDownloadLabel} disabled={!!generating}>
                                        {generating === 'label' ? <Loader2 size={13} className="spin" /> : <Tag size={13} />}
                                        Descargar Etiqueta
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    <div style={{ marginBottom: 24 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                            <h4 style={{ fontSize: 14, fontWeight: 600 }}>Estado de Conformidad (GPSR)</h4>
                            <StatusBadge risks={risks} />
                        </div>
                        <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                            El estado se calcula en base al Análisis de Riesgos (Paso 3).
                        </p>
                    </div>

                    <div className="check-item" style={{ marginTop: 20, background: 'var(--green-dim)', borderColor: 'var(--green)' }}>
                        <CheckCircle size={14} style={{ color: 'var(--green)', flexShrink: 0, marginTop: 2 }} />
                        <span style={{ fontSize: 13 }}>Los documentos generados quedarán custodiados por <strong>10 años</strong> según Art. 9 GPSR.</span>
                    </div>
                </div>
            )}

            {/* Navigation */}
            <div className="wizard-nav">
                <button className="btn btn-secondary" onClick={prev} disabled={step === 1}>
                    <ChevronLeft size={16} /> Atrás
                </button>
                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Paso {step} de {STEPS.length}</span>
                {step < 5
                    ? <button className="btn btn-primary" onClick={next} disabled={!canNext() || loading}>
                        {loading ? <><Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> Analizando...</> : <>Siguiente <ChevronRight size={16} /></>}
                    </button>
                    : <button
                        className="btn btn-primary"
                        style={{ background: saved ? 'var(--green)' : undefined }}
                        onClick={handleFinalize}
                        disabled={saved}
                    >
                        <CheckCircle size={16} /> {saved ? 'Guardado ✓' : 'Finalizar y Guardar'}
                    </button>
                }
            </div>

            <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
        </div >
    )
}
