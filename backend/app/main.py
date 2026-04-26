from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    ApplyResponse,
    ChangeRequest,
    OverviewResponse,
    PreviewResponse,
    ProviderSettingsRequest,
    ProviderSettingsResponse,
    VisibilitySettingsRequest,
    VisibilitySettingsResponse,
    AgentSettingsRequest,
    AgentSettingsResponse,
)
from app.services.config_manager import ConfigManager


def default_config_paths() -> Dict[str, Path]:
    config_base = Path.home() / ".config"
    config_root = config_base / "opencode"
    split_omo_root = config_base / "opencode-omo"
    omo_root = (
        split_omo_root
        if split_omo_root.exists()
        and ((split_omo_root / "opencode.json").exists() or (split_omo_root / "oh-my-openagent.json").exists())
        else config_root
    )
    return {
        "opencode_path": config_root / "opencode.json",
        "omo_opencode_path": omo_root / "opencode.json",
        "omo_path": omo_root / "oh-my-openagent.json",
        "settings_path": config_root / "agent-model-manager.json",
    }


def create_app(config: Optional[Dict[str, Any]] = None) -> FastAPI:
    app = FastAPI(title="Agent Model Manager API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    settings = default_config_paths()
    if config:
        settings.update({key: value for key, value in config.items() if value is not None})

    manager = ConfigManager(
        opencode_path=Path(settings["opencode_path"]),
        omo_opencode_path=Path(settings["omo_opencode_path"]),
        omo_path=Path(settings["omo_path"]),
        settings_path=Path(settings["settings_path"]),
    )

    @app.get("/api/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/config/overview", response_model=OverviewResponse)
    def overview() -> OverviewResponse:
        try:
            return manager.get_overview()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/config/preview", response_model=PreviewResponse)
    def preview(request: ChangeRequest) -> PreviewResponse:
        try:
            return manager.preview_changes(request.changes)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/config/apply", response_model=ApplyResponse)
    def apply(request: ChangeRequest) -> ApplyResponse:
        try:
            return manager.apply_changes(request.changes)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/config/reload", response_model=OverviewResponse)
    def reload() -> OverviewResponse:
        try:
            return manager.reload()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/settings/visibility", response_model=VisibilitySettingsResponse)
    def visibility_settings() -> VisibilitySettingsResponse:
        try:
            return manager.get_visibility_settings()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/settings/visibility", response_model=VisibilitySettingsResponse)
    def save_visibility_settings(request: VisibilitySettingsRequest) -> VisibilitySettingsResponse:
        try:
            return manager.save_visibility_settings(request.visibility_rules, request.custom_tabs)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/providers", response_model=ProviderSettingsResponse)
    def providers(source: str = "opencode") -> ProviderSettingsResponse:
        try:
            return manager.get_provider_settings(source=source)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/providers/preview", response_model=PreviewResponse)
    def preview_providers(request: ProviderSettingsRequest, source: str = "opencode") -> PreviewResponse:
        try:
            return manager.preview_provider_settings(request.providers, source=source)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/providers/apply", response_model=ApplyResponse)
    def apply_providers(request: ProviderSettingsRequest, source: str = "opencode") -> ApplyResponse:
        try:
            return manager.apply_provider_settings(request.providers, source=source)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/agents", response_model=AgentSettingsResponse)
    def agents() -> AgentSettingsResponse:
        try:
            return manager.get_agent_settings()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/agents/preview", response_model=PreviewResponse)
    def preview_agents(request: AgentSettingsRequest) -> PreviewResponse:
        try:
            return manager.preview_agent_settings(request.agents)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/agents/apply", response_model=ApplyResponse)
    def apply_agents(request: AgentSettingsRequest) -> ApplyResponse:
        try:
            return manager.apply_agent_settings(request.agents)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()
