import { describe, expect, it } from 'vitest'

import type { TargetInfo } from '@/types'
import { getDefaultSourceTab, getVisibleTargetsBySource } from '@/utils/source-tabs'

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
]

describe('source tabs helpers', () => {
  it('defaults to opencode tab', () => {
    expect(getDefaultSourceTab()).toBe('opencode')
  })

  it('returns only targets for selected source', () => {
    expect(getVisibleTargetsBySource(targets, 'opencode').map((item) => item.id)).toEqual([
      'opencode:agent:build',
    ])
    expect(getVisibleTargetsBySource(targets, 'omo').map((item) => item.id)).toEqual([
      'omo:agent:atlas',
    ])
  })
})
