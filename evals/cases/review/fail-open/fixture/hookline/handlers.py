"""HTTP entry point for POST /hooks/<provider>."""
import json
import time

from .events import dispatch
from .signatures import SignatureError, verify


def handle(request, providers, ledger, clock=time.time):
    name = request["path"].rstrip("/").rsplit("/", 1)[-1]
    provider = providers.get(name)
    if provider is None:
        return 404, {"error": "unknown provider"}
    try:
        verify(provider, request["headers"], request["body"], int(clock()))
    except SignatureError as error:
        return 401, {"error": str(error)}
    try:
        event = json.loads(request["body"])
    except ValueError:
        return 400, {"error": "body is not JSON"}
    if not isinstance(event, dict):
        return 400, {"error": "body must be a JSON object"}
    return dispatch(provider.name, event, ledger)
