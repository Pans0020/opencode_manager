import { describe, expect, it } from 'vitest'

import type { AgentEditableRecord } from '@/types'
import {
  createEmptyAgentDraft,
  createAgentDrafts,
  hasAgentIdInSource,
  serializeAgentDrafts,
  shouldShowAgentSourceTabs,
} from '@/utils/agent-form'

const sourceRecords: AgentEditableRecord[] = [
  {
    id: 'Default',
    originalId: 'Default',
    source: 'opencode',
    description: null,
    color: null,
    prompt: null,
    payload: { mode: 'primary' },
  },
  {
    id: 'Default',
    originalId: 'Default',
    source: 'omo',
    description: null,
    color: null,
    prompt: null,
    payload: { mode: 'primary' },
  },
]

describe('agent form utilities', () => {
  it('keeps same agent id distinct across sources', () => {
    const drafts = createAgentDrafts(sourceRecords)

    expect(drafts.map((draft) => draft.clientKey)).toEqual([
      'opencode:Default:0',
      'omo:Default:1',
    ])
    expect(hasAgentIdInSource(drafts, 'opencode', 'Default')).toBe(true)
    expect(hasAgentIdInSource(drafts, 'omo', 'Default')).toBe(true)
    expect(hasAgentIdInSource(drafts, 'omo', 'Default', drafts[1].clientKey)).toBe(false)
  })

  it('creates new agents in the active source', () => {
    const draft = createEmptyAgentDraft('omo', 'new-1')

    expect(draft.source).toBe('omo')
    expect(draft.clientKey).toBe('new-1')
    expect(draft.payload).toEqual({ mode: 'primary' })
  })

  it('keeps client key stable when an agent is renamed', () => {
    const [draft] = createAgentDrafts([sourceRecords[0]])
    draft.id = 'Renamed'

    expect(draft.clientKey).toBe('opencode:Default:0')
    expect(serializeAgentDrafts([draft])[0]).toMatchObject({
      id: 'Renamed',
      originalId: 'Default',
      source: 'opencode',
    })
  })

  it('only shows source tabs when multiple sources are available', () => {
    expect(shouldShowAgentSourceTabs(['opencode'])).toBe(false)
    expect(shouldShowAgentSourceTabs(['opencode', 'omo'])).toBe(true)
  })
})
