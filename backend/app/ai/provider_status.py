from urllib.parse import urlparse

from pydantic import BaseModel

from app.core.config import Settings

EXTERNAL_PROVIDERS = {"openai", "openai_compatible"}
LOCAL_PROVIDER = "local_template"
PLACEHOLDER_API_KEYS = {
    "changeme",
    "replace-me",
    "replace_me",
    "your-api-key",
    "your_api_key",
    "your-key-here",
}


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
    provider = (settings.ai_provider or LOCAL_PROVIDER).strip().lower() or LOCAL_PROVIDER
    default_model = "local-template-v1" if provider == LOCAL_PROVIDER else ""
    model_name = (settings.ai_model or default_model).strip()
    requires_api_key = provider in EXTERNAL_PROVIDERS
    api_key = (settings.ai_api_key or "").strip()
    api_key_configured = bool(api_key) and api_key.lower() not in PLACEHOLDER_API_KEYS
    base_url = (settings.ai_base_url or "").strip()
    base_url_configured = bool(base_url)
    issues: list[str] = []

    if provider == LOCAL_PROVIDER:
        mode = "local_template"
    elif provider in EXTERNAL_PROVIDERS:
        mode = "external"
        if not api_key_configured:
            issues.append("AI_API_KEY is required for the configured external AI provider.")
        if not model_name:
            issues.append("AI_MODEL is required for the configured external AI provider.")
        if provider == "openai_compatible" and not base_url_configured:
            issues.append("AI_BASE_URL is required for openai_compatible providers.")
        if base_url_configured and not _is_valid_http_url(base_url):
            issues.append("AI_BASE_URL must be a valid http or https URL.")
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


def _is_valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
