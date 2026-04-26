import { describe, expect, it } from 'vitest'

import type { ProviderInfo, TargetDraft, TargetInfo } from '@/types'
import { buildDraftChanges, getModelOptions, getProvidersForSource, getStrengthOptions, mergeDraft } from '@/utils/config'

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
})
