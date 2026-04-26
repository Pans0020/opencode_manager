import { describe, expect, it } from 'vitest'

import type { TargetInfo, VisibilityRule } from '@/types'
import { buildVisibilitySections } from '@/utils/visibility'

const targets: TargetInfo[] = [
  {
    id: 'opencode:agent:build',
    source: 'opencode',
    kind: 'agent',
    name: 'build',
    currentProvider: 'OpenAI',
    currentModel: 'gpt-5.4',
    currentStrength: 'high',
    availableProviders: ['OpenAI'],
  },
  {
    id: 'omo:agent:atlas',
    source: 'omo',
    kind: 'agent',
    name: 'atlas',
    currentProvider: 'OpenAI',
    currentModel: 'gpt-5.4-mini',
    currentStrength: 'medium',
    availableProviders: ['OpenAI'],
  },
  {
    id: 'omo:subagent:librarian',
    source: 'omo',
    kind: 'subagent',
    name: 'librarian',
    currentProvider: 'OpenAI',
    currentModel: 'gpt-5.4-mini',
    currentStrength: 'medium',
    availableProviders: ['OpenAI'],
  },
]

const rules: VisibilityRule[] = [
  { targetId: 'opencode:agent:build', visible: false, kindOverride: null },
  { targetId: 'omo:agent:atlas', visible: true, kindOverride: 'subagent' },
  { targetId: 'omo:subagent:librarian', visible: true, kindOverride: 'subagent' },
]

describe('buildVisibilitySections', () => {
  it('groups targets for opencode, omo agents, and omo subagents', () => {
    const sections = buildVisibilitySections(targets, rules)

    expect(sections.opencode.map((item) => item.target.id)).toEqual(['opencode:agent:build'])
    expect(sections.omoAgents).toEqual([])
    expect(sections.omoSubagents.map((item) => item.target.id)).toEqual([
      'omo:agent:atlas',
      'omo:subagent:librarian',
    ])
  })
})
