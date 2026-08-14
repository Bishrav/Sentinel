from sentinel_investigation import (
    HttpInvestigationProvider,
    InvestigationProviderSettings,
)


def test_provider_settings_are_disabled_without_endpoint(monkeypatch) -> None:
    monkeypatch.delenv("SENTINEL_INVESTIGATION_ENDPOINT", raising=False)

    settings = InvestigationProviderSettings.from_environment()

    assert settings.build_provider() is None


def test_provider_settings_build_http_adapter_from_environment(monkeypatch) -> None:
    monkeypatch.setenv(
        "SENTINEL_INVESTIGATION_ENDPOINT",
        "https://provider.example.test/investigate",
    )
    monkeypatch.setenv("SENTINEL_INVESTIGATION_API_KEY", "test-key")
    monkeypatch.setenv("SENTINEL_INVESTIGATION_TIMEOUT_SECONDS", "7")

    settings = InvestigationProviderSettings.from_environment()
    provider = settings.build_provider()

    assert isinstance(provider, HttpInvestigationProvider)
    assert settings.timeout_seconds == 7
