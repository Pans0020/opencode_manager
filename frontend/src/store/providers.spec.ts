import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useProviderStore } from '@/store/providers'
import type { ProviderDraft } from '@/types'

function providerDraft(id: string): ProviderDraft {
  return {
    id,
    npm: '',
    apiKey: '',
    baseURL: '',
    extraOptionsText: '{}',
    models: [],
  }
}

describe('provider store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('keeps the selected provider stable when its id is edited', () => {
    const store = useProviderStore()
    store.drafts = [providerDraft('OpenAI'), providerDraft('Anthropic')]

    store.selectProvider('Anthropic')
    store.selectedProvider!.id = 'Claude'

    expect(store.selectedProvider?.id).toBe('Claude')
  })
})
