"""xAI Grok LLM service (OpenAI-compatible API)."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from openai import OpenAI

from app.services.credentials import resolve_credentials
from app.services.yaml_store import YamlStore, get_store

logger = logging.getLogger(__name__)

XAI_BASE_URL = "https://api.x.ai/v1"
XAI_TEMPERATURE = 0.7


class LlmService:
    def __init__(self, store: YamlStore | None = None) -> None:
        self.store = store or get_store()

    def _get_client(self) -> tuple[OpenAI, str]:
        creds = resolve_credentials(store=self.store)
        if not creds.xai_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="xAI API key is not configured. Add it in Settings.",
            )
        return (
            OpenAI(api_key=creds.xai_api_key, base_url=XAI_BASE_URL),
            creds.xai_model,
        )

    def complete(self, system: str, user: str) -> str:
        client, model = self._get_client()
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=XAI_TEMPERATURE,
            )
        except Exception as exc:
            logger.exception("xAI completion failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"xAI API request failed: {exc}",
            ) from exc

        content = response.choices[0].message.content
        if not content:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="xAI API returned empty response",
            )
        return content.strip()


def get_llm_service() -> LlmService:
    return LlmService()
