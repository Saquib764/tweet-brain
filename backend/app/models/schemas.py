"""Pydantic schemas for Tweet Brain."""

from typing import Any, Literal, Self

from pydantic import BaseModel, Field, model_validator


def post_url(author: str, post_id: str) -> str:
    handle = author.lstrip("@")
    return f"https://x.com/{handle}/status/{post_id}"


class GroupFetchConfig(BaseModel):
    posts_per_user: int = 10


class GroupMember(BaseModel):
    account: str


class GroupStepItem(BaseModel):
    name: str = "Step"
    content: str = ""


class GroupSteps(BaseModel):
    items: list[GroupStepItem] = Field(default_factory=list)
    stem: str = ""
    combine: str = ""
    craft: str = ""

    @model_validator(mode="before")
    @classmethod
    def sync_steps(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        if "items" not in data:
            data["items"] = [
                {"name": name, "content": data.get(key) or ""}
                for name, key in [("Stem", "stem"), ("Combine", "combine"), ("Craft", "craft")]
            ]

        items = data.get("items") or []
        if items:
            data["stem"] = items[0].get("content", "") if len(items) > 0 else ""
            data["combine"] = items[1].get("content", "") if len(items) > 1 else ""
            data["craft"] = items[2].get("content", "") if len(items) > 2 else ""

        return data


class Group(BaseModel):
    id: str
    name: str
    category: str
    description: str = ""
    members: list[GroupMember] = Field(default_factory=list)
    fetch: GroupFetchConfig = Field(default_factory=GroupFetchConfig)
    steps: GroupSteps = Field(default_factory=GroupSteps)

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "accounts" in data and "members" not in data:
            data["members"] = [
                {"account": account} for account in data.pop("accounts")
            ]
        if "prompts" in data and "steps" not in data:
            data["steps"] = data.pop("prompts")
        return data

    def member_accounts(self) -> list[str]:
        return [member.account.lstrip("@") for member in self.members if member.account.strip()]


class GroupInput(BaseModel):
    id: str | None = None
    name: str
    category: str
    description: str = ""
    members: list[GroupMember] = Field(default_factory=list)
    fetch: GroupFetchConfig = Field(default_factory=GroupFetchConfig)
    steps: GroupSteps = Field(default_factory=GroupSteps)


class GroupCreateInput(BaseModel):
    name: str
    category: str
    description: str = ""


class Post(BaseModel):
    id: str
    author: str
    text: str
    created_at: str
    url: str = ""

    @model_validator(mode="after")
    def fill_url(self) -> Self:
        if not self.url:
            self.url = post_url(self.author, self.id)
        return self


class PostCache(BaseModel):
    group_id: str
    fetched_at: str
    posts: list[Post]


class StemResult(BaseModel):
    post_id: str
    author: str
    analysis: str


class CombineResult(BaseModel):
    ideas: list[str]


class CraftResult(BaseModel):
    tweet: str


class StepResult(BaseModel):
    name: str
    index: int
    output: str


class WorkflowStages(BaseModel):
    steps: list[StepResult] = Field(default_factory=list)
    stem: list[StemResult] = Field(default_factory=list)
    combine: CombineResult | None = None
    craft: CraftResult | None = None


class WorkflowRun(BaseModel):
    run_id: str
    group_id: str
    started_at: str
    completed_at: str | None = None
    status: Literal["running", "completed", "failed"] = "running"
    stages: WorkflowStages = Field(default_factory=WorkflowStages)
    error: str | None = None


class RunSummary(BaseModel):
    run_id: str
    group_id: str
    started_at: str
    completed_at: str | None = None
    status: Literal["running", "completed", "failed"]
    idea_count: int = 0
    crafted_tweet: str | None = None


class RunListResponse(BaseModel):
    runs: list[RunSummary]


class GroupMeta(BaseModel):
    """Optional metadata for dashboard cards."""

    last_fetched_at: str | None = None
    post_count: int = 0
    last_run_at: str | None = None
    last_run_status: str | None = None


class GroupWithMeta(BaseModel):
    group: Group
    meta: GroupMeta = Field(default_factory=GroupMeta)


class GroupsWithMetaResponse(BaseModel):
    groups: list[GroupWithMeta]


class XApiSettings(BaseModel):
    bearer_token: str = ""


class XaiSettings(BaseModel):
    api_key: str = ""
    model: str = "grok-4.3"


class AppSettings(BaseModel):
    x_api: XApiSettings = Field(default_factory=XApiSettings)
    xai: XaiSettings = Field(default_factory=XaiSettings)


class SecretFieldStatus(BaseModel):
    configured: bool = False
    masked: str = ""


class XApiSettingsPublic(BaseModel):
    bearer_token: SecretFieldStatus = Field(default_factory=SecretFieldStatus)


class XaiSettingsPublic(BaseModel):
    api_key: SecretFieldStatus = Field(default_factory=SecretFieldStatus)
    model: str = "grok-4.3"


class AppSettingsPublic(BaseModel):
    x_api: XApiSettingsPublic = Field(default_factory=XApiSettingsPublic)
    xai: XaiSettingsPublic = Field(default_factory=XaiSettingsPublic)
    x_api_configured: bool = False
    xai_configured: bool = False


class AppSettingsUpdate(BaseModel):
    x_api: XApiSettings | None = None
    xai: XaiSettings | None = None
