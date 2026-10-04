from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as investigation_router
from app.core.config import setting

from app.models.base import Base
from app.models.investigation import Investigation
from app.core.database import engine


app = FastAPI(
    title=setting.app_name,
    version="0.2.0",
    description=(
        "FinInvestigator - "
        "Evidence-grounded financial investigation system."
    ),
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(
    investigation_router
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "message": "FinInvestigator is Running",
        "version": "0.2.0",
    }


@app.get("/health")
async def health():

    return {
        "status": "ok",
        "service": "fininvestigator",
    }