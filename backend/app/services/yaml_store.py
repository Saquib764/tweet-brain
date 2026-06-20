"""YAML file storage for local database."""

from __future__ import annotations

import logging
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from app.config import Settings, settings
from app.models.schemas import (
    AppSettings,
    Group,
    GroupMeta,
    PostCache,
    RunSummary,
    WorkflowRun,
    XApiSettings,
    XaiSettings,
)

logger = logging.getLogger(__name__)

DEFAULT_GROUPS_PATH = Path(__file__).resolve().parent.parent.parent / "default_groups.yaml"


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _write_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
        suffix=".tmp",
    ) as tmp:
        tmp.write(payload)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


class YamlStore:
    def __init__(self, app_settings: Settings | None = None) -> None:
        self.settings = app_settings or settings
        self.settings.posts_dir.mkdir(parents=True, exist_ok=True)
        self.settings.runs_dir.mkdir(parents=True, exist_ok=True)

    def list_groups(self) -> list[Group]:
        data = _read_yaml(self.settings.groups_path)
        if not data or "groups" not in data:
            return []
        return [Group.model_validate(item) for item in data["groups"]]

    def ensure_default_groups(self) -> bool:
        """Seed groups from bundled default when the database has none."""
        if self.list_groups():
            return False
        if not DEFAULT_GROUPS_PATH.is_file():
            logger.warning("No groups found and default file missing: %s", DEFAULT_GROUPS_PATH)
            return False
        self.settings.groups_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DEFAULT_GROUPS_PATH, self.settings.groups_path)
        logger.info("Seeded default groups from %s", DEFAULT_GROUPS_PATH)
        return True

    def save_groups(self, groups: list[Group]) -> list[Group]:
        _write_yaml(self.settings.groups_path, {"groups": [group.model_dump() for group in groups]})
        return groups

    def get_group(self, group_id: str) -> Group | None:
        for group in self.list_groups():
            if group.id == group_id:
                return group
        return None

    def create_group(self, group: Group) -> Group:
        groups = self.list_groups()
        if any(existing.id == group.id for existing in groups):
            raise ValueError(f"Group '{group.id}' already exists")
        groups.append(group)
        self.save_groups(groups)
        return group

    def update_group(self, group_id: str, group: Group) -> Group:
        groups = self.list_groups()
        index = next((i for i, existing in enumerate(groups) if existing.id == group_id), None)
        if index is None:
            raise ValueError(f"Group '{group_id}' not found")
        if group.id != group_id:
            if any(existing.id == group.id for i, existing in enumerate(groups) if i != index):
                raise ValueError(f"Group '{group.id}' already exists")
        groups[index] = group
        self.save_groups(groups)
        return group

    def delete_group(self, group_id: str) -> None:
        groups = self.list_groups()
        filtered = [group for group in groups if group.id != group_id]
        if len(filtered) == len(groups):
            raise ValueError(f"Group '{group_id}' not found")
        self.save_groups(filtered)

    def get_group_meta(self, group_id: str) -> GroupMeta:
        meta = GroupMeta()
        post_cache = self.get_posts(group_id)
        if post_cache:
            meta.last_fetched_at = post_cache.fetched_at
            meta.post_count = len(post_cache.posts)

        runs = self.list_runs(group_id=group_id)
        if runs:
            latest = runs[0]
            meta.last_run_at = latest.completed_at or latest.started_at
            meta.last_run_status = latest.status
        return meta

    def get_posts(self, group_id: str) -> PostCache | None:
        path = self.settings.posts_dir / f"{group_id}.yaml"
        data = _read_yaml(path)
        if not data:
            return None
        return PostCache.model_validate(data)

    def save_posts(self, cache: PostCache) -> PostCache:
        path = self.settings.posts_dir / f"{cache.group_id}.yaml"
        _write_yaml(path, cache.model_dump())
        return cache

    def save_run(self, run: WorkflowRun) -> WorkflowRun:
        path = self.settings.runs_dir / f"{run.run_id}.yaml"
        _write_yaml(path, run.model_dump())
        return run

    def get_run(self, run_id: str) -> WorkflowRun | None:
        path = self.settings.runs_dir / f"{run_id}.yaml"
        data = _read_yaml(path)
        if not data:
            return None
        return WorkflowRun.model_validate(data)

    def list_runs(self, group_id: str | None = None) -> list[RunSummary]:
        summaries: list[RunSummary] = []
        for path in sorted(self.settings.runs_dir.glob("*.yaml"), reverse=True):
            data = _read_yaml(path)
            if not data:
                continue
            run = WorkflowRun.model_validate(data)
            if group_id and run.group_id != group_id:
                continue
            idea_count = 0
            crafted_tweet = None
            if run.stages.steps:
                crafted_tweet = run.stages.steps[-1].output
                idea_count = len(run.stages.steps)
            elif run.stages.combine:
                idea_count = len(run.stages.combine.ideas)
            if run.stages.craft:
                crafted_tweet = run.stages.craft.tweet
            summaries.append(
                RunSummary(
                    run_id=run.run_id,
                    group_id=run.group_id,
                    started_at=run.started_at,
                    completed_at=run.completed_at,
                    status=run.status,
                    idea_count=idea_count,
                    crafted_tweet=crafted_tweet,
                )
            )
        return summaries

    def delete_run(self, run_id: str) -> None:
        path = self.settings.runs_dir / f"{run_id}.yaml"
        if not path.exists():
            raise ValueError(f"Run '{run_id}' not found")
        path.unlink()

    def delete_runs_for_group(self, group_id: str) -> int:
        deleted = 0
        for path in self.settings.runs_dir.glob("*.yaml"):
            data = _read_yaml(path)
            if not data:
                continue
            run = WorkflowRun.model_validate(data)
            if run.group_id == group_id:
                path.unlink()
                deleted += 1
        return deleted

    def new_run_id(self, group_id: str) -> str:
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        return f"{stamp}-{group_id}"

    def get_settings(self) -> AppSettings:
        data = _read_yaml(self.settings.settings_path)
        if not data:
            return AppSettings()
        return AppSettings.model_validate(data)

    def save_settings(self, app_settings: AppSettings) -> AppSettings:
        _write_yaml(self.settings.settings_path, app_settings.model_dump())
        return app_settings

    def update_settings(self, update: AppSettings) -> AppSettings:
        current = self.get_settings()
        merged = AppSettings(
            x_api=XApiSettings(
                bearer_token=update.x_api.bearer_token or current.x_api.bearer_token,
            ),
            xai=XaiSettings(
                api_key=update.xai.api_key or current.xai.api_key,
                model=update.xai.model or current.xai.model,
            ),
        )
        return self.save_settings(merged)

    @staticmethod
    def utc_now_iso() -> str:
        return _utc_now_iso()


def get_store() -> YamlStore:
    return YamlStore()
