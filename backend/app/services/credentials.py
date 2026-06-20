"""Resolve API credentials from database settings with env fallback."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings, settings
from app.models.schemas import (
    AppSettingsPublic,
    SecretFieldStatus,
    XApiSettingsPublic,
    XaiSettingsPublic,
)
from app.services.yaml_store import YamlStore, get_store


@dataclass(frozen=True)
class ResolvedCredentials:
    x_bearer_token: str
    xai_api_key: str
    xai_model: str

    def x_configured(self) -> bool:
        return bool(self.x_bearer_token)

    def xai_configured(self) -> bool:
        return bool(self.xai_api_key)


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "****"
    return "*" * (len(value) - 4) + value[-4:]


def resolve_credentials(
    app_settings: Settings | None = None,
    store: YamlStore | None = None,
) -> ResolvedCredentials:
    env = app_settings or settings
    stored = (store or get_store()).get_settings()

    return ResolvedCredentials(
        x_bearer_token=stored.x_api.bearer_token or env.x_bearer_token,
        xai_api_key=stored.xai.api_key or env.xai_api_key,
        xai_model=stored.xai.model or env.xai_model,
    )


def public_settings(store: YamlStore) -> AppSettingsPublic:
    stored = store.get_settings()
    resolved = resolve_credentials(store=store)

    def field_status(value: str) -> SecretFieldStatus:
        return SecretFieldStatus(configured=bool(value), masked=mask_secret(value))

    return AppSettingsPublic(
        x_api=XApiSettingsPublic(
            bearer_token=field_status(stored.x_api.bearer_token),
        ),
        xai=XaiSettingsPublic(
            api_key=field_status(stored.xai.api_key),
            model=stored.xai.model,
        ),
        x_api_configured=resolved.x_configured(),
        xai_configured=resolved.xai_configured(),
    )
