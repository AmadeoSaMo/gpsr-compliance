# GPSR Compliance SaaS

SaaS para el cumplimiento del **Reglamento (UE) 2023/988 (GPSR)** orientado a artesanos y PYMES que venden en Amazon Handmade y marketplaces de la UE.

## Stack

| Capa | Tecnología |
|------|------------|
| Backend | Python 3.12 + FastAPI |
| Base de Datos | PostgreSQL + SQLAlchemy + Alembic |
| PDFs | WeasyPrint + ReportLab |
| Etiquetas | Pillow + qrcode |
| Frontend | React + Vite |

## Estructura del Proyecto

```
App Cumplimiento de Seguridad Amazon/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # HTTP layer (adapters)
│   │   ├── core/               # Config, security
│   │   ├── db/                 # Database session
│   │   ├── models/             # SQLAlchemy models (domain)
│   │   ├── schemas/            # Pydantic schemas (I/O validation)
│   │   ├── services/
│   │   │   ├── risk_engine/    # CORE DOMAIN: legal logic
│   │   │   ├── pdf_generator/  # PDF output (adapter)
│   │   │   └── label_generator/ # Label output (adapter)
│   │   └── main.py
│   ├── alembic/                # Database migrations
│   └── requirements.txt
├── frontend/                   # React Wizard UI
└── docs/
```

## Ejecutar en desarrollo

```bash
# 1. Instalar dependencias
cd backend
pip install -r requirements.txt

# 2. Copiar y configurar .env
cp .env.example .env

# 3. Ejecutar el servidor
uvicorn app.main:app --reload

# 4. Ver API docs
# http://localhost:8000/api/docs
```

## Módulos MVP

1. **Wizard Inteligente** — Cuestionario adaptativo por categoría de producto
2. **Motor de Riesgos** — Análisis automático por materiales + matriz 5×5
3. **Generador de Expediente Técnico** — PDF listo para archivo (10 años)
4. **Generador de Etiqueta** — PDF para impresión física
5. **Pack Amazon** — Imagen Art. 19 + texto para Seller Central
