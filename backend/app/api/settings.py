"""Settings API routes."""

from fastapi import APIRouter, Depends

from app.models.schemas import AppSettings, AppSettingsPublic, AppSettingsUpdate
from app.services.credentials import public_settings
from app.services.yaml_store import YamlStore, get_store

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=AppSettingsPublic)
def get_settings(store: YamlStore = Depends(get_store)) -> AppSettingsPublic:
    return public_settings(store)


@router.put("", response_model=AppSettingsPublic)
def update_settings(
    payload: AppSettingsUpdate,
    store: YamlStore = Depends(get_store),
) -> AppSettingsPublic:
    update = AppSettings()
    if payload.x_api is not None:
        update.x_api = payload.x_api
    if payload.xai is not None:
        update.xai = payload.xai

    store.update_settings(update)
    return public_settings(store)
