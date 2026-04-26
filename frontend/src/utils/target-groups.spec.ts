import { describe, expect, it } from 'vitest'

import type { TargetInfo } from '@/types'
import { splitTargetsByKind } from '@/utils/target-groups'

const targets: TargetInfo[] = [
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
    id: 'omo:subagent:deep',
    source: 'omo',
    kind: 'subagent',
    name: 'deep',
    currentProvider: 'OpenAI',
    currentModel: 'gpt-5.4',
    currentStrength: 'xhigh',
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

describe('splitTargetsByKind', () => {
  it('separates agents and subagents for the OMO view', () => {
    const groups = splitTargetsByKind(targets)

    expect(groups.agents.map((item) => item.id)).toEqual(['omo:agent:atlas'])
    expect(groups.subagents.map((item) => item.id)).toEqual([
      'omo:subagent:deep',
      'omo:subagent:librarian',
    ])
    expect(groups.others).toEqual([])
  })
})
