import type {
  ApplyResponse,
  ConfigSource,
  DraftChange,
  OverviewResponse,
  PreviewResponse,
  ProviderEditableRecord,
  ProviderSettingsResponse,
  VisibilityRule,
  VisibilitySettingsResponse,
  AgentEditableRecord,
  AgentSettingsResponse,
} from '@/types'
import { getApiBaseUrl, getDesktopRuntime } from '@/utils/runtime'

const API_BASE = getApiBaseUrl({
  envApiBase: import.meta.env.VITE_API_BASE,
  desktopRuntime: getDesktopRuntime(window.__AGENT_MODEL_MANAGER__),
})

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new Error(payload?.detail ?? `Request failed: ${response.status}`)
  }

  return response.json() as Promise<T>
}

export function fetchOverview() {
  return request<OverviewResponse>('/api/config/overview')
}

export function previewChanges(changes: DraftChange[]) {
  return request<PreviewResponse>('/api/config/preview', {
    method: 'POST',
    body: JSON.stringify({ changes }),
  })
}

export function applyChanges(changes: DraftChange[]) {
  return request<ApplyResponse>('/api/config/apply', {
    method: 'POST',
    body: JSON.stringify({ changes }),
  })
}

export function reloadOverview() {
  return request<OverviewResponse>('/api/config/reload', {
    method: 'POST',
  })
}

export function fetchVisibilitySettings() {
  return request<VisibilitySettingsResponse>('/api/settings/visibility')
}

export function saveVisibilitySettings(visibilityRules: VisibilityRule[], customTabs: string[]) {
  return request<VisibilitySettingsResponse>('/api/settings/visibility', {
    method: 'POST',
    body: JSON.stringify({ visibilityRules, customTabs }),
  })
}

export function fetchProviderSettings(source: ConfigSource = 'opencode') {
  return request<ProviderSettingsResponse>(`/api/providers?source=${encodeURIComponent(source)}`)
}

export function previewProviderSettings(providers: ProviderEditableRecord[], source: ConfigSource = 'opencode') {
  return request<PreviewResponse>(`/api/providers/preview?source=${encodeURIComponent(source)}`, {
    method: 'POST',
    body: JSON.stringify({ providers }),
  })
}

export function applyProviderSettings(providers: ProviderEditableRecord[], source: ConfigSource = 'opencode') {
  return request<ApplyResponse>(`/api/providers/apply?source=${encodeURIComponent(source)}`, {
    method: 'POST',
    body: JSON.stringify({ providers }),
  })
}

export function fetchAgentSettings() {
  return request<AgentSettingsResponse>('/api/agents')
}

export function previewAgentSettings(agents: AgentEditableRecord[]) {
  return request<PreviewResponse>('/api/agents/preview', {
    method: 'POST',
    body: JSON.stringify({ agents }),
  })
}

export function applyAgentSettings(agents: AgentEditableRecord[]) {
  return request<ApplyResponse>('/api/agents/apply', {
    method: 'POST',
    body: JSON.stringify({ agents }),
  })
}
