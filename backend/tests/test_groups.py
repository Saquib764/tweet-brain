"""Group CRUD tests."""

from pathlib import Path

import yaml

from app.models.schemas import Group, GroupMember, GroupSteps
from app.services.yaml_store import YamlStore


def test_create_update_delete_group(tmp_path: Path) -> None:
    database_root = tmp_path / "database"
    database_root.mkdir()
    (database_root / "posts").mkdir()
    (database_root / "runs").mkdir()
    (database_root / "groups.yaml").write_text("groups: []\n", encoding="utf-8")

    from app.config import Settings

    store = YamlStore(Settings(database_root=database_root))
    group = Group(
        id="new-group",
        name="New Group",
        category="tech",
        description="A test group",
        members=[GroupMember(account="sama")],
        steps=GroupSteps(stem="s", combine="c", craft="f"),
    )
    store.create_group(group)

    loaded = store.get_group("new-group")
    assert loaded is not None
    assert loaded.members[0].account == "sama"

    updated = Group(
        id="new-group",
        name="Updated Group",
        category="tech",
        description="Updated",
        members=[GroupMember(account="karpathy")],
        steps=GroupSteps(stem="s2", combine="c2", craft="f2"),
    )
    store.update_group("new-group", updated)
    assert store.get_group("new-group").name == "Updated Group"

    store.delete_group("new-group")
    assert store.get_group("new-group") is None


def test_legacy_accounts_migration(tmp_path: Path) -> None:
    database_root = tmp_path / "database"
    database_root.mkdir()
    (database_root / "posts").mkdir()
    (database_root / "runs").mkdir()

    groups_data = {
        "groups": [
            {
                "id": "legacy",
                "name": "Legacy",
                "category": "test",
                "accounts": ["user1", "user2"],
                "prompts": {"stem": "s", "combine": "c", "craft": "f"},
            }
        ]
    }
    with (database_root / "groups.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(groups_data, handle)

    from app.config import Settings

    store = YamlStore(Settings(database_root=database_root))
    group = store.get_group("legacy")
    assert group is not None
    assert len(group.members) == 2
    assert group.members[0].account == "user1"
    assert group.steps.stem == "s"
