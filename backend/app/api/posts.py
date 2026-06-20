"""Posts API routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.schemas import PostCache
from app.services.pipeline import PipelineService, get_pipeline_service
from app.services.yaml_store import YamlStore, get_store

router = APIRouter(prefix="/groups", tags=["posts"])


@router.get("/{group_id}/posts", response_model=PostCache)
def get_cached_posts(group_id: str, store: YamlStore = Depends(get_store)) -> PostCache:
    group = store.get_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found",
        )
    cache = store.get_posts(group_id)
    if not cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached posts for group '{group_id}'. Use POST /fetch first.",
        )
    return cache


@router.post("/{group_id}/fetch", response_model=PostCache)
def fetch_posts(
    group_id: str,
    days: int = 3,
    store: YamlStore = Depends(get_store),
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> PostCache:
    group = store.get_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found",
        )
    return pipeline.fetch_group_posts(group, days=days)
