"""X API client wrapper using xdk."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from xdk import Client

from app.models.schemas import Post, post_url
from app.services.credentials import resolve_credentials
from app.services.yaml_store import YamlStore, get_store

logger = logging.getLogger(__name__)


class TwitterService:
    def __init__(self, store: YamlStore | None = None) -> None:
        self.store = store or get_store()

    def _get_client(self) -> Client:
        creds = resolve_credentials(store=self.store)
        if not creds.x_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="X API credentials are not configured. Add them in Settings.",
            )
        return Client(bearer_token=creds.x_bearer_token)

    @staticmethod
    def _attr(obj: Any, key: str, default: Any = None) -> Any:
        if obj is None:
            return default
        if hasattr(obj, key):
            return getattr(obj, key)
        if isinstance(obj, dict):
            return obj.get(key, default)
        return default

    @staticmethod
    def _parse_created_at(value: str) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def get_user_recent_posts(
        self,
        username: str,
        limit: int = 10,
        days: int | None = None,
    ) -> list[Post]:
        client = self._get_client()
        clean_username = username.lstrip("@")
        cutoff = datetime.now(UTC) - timedelta(days=days) if days is not None else None

        try:
            user_response = client.users.get_by_username(username=clean_username)
        except Exception as exc:
            logger.exception("Failed to look up user %s", clean_username)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"X API user lookup failed for @{clean_username}: {exc}",
            ) from exc

        user_data = self._attr(user_response, "data")
        user_id = self._attr(user_data, "id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User @{clean_username} not found",
            )

        posts: list[Post] = []
        try:
            for page in client.users.get_posts(
                id=str(user_id),
                max_results=min(limit, 100),
                exclude=["retweets", "replies"],
                tweet_fields=["created_at", "text"],
            ):
                page_data = self._attr(page, "data") or []
                if not page_data:
                    break

                page_has_older_than_cutoff = False
                for item in page_data:
                    post_id = str(self._attr(item, "id", ""))
                    text = self._attr(item, "text", "") or ""
                    created_at = self._attr(item, "created_at", "") or ""
                    if not post_id or not text:
                        continue

                    created_dt = self._parse_created_at(created_at)
                    if cutoff and created_dt and created_dt < cutoff:
                        page_has_older_than_cutoff = True
                        continue

                    posts.append(
                        Post(
                            id=post_id,
                            author=clean_username,
                            text=text,
                            created_at=created_at,
                            url=post_url(clean_username, post_id),
                        )
                    )

                if cutoff and page_has_older_than_cutoff:
                    break
        except Exception as exc:
            logger.exception("Failed to fetch posts for %s", clean_username)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"X API posts fetch failed for @{clean_username}: {exc}",
            ) from exc

        return posts


def get_twitter_service() -> TwitterService:
    return TwitterService()
