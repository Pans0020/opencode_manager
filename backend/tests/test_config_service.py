from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.config_manager import ConfigManager


def make_manager(sample_workspace: dict[str, Path]) -> ConfigManager:
    return ConfigManager(
        opencode_path=sample_workspace["opencode_path"],
        omo_path=sample_workspace["omo_path"],
        settings_path=sample_workspace["settings_path"],
        omo_opencode_path=sample_workspace.get("omo_opencode_path"),
    )


def test_overview_normalizes_providers_and_targets(sample_workspace: dict[str, Path]) -> None:
    manager = make_manager(sample_workspace)

    overview = manager.get_overview()

    provider_ids = [provider.id for provider in overview.providers]
    assert provider_ids == ["Anthropic", "OpenAI"]
    assert any(target.id == "opencode:agent:planner" for target in overview.targets)
    assert any(target.id == "omo:agent:sisyphus" for target in overview.targets)
    assert any(target.id == "omo:category:deep" for target in overview.targets)
    assert any(target.id == "omo:subagent:librarian" for target in overview.targets)
    deep = next(target for target in overview.targets if target.id == "omo:category:deep")
    assert deep.kind == "category"
    librarian = next(target for target in overview.targets if target.id == "omo:subagent:librarian")
    assert librarian.kind == "subagent"
    
    # Hidden targets should be present but marked as visible=False
    def is_invisible(target_id: str) -> bool:
        t = next((target for target in overview.targets if target.id == target_id), None)
        return t is not None and t.visible is False

    assert is_invisible("opencode:default:model")
    assert is_invisible("opencode:default:small_model")
    assert is_invisible("opencode:agent:build")
    assert is_invisible("opencode:agent:general")
    assert is_invisible("opencode:agent:compaction")
    assert is_invisible("opencode:agent:Sisyphus-Junior")

    planner = next(target for target in overview.targets if target.id == "opencode:agent:planner")
    assert planner.current_provider == "OpenAI"
    assert planner.current_model == "gpt-5.4"
    assert planner.current_strength == "high"


def test_preview_groups_changes_by_file(sample_workspace: dict[str, Path]) -> None:
    manager = make_manager(sample_workspace)

    preview = manager.preview_changes(
        [
            {
                "targetId": "opencode:agent:planner",
                "provider": "Anthropic",
                "model": "claude-sonnet-4",
                "strength": "low",
            },
            {
                "targetId": "omo:category:quick",
                "provider": "OpenAI",
                "model": "gpt-5.4",
                "strength": "high",
            },
        ]
    )

    changed_paths = [change.file_path for change in preview.files]
    assert sample_workspace["opencode_path"].as_posix() in changed_paths
    assert sample_workspace["omo_path"].as_posix() in changed_paths
    assert any(item.path == "agent.planner.model" for file in preview.files for item in file.items)
    assert any(item.path == "categories.quick.variant" for file in preview.files for item in file.items)


def test_preview_rejects_invalid_strength(sample_workspace: dict[str, Path]) -> None:
    manager = make_manager(sample_workspace)

    with pytest.raises(ValueError, match="strength"):
        manager.preview_changes(
            [
                {
                    "targetId": "omo:agent:atlas",
                    "provider": "OpenAI",
                    "model": "gpt-5.4-mini",
                    "strength": "xhigh",
                }
            ]
        )


def test_apply_writes_backup_and_updates_only_target_fields(sample_workspace: dict[str, Path]) -> None:
    manager = make_manager(sample_workspace)

    result = manager.apply_changes(
        [
            {
                "targetId": "opencode:agent:planner",
                "provider": "Anthropic",
                "model": "claude-sonnet-4",
                "strength": "high",
            }
        ]
    )

    opencode_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    assert opencode_payload["agent"]["planner"]["model"] == "Anthropic/claude-sonnet-4"
    assert "variant" not in opencode_payload["agent"]["planner"]
    assert opencode_payload["agent"]["general"]["model"] == "OpenAI/gpt-5.4-mini"
    assert len(result.backups) == 1
    assert Path(result.backups[0]).exists()


def test_opencode_agent_strength_is_written_as_options_not_variant(sample_workspace: dict[str, Path]) -> None:
    manager = make_manager(sample_workspace)

    manager.apply_changes(
        [
            {
                "targetId": "opencode:agent:planner",
                "provider": "OpenAI",
                "model": "gpt-5.4",
                "strength": "low",
            }
        ]
    )

    opencode_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    planner = opencode_payload["agent"]["planner"]
    assert "variant" not in planner
    assert planner["options"]["reasoningEffort"] == "low"
    assert planner["reasoningEffort"] == "low"


