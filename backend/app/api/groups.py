"""Group API routes."""

import re

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.schemas import Group, GroupCreateInput, GroupInput, GroupWithMeta, GroupsWithMetaResponse
from app.services.yaml_store import YamlStore, get_store

router = APIRouter(prefix="/groups", tags=["groups"])


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "group"


def _to_group(payload: GroupInput, fallback_id: str | None = None) -> Group:
    group_id = (payload.id or fallback_id or _slugify(payload.name)).strip()
    return Group(
        id=group_id,
        name=payload.name.strip(),
        category=payload.category.strip(),
        description=payload.description,
        members=payload.members,
        fetch=payload.fetch,
        steps=payload.steps,
    )


@router.get("", response_model=GroupsWithMetaResponse)
def list_groups(store: YamlStore = Depends(get_store)) -> GroupsWithMetaResponse:
    groups = store.list_groups()
    return GroupsWithMetaResponse(
        groups=[
            GroupWithMeta(group=group, meta=store.get_group_meta(group.id))
            for group in groups
        ]
    )


@router.post("", response_model=GroupWithMeta, status_code=status.HTTP_201_CREATED)
def create_group(payload: GroupCreateInput, store: YamlStore = Depends(get_store)) -> GroupWithMeta:
    group = _to_group(GroupInput(**payload.model_dump()))
    try:
        created = store.create_group(group)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return GroupWithMeta(group=created, meta=store.get_group_meta(created.id))


@router.get("/{group_id}", response_model=GroupWithMeta)
def get_group(group_id: str, store: YamlStore = Depends(get_store)) -> GroupWithMeta:
    group = store.get_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found",
        )
    return GroupWithMeta(group=group, meta=store.get_group_meta(group_id))


@router.put("/{group_id}", response_model=GroupWithMeta)
def update_group(
    group_id: str,
    payload: GroupInput,
    store: YamlStore = Depends(get_store),
) -> GroupWithMeta:
    if not store.get_group(group_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found",
        )
    group = _to_group(payload, fallback_id=group_id)
    try:
        updated = store.update_group(group_id, group)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return GroupWithMeta(group=updated, meta=store.get_group_meta(updated.id))


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: str, store: YamlStore = Depends(get_store)) -> None:
    if not store.get_group(group_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found",
        )
    try:
        store.delete_group(group_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
