"""
OmniSight — Webhook Signature Security Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Verifies HMAC-SHA256 signature validation logic used for incoming
GitHub and CI/CD webhook payloads.
"""

import hashlib
import hmac
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.api.webhook import verify_github_signature


def _make_request(body_bytes: bytes) -> Request:
    async def receive():
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    scope = {"type": "http", "method": "POST", "path": "/api/v1/webhook/ci-cd-trigger", "headers": []}
    return Request(scope, receive)


@pytest.mark.asyncio
async def test_valid_hmac_signature_passes():
    secret = "omnisight_test_secret"
    payload = b'{"repository":"infotact/omnisight","branch":"main"}'
    sig = "sha256=" + hmac.new(secret.encode("utf-8"), msg=payload, digestmod=hashlib.sha256).hexdigest()
    req = _make_request(payload)
    await verify_github_signature(req, sig, secret)


@pytest.mark.asyncio
async def test_invalid_hmac_signature_raises_401():
    secret = "omnisight_test_secret"
    payload = b'{"repository":"infotact/omnisight","branch":"main"}'
    req = _make_request(payload)
    with pytest.raises(HTTPException) as exc_info:
        await verify_github_signature(req, "sha256=invalid_digest", secret)
    assert exc_info.value.status_code == 401