def test_opencode_agent_target_names_may_contain_colons(sample_workspace: dict[str, Path]) -> None:
    opencode_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    opencode_payload["agent"]["pua:cto-p10"] = {
        "model": "OpenAI/gpt-5.4",
        "mode": "primary",
        "options": {"reasoningEffort": "low"},
    }
    sample_workspace["opencode_path"].write_text(
        json.dumps(opencode_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    manager = make_manager(sample_workspace)

    result = manager.apply_changes(
        [
            {
                "targetId": "opencode:agent:pua:cto-p10",
                "provider": "OpenAI",
                "model": "gpt-5.4",
                "strength": "high",
            }
        ]
    )

    updated_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    assert result.applied_files == [sample_workspace["opencode_path"].as_posix()]
    assert updated_payload["agent"]["pua:cto-p10"]["options"]["reasoningEffort"] == "high"
    assert "cto-p10" not in updated_payload["agent"]


def test_opencode_agent_model_without_variants_removes_strength_options(sample_workspace: dict[str, Path]) -> None:
    opencode_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    opencode_payload["provider"]["OpenAI"]["models"]["plain-model"] = {"name": "Plain Model"}
    opencode_payload["agent"]["planner"]["options"] = {
        "reasoningEffort": "high",
        "reasoningSummary": "auto",
        "textVerbosity": "low",
        "customOption": "keep-me",
    }
    opencode_payload["agent"]["planner"]["variant"] = "high"
    sample_workspace["opencode_path"].write_text(
        json.dumps(opencode_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    manager = make_manager(sample_workspace)

    preview = manager.preview_changes(
        [
            {
                "targetId": "opencode:agent:planner",
                "provider": "OpenAI",
                "model": "plain-model",
                "strength": None,
            }
        ]
    )

    assert any(item.path == "agent.planner.options.reasoningEffort" and item.new_value is None for file in preview.files for item in file.items)
    assert any(item.path == "agent.planner.options.reasoningSummary" and item.new_value is None for file in preview.files for item in file.items)
    assert any(item.path == "agent.planner.options.textVerbosity" and item.new_value is None for file in preview.files for item in file.items)

    manager.apply_changes(
        [
            {
                "targetId": "opencode:agent:planner",
                "provider": "OpenAI",
                "model": "plain-model",
                "strength": None,
            }
        ]
    )

    updated_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    planner = updated_payload["agent"]["planner"]
    assert planner["model"] == "OpenAI/plain-model"
    assert "variant" not in planner
    assert "reasoningEffort" not in planner
    assert planner["options"] == {"customOption": "keep-me"}


def test_opencode_agent_variant_switch_removes_stale_strength_options(sample_workspace: dict[str, Path]) -> None:
    opencode_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    opencode_payload["provider"]["OpenAI"]["models"]["gpt-5.4"]["variants"]["rich"] = {
        "reasoningEffort": "high",
        "reasoningSummary": "auto",
        "textVerbosity": "low",
    }
    opencode_payload["provider"]["OpenAI"]["models"]["gpt-5.4"]["variants"]["simple"] = {
        "reasoningEffort": "low",
    }
    opencode_payload["agent"]["planner"]["variant"] = "rich"
    opencode_payload["agent"]["planner"]["reasoningEffort"] = "high"
    opencode_payload["agent"]["planner"]["options"] = {
        "reasoningEffort": "high",
        "reasoningSummary": "auto",
        "textVerbosity": "low",
        "customOption": "keep-me",
    }
    sample_workspace["opencode_path"].write_text(
        json.dumps(opencode_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    manager = make_manager(sample_workspace)

    preview = manager.preview_changes(
        [
            {
                "targetId": "opencode:agent:planner",
                "provider": "OpenAI",
                "model": "gpt-5.4",
                "strength": "simple",
            }
        ]
    )

    assert any(item.path == "agent.planner.options.reasoningSummary" and item.new_value is None for file in preview.files for item in file.items)
    assert any(item.path == "agent.planner.options.textVerbosity" and item.new_value is None for file in preview.files for item in file.items)

    manager.apply_changes(
        [
            {
                "targetId": "opencode:agent:planner",
                "provider": "OpenAI",
                "model": "gpt-5.4",
                "strength": "simple",
            }
        ]
    )

    updated_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    planner = updated_payload["agent"]["planner"]
    assert planner["reasoningEffort"] == "low"
    assert planner["options"] == {
        "reasoningEffort": "low",
        "customOption": "keep-me",
    }


def test_opencode_agent_variant_without_reasoning_effort_removes_root_strength(sample_workspace: dict[str, Path]) -> None:
    opencode_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    opencode_payload["provider"]["OpenAI"]["models"]["gpt-5.4"]["variants"]["quiet"] = {
        "textVerbosity": "low",
    }
    opencode_payload["agent"]["planner"]["reasoningEffort"] = "high"
    opencode_payload["agent"]["planner"]["options"] = {
        "reasoningEffort": "high",
        "customOption": "keep-me",
    }
    sample_workspace["opencode_path"].write_text(
        json.dumps(opencode_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    manager = make_manager(sample_workspace)

    preview = manager.preview_changes(
        [
            {
                "targetId": "opencode:agent:planner",
                "provider": "OpenAI",
                "model": "gpt-5.4",
                "strength": "quiet",
            }
        ]
    )

    assert any(item.path == "agent.planner.reasoningEffort" and item.new_value is None for file in preview.files for item in file.items)
    assert any(item.path == "agent.planner.options.reasoningEffort" and item.new_value is None for file in preview.files for item in file.items)
    assert any(item.path == "agent.planner.options.textVerbosity" and item.new_value == "low" for file in preview.files for item in file.items)

    manager.apply_changes(
        [
            {
                "targetId": "opencode:agent:planner",
                "provider": "OpenAI",
                "model": "gpt-5.4",
                "strength": "quiet",
            }
        ]
    )

    updated_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    planner = updated_payload["agent"]["planner"]
    assert "reasoningEffort" not in planner
    assert planner["options"] == {
        "textVerbosity": "low",
        "customOption": "keep-me",
    }


def test_overview_reads_opencode_agent_strength_from_options(sample_workspace: dict[str, Path]) -> None:
    opencode_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    planner = opencode_payload["agent"]["planner"]
    planner.pop("variant", None)
    planner.pop("reasoningEffort", None)
    planner["options"] = {"reasoningEffort": "high"}
    sample_workspace["opencode_path"].write_text(json.dumps(opencode_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    manager = make_manager(sample_workspace)

    overview = manager.get_overview()

    target = next(target for target in overview.targets if target.id == "opencode:agent:planner")
    assert target.current_strength == "high"


def test_opencode_default_model_apply_removes_legacy_root_variant(sample_workspace: dict[str, Path]) -> None:
    opencode_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    opencode_payload["variant"] = "high"
    sample_workspace["opencode_path"].write_text(json.dumps(opencode_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    manager = make_manager(sample_workspace)

    manager.apply_changes(
        [
            {
                "targetId": "opencode:default:model",
                "provider": "Anthropic",
                "model": "claude-sonnet-4",
                "strength": "high",
            }
        ]
    )

    updated_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    assert updated_payload["model"] == "Anthropic/claude-sonnet-4"
    assert "variant" not in updated_payload


def test_reload_fails_on_corrupt_json(sample_workspace: dict[str, Path]) -> None:
    sample_workspace["opencode_path"].write_text("{invalid json", encoding="utf-8")
    manager = make_manager(sample_workspace)

    with pytest.raises(ValueError, match="Failed to parse"):
        manager.get_overview()


def test_visibility_settings_can_override_default_visibility_and_kind(sample_workspace: dict[str, Path]) -> None:
    manager = make_manager(sample_workspace)

    settings = manager.get_visibility_settings()
    assert any(rule.target_id == "opencode:agent:build" and rule.visible is False for rule in settings.visibility_rules)
    assert any(
        rule.target_id == "omo:subagent:librarian" and rule.kind_override == "subagent"
        for rule in settings.visibility_rules
    )

    manager.save_visibility_settings(
        [
            {
                "targetId": "opencode:agent:build",
                "visible": True,
                "kindOverride": None,
            },
            {
                "targetId": "omo:agent:atlas",
                "visible": True,
                "kindOverride": "subagent",
            },
        ]
    )

    overview = manager.get_overview()
    assert any(target.id == "opencode:agent:build" for target in overview.targets)
    atlas = next(target for target in overview.targets if target.id == "omo:agent:atlas")
    assert atlas.kind == "subagent"


def test_provider_preview_and_apply_support_add_update_and_delete(sample_workspace: dict[str, Path]) -> None:
    manager = make_manager(sample_workspace)

    providers = manager.get_provider_settings().providers
    updated = [
        provider.model_copy(deep=True)
        for provider in providers
        if provider.id != "Anthropic"
    ]
    openai = next(provider for provider in updated if provider.id == "OpenAI")
    openai.options["baseURL"] = "https://example.test/v1"
    openai.models[0].variants["turbo"] = {"reasoningEffort": "high"}
    updated.append(
        {
            "id": "Custom",
            "npm": "@ai-sdk/openai-compatible",
            "options": {"apiKey": "test-key", "baseURL": "https://custom.test/v1"},
            "models": [
                {
                    "id": "custom-model",
                    "name": "Custom Model",
                    "limit": {"context": 128000, "output": 8192},
                    "cost": {"input": 1, "output": 2},
                    "options": {"reasoningEffort": "medium"},
                    "maxTokens": 8192,
                    "variants": {"medium": {"reasoningEffort": "medium"}},
                }
            ],
        }
    )

    preview = manager.preview_provider_settings(updated)
    assert any(item.path == "provider.OpenAI.options.baseURL" for file in preview.files for item in file.items)
    assert any(
        item.path == "provider.OpenAI.models.gpt-5.4.variants.turbo.reasoningEffort"
        for file in preview.files
        for item in file.items
    )
    assert any(item.path.startswith("provider.Anthropic.") for file in preview.files for item in file.items)
    assert any(item.path.startswith("provider.Custom.") for file in preview.files for item in file.items)

    result = manager.apply_provider_settings(updated)
    opencode_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    assert opencode_payload["provider"]["OpenAI"]["options"]["baseURL"] == "https://example.test/v1"
    assert opencode_payload["provider"]["OpenAI"]["models"]["gpt-5.4"]["variants"]["turbo"]["reasoningEffort"] == "high"
    assert "Anthropic" not in opencode_payload["provider"]
    assert "Custom" in opencode_payload["provider"]
    assert len(result.backups) == 1


def test_split_overview_uses_omo_opencode_providers(split_workspace: dict[str, Path]) -> None:
    manager = make_manager(split_workspace)

    overview = manager.get_overview()

    assert overview.config_paths["opencode"] == split_workspace["opencode_path"].as_posix()
    assert overview.config_paths["omoOpencode"] == split_workspace["omo_opencode_path"].as_posix()
    assert overview.config_paths["omo"] == split_workspace["omo_path"].as_posix()
    assert [provider.id for provider in overview.providers_by_source["opencode"]] == ["Anthropic", "OpenAI"]
    assert [provider.id for provider in overview.providers_by_source["omo"]] == ["OmoOnly"]

    atlas = next(target for target in overview.targets if target.id == "omo:agent:atlas")
    assert atlas.current_provider == "OmoOnly"
    assert atlas.available_providers == ["OmoOnly"]


def test_split_omo_model_apply_writes_only_split_oh_my_openagent(split_workspace: dict[str, Path]) -> None:
    manager = make_manager(split_workspace)
    oc_before = split_workspace["opencode_path"].read_text(encoding="utf-8")
    omo_oc_before = split_workspace["omo_opencode_path"].read_text(encoding="utf-8")

    result = manager.apply_changes(
        [
            {
                "targetId": "omo:agent:atlas",
                "provider": "OmoOnly",
                "model": "omo-model",
                "strength": "deep",
            }
        ]
    )

    assert result.applied_files == [split_workspace["omo_path"].as_posix()]
    assert split_workspace["opencode_path"].read_text(encoding="utf-8") == oc_before
    assert split_workspace["omo_opencode_path"].read_text(encoding="utf-8") == omo_oc_before
    omo_payload = json.loads(split_workspace["omo_path"].read_text(encoding="utf-8"))
    assert omo_payload["agents"]["atlas"]["model"] == "OmoOnly/omo-model"
    assert omo_payload["agents"]["atlas"]["variant"] == "deep"


def test_omo_category_with_agent_name_writes_category_not_agent(sample_workspace: dict[str, Path]) -> None:
    omo_payload = json.loads(sample_workspace["omo_path"].read_text(encoding="utf-8"))
    omo_payload["agents"]["explore"]["model"] = "OpenAI/gpt-5.4"
    omo_payload["agents"]["explore"]["variant"] = "xhigh"
    omo_payload["categories"]["explore"] = {
        "model": "OpenAI/gpt-5.4",
        "variant": "medium",
    }
    sample_workspace["omo_path"].write_text(json.dumps(omo_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    manager = make_manager(sample_workspace)

    preview = manager.preview_changes(
        [
            {
                "targetId": "omo:category:explore",
                "provider": "OpenAI",
                "model": "gpt-5.4",
                "strength": "xhigh",
            }
        ]
    )

    assert any(
        item.path == "categories.explore.variant"
        and item.old_value == "medium"
        and item.new_value == "xhigh"
        for file in preview.files
        for item in file.items
    )
    assert not any(item.path == "agents.explore.variant" for file in preview.files for item in file.items)


def test_omo_target_names_may_contain_colons(sample_workspace: dict[str, Path]) -> None:
    omo_payload = json.loads(sample_workspace["omo_path"].read_text(encoding="utf-8"))
    omo_payload["agents"]["agent:withcolon"] = {
        "model": "OpenAI/gpt-5.4",
        "variant": "medium",
    }
    omo_payload["categories"]["cat:withcolon"] = {
        "model": "OpenAI/gpt-5.4",
        "variant": "medium",
    }
    sample_workspace["omo_path"].write_text(json.dumps(omo_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    manager = make_manager(sample_workspace)

    preview = manager.preview_changes(
        [
            {
                "targetId": "omo:agent:agent:withcolon",
                "provider": "OpenAI",
                "model": "gpt-5.4",
                "strength": "xhigh",
            },
            {
                "targetId": "omo:category:cat:withcolon",
                "provider": "OpenAI",
                "model": "gpt-5.4",
                "strength": "xhigh",
            },
        ]
    )

    assert any(item.path == "agents.agent:withcolon.variant" for file in preview.files for item in file.items)
    assert any(item.path == "categories.cat:withcolon.variant" for file in preview.files for item in file.items)


def test_split_provider_apply_writes_only_omo_opencode(split_workspace: dict[str, Path]) -> None:
    manager = make_manager(split_workspace)
    oc_before = split_workspace["opencode_path"].read_text(encoding="utf-8")
    oh_my_before = split_workspace["omo_path"].read_text(encoding="utf-8")

    providers = manager.get_provider_settings(source="omo").providers
    providers[0].options["baseURL"] = "https://omo-provider.test/v1"

    result = manager.apply_provider_settings(providers, source="omo")

    assert result.applied_files == [split_workspace["omo_opencode_path"].as_posix()]
    assert split_workspace["opencode_path"].read_text(encoding="utf-8") == oc_before
    assert split_workspace["omo_path"].read_text(encoding="utf-8") == oh_my_before
    omo_opencode_payload = json.loads(split_workspace["omo_opencode_path"].read_text(encoding="utf-8"))
    assert omo_opencode_payload["provider"]["OmoOnly"]["options"]["baseURL"] == "https://omo-provider.test/v1"


def test_single_agent_settings_only_exposes_opencode_source(sample_workspace: dict[str, Path]) -> None:
    manager = make_manager(sample_workspace)

    settings = manager.get_agent_settings()

    assert settings.available_sources == ["opencode"]
    assert settings.config_paths["opencode"] == sample_workspace["opencode_path"].as_posix()
    assert {agent.source for agent in settings.agents} == {"opencode"}
    assert any(agent.id == "planner" for agent in settings.agents)
    assert all(agent.id != "atlas" for agent in settings.agents)


def test_split_agent_settings_reads_tab_agents_from_both_opencode_roots(split_workspace: dict[str, Path]) -> None:
    manager = make_manager(split_workspace)

    settings = manager.get_agent_settings()
    agents_by_source = {
        source: sorted(agent.id for agent in settings.agents if agent.source == source)
        for source in settings.available_sources
    }

    assert settings.available_sources == ["opencode", "omo"]
    assert settings.config_paths["opencode"] == split_workspace["opencode_path"].as_posix()
    assert settings.config_paths["omoOpencode"] == split_workspace["omo_opencode_path"].as_posix()
    assert "planner" in agents_by_source["opencode"]
    assert "planner" in agents_by_source["omo"]
    assert "OmoTabOnly" in agents_by_source["omo"]
    assert "atlas" not in agents_by_source["omo"]


def test_split_agent_apply_writes_only_omo_opencode(split_workspace: dict[str, Path]) -> None:
    manager = make_manager(split_workspace)
    oc_before = split_workspace["opencode_path"].read_text(encoding="utf-8")
    oh_my_before = split_workspace["omo_path"].read_text(encoding="utf-8")
    omo_opencode_payload = json.loads(split_workspace["omo_opencode_path"].read_text(encoding="utf-8"))
    omo_opencode_payload["agent"]["OmoTabOnly"]["variant"] = "deep"
    split_workspace["omo_opencode_path"].write_text(
        json.dumps(omo_opencode_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    agents = manager.get_agent_settings().agents
    omo_agent = next(agent for agent in agents if agent.source == "omo" and agent.id == "OmoTabOnly")
    omo_agent.description = "Updated OMO tab"

    result = manager.apply_agent_settings(agents)

    assert result.applied_files == [split_workspace["omo_opencode_path"].as_posix()]
    assert split_workspace["opencode_path"].read_text(encoding="utf-8") == oc_before
    assert split_workspace["omo_path"].read_text(encoding="utf-8") == oh_my_before
    updated_omo_opencode_payload = json.loads(split_workspace["omo_opencode_path"].read_text(encoding="utf-8"))
    assert updated_omo_opencode_payload["agent"]["OmoTabOnly"]["description"] == "Updated OMO tab"
    assert "variant" not in updated_omo_opencode_payload["agent"]["OmoTabOnly"]
    assert updated_omo_opencode_payload["agent"]["OmoTabOnly"]["options"]["reasoningEffort"] == "high"


def test_agent_settings_apply_removes_stale_opencode_strength_options(sample_workspace: dict[str, Path]) -> None:
    opencode_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    opencode_payload["provider"]["OpenAI"]["models"]["gpt-5.4"]["variants"]["simple"] = {
        "reasoningEffort": "low",
    }
    opencode_payload["agent"]["planner"] = {
        "model": "OpenAI/gpt-5.4",
        "variant": "simple",
        "mode": "primary",
        "options": {
            "reasoningEffort": "high",
            "reasoningSummary": "auto",
            "textVerbosity": "low",
            "customOption": "keep-me",
        },
    }
    sample_workspace["opencode_path"].write_text(
        json.dumps(opencode_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    manager = make_manager(sample_workspace)
    agents = manager.get_agent_settings().agents

    preview = manager.preview_agent_settings(agents)

    assert any(item.path == "agent.planner.options.reasoningEffort" and item.new_value == "low" for file in preview.files for item in file.items)
    assert any(item.path == "agent.planner.options.reasoningSummary" and item.new_value is None for file in preview.files for item in file.items)
    assert any(item.path == "agent.planner.options.textVerbosity" and item.new_value is None for file in preview.files for item in file.items)

    manager.apply_agent_settings(agents)

    updated_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    planner = updated_payload["agent"]["planner"]
    assert "variant" not in planner
    assert planner["options"] == {
        "reasoningEffort": "low",
        "customOption": "keep-me",
    }


def test_agent_settings_apply_removes_strength_options_when_legacy_variant_has_no_options(sample_workspace: dict[str, Path]) -> None:
    opencode_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    opencode_payload["provider"]["OpenAI"]["models"]["plain-model"] = {"name": "Plain Model"}
    opencode_payload["agent"]["planner"] = {
        "model": "OpenAI/plain-model",
        "variant": "missing",
        "mode": "primary",
        "reasoningEffort": "high",
        "options": {
            "reasoningEffort": "high",
            "reasoningSummary": "auto",
            "textVerbosity": "low",
            "customOption": "keep-me",
        },
    }
    sample_workspace["opencode_path"].write_text(
        json.dumps(opencode_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    manager = make_manager(sample_workspace)
    agents = manager.get_agent_settings().agents

    preview = manager.preview_agent_settings(agents)

    assert any(item.path == "agent.planner.reasoningEffort" and item.new_value is None for file in preview.files for item in file.items)
    assert any(item.path == "agent.planner.options.reasoningEffort" and item.new_value is None for file in preview.files for item in file.items)
    assert any(item.path == "agent.planner.options.reasoningSummary" and item.new_value is None for file in preview.files for item in file.items)
    assert any(item.path == "agent.planner.options.textVerbosity" and item.new_value is None for file in preview.files for item in file.items)

    manager.apply_agent_settings(agents)

    updated_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    planner = updated_payload["agent"]["planner"]
    assert "variant" not in planner
    assert "reasoningEffort" not in planner
    assert planner["options"] == {"customOption": "keep-me"}
