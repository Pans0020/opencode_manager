import type { AgentDraft, AgentEditableRecord, ConfigSource } from '@/types'

export const HIDDEN_OPENCODE_AGENTS = [
  'compaction',
  'build',
  'general',
  'pua:cto-p10',
  'plan',
  'pua:senior-engineer-p7',
  'pua:tech-lead-p9',
  'summary',
  'superpowers:code-reviewer',
  'title',
  'Sisyphus-Junior',
]

export function createAgentDrafts(agents: AgentEditableRecord[]): AgentDraft[] {
  return agents.map((agent, index) => ({
    ...structuredClone(agent),
    clientKey: `${agent.source}:${agent.originalId ?? agent.id}:${index}`,
  }))
}

export function serializeAgentDrafts(drafts: AgentDraft[]): AgentEditableRecord[] {
  return drafts.map(({ clientKey: _clientKey, ...agent }) => structuredClone(agent))
}

export function shouldShowAgentSourceTabs(sources: ConfigSource[]) {
  return sources.length > 1
}

export function createEmptyAgentDraft(source: ConfigSource, clientKey: string): AgentDraft {
  return {
    clientKey,
    id: '',
    originalId: null,
    source,
    description: '',
    color: '#4F86F7',
    prompt: '',
    payload: { mode: 'primary' },
  }
}

export function duplicateAgentDraft(source: AgentDraft, id: string, clientKey: string): AgentDraft {
  return {
    ...structuredClone(source),
    clientKey,
    id,
    originalId: null,
  }
}

export function isHiddenAgent(agent: AgentDraft) {
  if (agent.payload?.mode === 'subagent') {
    return true
  }
  return agent.source === 'opencode' && HIDDEN_OPENCODE_AGENTS.includes(agent.id)
}

export function filterAgentsBySource(agents: AgentDraft[], source: ConfigSource) {
  return agents.filter((agent) => agent.source === source)
}

export function getDisplayAgents(agents: AgentDraft[], source: ConfigSource) {
  return filterAgentsBySource(agents, source).filter((agent) => !isHiddenAgent(agent))
}

export function getHiddenAgents(agents: AgentDraft[], source: ConfigSource) {
  return filterAgentsBySource(agents, source).filter((agent) => isHiddenAgent(agent))
}

export function hasAgentIdInSource(
  agents: AgentDraft[],
  source: ConfigSource,
  id: string,
  exceptClientKey?: string,
) {
  return agents.some(
    (agent) =>
      agent.source === source &&
      agent.id === id &&
      agent.clientKey !== exceptClientKey,
  )
}
