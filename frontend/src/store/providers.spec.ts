import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useProviderStore } from '@/store/providers'
import type { ProviderDraft, ProviderModelDraft } from '@/types'

function providerDraft(id: string): ProviderDraft {
  return {
    clientKey: `provider:${id}`,
    id,
    npm: '',
    apiKey: '',
    baseURL: '',
    extraOptionsText: '{}',
    models: [],
  }
}

function modelDraft(id: string): ProviderModelDraft {
  return {
    clientKey: `model:${id}`,
    id,
    name: '',
    maxTokensText: '',
    limitText: '{}',
    costText: '{}',
    optionsText: '{}',
    variants: [],
  }
}

describe('provider store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('keeps the selected provider stable when its id is edited', () => {
    const store = useProviderStore()
    store.drafts = [providerDraft('OpenAI'), providerDraft('Anthropic')]

    store.selectProvider(store.drafts[1].clientKey)
    store.selectedProvider!.id = 'Claude'

    expect(store.selectedProvider?.id).toBe('Claude')
  })

  it('adds models to the selected provider by stable key after provider id edits', () => {
    const store = useProviderStore()
    store.drafts = [providerDraft('OpenAI'), providerDraft('Anthropic')]
    store.selectProviderIndex(1)
    store.selectedProvider!.id = 'OpenAI'

    store.addModel(store.selectedProvider!.clientKey)

    expect(store.drafts[0].models).toHaveLength(0)
    expect(store.drafts[1].models).toHaveLength(1)
  })

  it('removes only the selected model by stable key after model id edits', () => {
    const store = useProviderStore()
    const provider = providerDraft('OpenAI')
    provider.models = [
      { ...modelDraft('same-id'), clientKey: 'model:first' },
      { ...modelDraft('same-id'), clientKey: 'model:second' },
    ]
    store.drafts = [provider]

    store.removeModel(provider.clientKey, 'model:second')

    expect(store.drafts[0].models).toHaveLength(1)
    expect(store.drafts[0].models[0].clientKey).toBe('model:first')
  })

  it('removes only the selected variant by stable key after variant id edits', () => {
    const store = useProviderStore()
    const provider = providerDraft('OpenAI')
    const model = modelDraft('gpt')
    model.variants = [
      { clientKey: 'variant:first', id: 'same-id', valueText: '{}' },
      { clientKey: 'variant:second', id: 'same-id', valueText: '{}' },
    ]
    provider.models = [model]
    store.drafts = [provider]

    store.removeVariant(provider.clientKey, model.clientKey, 'variant:second')

    expect(store.drafts[0].models[0].variants).toEqual([
      { clientKey: 'variant:first', id: 'same-id', valueText: '{}' },
    ])
  })
})
