"""Workflow API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.schemas import RunListResponse, WorkflowRun
from app.services.pipeline import PipelineService, get_pipeline_service
from app.services.yaml_store import YamlStore, get_store

router = APIRouter(tags=["workflows"])


@router.post("/groups/{group_id}/runs", response_model=WorkflowRun)
def start_run(
    group_id: str,
    store: YamlStore = Depends(get_store),
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> WorkflowRun:
    group = store.get_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found",
        )
    return pipeline.start_run(group)


@router.post("/groups/{group_id}/runs/{run_id}/steps/{step_index}", response_model=WorkflowRun)
def execute_step(
    group_id: str,
    run_id: str,
    step_index: int,
    store: YamlStore = Depends(get_store),
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> WorkflowRun:
    group = store.get_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found",
        )
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )
    if run.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Run '{run_id}' does not belong to group '{group_id}'",
        )
    return pipeline.execute_step(group, run, step_index)


@router.post("/groups/{group_id}/run", response_model=WorkflowRun)
def run_workflow(
    group_id: str,
    store: YamlStore = Depends(get_store),
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> WorkflowRun:
    group = store.get_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found",
        )
    return pipeline.run_workflow(group)


@router.get("/runs", response_model=RunListResponse)
def list_runs(
    group_id: str | None = Query(default=None),
    store: YamlStore = Depends(get_store),
) -> RunListResponse:
    return RunListResponse(runs=store.list_runs(group_id=group_id))


@router.get("/runs/{run_id}", response_model=WorkflowRun)
def get_run(run_id: str, store: YamlStore = Depends(get_store)) -> WorkflowRun:
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )
    return run


@router.delete("/groups/{group_id}/runs", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_runs(group_id: str, store: YamlStore = Depends(get_store)) -> None:
    group = store.get_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found",
        )
    store.delete_runs_for_group(group_id)


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: str, store: YamlStore = Depends(get_store)) -> None:
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )
    try:
        store.delete_run(run_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
