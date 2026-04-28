import { describe, expect, it } from 'vitest'

import type { TargetInfo } from '@/types'
import { getTargetKindLabel, splitTargetsByKind } from '@/utils/target-groups'

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

describe('getTargetKindLabel', () => {
  it('disambiguates OMO category targets even when displayed as subagents', () => {
    expect(
      getTargetKindLabel({
        id: 'omo:subagent:explore',
        source: 'omo',
        kind: 'subagent',
        name: 'explore',
        currentProvider: 'OpenAI',
        currentModel: 'gpt-5.5',
        currentStrength: 'xhigh',
        availableProviders: ['OpenAI'],
      }),
    ).toBe('subagent · agents.explore')

    expect(
      getTargetKindLabel({
        id: 'omo:category:explore',
        source: 'omo',
        kind: 'subagent',
        name: 'explore',
        currentProvider: 'OpenAI',
        currentModel: 'gpt-5.5',
        currentStrength: 'medium',
        availableProviders: ['OpenAI'],
      }),
    ).toBe('category · categories.explore')
  })

  it('keeps colons in OMO target names', () => {
    expect(
      getTargetKindLabel({
        id: 'omo:subagent:agent:withcolon',
        source: 'omo',
        kind: 'subagent',
        name: 'agent:withcolon',
        currentProvider: 'OpenAI',
        currentModel: 'gpt-5.5',
        currentStrength: 'xhigh',
        availableProviders: ['OpenAI'],
      }),
    ).toBe('subagent · agents.agent:withcolon')

    expect(
      getTargetKindLabel({
        id: 'omo:category:cat:withcolon',
        source: 'omo',
        kind: 'category',
        name: 'cat:withcolon',
        currentProvider: 'OpenAI',
        currentModel: 'gpt-5.5',
        currentStrength: 'medium',
        availableProviders: ['OpenAI'],
      }),
    ).toBe('category · categories.cat:withcolon')
  })
})
