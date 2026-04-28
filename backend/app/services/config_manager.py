from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from app.models import (
    ApplyResponse,
    DiffItem,
    DraftChange,
    FileDiff,
    OverviewResponse,
    ProviderEditableModel,
    ProviderEditableRecord,
    ProviderSettingsResponse,
    PreviewResponse,
    ProviderInfo,
    ProviderModelInfo,
    TargetInfo,
    VisibilityRule,
    VisibilitySettingsResponse,
    AgentEditableRecord,
    AgentSettingsResponse,
)

HIDDEN_OPENCODE_DEFAULTS = {"model", "small_model"}
HIDDEN_OPENCODE_AGENTS = {
    "compaction",
    "build",
    "general",
    "pua:cto-p10",
    "plan",
    "pua:senior-engineer-p7",
    "pua:tech-lead-p9",
    "summary",
    "superpowers:code-reviewer",
    "title",
    "Sisyphus-Junior",
}
OMO_SUBAGENT_AGENT_NAMES = {
    "librarian",
    "metis",
    "explore",
    "momus",
    "oracle",
    "multimodal-looker",
}
DEFAULT_SETTINGS_PAYLOAD = {"visibilityRules": [], "customTabs": []}


class ConfigManager:
    def __init__(
        self,
        opencode_path: Path,
        omo_path: Path,
        settings_path: Optional[Path] = None,
        omo_opencode_path: Optional[Path] = None,
    ) -> None:
        self.opencode_path = Path(opencode_path)
        self.omo_opencode_path = Path(omo_opencode_path) if omo_opencode_path else self.opencode_path
        self.omo_path = Path(omo_path)
        self.settings_path = Path(settings_path) if settings_path else self.opencode_path.parent / "agent-model-manager.json"

    def _load_opencode_payloads(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        opencode_payload = self._load_json(self.opencode_path)
        if self.omo_opencode_path == self.opencode_path:
            return opencode_payload, opencode_payload
        return opencode_payload, self._load_json(self.omo_opencode_path)

    def _provider_path_for_source(self, source: str) -> Path:
        if source == "opencode":
            return self.opencode_path
        if source == "omo":
            return self.omo_opencode_path
        raise ValueError("Unknown provider source: {0}".format(source))

    def _available_provider_sources(self) -> List[str]:
        if self.omo_opencode_path == self.opencode_path:
            return ["opencode"]
        return ["opencode", "omo"]

    def get_overview(self) -> OverviewResponse:
        opencode_payload, omo_opencode_payload = self._load_opencode_payloads()
        omo_payload = self._load_json(self.omo_path)
        providers = self._build_providers(opencode_payload)
        omo_providers = self._build_providers(omo_opencode_payload)
        raw_targets = self._build_targets(opencode_payload, omo_payload, providers, omo_providers)
        settings_payload = self._load_settings_payload()
        custom_tabs = settings_payload.get("customTabs", [])
        targets = self._apply_visibility_rules(raw_targets, self._resolve_visibility_rules(raw_targets, settings_payload))
        return OverviewResponse(
            providers=providers,
            providersBySource={
                "opencode": providers,
                "omo": omo_providers,
            },
            targets=targets,
            configPaths={
                "opencode": self.opencode_path.as_posix(),
                "omoOpencode": self.omo_opencode_path.as_posix(),
                "omo": self.omo_path.as_posix(),
            },
            loadedAt=datetime.now().isoformat(timespec="seconds"),
            customTabs=custom_tabs,
        )

    def reload(self) -> OverviewResponse:
        return self.get_overview()

    def get_visibility_settings(self) -> VisibilitySettingsResponse:
        opencode_payload, omo_opencode_payload = self._load_opencode_payloads()
        omo_payload = self._load_json(self.omo_path)
        providers = self._build_providers(opencode_payload)
        omo_providers = self._build_providers(omo_opencode_payload)
        targets = self._build_targets(opencode_payload, omo_payload, providers, omo_providers)
        settings_payload = self._load_settings_payload()
        custom_tabs = settings_payload.get("customTabs", [])
        return VisibilitySettingsResponse(
            targets=targets,
            visibilityRules=self._resolve_visibility_rules(targets, settings_payload),
            customTabs=custom_tabs,
        )

    def save_visibility_settings(
        self, rules: Union[List[VisibilityRule], List[Dict[str, Any]]], custom_tabs: Optional[List[str]] = None
    ) -> VisibilitySettingsResponse:
        opencode_payload, omo_opencode_payload = self._load_opencode_payloads()
        omo_payload = self._load_json(self.omo_path)
        providers = self._build_providers(opencode_payload)
        omo_providers = self._build_providers(omo_opencode_payload)
        targets = self._build_targets(opencode_payload, omo_payload, providers, omo_providers)
        validated = self._coerce_visibility_rules(rules, targets)
        
        settings_payload = self._load_settings_payload()
        if custom_tabs is None:
            custom_tabs = settings_payload.get("customTabs", [])
            
        payload = {
            "visibilityRules": [rule.model_dump(by_alias=True) for rule in validated],
            "customTabs": custom_tabs,
        }
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return VisibilitySettingsResponse(targets=targets, visibilityRules=validated, customTabs=custom_tabs)

    def get_provider_settings(self, source: str = "opencode") -> ProviderSettingsResponse:
        provider_path = self._provider_path_for_source(source)
        payload = self._load_json(provider_path)
        return ProviderSettingsResponse(
            providers=self._build_provider_records(payload),
            source=source,
            configPath=provider_path.as_posix(),
            availableSources=self._available_provider_sources(),
        )

    def preview_provider_settings(
        self, providers: Union[List[ProviderEditableRecord], List[Dict[str, Any]]], source: str = "opencode"
    ) -> PreviewResponse:
        provider_path, _, diffs = self._build_provider_preview(self._coerce_provider_records(providers), source)
        return PreviewResponse(
            files=[FileDiff(filePath=provider_path.as_posix(), items=diffs)] if diffs else []
        )

    def apply_provider_settings(
        self, providers: Union[List[ProviderEditableRecord], List[Dict[str, Any]]], source: str = "opencode"
    ) -> ApplyResponse:
        provider_path, mutated_payload, diffs = self._build_provider_preview(self._coerce_provider_records(providers), source)
        if not diffs:
            return ApplyResponse(appliedFiles=[], backups=[])

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = provider_path.with_name(f"{provider_path.name}.bak_{timestamp}")
        backup_path.write_text(provider_path.read_text(encoding="utf-8"), encoding="utf-8")
        provider_path.write_text(
            json.dumps(mutated_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return ApplyResponse(
            appliedFiles=[provider_path.as_posix()],
            backups=[backup_path.as_posix()],
        )

    def preview_changes(self, changes: Union[List[DraftChange], List[Dict[str, Any]]]) -> PreviewResponse:
        _, diff_map = self._build_mutation_preview(self._coerce_changes(changes))
        files = [
            FileDiff(filePath=path.as_posix(), items=items)
            for path, items in diff_map.items()
            if items
        ]
        return PreviewResponse(files=files)

    def apply_changes(self, changes: Union[List[DraftChange], List[Dict[str, Any]]]) -> ApplyResponse:
        mutated, diff_map = self._build_mutation_preview(self._coerce_changes(changes))

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backups: List[str] = []
        applied_files: List[str] = []

        for path, payload in mutated.items():
            if not diff_map[path]:
                continue
            backup_path = path.with_name(f"{path.name}.bak_{timestamp}")
            backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            backups.append(backup_path.as_posix())
            applied_files.append(path.as_posix())

        return ApplyResponse(appliedFiles=applied_files, backups=backups)

    def get_agent_settings(self) -> AgentSettingsResponse:
        opencode_payload, omo_opencode_payload = self._load_opencode_payloads()
        agents: List[AgentEditableRecord] = []
        agents.extend(self._build_agent_records(opencode_payload, "opencode"))
        if self.omo_opencode_path != self.opencode_path:
            agents.extend(self._build_agent_records(omo_opencode_payload, "omo"))
        return AgentSettingsResponse(
            agents=agents,
            availableSources=self._available_provider_sources(),
            configPaths={
                "opencode": self.opencode_path.as_posix(),
                "omoOpencode": self.omo_opencode_path.as_posix(),
            },
        )

    def preview_agent_settings(self, agents: Union[List[AgentEditableRecord], List[Dict[str, Any]]]) -> PreviewResponse:
        preview_items = self._build_agent_preview(self._coerce_agent_records(agents))
        files = []
        for path, diffs, _ in preview_items:
            if diffs:
                files.append(FileDiff(filePath=path.as_posix(), items=diffs))
        return PreviewResponse(files=files)

    def apply_agent_settings(self, agents: Union[List[AgentEditableRecord], List[Dict[str, Any]]]) -> ApplyResponse:
        preview_items = self._build_agent_preview(self._coerce_agent_records(agents))
        changed_items = [(path, diffs, payload) for path, diffs, payload in preview_items if diffs]
        if not changed_items:
            return ApplyResponse(appliedFiles=[], backups=[])

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        applied = []
        backups = []
        for path, _, payload in changed_items:
            backup_path = path.with_name(f"{path.name}.bak_{timestamp}")
            backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            applied.append(path.as_posix())
            backups.append(backup_path.as_posix())
            
        return ApplyResponse(appliedFiles=applied, backups=backups)

    def _build_agent_records(self, payload: Dict[str, Any], source: str) -> List[AgentEditableRecord]:
        records: List[AgentEditableRecord] = []
        for agent_id, agent_payload in payload.get("agent", {}).items():
            records.append(
                AgentEditableRecord(
                    id=agent_id,
                    originalId=agent_id,
                    source=source,
                    description=agent_payload.get("description"),
                    color=agent_payload.get("color"),
                    prompt=agent_payload.get("prompt"),
                    payload=copy.deepcopy(agent_payload),
                )
            )
        return records

    def _build_agent_preview(self, agents: List[AgentEditableRecord]) -> List[Tuple[Path, List[DiffItem], Dict[str, Any]]]:
        oc_payload, omo_opencode_payload = self._load_opencode_payloads()
        mutated_oc = copy.deepcopy(oc_payload)
        mutated_omo = copy.deepcopy(omo_opencode_payload)
        
        agent_payload_oc: Dict[str, Any] = {}
        agent_payload_omo: Dict[str, Any] = {}
        seen_by_source: Dict[str, set[str]] = {source: set() for source in self._available_provider_sources()}
        
        for agent in agents:
            if not agent.id.strip():
                raise ValueError("Agent id cannot be empty")
            if agent.source not in seen_by_source:
                raise ValueError("Unknown agent source: {0}".format(agent.source))
            if agent.id in seen_by_source[agent.source]:
                raise ValueError("Duplicate agent id for {0}: {1}".format(agent.source, agent.id))
            seen_by_source[agent.source].add(agent.id)
            
            node = copy.deepcopy(agent.payload)
            if agent.description is not None:
                node["description"] = agent.description
            elif "description" in node:
                del node["description"]
                
            if agent.color is not None:
                node["color"] = agent.color
            elif "color" in node:
                del node["color"]
                
            if agent.source == "opencode":
                if agent.prompt is not None:
                    node["prompt"] = agent.prompt
                elif "prompt" in node:
                    del node["prompt"]
                self._sanitize_opencode_agent_node(node, oc_payload)
                agent_payload_oc[agent.id] = node
            else:
                if agent.prompt is not None:
                    node["prompt"] = agent.prompt
                elif "prompt" in node:
                    del node["prompt"]
                self._sanitize_opencode_agent_node(node, omo_opencode_payload)
                agent_payload_omo[agent.id] = node
            
        mutated_oc["agent"] = agent_payload_oc
        if self.omo_opencode_path != self.opencode_path:
            mutated_omo["agent"] = agent_payload_omo
        
        diffs_oc: List[DiffItem] = []
        self._append_diff_items(oc_payload.get("agent", {}), mutated_oc.get("agent", {}), "agent", diffs_oc)
        result: List[Tuple[Path, List[DiffItem], Dict[str, Any]]] = [(self.opencode_path, diffs_oc, mutated_oc)]

        if self.omo_opencode_path != self.opencode_path:
            diffs_omo: List[DiffItem] = []
            self._append_diff_items(
                omo_opencode_payload.get("agent", {}),
                mutated_omo.get("agent", {}),
                "agent",
                diffs_omo,
            )
            result.append((self.omo_opencode_path, diffs_omo, mutated_omo))

        return result

    def _coerce_agent_records(self, agents: Union[List[AgentEditableRecord], List[Dict[str, Any]]]) -> List[AgentEditableRecord]:
        return [
            agent if isinstance(agent, AgentEditableRecord) else AgentEditableRecord.model_validate(agent)
            for agent in agents
        ]

    def _build_mutation_preview(
        self, changes: List[DraftChange]
    ) -> Tuple[Dict[Path, Dict[str, Any]], Dict[Path, List[DiffItem]]]:
        opencode_payload, omo_opencode_payload = self._load_opencode_payloads()
        omo_payload = self._load_json(self.omo_path)
        providers = self._build_providers(opencode_payload)
        omo_providers = self._build_providers(omo_opencode_payload)
        targets = {
            target.id: target
            for target in self._build_targets(opencode_payload, omo_payload, providers, omo_providers)
        }

        mutated = {
            self.opencode_path: copy.deepcopy(opencode_payload),
            self.omo_path: copy.deepcopy(omo_payload),
        }
        diff_map: Dict[Path, List[DiffItem]] = {
            self.opencode_path: [],
            self.omo_path: [],
        }

        for change in changes:
            target = targets.get(change.target_id)
            if target is None:
                raise ValueError("Unknown target: {0}".format(change.target_id))
            if target.source == "opencode":
                self._validate_change(change, providers)
                self._apply_opencode_change(mutated[self.opencode_path], target, change, diff_map[self.opencode_path])
            else:
                self._validate_change(change, omo_providers)
                self._apply_omo_change(mutated[self.omo_path], target, change, diff_map[self.omo_path])

        return mutated, diff_map

    def _build_providers(self, payload: Dict[str, Any]) -> List[ProviderInfo]:
        providers: List[ProviderInfo] = []
        variant_order = {
            "none": 0,
            "default": 0,
            "nano": 1,
            "mini": 2,
            "minimal": 3,
            "low": 4,
            "medium": 5,
            "high": 6,
            "xhigh": 7,
        }
        for provider_id in sorted(payload.get("provider", {}).keys()):
            provider_payload = payload["provider"][provider_id]
            models: List[ProviderModelInfo] = []
            for model_id in sorted(provider_payload.get("models", {}).keys()):
                model_payload = provider_payload["models"][model_id]
                variants = list(model_payload.get("variants", {}).keys())
                models.append(
                    ProviderModelInfo(
                        id=model_id,
                        label=model_payload.get("name", model_id),
                        strengthOptions=sorted(variants, key=lambda k: (variant_order.get(k.lower(), 99), k)),
                    )
                )
            providers.append(ProviderInfo(id=provider_id, label=provider_id, models=models))
        return providers

    def _build_targets(
        self,
        opencode_payload: Dict[str, Any],
        omo_payload: Dict[str, Any],
        providers: List[ProviderInfo],
        omo_providers: Optional[List[ProviderInfo]] = None,
    ) -> List[TargetInfo]:
        available_provider_ids = [provider.id for provider in providers]
        omo_available_provider_ids = [provider.id for provider in (omo_providers or providers)]
        targets: List[TargetInfo] = []

        for field_name, label in [("model", "Default Model"), ("small_model", "Small Model")]:
            provider_id, model_id = self._split_model_ref(opencode_payload.get(field_name))
            targets.append(
                TargetInfo(
                    id="opencode:default:{0}".format(field_name),
                    source="opencode",
                    kind="default",
                    name=label,
                    currentProvider=provider_id,
                    currentModel=model_id,
                    currentStrength=opencode_payload.get("variant") if field_name == "model" else None,
                    availableProviders=available_provider_ids,
                )
            )

        for agent_name in sorted(opencode_payload.get("agent", {}).keys()):
            agent_payload = opencode_payload["agent"][agent_name]
            provider_id, model_id = self._split_model_ref(agent_payload.get("model"))
            targets.append(
                TargetInfo(
                    id="opencode:agent:{0}".format(agent_name),
                    source="opencode",
                    kind="agent",
                    name=agent_name,
                    currentProvider=provider_id,
                    currentModel=model_id,
                    currentStrength=self._get_opencode_agent_strength(agent_payload),
                    availableProviders=available_provider_ids,
                )
            )

        for agent_name in sorted(omo_payload.get("agents", {}).keys()):
            agent_payload = omo_payload["agents"][agent_name]
            provider_id, model_id = self._split_model_ref(agent_payload.get("model"))
            kind = "subagent" if agent_name in OMO_SUBAGENT_AGENT_NAMES else "agent"
            targets.append(
                TargetInfo(
                    id="omo:{0}:{1}".format(kind, agent_name),
                    source="omo",
                    kind=kind,
                    name=agent_name,
                    currentProvider=provider_id,
                    currentModel=model_id,
                    currentStrength=agent_payload.get("variant"),
                    availableProviders=omo_available_provider_ids,
                )
            )

        for category_name in sorted(omo_payload.get("categories", {}).keys()):
            category_payload = omo_payload["categories"][category_name]
            provider_id, model_id = self._split_model_ref(category_payload.get("model"))
            targets.append(
                TargetInfo(
                    id="omo:category:{0}".format(category_name),
                    source="omo",
                    kind="category",
                    name=category_name,
                    currentProvider=provider_id,
                    currentModel=model_id,
                    currentStrength=category_payload.get("variant"),
                    availableProviders=omo_available_provider_ids,
                )
            )

        return targets

    def _build_provider_records(self, payload: Dict[str, Any]) -> List[ProviderEditableRecord]:
        records: List[ProviderEditableRecord] = []
        for provider_id in sorted(payload.get("provider", {}).keys()):
            provider_payload = payload["provider"][provider_id]
            models: List[ProviderEditableModel] = []
            for model_id in sorted(provider_payload.get("models", {}).keys()):
                model_payload = provider_payload["models"][model_id]
                models.append(
                    ProviderEditableModel(
                        id=model_id,
                        name=model_payload.get("name"),
                        limit=copy.deepcopy(model_payload.get("limit", {})),
                        cost=copy.deepcopy(model_payload.get("cost", {})),
                        options=copy.deepcopy(model_payload.get("options", {})),
                        maxTokens=model_payload.get("maxTokens"),
                        variants=copy.deepcopy(model_payload.get("variants", {})),
                    )
                )
            records.append(
                ProviderEditableRecord(
                    id=provider_id,
                    npm=provider_payload.get("npm"),
                    options=copy.deepcopy(provider_payload.get("options", {})),
                    models=models,
                )
            )
        return records

    def _build_provider_preview(
        self, providers: List[ProviderEditableRecord], source: str = "opencode"
    ) -> Tuple[Path, Dict[str, Any], List[DiffItem]]:
        provider_path = self._provider_path_for_source(source)
        payload = self._load_json(provider_path)
        mutated = copy.deepcopy(payload)
        mutated["provider"] = self._provider_records_to_payload(providers)
        diffs: List[DiffItem] = []
        self._append_diff_items(payload.get("provider", {}), mutated.get("provider", {}), "provider", diffs)
        return provider_path, mutated, diffs

    def _provider_records_to_payload(self, providers: List[ProviderEditableRecord]) -> Dict[str, Any]:
        provider_payload: Dict[str, Any] = {}
        seen_provider_ids: set[str] = set()
        for provider in providers:
            if not provider.id.strip():
                raise ValueError("Provider id cannot be empty")
            if provider.id in seen_provider_ids:
                raise ValueError("Duplicate provider id: {0}".format(provider.id))
            seen_provider_ids.add(provider.id)

            models_payload: Dict[str, Any] = {}
            seen_model_ids: set[str] = set()
            for model in provider.models:
                if not model.id.strip():
                    raise ValueError("Model id cannot be empty")
                if model.id in seen_model_ids:
                    raise ValueError("Duplicate model id: {0}".format(model.id))
                seen_model_ids.add(model.id)
                model_payload = {
                    "name": model.name,
                    "limit": model.limit,
                    "cost": model.cost,
                    "options": model.options,
                    "maxTokens": model.max_tokens,
                    "variants": model.variants,
                }
                models_payload[model.id] = {
                    key: value
                    for key, value in model_payload.items()
                    if value not in (None, {}, [])
                }

            provider_record = {
                "npm": provider.npm,
                "options": provider.options,
                "models": models_payload,
            }
            provider_payload[provider.id] = {
                key: value
                for key, value in provider_record.items()
                if value not in (None, {}, [])
            }
        return provider_payload

    def _append_diff_items(self, old_value: Any, new_value: Any, path: str, diffs: List[DiffItem]) -> None:
        if old_value == new_value:
            return
        if isinstance(old_value, dict) and isinstance(new_value, dict):
            keys = sorted(set(old_value.keys()) | set(new_value.keys()))
            for key in keys:
                next_path = "{0}.{1}".format(path, key) if path else key
                if key not in old_value:
                    self._append_diff_items(None, new_value[key], next_path, diffs)
                elif key not in new_value:
                    self._append_diff_items(old_value[key], None, next_path, diffs)
                else:
                    self._append_diff_items(old_value[key], new_value[key], next_path, diffs)
            return
        if isinstance(new_value, dict) and old_value is None:
            for key in sorted(new_value.keys()):
                next_path = "{0}.{1}".format(path, key) if path else key
                self._append_diff_items(None, new_value[key], next_path, diffs)
            return
        if isinstance(old_value, dict) and new_value is None:
            for key in sorted(old_value.keys()):
                next_path = "{0}.{1}".format(path, key) if path else key
                self._append_diff_items(old_value[key], None, next_path, diffs)
            return
        diffs.append(DiffItem(path=path, oldValue=old_value, newValue=new_value))

    def _resolve_visibility_rules(self, targets: List[TargetInfo], settings_payload: Dict[str, Any]) -> List[VisibilityRule]:
        persisted_map = {
            rule["targetId"]: rule
            for rule in settings_payload.get("visibilityRules", [])
            if isinstance(rule, dict) and "targetId" in rule
        }
        rules: List[VisibilityRule] = []
        for target in targets:
            default_visible = self._default_visibility_for_target(target)
            default_kind_override = self._default_kind_override_for_target(target)
            persisted = persisted_map.get(target.id, {})
            rules.append(
                VisibilityRule(
                    targetId=target.id,
                    visible=bool(persisted.get("visible", default_visible)),
                    kindOverride=persisted.get("kindOverride", default_kind_override),
                    tabOverride=persisted.get("tabOverride", None),
                )
            )
        return rules

    def _apply_visibility_rules(
        self, targets: List[TargetInfo], visibility_rules: List[VisibilityRule]
    ) -> List[TargetInfo]:
        rules_map = {rule.target_id: rule for rule in visibility_rules}
        result: List[TargetInfo] = []
        for target in targets:
            rule = rules_map.get(target.id)
            next_target = target.model_copy(deep=True)
            if rule:
                next_target.visible = rule.visible
                if rule.kind_override:
                    next_target.kind = rule.kind_override
                if rule.tab_override:
                    next_target.custom_tab = rule.tab_override
            else:
                # 如果没有规则（通常不会发生），保持默认可见性
                next_target.visible = self._default_visibility_for_target(target)
                
            result.append(next_target)
        return result

    def _default_visibility_for_target(self, target: TargetInfo) -> bool:
        if target.source == "opencode" and target.id.startswith("opencode:default:"):
            return False
        if target.source == "opencode" and target.name in HIDDEN_OPENCODE_AGENTS:
            return False
        return True

    def _default_kind_override_for_target(self, target: TargetInfo) -> Optional[str]:
        if target.source != "omo":
            return None
        if target.name in OMO_SUBAGENT_AGENT_NAMES:
            return "subagent"
        return None

    def _load_settings_payload(self) -> Dict[str, Any]:
        if not self.settings_path.exists():
            return copy.deepcopy(DEFAULT_SETTINGS_PAYLOAD)
        try:
            payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Failed to parse JSON at {0}".format(self.settings_path)) from exc
        if not isinstance(payload, dict):
            raise ValueError("Invalid settings payload at {0}".format(self.settings_path))
        return payload

    def _coerce_visibility_rules(
        self, rules: Union[List[VisibilityRule], List[Dict[str, Any]]], targets: List[TargetInfo]
    ) -> List[VisibilityRule]:
        target_map = {target.id: target for target in targets}
        validated: List[VisibilityRule] = []
        for rule in rules:
            next_rule = rule if isinstance(rule, VisibilityRule) else VisibilityRule.model_validate(rule)
            target = target_map.get(next_rule.target_id)
            if target is None:
                raise ValueError("Unknown target for visibility settings: {0}".format(next_rule.target_id))
            if next_rule.kind_override and target.source != "omo":
                raise ValueError("kindOverride is only supported for OMO targets")
            if next_rule.kind_override and next_rule.kind_override not in {"agent", "subagent"}:
                raise ValueError("Invalid kindOverride: {0}".format(next_rule.kind_override))
            validated.append(next_rule)
        return validated

    def _coerce_provider_records(
        self, providers: Union[List[ProviderEditableRecord], List[Dict[str, Any]]]
    ) -> List[ProviderEditableRecord]:
        return [
            provider if isinstance(provider, ProviderEditableRecord) else ProviderEditableRecord.model_validate(provider)
            for provider in providers
        ]

    def _apply_opencode_change(
        self,
        payload: Dict[str, Any],
        target: TargetInfo,
        change: DraftChange,
        diffs: List[DiffItem],
    ) -> None:
        model_ref = "{0}/{1}".format(change.provider, change.model)
        segments = target.id.split(":")
        if target.kind == "default":
            field_name = segments[-1]
            self._record_update(payload, field_name, model_ref, diffs, "")
            if field_name == "model":
                self._record_update(payload, "variant", None, diffs, "")
        else:
            agent_name = segments[-1]
            agent_payload = payload.setdefault("agent", {}).setdefault(agent_name, {})
            prefix = "agent.{0}.".format(agent_name)
            self._record_update(agent_payload, "model", model_ref, diffs, prefix)
            self._record_update(agent_payload, "variant", None, diffs, prefix)
            variant_options = self._get_opencode_variant_options(
                payload,
                change.provider,
                change.model,
                change.strength,
            )
            if variant_options:
                options_payload = agent_payload.setdefault("options", {})
                for option_key, option_value in sorted(variant_options.items()):
                    self._record_update(
                        options_payload,
                        option_key,
                        copy.deepcopy(option_value),
                        diffs,
                        "{0}options.".format(prefix),
                    )
            if "reasoningEffort" in agent_payload:
                self._record_update(
                    agent_payload,
                    "reasoningEffort",
                    variant_options.get("reasoningEffort", change.strength),
                    diffs,
                    prefix,
                )

    def _apply_omo_change(
        self,
        payload: Dict[str, Any],
        target: TargetInfo,
        change: DraftChange,
        diffs: List[DiffItem],
    ) -> None:
        model_ref = "{0}/{1}".format(change.provider, change.model)
        _, kind, name = target.id.split(":")
        
        if kind in {"category", "subagent"}:
            if name in payload.get("agents", {}) or name in OMO_SUBAGENT_AGENT_NAMES:
                group_name = "agents"
            else:
                group_name = "categories"
        else:
            group_name = "{0}s".format(kind)
            
        node = payload.setdefault(group_name, {}).setdefault(name, {})
        prefix = "{0}.{1}.".format(group_name, name)
        self._record_update(node, "model", model_ref, diffs, prefix)
        self._record_update(node, "variant", change.strength, diffs, prefix)

    def _record_update(
        self,
        node: Dict[str, Any],
        key: str,
        new_value: Any,
        diffs: List[DiffItem],
        prefix: str,
    ) -> None:
        old_value = node.get(key)
        if old_value == new_value:
            return
        if new_value is None:
            if key in node:
                del node[key]
                diffs.append(DiffItem(path="{0}{1}".format(prefix, key).strip("."), oldValue=old_value, newValue=None))
        else:
            node[key] = new_value
            diffs.append(DiffItem(path="{0}{1}".format(prefix, key).strip("."), oldValue=old_value, newValue=new_value))

    def _sanitize_opencode_agent_node(self, node: Dict[str, Any], payload: Dict[str, Any]) -> None:
        legacy_variant = node.pop("variant", None)
        provider, model = self._split_model_ref(node.get("model"))
        if not legacy_variant or not provider or not model:
            return

        variant_options = self._get_opencode_variant_options(payload, provider, model, legacy_variant)
        if not variant_options:
            return

        options_payload = node.setdefault("options", {})
        for option_key, option_value in variant_options.items():
            options_payload[option_key] = copy.deepcopy(option_value)
        if "reasoningEffort" in node and "reasoningEffort" in variant_options:
            node["reasoningEffort"] = variant_options["reasoningEffort"]

    def _get_opencode_agent_strength(self, node: Dict[str, Any]) -> Optional[str]:
        options = node.get("options", {})
        option_reasoning = options.get("reasoningEffort") if isinstance(options, dict) else None
        return node.get("variant") or node.get("reasoningEffort") or option_reasoning

    def _get_opencode_variant_options(
        self,
        payload: Dict[str, Any],
        provider: str,
        model: str,
        strength: Optional[str],
    ) -> Dict[str, Any]:
        if not strength:
            return {}
        variant_payload = (
            payload.get("provider", {})
            .get(provider, {})
            .get("models", {})
            .get(model, {})
            .get("variants", {})
            .get(strength, {})
        )
        return copy.deepcopy(variant_payload) if isinstance(variant_payload, dict) else {}

    def _validate_change(self, change: DraftChange, providers: List[ProviderInfo]) -> None:
        provider_map = {provider.id: provider for provider in providers}
        if change.provider not in provider_map:
            raise ValueError("Unknown provider: {0}".format(change.provider))

        model_map = {model.id: model for model in provider_map[change.provider].models}
        if change.model not in model_map:
            raise ValueError("Unknown model: {0}".format(change.model))

        if change.strength and change.strength not in model_map[change.model].strength_options:
            raise ValueError("Invalid strength '{0}' for model '{1}'".format(change.strength, change.model))

    def _coerce_changes(self, changes: Union[List[DraftChange], List[Dict[str, Any]]]) -> List[DraftChange]:
        return [
            change if isinstance(change, DraftChange) else DraftChange.model_validate(change)
            for change in changes
        ]

    def _split_model_ref(self, value: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        if not value:
            return None, None
        if "/" not in value:
            return None, value
        provider, model = value.split("/", 1)
        return provider, model

    def _load_json(self, path: Path) -> Dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Failed to parse JSON at {0}".format(path)) from exc
