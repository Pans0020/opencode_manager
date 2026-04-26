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
    id: '',
    valueText: '{}',
  }
}

export function createProviderDrafts(providers: ProviderEditableRecord[]): ProviderDraft[] {
  return providers.map((provider) => {
    const options = { ...provider.options }
    const apiKey = typeof options.apiKey === 'string' ? options.apiKey : ''
    const baseURL = typeof options.baseURL === 'string' ? options.baseURL : ''
    delete options.apiKey
    delete options.baseURL

    return {
      id: provider.id,
      npm: provider.npm ?? '',
      apiKey,
      baseURL,
      extraOptionsText: stableJson(options),
      models: provider.models.map((model) => ({
        id: model.id,
        name: model.name ?? '',
        maxTokensText: model.maxTokens == null ? '' : String(model.maxTokens),
        limitText: stableJson(model.limit),
        costText: stableJson(model.cost),
        optionsText: stableJson(model.options),
        variants: Object.entries(model.variants).map(([id, value]) => ({
          id,
          valueText: stableJson(value),
        })),
      })),
    }
  })
}

export function serializeProviderDrafts(drafts: ProviderDraft[]): ProviderEditableRecord[] {
  return drafts.map((provider) => {
    if (!provider.id.trim()) {
      throw new Error('Provider id 不能为空')
    }

    const extraOptions = parseJson(provider.extraOptionsText, `Provider ${provider.id} 的额外 options`)
    const options: Record<string, unknown> = { ...extraOptions }
    if (provider.apiKey.trim()) {
      options.apiKey = provider.apiKey.trim()
    }
    if (provider.baseURL.trim()) {
      options.baseURL = provider.baseURL.trim()
    }

    return {
      id: provider.id.trim(),
      npm: provider.npm.trim() || null,
      options,
      models: provider.models.map((model) => {
        if (!model.id.trim()) {
          throw new Error(`Provider ${provider.id} 下存在空的 model id`)
        }
        const variants = Object.fromEntries(
          model.variants.map((variant) => {
            if (!variant.id.trim()) {
              throw new Error(`Model ${model.id} 下存在空的 variant id`)
            }
            return [
              variant.id.trim(),
              parseJson(variant.valueText, `Variant ${variant.id} 的配置`),
            ]
          }),
        )

        return {
          id: model.id.trim(),
          name: model.name.trim() || null,
          limit: parseJson(model.limitText, `Model ${model.id} 的 limit`),
          cost: parseJson(model.costText, `Model ${model.id} 的 cost`),
          options: parseJson(model.optionsText, `Model ${model.id} 的 options`),
          maxTokens: model.maxTokensText.trim() ? Number(model.maxTokensText) : null,
          variants,
        }
      }),
    }
  })
}
