import asyncio

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from sentinel_api.security import ApiKeyAuthenticator


def request_with_auth(value: str) -> Request:
    return Request({"type": "http", "headers": [(b"authorization", value.encode())]})


def test_authenticator_is_disabled_for_local_development_without_keys() -> None:
    authenticator = ApiKeyAuthenticator({})

    assert authenticator.enabled is False


def test_environment_parser_assigns_roles(monkeypatch) -> None:
    monkeypatch.setenv("SENTINEL_API_KEYS", "investigator-key:investigator,ops-key:operator")

    authenticator = ApiKeyAuthenticator.from_environment()

    assert authenticator.enabled is True


def test_invalid_bearer_key_is_rejected() -> None:
    authenticator = ApiKeyAuthenticator({"known": "investigator"})

    with pytest.raises(HTTPException, match="Invalid authentication credentials"):
        authenticator.authenticate(request_with_auth("Bearer wrong"))


def test_investigator_cannot_use_operator_action() -> None:
    authenticator = ApiKeyAuthenticator({"investigator-key": "investigator"})

    with pytest.raises(HTTPException, match="Insufficient role"):
        asyncio.run(authenticator.require("operator")(request_with_auth("Bearer investigator-key")))
