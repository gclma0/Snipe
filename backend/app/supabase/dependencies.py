from fastapi import Depends

from app.auth.dependencies import get_request_settings
from app.core.config import Settings
from app.supabase.client import SupabaseClient

RequestSettings = Depends(get_request_settings)


def get_supabase_client(settings: Settings = RequestSettings) -> SupabaseClient:
    return SupabaseClient(settings)
