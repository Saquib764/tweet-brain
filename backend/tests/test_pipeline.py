"""Pipeline helper tests."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.schemas import (
    Group,
    GroupFetchConfig,
    GroupMember,
    GroupStepItem,
    GroupSteps,
    Post,
    PostCache,
    StepResult,
    WorkflowRun,
    WorkflowStages,
)
from app.services.pipeline import PipelineService, _format_posts


def test_format_posts() -> None:
    cache = PostCache(
        group_id="test",
        fetched_at="2026-01-01T00:00:00Z",
        posts=[
            Post(id="1", author="alice", text="Hello", created_at="2026-01-01T00:00:00Z"),
            Post(id="2", author="bob", text="World", created_at="2026-01-02T00:00:00Z"),
        ],
    )
    result = _format_posts(cache)
    assert "@alice" in result
    assert "@bob" in result
    assert "---" in result
    assert "Hello" in result
    assert "World" in result


def _make_group() -> Group:
    return Group(
        id="test-group",
        name="Test",
        category="test",
        members=[GroupMember(account="alice")],
        fetch=GroupFetchConfig(posts_per_user=10),
        steps=GroupSteps(
            items=[
                {"name": "Analyze", "content": "Analyze posts"},
                {"name": "Summarize", "content": "Summarize analysis"},
            ],
        ),
    )


def test_execute_step_chain() -> None:
    store = MagicMock()
    llm = MagicMock()
    llm.complete.side_effect = ["analysis output", "summary output"]

    store.get_posts.return_value = PostCache(
        group_id="test-group",
        fetched_at="2026-01-01T00:00:00Z",
        posts=[Post(id="1", author="alice", text="Hi", created_at="2026-01-01T00:00:00Z")],
    )
    store.utc_now_iso.return_value = "2026-01-01T00:00:00Z"
    store.save_run.side_effect = lambda run: run

    group = _make_group()
    run = WorkflowRun(
        run_id="run-1",
        group_id="test-group",
        started_at="2026-01-01T00:00:00Z",
        status="running",
    )

    pipeline = PipelineService(store=store, twitter=MagicMock(), llm=llm)

    run = pipeline.execute_step(group, run, 0)
    assert len(run.stages.steps) == 1
    assert run.stages.steps[0].output == "analysis output"
    llm.complete.assert_called_once()
    assert "Hi" in llm.complete.call_args.kwargs["user"]

    run = pipeline.execute_step(group, run, 1)
    assert len(run.stages.steps) == 2
    assert run.stages.steps[1].output == "summary output"
    assert run.status == "completed"
    assert llm.complete.call_args.kwargs["user"] == "analysis output"


def test_execute_step_requires_posts() -> None:
    store = MagicMock()
    store.get_posts.return_value = None
    store.utc_now_iso.return_value = "2026-01-01T00:00:00Z"
    store.save_run.side_effect = lambda run: run

    group = _make_group()
    run = WorkflowRun(
        run_id="run-1",
        group_id="test-group",
        started_at="2026-01-01T00:00:00Z",
        status="running",
    )

    pipeline = PipelineService(store=store, twitter=MagicMock(), llm=MagicMock())

    with pytest.raises(HTTPException) as exc_info:
        pipeline.execute_step(group, run, 0)
    assert exc_info.value.status_code == 400


def test_execute_step_out_of_order() -> None:
    store = MagicMock()
    store.utc_now_iso.return_value = "2026-01-01T00:00:00Z"

    group = _make_group()
    run = WorkflowRun(
        run_id="run-1",
        group_id="test-group",
        started_at="2026-01-01T00:00:00Z",
        status="running",
    )

    pipeline = PipelineService(store=store, twitter=MagicMock(), llm=MagicMock())

    with pytest.raises(HTTPException) as exc_info:
        pipeline.execute_step(group, run, 1)
    assert exc_info.value.status_code == 400
