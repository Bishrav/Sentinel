from sentinel_api.security import ApiKeyAuthenticator


def test_authenticator_is_disabled_for_local_development_without_keys() -> None:
    authenticator = ApiKeyAuthenticator({})

    assert authenticator.enabled is False


def test_environment_parser_assigns_roles(monkeypatch) -> None:
    monkeypatch.setenv("SENTINEL_API_KEYS", "investigator-key:investigator,ops-key:operator")

    authenticator = ApiKeyAuthenticator.from_environment()

    assert authenticator.enabled is True
