from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ai import router as ai_router
from app.api.routes.analyses import router as analyses_router
from app.api.routes.auth import router as auth_router
from app.api.routes.generated_outputs import router as generated_outputs_router
from app.api.routes.health import router as health_router
from app.api.routes.interview import router as interview_router
from app.api.routes.job_descriptions import router as job_descriptions_router
from app.api.routes.job_matches import router as job_matches_router
from app.api.routes.privacy import router as privacy_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.rag import router as rag_router
from app.api.routes.reports import router as reports_router
from app.api.routes.sources import router as sources_router
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    app = FastAPI(
        title=active_settings.app_name,
        version=active_settings.app_version,
        docs_url="/docs" if active_settings.enable_docs else None,
        redoc_url="/redoc" if active_settings.enable_docs else None,
    )
    app.state.settings = active_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(profiles_router, prefix="/api/v1")
    app.include_router(sources_router, prefix="/api/v1")
    app.include_router(analyses_router, prefix="/api/v1")
    app.include_router(job_descriptions_router, prefix="/api/v1")
    app.include_router(job_matches_router, prefix="/api/v1")
    app.include_router(reports_router, prefix="/api/v1")
    app.include_router(ai_router, prefix="/api/v1")
    app.include_router(generated_outputs_router, prefix="/api/v1")
    app.include_router(rag_router, prefix="/api/v1")
    app.include_router(interview_router, prefix="/api/v1")
    app.include_router(privacy_router, prefix="/api/v1")
    return app


app = create_app()
