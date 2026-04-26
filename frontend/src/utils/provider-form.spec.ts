import { describe, expect, it } from 'vitest'

import type { ProviderEditableRecord } from '@/types'
import { createProviderDrafts, serializeProviderDrafts } from '@/utils/provider-form'

const providers: ProviderEditableRecord[] = [
  {
    id: 'OpenAI',
    npm: '@ai-sdk/openai',
    options: {
      apiKey: 'secret',
      baseURL: 'https://api.openai.com/v1',
      timeout: 30,
    },
    models: [
      {
        id: 'gpt-5.4',
        name: 'GPT-5.4',
        limit: { context: 1000 },
        cost: { input: 1 },
        options: { reasoningEffort: 'high' },
        maxTokens: 2048,
        variants: {
          high: { reasoningEffort: 'high' },
        },
      },
    ],
  },
]

describe('provider draft transforms', () => {
  it('creates editable drafts and serializes them back to provider payloads', () => {
    const drafts = createProviderDrafts(providers)
    drafts[0].baseURL = 'https://custom.test/v1'
    drafts[0].extraOptionsText = '{"timeout":45,"region":"us"}'
    drafts[0].models[0].variants[0].valueText = '{"reasoningEffort":"medium"}'

    const serialized = serializeProviderDrafts(drafts)

    expect(serialized[0].options).toEqual({
      apiKey: 'secret',
      baseURL: 'https://custom.test/v1',
      timeout: 45,
      region: 'us',
    })
    expect(serialized[0].models[0].variants).toEqual({
      high: { reasoningEffort: 'medium' },
    })
  })
})
