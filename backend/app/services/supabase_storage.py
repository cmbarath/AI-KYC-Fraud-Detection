from functools import lru_cache
from urllib.parse import urlsplit, urlunsplit

from supabase import Client, create_client

from backend.app.config import settings


def _project_url() -> str:
    raw_url = settings.SUPABASE_URL.strip()
    parsed = urlsplit(raw_url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path.rstrip("/") not in ("", "/rest/v1")
    ):
        raise RuntimeError("SUPABASE_URL must be the Supabase project URL.")

    return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    secret_key = (
        settings.SUPABASE_SERVICE_ROLE_KEY
        or settings.SUPABASE_SECRET_KEY
    )
    if not secret_key:
        raise RuntimeError("A backend-only Supabase secret key is required.")

    return create_client(_project_url(), secret_key)


def get_storage_bucket():
    if not settings.SUPABASE_STORAGE_BUCKET:
        raise RuntimeError("SUPABASE_STORAGE_BUCKET is not configured.")
    return get_supabase_client().storage.from_(settings.SUPABASE_STORAGE_BUCKET)
