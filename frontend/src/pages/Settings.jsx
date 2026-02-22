import { useState, useEffect } from 'react'
import { Settings as SettingsIcon, User, Mail, MapPin, Phone, Building2, CheckCircle, Save, Loader2 } from 'lucide-react'
import { listResponsiblePersons, createResponsiblePerson, updateResponsiblePerson } from '../api/gpsr'

// Legacy localStorage key — kept for migration if any exist
const LS_KEY = 'gpsr_responsible_person'

const defaultRP = {
    name: '',
    trade_name: '',
    email: '',
    phone: '',
    address: '',
    country: 'España',
    logo_data: '',
    is_self: true,
}

const COUNTRIES = [
    'Alemania', 'Austria', 'Bélgica', 'Bulgaria', 'Chipre', 'Croacia',
    'Dinamarca', 'Eslovaquia', 'Eslovenia', 'España', 'Estonia', 'Finlandia',
    'Francia', 'Grecia', 'Hungría', 'Irlanda', 'Italia', 'Letonia',
    'Lituania', 'Luxemburgo', 'Malta', 'Países Bajos', 'Polonia', 'Portugal',
    'República Checa', 'Rumanía', 'Suecia',
]

export default function Settings() {
    const [rp, setRp] = useState(defaultRP)
    const [rpId, setRpId] = useState(null)   // existing DB id if any
    const [saved, setSaved] = useState(false)
    const [saving, setSaving] = useState(false)
    const [hasExisting, setHasExisting] = useState(false)

    useEffect(() => {
        listResponsiblePersons()
            .then(list => {
                if (list.length > 0) {
                    const existing = list[0]
                    setRp({
                        name: existing.name, trade_name: existing.trade_name || '',
                        email: existing.email, phone: existing.phone || '',
                        address: existing.address, country: existing.country,
                        logo_data: existing.logo_data || '',
                        is_self: existing.is_self
                    })
                    setRpId(existing.id)
                    setHasExisting(true)
                }
            })
            .catch(() => {
                // Fallback to localStorage if API unavailable
                const stored = localStorage.getItem(LS_KEY)
                if (stored) { try { setRp(JSON.parse(stored)); setHasExisting(true) } catch { } }
            })
    }, [])

    const set = (field, value) => {
        setSaved(false)
        setRp(prev => ({ ...prev, [field]: value }))
    }

    const handleLogoUpload = (e) => {
        const file = e.target.files[0]
        if (!file) return
        if (file.size > 1024 * 1024) {
            alert('El logo es demasiado pesado. Máximo 1MB.')
            return
        }
        const reader = new FileReader()
        reader.onload = (event) => {
            set('logo_data', event.target.result)
        }
        reader.readAsDataURL(file)
    }

    const handleSave = async () => {
        setSaving(true)
        try {
            let result
            if (rpId) {
                result = await updateResponsiblePerson(rpId, rp)
            } else {
                result = await createResponsiblePerson(rp)
                setRpId(result.id)
            }
            // Also keep localStorage as fallback
            localStorage.setItem(LS_KEY, JSON.stringify(rp))
            setSaved(true)
            setHasExisting(true)
        } catch (err) {
            alert('Error al guardar: ' + (err.response?.data?.detail || err.message))
        } finally {
            setSaving(false)
        }
    }

    const isValid = rp.name && rp.email && rp.address && rp.country

    return (
        <>
            <div className="page-header">
                <h2>Configuración del Sistema</h2>
                <p>Define la Persona Responsable y ajusta los valores predeterminados de tus documentos.</p>
            </div>

            {/* Banner informativo GPSR */}
            <div className="check-item" style={{
                background: 'var(--blue-dim)', borderColor: 'var(--blue)',
                marginBottom: 24, alignItems: 'flex-start'
            }}>
                <SettingsIcon size={16} style={{ color: 'var(--blue)', flexShrink: 0, marginTop: 2 }} />
                <div style={{ fontSize: 13 }}>
                    <strong>Art. 4 GPSR — Persona Responsable (PR):</strong> Si fabricas y vendes dentro de la UE, TÚ eres la Persona Responsable.
                    Estos datos aparecerán en el Expediente Técnico y en la etiqueta física de todos tus productos.
                    Si vendes desde fuera de la UE, debes designar un representante legal europeo.
                </div>
            </div>

            <div className="card">
                <div className="card-title">
                    <User size={18} style={{ color: 'var(--blue)' }} />
                    Persona Responsable
                    {hasExisting && <span className="badge badge-green" style={{ marginLeft: 8 }}>✓ Configurado</span>}
                </div>

                {/* ¿Eres tú la PR? */}
                <div className="form-group">
                    <label className="form-label">¿Quién es la Persona Responsable?</label>
                    <div style={{ display: 'flex', gap: 10, marginTop: 6 }}>
                        <button
                            type="button"
                            onClick={() => set('is_self', true)}
                            style={{
                                flex: 1, padding: '12px 16px', borderRadius: 'var(--radius-sm)',
                                border: `1.5px solid ${rp.is_self ? 'var(--blue)' : 'var(--border)'}`,
                                background: rp.is_self ? 'var(--blue-dim)' : 'var(--bg)',
                                color: rp.is_self ? 'var(--blue)' : 'var(--text-muted)',
                                cursor: 'pointer', fontWeight: rp.is_self ? 600 : 400,
                                textAlign: 'left', transition: 'all 0.15s'
                            }}
                        >
                            <div style={{ fontWeight: 600, marginBottom: 3 }}>Yo mismo/a</div>
                            <div style={{ fontSize: 12 }}>Soy artesano/a UE — soy el fabricante y la PR al mismo tiempo.</div>
                        </button>
                        <button
                            type="button"
                            onClick={() => set('is_self', false)}
                            style={{
                                flex: 1, padding: '12px 16px', borderRadius: 'var(--radius-sm)',
                                border: `1.5px solid ${!rp.is_self ? 'var(--blue)' : 'var(--border)'}`,
                                background: !rp.is_self ? 'var(--blue-dim)' : 'var(--bg)',
                                color: !rp.is_self ? 'var(--blue)' : 'var(--text-muted)',
                                cursor: 'pointer', fontWeight: !rp.is_self ? 600 : 400,
                                textAlign: 'left', transition: 'all 0.15s'
                            }}
                        >
                            <div style={{ fontWeight: 600, marginBottom: 3 }}>Representante designado</div>
                            <div style={{ fontSize: 12 }}>Vendo desde fuera de la UE — tengo un representante legal europeo.</div>
                        </button>
                    </div>
                </div>

                {/* Logo Upload Section */}
                <div className="form-group" style={{ marginBottom: 24 }}>
                    <label className="form-label">Logo de tu Marca (Recomendado)</label>
                    <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginTop: 8 }}>
                        <div style={{
                            width: 100, height: 100, borderRadius: 'var(--radius-sm)',
                            border: '2px dashed var(--border)',
                            background: 'var(--bg)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            overflow: 'hidden', position: 'relative'
                        }}>
                            {rp.logo_data ? (
                                <img src={rp.logo_data} alt="Logo" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                            ) : (
                                <div style={{ textAlign: 'center', color: 'var(--text-dim)', fontSize: 11 }}>Sin logo</div>
                            )}
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <label className="btn btn-secondary" style={{ cursor: 'pointer', display: 'inline-flex', gap: 8, fontSize: 13 }}>
                                📷 Seleccionar Logo
                                <input type="file" accept="image/*" onChange={handleLogoUpload} style={{ display: 'none' }} />
                            </label>
                            {rp.logo_data && (
                                <button className="btn btn-sm btn-secondary"
                                    onClick={() => set('logo_data', '')}
                                    style={{ color: 'var(--red)', border: 'none', padding: 0, justifyContent: 'flex-start', background: 'none' }}>
                                    Quitar logo
                                </button>
                            )}
                            <div className="form-hint" style={{ marginTop: 0 }}>
                                Proporción cuadrada recomendada. Máximo 1MB.
                            </div>
                        </div>
                    </div>
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label className="form-label">
                            <User size={13} style={{ marginRight: 5, verticalAlign: 'middle' }} />
                            Nombre completo / Razón Social <span>*</span>
                        </label>
                        <input
                            className="form-input"
                            value={rp.name}
                            onChange={e => set('name', e.target.value)}
                            placeholder="María García López"
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">
                            <Building2 size={13} style={{ marginRight: 5, verticalAlign: 'middle' }} />
                            Nombre comercial / Marca
                        </label>
                        <input
                            className="form-input"
                            value={rp.trade_name}
                            onChange={e => set('trade_name', e.target.value)}
                            placeholder="Artesanía El Telar (opcional)"
                        />
                        <div className="form-hint">Si tienes nombre de marca, aparecerá en la etiqueta junto a tu nombre legal.</div>
                    </div>
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label className="form-label">
                            <Mail size={13} style={{ marginRight: 5, verticalAlign: 'middle' }} />
                            Email de contacto <span>*</span>
                        </label>
                        <input
                            className="form-input"
                            type="email"
                            value={rp.email}
                            onChange={e => set('email', e.target.value)}
                            placeholder="contacto@tuartesania.com"
                        />
                        <div className="form-hint">Obligatorio por Art. 19 GPSR. Debe aparecer en la etiqueta física.</div>
                    </div>
                    <div className="form-group">
                        <label className="form-label">
                            <Phone size={13} style={{ marginRight: 5, verticalAlign: 'middle' }} />
                            Teléfono (recomendado)
                        </label>
                        <input
                            className="form-input"
                            type="tel"
                            value={rp.phone}
                            onChange={e => set('phone', e.target.value)}
                            placeholder="+34 600 000 000"
                        />
                    </div>
                </div>

                <div className="form-group">
                    <label className="form-label">
                        <MapPin size={13} style={{ marginRight: 5, verticalAlign: 'middle' }} />
                        Dirección postal completa <span>*</span>
                    </label>
                    <input
                        className="form-input"
                        value={rp.address}
                        onChange={e => set('address', e.target.value)}
                        placeholder="Calle Mayor 42, 3ºB — 28001 Madrid"
                    />
                    <div className="form-hint">Dirección dentro de la UE. Aparecerá en el Expediente Técnico y en la etiqueta.</div>
                </div>

                <div className="form-group" style={{ maxWidth: 320 }}>
                    <label className="form-label">País (UE) <span>*</span></label>
                    <select className="form-select" value={rp.country} onChange={e => set('country', e.target.value)}>
                        {COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                </div>

                {/* Preview */}
                {rp.name && (
                    <div style={{
                        marginTop: 20,
                        background: 'var(--bg)',
                        border: '1px dashed var(--border)',
                        borderRadius: 'var(--radius-sm)',
                        padding: 16
                    }}>
                        <div style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span>Vista previa — así aparecerá en tus etiquetas y documentos</span>
                            {rp.logo_data && <img src={rp.logo_data} alt="Logo preview" style={{ height: 24, objectFit: 'contain' }} />}
                        </div>
                        <div style={{ fontWeight: 700, fontSize: 14 }}>{rp.name}</div>
                        {rp.trade_name && <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>({rp.trade_name})</div>}
                        <div style={{ fontSize: 13, marginTop: 4 }}>{rp.address}, {rp.country}</div>
                        <div style={{ fontSize: 13 }}>{rp.email}{rp.phone ? ` · ${rp.phone}` : ''}</div>
                    </div>
                )}

                <div style={{ marginTop: 24, display: 'flex', gap: 10, alignItems: 'center' }}>
                    <button
                        className="btn btn-primary"
                        onClick={handleSave}
                        disabled={!isValid || saving}
                    >
                        {saving ? <Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} /> : <Save size={15} />}
                        {saving ? 'Guardando...' : saved ? 'Guardado ✓' : 'Guardar configuración'}
                    </button>
                    {saved && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--green)', fontSize: 13, fontWeight: 600 }}>
                            <CheckCircle size={15} /> Datos guardados correctamente en este dispositivo.
                        </div>
                    )}
                    {!isValid && (
                        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                            Completa los campos obligatorios (*) para guardar.
                        </span>
                    )}
                </div>
            </div>

            {/* Próximamente */}
            <div className="card" style={{ marginTop: 20, opacity: 0.6 }}>
                <div className="card-title">
                    <SettingsIcon size={18} style={{ color: 'var(--text-muted)' }} />
                    Más ajustes (próximamente)
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <span>• Tamaño de etiqueta predeterminado para toda la cuenta</span>
                    <span>• Normas técnicas (EN/ISO) aplicadas por defecto según categoría</span>
                    <span>• Configuración de copia de seguridad en la nube</span>
                    <span>• Exportación masiva de expedientes ZIP</span>
                </div>
            </div>
        </>
    )
}
