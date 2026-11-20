"""Process wiring and request handlers for the directory API."""

from .cache import NullCache, TTLCache
from .models import InvalidChange
from .service import DirectoryService
from .settings import Settings
from .store import ProfileNotFound, ProfileStore


def build_service(store=None, settings=None):
    store = store if store is not None else ProfileStore()
    settings = settings if settings is not None else Settings.from_env()
    if settings.profile_cache_ttl > 0:
        cache = TTLCache(ttl=settings.profile_cache_ttl)
    else:
        cache = NullCache()
    return DirectoryService(store, cache=cache)


def profile_payload(profile):
    return {
        "org": profile.org_id,
        "id": profile.user_id,
        "email": profile.email,
        "name": profile.display_name,
        "title": profile.title,
        "timezone": profile.timezone,
        "pronouns": profile.pronouns,
    }


def handle_get(service, org_id, user_id):
    try:
        profile = service.get_profile(org_id, user_id)
    except ProfileNotFound:
        return 404, {"error": "not_found"}
    return 200, profile_payload(profile)


def handle_patch(service, org_id, user_id, body):
    if not isinstance(body, dict):
        return 400, {"error": "invalid", "detail": "body must be an object"}
    try:
        updated = service.update_profile(org_id, user_id, **body)
    except ProfileNotFound:
        return 404, {"error": "not_found"}
    except InvalidChange as exc:
        return 400, {"error": "invalid", "detail": str(exc)}
    return 200, profile_payload(updated)


def handle_search(service, org_id, query):
    return 200, {"results": [profile_payload(p) for p in service.search(org_id, query)]}
