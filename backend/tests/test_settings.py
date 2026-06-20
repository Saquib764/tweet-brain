"""Tests for settings storage."""

from pathlib import Path

import yaml

from app.models.schemas import AppSettings, XApiSettings, XaiSettings
from app.services.credentials import mask_secret, resolve_credentials
from app.services.yaml_store import YamlStore


def test_mask_secret() -> None:
    assert mask_secret("") == ""
    assert mask_secret("abc") == "****"
    assert mask_secret("abcdefghij").endswith("ghij")


def test_settings_round_trip(tmp_path: Path) -> None:
    database_root = tmp_path / "database"
    database_root.mkdir()
    (database_root / "posts").mkdir()
    (database_root / "runs").mkdir()
    (database_root / "groups.yaml").write_text("groups: []\n", encoding="utf-8")

    from app.config import Settings

    store = YamlStore(Settings(database_root=database_root))
    saved = store.save_settings(
        AppSettings(
            x_api=XApiSettings(bearer_token="bearer123"),
            xai=XaiSettings(api_key="xai-key", model="grok-test"),
        )
    )
    loaded = store.get_settings()
    assert loaded.x_api.bearer_token == saved.x_api.bearer_token
    assert loaded.xai.model == "grok-test"


def test_settings_merge_keeps_existing(tmp_path: Path) -> None:
    database_root = tmp_path / "database"
    database_root.mkdir()
    (database_root / "posts").mkdir()
    (database_root / "runs").mkdir()
    (database_root / "groups.yaml").write_text("groups: []\n", encoding="utf-8")

    from app.config import Settings

    store = YamlStore(Settings(database_root=database_root))
    store.save_settings(
        AppSettings(
            x_api=XApiSettings(bearer_token="keep-me"),
        )
    )
    merged = store.update_settings(AppSettings(x_api=XApiSettings(bearer_token="new-token")))
    assert merged.x_api.bearer_token == "new-token"


def test_resolve_credentials_prefers_database(tmp_path: Path) -> None:
    database_root = tmp_path / "database"
    database_root.mkdir()
    (database_root / "posts").mkdir()
    (database_root / "runs").mkdir()

    settings_data = {
        "x_api": {
            "bearer_token": "db-bearer",
        },
        "xai": {"api_key": "db-xai", "model": "grok-db"},
    }
    with (database_root / "settings.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(settings_data, handle)

    from app.config import Settings

    env = Settings(
        database_root=database_root,
        x_bearer_token="env-bearer",
        xai_api_key="env-xai",
    )
    store = YamlStore(env)
    creds = resolve_credentials(app_settings=env, store=store)
    assert creds.x_bearer_token == "db-bearer"
    assert creds.xai_api_key == "db-xai"
    assert creds.xai_model == "grok-db"
