from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.ai.provider_status import AIProviderStatus, get_ai_provider_status

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/health/ai-provider", response_model=AIProviderStatus)
def ai_provider_health(request: Request) -> AIProviderStatus:
    return get_ai_provider_status(request.app.state.settings)
