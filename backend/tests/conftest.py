from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture()
def sample_workspace(tmp_path: Path) -> dict[str, Path]:
    config_dir = tmp_path / ".config" / "opencode"
    config_dir.mkdir(parents=True)

    opencode_path = config_dir / "opencode.json"
    omo_path = config_dir / "oh-my-openagent.json"
    settings_path = config_dir / "agent-model-manager.json"

    opencode_payload = {
        "$schema": "https://opencode.ai/config.json",
        "model": "OpenAI/gpt-5.4",
        "small_model": "OpenAI/gpt-5.4-mini",
        "agent": {
            "build": {"model": "OpenAI/gpt-5.4", "mode": "primary"},
            "general": {"model": "OpenAI/gpt-5.4-mini", "mode": "subagent"},
            "compaction": {"model": "OpenAI/gpt-5.4-mini", "mode": "primary"},
            "Sisyphus-Junior": {"model": "OpenAI/gpt-5.4-mini", "mode": "primary"},
            "planner": {
                "model": "OpenAI/gpt-5.4",
                "reasoningEffort": "high",
                "mode": "primary",
            },
        },
        "provider": {
            "OpenAI": {
                "models": {
                    "gpt-5.4": {
                        "name": "GPT-5.4",
                        "options": {"reasoningEffort": "medium"},
                        "variants": {
                            "low": {"reasoningEffort": "low"},
                            "medium": {"reasoningEffort": "medium"},
                            "high": {"reasoningEffort": "high"},
                            "xhigh": {"reasoningEffort": "xhigh"},
                        },
                    },
                    "gpt-5.4-mini": {
                        "name": "GPT-5.4 Mini",
                        "options": {"reasoningEffort": "medium"},
                        "variants": {
                            "low": {"reasoningEffort": "low"},
                            "medium": {"reasoningEffort": "medium"},
                        },
                    },
                }
            },
            "Anthropic": {
                "models": {
                    "claude-sonnet-4": {
                        "name": "Claude Sonnet 4",
                        "variants": {
                            "low": {"reasoningEffort": "low"},
                            "high": {"reasoningEffort": "high"},
                        },
                    }
                }
            },
        },
    }

    omo_payload = {
        "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/oh-my-opencode.schema.json",
        "agents": {
            "sisyphus": {"model": "OpenAI/gpt-5.4", "variant": "xhigh"},
            "atlas": {"model": "OpenAI/gpt-5.4-mini", "variant": "medium"},
            "librarian": {"model": "OpenAI/gpt-5.4-mini", "variant": "medium"},
            "explore": {"model": "OpenAI/gpt-5.4-mini", "variant": "medium"},
        },
        "categories": {
            "quick": {"model": "OpenAI/gpt-5.4-mini", "variant": "medium"},
            "deep": {"model": "Anthropic/claude-sonnet-4", "variant": "high"},
        },
    }

    write_json(opencode_path, opencode_payload)
    write_json(omo_path, omo_payload)
    write_json(settings_path, {"visibilityRules": []})

    return {
        "root": tmp_path,
        "opencode_path": opencode_path,
        "omo_path": omo_path,
        "settings_path": settings_path,
    }


@pytest.fixture()
def split_workspace(sample_workspace: dict[str, Path]) -> dict[str, Path]:
    omo_config_dir = sample_workspace["root"] / ".config" / "opencode-omo"
    omo_config_dir.mkdir(parents=True)

    omo_opencode_path = omo_config_dir / "opencode.json"
    omo_path = omo_config_dir / "oh-my-openagent.json"

    oc_payload = json.loads(sample_workspace["opencode_path"].read_text(encoding="utf-8"))
    omo_opencode_payload = {
        **oc_payload,
        "model": "OmoOnly/omo-model",
        "small_model": "OmoOnly/omo-model",
        "agent": {
            **oc_payload["agent"],
            "OmoTabOnly": {
                "model": "OmoOnly/omo-model",
                "mode": "primary",
                "description": "Only in OMO opencode",
            },
        },
        "provider": {
            "OmoOnly": {
                "models": {
                    "omo-model": {
                        "name": "OMO Model",
                        "variants": {
                            "spark": {"reasoningEffort": "low"},
                            "deep": {"reasoningEffort": "high"},
                        },
                    }
                }
            }
        },
    }

    omo_payload = json.loads(sample_workspace["omo_path"].read_text(encoding="utf-8"))
    omo_payload["agents"]["atlas"]["model"] = "OmoOnly/omo-model"
    omo_payload["agents"]["atlas"]["variant"] = "spark"

    write_json(omo_opencode_path, omo_opencode_payload)
    write_json(omo_path, omo_payload)

    return {
        **sample_workspace,
        "omo_opencode_path": omo_opencode_path,
        "omo_path": omo_path,
    }
