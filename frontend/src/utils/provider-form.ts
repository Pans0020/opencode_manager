import type {
  ProviderDraft,
  ProviderEditableRecord,
  ProviderModelDraft,
  ProviderVariantDraft,
} from '@/types'

function stableJson(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2)
}

function parseJson(text: string, label: string): Record<string, unknown> {
  const trimmed = text.trim()
  if (!trimmed) {
    return {}
  }

  let parsed: unknown
  try {
    parsed = JSON.parse(trimmed)
  } catch (error) {
    throw new Error(`${label} 不是合法 JSON`)
  }

  if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
    throw new Error(`${label} 必须是 JSON 对象`)
  }

  return parsed as Record<string, unknown>
}

export function createEmptyProviderDraft(): ProviderDraft {
  return {
    clientKey: 'provider:new',
    id: '',
    npm: '',
    apiKey: '',
    baseURL: '',
    extraOptionsText: '{}',
    models: [],
  }
}

export function createEmptyModelDraft(): ProviderModelDraft {
  return {
    clientKey: 'model:new',
    id: '',
    name: '',
    maxTokensText: '',
    limitText: '{}',
    costText: '{}',
    optionsText: '{}',
    variants: [],
  }
}

export function createEmptyVariantDraft(): ProviderVariantDraft {
  return {
    clientKey: 'variant:new',
    id: '',
    valueText: '{}',
  }
}

export function createProviderDrafts(providers: ProviderEditableRecord[]): ProviderDraft[] {
  return providers.map((provider, providerIndex) => {
    const options = { ...provider.options }
    const apiKey = typeof options.apiKey === 'string' ? options.apiKey : ''
    const baseURL = typeof options.baseURL === 'string' ? options.baseURL : ''
    delete options.apiKey
    delete options.baseURL

    return {
      clientKey: `provider:${provider.id}:${providerIndex}`,
      id: provider.id,
      npm: provider.npm ?? '',
      apiKey,
      baseURL,
      extraOptionsText: stableJson(options),
      models: provider.models.map((model, modelIndex) => ({
        clientKey: `model:${model.id}:${providerIndex}-${modelIndex}`,
        id: model.id,
        name: model.name ?? '',
        maxTokensText: model.maxTokens == null ? '' : String(model.maxTokens),
        limitText: stableJson(model.limit),
        costText: stableJson(model.cost),
        optionsText: stableJson(model.options),
        variants: Object.entries(model.variants).map(([id, value], variantIndex) => ({
          clientKey: `variant:${id}:${providerIndex}-${modelIndex}-${variantIndex}`,
          id,
          valueText: stableJson(value),
        })),
      })),
    }
  })
}

export function serializeProviderDrafts(drafts: ProviderDraft[]): ProviderEditableRecord[] {
  const seenProviderIds = new Set<string>()

  return drafts.map((provider) => {
    if (!provider.id.trim()) {
      throw new Error('Provider id 不能为空')
    }
    const providerId = provider.id.trim()
    if (seenProviderIds.has(providerId)) {
      throw new Error(`重复的 provider id: ${providerId}`)
    }
    seenProviderIds.add(providerId)

    const extraOptions = parseJson(provider.extraOptionsText, `Provider ${providerId} 的额外 options`)
    const options: Record<string, unknown> = { ...extraOptions }
    if (provider.apiKey.trim()) {
      options.apiKey = provider.apiKey.trim()
    }
    if (provider.baseURL.trim()) {
      options.baseURL = provider.baseURL.trim()
    }
    const seenModelIds = new Set<string>()

    return {
      id: providerId,
      npm: provider.npm.trim() || null,
      options,
      models: provider.models.map((model) => {
        if (!model.id.trim()) {
          throw new Error(`Provider ${providerId} 下存在空的 model id`)
        }
        const modelId = model.id.trim()
        if (seenModelIds.has(modelId)) {
          throw new Error(`Provider ${providerId} 下存在重复的 model id: ${modelId}`)
        }
        seenModelIds.add(modelId)
        const seenVariantIds = new Set<string>()
        const variants: Record<string, Record<string, unknown>> = {}
        for (const variant of model.variants) {
          if (!variant.id.trim()) {
            throw new Error(`Model ${modelId} 下存在空的 variant id`)
          }
          const variantId = variant.id.trim()
          if (seenVariantIds.has(variantId)) {
            throw new Error(`Model ${modelId} 下存在重复的 variant id: ${variantId}`)
          }
          seenVariantIds.add(variantId)
          variants[variantId] = parseJson(variant.valueText, `Variant ${variantId} 的配置`)
        }

        return {
          id: modelId,
          name: model.name.trim() || null,
          limit: parseJson(model.limitText, `Model ${modelId} 的 limit`),
          cost: parseJson(model.costText, `Model ${modelId} 的 cost`),
          options: parseJson(model.optionsText, `Model ${modelId} 的 options`),
          maxTokens: model.maxTokensText.trim() ? Number(model.maxTokensText) : null,
          variants,
        }
      }),
    }
  })
}
