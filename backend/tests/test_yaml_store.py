"""Tests for YAML storage."""

from pathlib import Path

import pytest
import yaml

from app.models.schemas import Post, PostCache, WorkflowRun
from app.services.yaml_store import YamlStore


@pytest.fixture
def temp_store(tmp_path: Path) -> YamlStore:
    database_root = tmp_path / "database"
    database_root.mkdir()
    (database_root / "posts").mkdir()
    (database_root / "runs").mkdir()

    groups_data = {
        "groups": [
            {
                "id": "test-group",
                "name": "Test Group",
                "category": "test",
                "members": [{"account": "user1"}],
                "steps": {
                    "stem": "analyze",
                    "combine": "combine",
                    "craft": "craft",
                },
            }
        ]
    }
    with (database_root / "groups.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(groups_data, handle)

    from app.config import Settings

    settings = Settings(database_root=database_root)
    return YamlStore(settings)


def test_list_groups(temp_store: YamlStore) -> None:
    groups = temp_store.list_groups()
    assert len(groups) == 1
    assert groups[0].id == "test-group"


def test_ensure_default_groups_seeds_empty_database(tmp_path: Path) -> None:
    database_root = tmp_path / "database"
    database_root.mkdir()
    (database_root / "posts").mkdir()
    (database_root / "runs").mkdir()

    from app.config import Settings

    store = YamlStore(Settings(database_root=database_root))
    assert store.list_groups() == []

    seeded = store.ensure_default_groups()
    assert seeded is True

    groups = store.list_groups()
    assert len(groups) == 1
    assert groups[0].id == "researcher"
    assert groups[0].name == "Researcher"


def test_ensure_default_groups_skips_existing(tmp_path: Path) -> None:
    database_root = tmp_path / "database"
    database_root.mkdir()
    (database_root / "posts").mkdir()
    (database_root / "runs").mkdir()
    (database_root / "groups.yaml").write_text(
        "groups:\n  - id: existing\n    name: Existing\n    category: test\n",
        encoding="utf-8",
    )

    from app.config import Settings

    store = YamlStore(Settings(database_root=database_root))
    assert store.ensure_default_groups() is False
    assert store.get_group("existing") is not None
    assert store.get_group("researcher") is None


def test_get_group(temp_store: YamlStore) -> None:
    group = temp_store.get_group("test-group")
    assert group is not None
    assert group.name == "Test Group"
    assert temp_store.get_group("missing") is None


def test_posts_round_trip(temp_store: YamlStore) -> None:
    cache = PostCache(
        group_id="test-group",
        fetched_at="2026-06-20T12:00:00Z",
        posts=[
            Post(
                id="1",
                author="user1",
                text="hello",
                created_at="2026-06-20T11:00:00Z",
            )
        ],
    )
    temp_store.save_posts(cache)
    loaded = temp_store.get_posts("test-group")
    assert loaded is not None
    assert loaded.posts[0].text == "hello"


def test_runs_round_trip(temp_store: YamlStore) -> None:
    run = WorkflowRun(
        run_id="20260620-120000-test-group",
        group_id="test-group",
        started_at="2026-06-20T12:00:00Z",
        status="completed",
        completed_at="2026-06-20T12:01:00Z",
    )
    temp_store.save_run(run)
    loaded = temp_store.get_run(run.run_id)
    assert loaded is not None
    assert loaded.status == "completed"

    summaries = temp_store.list_runs(group_id="test-group")
    assert len(summaries) == 1
    assert summaries[0].run_id == run.run_id


def test_delete_runs_for_group(temp_store: YamlStore) -> None:
    for suffix in ("a", "b"):
        temp_store.save_run(
            WorkflowRun(
                run_id=f"20260620-12000{suffix}-test-group",
                group_id="test-group",
                started_at="2026-06-20T12:00:00Z",
                status="completed",
            )
        )
    temp_store.save_run(
        WorkflowRun(
            run_id="20260620-120003-other",
            group_id="other-group",
            started_at="2026-06-20T12:00:00Z",
            status="completed",
        )
    )

    deleted = temp_store.delete_runs_for_group("test-group")
    assert deleted == 2
    assert temp_store.list_runs(group_id="test-group") == []
    assert len(temp_store.list_runs(group_id="other-group")) == 1
