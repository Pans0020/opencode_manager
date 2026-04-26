from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app, default_config_paths


def make_client(sample_workspace: dict[str, Path]) -> TestClient:
    app = create_app(
        {
            "opencode_path": sample_workspace["opencode_path"],
            "omo_opencode_path": sample_workspace.get("omo_opencode_path"),
            "omo_path": sample_workspace["omo_path"],
            "settings_path": sample_workspace["settings_path"],
        }
    )
    return TestClient(app)


def test_health_endpoint(sample_workspace: dict[str, Path]) -> None:
    client = make_client(sample_workspace)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_overview_endpoint(sample_workspace: dict[str, Path]) -> None:
    client = make_client(sample_workspace)

    response = client.get("/api/config/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["configPaths"]["opencode"] == sample_workspace["opencode_path"].as_posix()
    assert any(target["id"] == "omo:agent:sisyphus" for target in payload["targets"])


def test_preview_endpoint(sample_workspace: dict[str, Path]) -> None:
    client = make_client(sample_workspace)

    response = client.post(
        "/api/config/preview",
        json={
            "changes": [
                {
                    "targetId": "opencode:agent:planner",
                    "provider": "Anthropic",
                    "model": "claude-sonnet-4",
                    "strength": "high",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["files"][0]["items"][0]["path"] == "agent.planner.model"


def test_apply_endpoint_returns_backups(sample_workspace: dict[str, Path]) -> None:
    client = make_client(sample_workspace)

    response = client.post(
        "/api/config/apply",
        json={
            "changes": [
                {
                    "targetId": "omo:agent:atlas",
                    "provider": "OpenAI",
                    "model": "gpt-5.4",
                    "strength": "high",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["appliedFiles"] == [sample_workspace["omo_path"].as_posix()]
    assert len(payload["backups"]) == 1


def test_visibility_settings_endpoints(sample_workspace: dict[str, Path]) -> None:
    client = make_client(sample_workspace)

    response = client.get("/api/settings/visibility")
    assert response.status_code == 200
    payload = response.json()
    assert any(rule["targetId"] == "opencode:agent:build" for rule in payload["visibilityRules"])

    save_response = client.post(
        "/api/settings/visibility",
        json={
            "visibilityRules": [
                {
                    "targetId": "opencode:agent:build",
                    "visible": True,
                    "kindOverride": None,
                }
            ]
        },
    )
    assert save_response.status_code == 200


def test_provider_management_endpoints(sample_workspace: dict[str, Path]) -> None:
    client = make_client(sample_workspace)

    response = client.get("/api/providers")
    assert response.status_code == 200
    payload = response.json()
    assert any(provider["id"] == "OpenAI" for provider in payload["providers"])

    preview_response = client.post(
        "/api/providers/preview",
        json={
            "providers": [
                {
                    "id": "OpenAI",
                    "npm": None,
                    "options": {"baseURL": "https://preview.test/v1"},
                    "models": [],
                }
            ]
        },
    )
    assert preview_response.status_code == 200


def test_default_config_paths_detects_split_omo_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_root = tmp_path / ".config"
    (config_root / "opencode").mkdir(parents=True)
    omo_root = config_root / "opencode-omo"
    omo_root.mkdir()
    (omo_root / "opencode.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    paths = default_config_paths()

    assert paths["opencode_path"] == config_root / "opencode" / "opencode.json"
    assert paths["omo_opencode_path"] == omo_root / "opencode.json"
    assert paths["omo_path"] == omo_root / "oh-my-openagent.json"


def test_provider_management_endpoint_supports_omo_source(split_workspace: dict[str, Path]) -> None:
    client = make_client(split_workspace)

    response = client.get("/api/providers?source=omo")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "omo"
    assert payload["configPath"] == split_workspace["omo_opencode_path"].as_posix()
    assert payload["availableSources"] == ["opencode", "omo"]
    assert [provider["id"] for provider in payload["providers"]] == ["OmoOnly"]


def test_agent_management_endpoint_supports_split_sources(split_workspace: dict[str, Path]) -> None:
    client = make_client(split_workspace)

    response = client.get("/api/agents")

    assert response.status_code == 200
    payload = response.json()
    assert payload["availableSources"] == ["opencode", "omo"]
    assert payload["configPaths"]["opencode"] == split_workspace["opencode_path"].as_posix()
    assert payload["configPaths"]["omoOpencode"] == split_workspace["omo_opencode_path"].as_posix()
    assert any(agent["source"] == "omo" and agent["id"] == "OmoTabOnly" for agent in payload["agents"])
    assert not any(agent["source"] == "omo" and agent["id"] == "atlas" for agent in payload["agents"])
