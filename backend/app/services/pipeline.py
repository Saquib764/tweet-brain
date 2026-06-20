"""Fetch and LLM workflow orchestration."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status

from app.models.schemas import (
    Group,
    PostCache,
    StepResult,
    WorkflowRun,
    WorkflowStages,
)
from app.services.llm import LlmService
from app.services.twitter import TwitterService
from app.services.yaml_store import YamlStore

logger = logging.getLogger(__name__)


def _format_posts(cache: PostCache) -> str:
    blocks = []
    for post in cache.posts:
        blocks.append(
            f"Author: @{post.author}\n"
            f"Post ID: {post.id}\n"
            f"URL: {post.url}\n"
            f"Posted at: {post.created_at}\n\n"
            f"Tweet text:\n{post.text}"
        )
    return "\n\n---\n\n".join(blocks)


class PipelineService:
    def __init__(
        self,
        store: YamlStore | None = None,
        twitter: TwitterService | None = None,
        llm: LlmService | None = None,
    ) -> None:
        from app.services.llm import get_llm_service
        from app.services.twitter import get_twitter_service
        from app.services.yaml_store import get_store

        self.store = store or get_store()
        self.twitter = twitter or get_twitter_service()
        self.llm = llm or get_llm_service()

    def fetch_group_posts(self, group: Group, days: int = 3) -> PostCache:
        all_posts = []
        limit = group.fetch.posts_per_user

        for username in group.member_accounts():
            posts = self.twitter.get_user_recent_posts(username, limit=limit, days=days)
            all_posts.extend(posts)

        cache = PostCache(
            group_id=group.id,
            fetched_at=self.store.utc_now_iso(),
            posts=all_posts,
        )
        return self.store.save_posts(cache)

    def start_run(self, group: Group) -> WorkflowRun:
        run = WorkflowRun(
            run_id=self.store.new_run_id(group.id),
            group_id=group.id,
            started_at=self.store.utc_now_iso(),
            status="running",
        )
        return self.store.save_run(run)

    def execute_step(self, group: Group, run: WorkflowRun, step_index: int) -> WorkflowRun:
        items = group.steps.items
        if step_index < 0 or step_index >= len(items):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Step index {step_index} out of range (0-{len(items) - 1})",
            )

        if step_index > len(run.stages.steps):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Step {step_index} cannot run before step {len(run.stages.steps)} completes",
            )

        if step_index < len(run.stages.steps):
            return run

        step = items[step_index]
        try:
            if step_index == 0:
                cache = self.store.get_posts(group.id)
                if not cache or not cache.posts:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"No cached posts for group '{group.id}'. Fetch posts first.",
                    )
                user_input = _format_posts(cache)
            else:
                prior = run.stages.steps[step_index - 1]
                user_input = prior.output

            output = self.llm.complete(system=step.content, user=user_input)
            run.stages.steps.append(
                StepResult(name=step.name, index=step_index, output=output)
            )

            if step_index == len(items) - 1:
                run.status = "completed"
                run.completed_at = self.store.utc_now_iso()
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Step %s failed for group %s", step_index, group.id)
            run.status = "failed"
            run.error = str(exc)
            run.completed_at = self.store.utc_now_iso()
            self.store.save_run(run)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Step {step_index} failed: {exc}",
            ) from exc

        return self.store.save_run(run)

    def run_workflow(self, group: Group) -> WorkflowRun:
        cache = self.store.get_posts(group.id)
        if not cache or not cache.posts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No cached posts for group '{group.id}'. Fetch posts first.",
            )

        items = group.steps.items
        if not items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Group '{group.id}' has no workflow steps configured.",
            )

        run = self.start_run(group)
        try:
            for index in range(len(items)):
                run = self.execute_step(group, run, index)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Workflow failed for group %s", group.id)
            run.status = "failed"
            run.error = str(exc)
            run.completed_at = self.store.utc_now_iso()
            self.store.save_run(run)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Workflow failed: {exc}",
            ) from exc

        return run


def get_pipeline_service() -> PipelineService:
    return PipelineService()
