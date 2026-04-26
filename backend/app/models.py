from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProviderModelInfo(BaseModel):
    id: str
    label: str
    strength_options: List[str] = Field(default_factory=list, alias="strengthOptions")

    model_config = {"populate_by_name": True}


class ProviderInfo(BaseModel):
    id: str
    label: str
    models: List[ProviderModelInfo]


class TargetInfo(BaseModel):
    id: str
    source: str
    kind: str
    name: str
    visible: bool = True
    current_provider: Optional[str] = Field(default=None, alias="currentProvider")
    current_model: Optional[str] = Field(default=None, alias="currentModel")
    current_strength: Optional[str] = Field(default=None, alias="currentStrength")
    available_providers: List[str] = Field(default_factory=list, alias="availableProviders")
    custom_tab: Optional[str] = Field(default=None, alias="customTab")

    model_config = {"populate_by_name": True}


class OverviewResponse(BaseModel):
    providers: List[ProviderInfo]
    providers_by_source: Dict[str, List[ProviderInfo]] = Field(default_factory=dict, alias="providersBySource")
    targets: List[TargetInfo]
    config_paths: Dict[str, str] = Field(alias="configPaths")
    loaded_at: str = Field(alias="loadedAt")
    custom_tabs: List[str] = Field(default_factory=list, alias="customTabs")

    model_config = {"populate_by_name": True}


class DraftChange(BaseModel):
    target_id: str = Field(alias="targetId")
    provider: str
    model: str
    strength: Optional[str] = None

    model_config = {"populate_by_name": True}


class DiffItem(BaseModel):
    path: str
    old_value: Any = Field(alias="oldValue")
    new_value: Any = Field(alias="newValue")

    model_config = {"populate_by_name": True}


class FileDiff(BaseModel):
    file_path: str = Field(alias="filePath")
    items: List[DiffItem]

    model_config = {"populate_by_name": True}


class PreviewResponse(BaseModel):
    files: List[FileDiff]


class ApplyResponse(BaseModel):
    applied_files: List[str] = Field(alias="appliedFiles")
    backups: List[str]

    model_config = {"populate_by_name": True}


class ChangeRequest(BaseModel):
    changes: List[DraftChange]


class VisibilityRule(BaseModel):
    target_id: str = Field(alias="targetId")
    visible: bool
    kind_override: Optional[str] = Field(default=None, alias="kindOverride")
    tab_override: Optional[str] = Field(default=None, alias="tabOverride")

    model_config = {"populate_by_name": True}


class VisibilitySettingsResponse(BaseModel):
    targets: List[TargetInfo]
    visibility_rules: List[VisibilityRule] = Field(alias="visibilityRules")
    custom_tabs: List[str] = Field(default_factory=list, alias="customTabs")

    model_config = {"populate_by_name": True}


class VisibilitySettingsRequest(BaseModel):
    visibility_rules: List[VisibilityRule] = Field(alias="visibilityRules")
    custom_tabs: List[str] = Field(default_factory=list, alias="customTabs")

    model_config = {"populate_by_name": True}


class ProviderEditableModel(BaseModel):
    id: str
    name: Optional[str] = None
    limit: Dict[str, Any] = Field(default_factory=dict)
    cost: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)
    max_tokens: Optional[int] = Field(default=None, alias="maxTokens")
    variants: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class ProviderEditableRecord(BaseModel):
    id: str
    npm: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)
    models: List[ProviderEditableModel] = Field(default_factory=list)


class ProviderSettingsResponse(BaseModel):
    providers: List[ProviderEditableRecord]
    source: str = "opencode"
    config_path: Optional[str] = Field(default=None, alias="configPath")
    available_sources: List[str] = Field(default_factory=lambda: ["opencode"], alias="availableSources")

    model_config = {"populate_by_name": True}


class ProviderSettingsRequest(BaseModel):
    providers: List[ProviderEditableRecord]


class AgentEditableRecord(BaseModel):
    id: str
    original_id: Optional[str] = Field(default=None, alias="originalId")
    source: str = "opencode"  # "opencode" or "omo"
    description: Optional[str] = None
    color: Optional[str] = None
    prompt: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class AgentSettingsResponse(BaseModel):
    agents: List[AgentEditableRecord]
    available_sources: List[str] = Field(default_factory=lambda: ["opencode"], alias="availableSources")
    config_paths: Dict[str, str] = Field(default_factory=dict, alias="configPaths")

    model_config = {"populate_by_name": True}


class AgentSettingsRequest(BaseModel):
    agents: List[AgentEditableRecord]
