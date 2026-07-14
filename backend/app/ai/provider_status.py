from pydantic import BaseModel

from app.core.config import Settings

EXTERNAL_PROVIDERS = {"openai", "openai_compatible"}
LOCAL_PROVIDER = "local_template"


class AIProviderStatus(BaseModel):
    provider: str
    model_name: str
    mode: str
    configured: bool
    requires_api_key: bool
    api_key_configured: bool
    base_url_configured: bool
    timeout_seconds: int
    issues: list[str]


def get_ai_provider_status(settings: Settings) -> AIProviderStatus:
    provider = (settings.ai_provider or LOCAL_PROVIDER).strip() or LOCAL_PROVIDER
    default_model = "local-template-v1" if provider == LOCAL_PROVIDER else ""
    model_name = (settings.ai_model or default_model).strip()
    requires_api_key = provider in EXTERNAL_PROVIDERS
    api_key_configured = bool(settings.ai_api_key)
    base_url_configured = bool(settings.ai_base_url)
    issues: list[str] = []

    if provider == LOCAL_PROVIDER:
        mode = "local_template"
    elif provider in EXTERNAL_PROVIDERS:
        mode = "external"
        if not api_key_configured:
            issues.append("AI_API_KEY is required for the configured external AI provider.")
        if not model_name:
            issues.append("AI_MODEL is required for the configured external AI provider.")
    else:
        mode = "unsupported"
        issues.append(f"Unsupported AI_PROVIDER: {provider}.")

    return AIProviderStatus(
        provider=provider,
        model_name=model_name,
        mode=mode,
        configured=not issues,
        requires_api_key=requires_api_key,
        api_key_configured=api_key_configured,
        base_url_configured=base_url_configured,
        timeout_seconds=settings.ai_timeout_seconds,
        issues=issues,
    )
