"""
FastAPI Application Entry Point — GPSR Compliance SaaS
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.endpoints import products, risk, documents, responsible_person
from app.db.database import engine, Base
from app.models import models  # noqa: F401 — ensure all models are registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all DB tables on startup (no-op if they already exist)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="SaaS para el cumplimiento del Reglamento (UE) 2023/988 (GPSR), orientado a artesanos y PYMES que venden en Amazon.",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(responsible_person.router, prefix="/api/v1/responsible-persons", tags=["Responsible Person"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(risk.router, prefix="/api/v1/risk", tags=["Risk Engine"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Document Generator"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

