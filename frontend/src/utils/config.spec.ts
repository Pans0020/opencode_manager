import { describe, expect, it } from 'vitest'

import type { ProviderInfo, TargetDraft, TargetInfo } from '@/types'
import {
  buildDraftChanges,
  getBatchProviderTargetIds,
  getModelOptions,
  getProvidersForSource,
  getStrengthOptions,
  getValidProviderIdForSource,
  mergeDraft,
  shouldShowStrengthControl,
} from '@/utils/config'

const providers: ProviderInfo[] = [
  {
    id: 'Anthropic',
    label: 'Anthropic',
    models: [
      {
        id: 'claude-sonnet-4',
        label: 'Claude Sonnet 4',
        strengthOptions: ['low', 'high'],
      },
    ],
  },
  {
    id: 'OpenAI',
    label: 'OpenAI',
    models: [
      {
        id: 'gpt-5.4',
        label: 'GPT-5.4',
        strengthOptions: ['low', 'medium', 'high', 'xhigh'],
      },
      {
        id: 'gpt-5.4-mini',
        label: 'GPT-5.4 Mini',
        strengthOptions: ['low', 'medium'],
      },
    ],
  },
]

const omoProviders: ProviderInfo[] = [
  {
    id: 'OmoOnly',
    label: 'OmoOnly',
    models: [
      {
        id: 'omo-model',
        label: 'OMO Model',
        strengthOptions: ['spark', 'deep'],
      },
    ],
  },
]

const targets: TargetInfo[] = [
  {
    id: 'opencode:agent:build',
    source: 'opencode',
    kind: 'agent',
    name: 'build',
    currentProvider: 'OpenAI',
    currentModel: 'gpt-5.4',
    currentStrength: 'high',
    availableProviders: ['OpenAI', 'Anthropic'],
  },
  {
    id: 'opencode:default:model',
    source: 'opencode',
    kind: 'default',
    name: 'Default Model',
    visible: false,
    currentProvider: 'OpenAI',
    currentModel: 'gpt-5.4',
    currentStrength: 'medium',
    availableProviders: ['OpenAI', 'Anthropic'],
  },
  {
    id: 'omo:agent:atlas',
    source: 'omo',
    kind: 'agent',
    name: 'atlas',
    visible: true,
    currentProvider: 'OmoOnly',
    currentModel: 'omo-model',
    currentStrength: 'spark',
    availableProviders: ['OmoOnly'],
  },
  {
    id: 'omo:subagent:librarian',
    source: 'omo',
    kind: 'subagent',
    name: 'librarian',
    visible: false,
    currentProvider: 'OmoOnly',
    currentModel: 'omo-model',
    currentStrength: 'spark',
    availableProviders: ['OmoOnly'],
  },
]

describe('config utils', () => {
  it('returns model options for selected provider', () => {
    expect(getModelOptions(providers, 'OpenAI').map((model) => model.id)).toEqual([
      'gpt-5.4',
      'gpt-5.4-mini',
    ])
  })

  it('returns strength options for selected model', () => {
    expect(getStrengthOptions(providers, 'OpenAI', 'gpt-5.4-mini')).toEqual(['low', 'medium'])
  })

  it('returns source-specific providers when split config exposes them', () => {
    expect(getProvidersForSource({ opencode: providers, omo: omoProviders }, providers, 'omo')).toEqual(omoProviders)
    expect(getProvidersForSource({ opencode: providers }, providers, 'omo')).toEqual(providers)
  })

  it('resets model and strength when provider changes', () => {
    const draft: TargetDraft = {
      provider: 'OpenAI',
      model: 'gpt-5.4',
      strength: 'high',
    }

    expect(mergeDraft(draft, providers, { provider: 'Anthropic' })).toEqual({
      provider: 'Anthropic',
      model: 'claude-sonnet-4',
      strength: 'low',
    })
  })

  it('clears strength when selected model has no strength options', () => {
    const draft: TargetDraft = {
      provider: 'OpenAI',
      model: 'gpt-5.4',
      strength: 'high',
    }
    const providersWithPlainModel: ProviderInfo[] = [
      {
        id: 'OpenAI',
        label: 'OpenAI',
        models: [
          {
            id: 'plain-model',
            label: 'Plain Model',
            strengthOptions: [],
          },
        ],
      },
    ]

    expect(mergeDraft(draft, providersWithPlainModel, { model: 'plain-model' })).toEqual({
      provider: 'OpenAI',
      model: 'plain-model',
      strength: null,
    })
  })

  it('shows strength control for agents but not default model targets', () => {
    expect(
      shouldShowStrengthControl(
        targets[0],
        providers,
        { provider: 'OpenAI', model: 'gpt-5.4', strength: 'high' },
      ),
    ).toBe(true)

    expect(
      shouldShowStrengthControl(
        targets[1],
        providers,
        { provider: 'OpenAI', model: 'gpt-5.4', strength: 'medium' },
      ),
    ).toBe(false)
  })

  it('builds payload only for changed rows', () => {
    const drafts = {
      'opencode:agent:build': {
        provider: 'Anthropic',
        model: 'claude-sonnet-4',
        strength: 'high',
      },
      untouched: {
        provider: 'OpenAI',
        model: 'gpt-5.4',
        strength: 'high',
      },
    }

    expect(buildDraftChanges(targets, drafts)).toEqual([
      {
        targetId: 'opencode:agent:build',
        provider: 'Anthropic',
        model: 'claude-sonnet-4',
        strength: 'high',
      },
    ])
  })

  it('selects only visible OpenCode targets for batch provider updates', () => {
    expect(getBatchProviderTargetIds(targets, 'opencode')).toEqual([
      'opencode:agent:build',
    ])
  })

  it('keeps OMO batch provider updates source-wide', () => {
    expect(getBatchProviderTargetIds(targets, 'omo')).toEqual([
      'omo:agent:atlas',
      'omo:subagent:librarian',
    ])
  })

  it('clears selected provider when it is not valid for the active source', () => {
    expect(getValidProviderIdForSource('OpenAI', providers)).toBe('OpenAI')
    expect(getValidProviderIdForSource('OpenAI', omoProviders)).toBeNull()
    expect(getValidProviderIdForSource(null, omoProviders)).toBeNull()
  })
})
