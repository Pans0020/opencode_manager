export interface ProviderModelInfo {
  id: string
  label: string
  strengthOptions: string[]
}

export interface ProviderInfo {
  id: string
  label: string
  models: ProviderModelInfo[]
}

export type AppPage = 'models' | 'visibility' | 'tabs' | 'providers'
export type ConfigSource = 'opencode' | 'omo'

export interface TargetInfo {
  id: string
  source: ConfigSource
  kind: 'default' | 'agent' | 'subagent' | 'category'
  name: string
  visible: boolean
  currentProvider: string | null
  currentModel: string | null
  currentStrength: string | null
  availableProviders: string[]
  customTab?: string | null
}

export interface OverviewResponse {
  providers: ProviderInfo[]
  providersBySource?: Partial<Record<ConfigSource, ProviderInfo[]>>
  targets: TargetInfo[]
  configPaths: Record<string, string>
  loadedAt: string
  customTabs: string[]
}

export interface DraftChange {
  targetId: string
  provider: string
  model: string
  strength: string | null
}

export interface DiffItem {
  path: string
  oldValue: unknown
  newValue: unknown
}

export interface FileDiff {
  filePath: string
  items: DiffItem[]
}

export interface PreviewResponse {
  files: FileDiff[]
}

export interface ApplyResponse {
  appliedFiles: string[]
  backups: string[]
}

export interface TargetDraft {
  provider: string | null
  model: string | null
  strength: string | null
}

export interface VisibilityRule {
  targetId: string
  visible: boolean
  kindOverride: 'agent' | 'subagent' | null
  tabOverride?: string | null
}

export interface VisibilitySettingsResponse {
  targets: TargetInfo[]
  visibilityRules: VisibilityRule[]
  customTabs: string[]
}

export interface ProviderEditableModel {
  id: string
  name: string | null
  limit: Record<string, unknown>
  cost: Record<string, unknown>
  options: Record<string, unknown>
  maxTokens: number | null
  variants: Record<string, Record<string, unknown>>
}

export interface ProviderEditableRecord {
  id: string
  npm: string | null
  options: Record<string, unknown>
  models: ProviderEditableModel[]
}

export interface ProviderSettingsResponse {
  providers: ProviderEditableRecord[]
  source: ConfigSource
  configPath: string | null
  availableSources: ConfigSource[]
}

export interface ProviderVariantDraft {
  clientKey: string
  id: string
  valueText: string
}

export interface ProviderModelDraft {
  clientKey: string
  id: string
  name: string
  maxTokensText: string
  limitText: string
  costText: string
  optionsText: string
  variants: ProviderVariantDraft[]
}

export interface ProviderDraft {
  clientKey: string
  id: string
  npm: string
  apiKey: string
  baseURL: string
  extraOptionsText: string
  models: ProviderModelDraft[]
}

export interface AgentEditableRecord {
  id: string
  originalId: string | null
  source: ConfigSource
  description: string | null
  color: string | null
  prompt: string | null
  payload: Record<string, unknown>
}

export interface AgentDraft extends AgentEditableRecord {
  clientKey: string
}

export interface AgentSettingsResponse {
  agents: AgentEditableRecord[]
  availableSources: ConfigSource[]
  configPaths: Record<string, string>
}
