/**
 * API client for the GPSR backend.
 * All calls go through here — single point of truth for the base URL.
 */
import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'
export const api = axios.create({ baseURL: BASE })

// ---------------------------------------------------------------------------
// Risk Engine
// ---------------------------------------------------------------------------

/** POST /risk/analyze — returns risk suggestions + mandatory checks + suggested warnings */
export async function analyzeRisk(category, materials) {
    const { data } = await api.post('/risk/analyze', { category, materials })
    return data
}

// ---------------------------------------------------------------------------
// Document Generation — Print-first approach (no WeasyPrint dependency)
// ---------------------------------------------------------------------------

/**
 * Opens a print-ready document in a new browser tab.
 * The page shows a toolbar with "Imprimir / Guardar PDF" and auto-triggers the
 * browser print dialog. Works on all platforms without WeasyPrint.
 */
export async function openPrintPage(endpoint, payload) {
    const { data: html } = await api.post(endpoint, payload, { responseType: 'text' })
    const blob = new Blob([html], { type: 'text/html; charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const tab = window.open(url, '_blank')
    if (tab) {
        setTimeout(() => window.URL.revokeObjectURL(url), 15000)
    } else {
        window.URL.revokeObjectURL(url)
        throw new Error('El navegador bloqueó la ventana emergente. Permite las ventanas emergentes para este sitio en la barra de direcciones.')
    }
}

/**
 * Opens the Technical File in a new tab with print toolbar + auto-print dialog.
 * User can print directly or choose "Guardar como PDF" in the print dialog.
 */
export async function downloadTechnicalFilePdf(payload) {
    await openPrintPage('/documents/technical-file/print', payload)
}

/**
 * Opens the printable label in a new tab with print toolbar + auto-print dialog.
 * The @page CSS sets exact label dimensions, so "Save as PDF" produces the correct size.
 */
export async function downloadLabelPdf(payload) {
    await openPrintPage('/documents/label/print', payload)
}

/**
 * Opens the Amazon Art. 19 Image generator in a new browser tab.
 */
export async function downloadAmazonImage(productId) {
    const { data: html } = await api.get(`/products/${productId}/amazon-image`, { responseType: 'text' })
    const blob = new Blob([html], { type: 'text/html; charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const tab = window.open(url, '_blank')
    if (tab) {
        setTimeout(() => window.URL.revokeObjectURL(url), 15000)
    } else {
        window.URL.revokeObjectURL(url)
        throw new Error('El navegador bloqueó la ventana emergente.')
    }
}

// ---------------------------------------------------------------------------
// Preview endpoints (HTML, for debugging)
// ---------------------------------------------------------------------------

/** POST /documents/technical-file/preview — returns raw HTML string */
export async function previewTechnicalFile(payload) {
    const { data } = await api.post('/documents/technical-file/preview', payload, {
        responseType: 'text',
    })
    return data
}

/** POST /documents/label/preview — returns raw HTML string for label */
export async function previewLabel(payload) {
    const { data } = await api.post('/documents/label/preview', payload, {
        responseType: 'text',
    })
    return data
}

// ---------------------------------------------------------------------------
// Products CRUD
// ---------------------------------------------------------------------------

/** GET /products — list all products from DB */
export async function listProducts() {
    const { data } = await api.get('/products/')
    return data
}

/** POST /products — create new product in DB */
export async function createProduct(payload) {
    const { data } = await api.post('/products/', payload)
    return data
}

/** PUT /products/:id — update existing product in DB */
export async function updateProduct(id, payload) {
    const { data } = await api.put(`/products/${id}`, payload)
    return data
}

/** DELETE /products/:id — delete product from DB */
export async function deleteProduct(id) {
    await api.delete(`/products/${id}`)
}

// ---------------------------------------------------------------------------
// Responsible Person CRUD
// ---------------------------------------------------------------------------

/** GET /responsible-persons — list all RPs */
export async function listResponsiblePersons() {
    const { data } = await api.get('/responsible-persons/')
    return data
}

/** POST /responsible-persons — create new RP */
export async function createResponsiblePerson(payload) {
    const { data } = await api.post('/responsible-persons/', payload)
    return data
}

/** PUT /responsible-persons/:id — update existing RP */
export async function updateResponsiblePerson(id, payload) {
    const { data } = await api.put(`/responsible-persons/${id}`, payload)
    return data
}
