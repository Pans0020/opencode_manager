import type { ConfigSource, DraftChange, ProviderInfo, TargetDraft, TargetInfo } from '@/types'

export function getProvidersForSource(
  providersBySource: Partial<Record<ConfigSource, ProviderInfo[]>> | undefined,
  fallbackProviders: ProviderInfo[],
  source: ConfigSource,
) {
  return providersBySource?.[source] ?? fallbackProviders
}

export function getModelOptions(providers: ProviderInfo[], providerId: string | null) {
  return providers.find((provider) => provider.id === providerId)?.models ?? []
}

export function getStrengthOptions(
  providers: ProviderInfo[],
  providerId: string | null,
  modelId: string | null,
) {
  return getModelOptions(providers, providerId).find((model) => model.id === modelId)?.strengthOptions ?? []
}

export function getBatchProviderTargetIds(targets: TargetInfo[], source: ConfigSource) {
  return targets
    .filter((target) => {
      if (target.source !== source) {
        return false
      }
      return source === 'opencode' ? target.visible !== false : true
    })
    .map((target) => target.id)
}

export function shouldShowStrengthControl(
  target: TargetInfo,
  providers: ProviderInfo[],
  draft: TargetDraft | undefined,
) {
  if (target.kind === 'default') {
    return false
  }
  return getStrengthOptions(providers, draft?.provider ?? null, draft?.model ?? null).length > 0
}

export function getValidProviderIdForSource(providerId: string | null, providers: ProviderInfo[]) {
  if (!providerId) {
    return null
  }
  return providers.some((provider) => provider.id === providerId) ? providerId : null
}

export function mergeDraft(
  current: TargetDraft,
  providers: ProviderInfo[],
  patch: Partial<TargetDraft>,
): TargetDraft {
  const next = { ...current, ...patch }

  if (patch.provider && patch.provider !== current.provider) {
    const nextModels = getModelOptions(providers, patch.provider)
    const matchedModel = nextModels.find((m) => m.id === current.model)

    if (matchedModel) {
      const strengths = matchedModel.strengthOptions ?? []
      const nextStrength = strengths.includes(current.strength ?? '') 
        ? current.strength 
        : (strengths[0] ?? null)
        
      return {
        provider: patch.provider,
        model: matchedModel.id,
        strength: nextStrength,
      }
    }

    const firstModel = nextModels[0] ?? null
    const firstStrength = firstModel?.strengthOptions?.[0] ?? null
    return {
      provider: patch.provider,
      model: firstModel?.id ?? null,
      strength: firstStrength,
    }
  }

  if (patch.model && patch.model !== current.model) {
    const strengths = getStrengthOptions(providers, next.provider, patch.model)
    return {
      ...next,
      strength: strengths.includes(next.strength ?? '') ? next.strength : (strengths[0] ?? null),
    }
  }

  if (patch.strength !== undefined) {
    return next
  }

  return next
}

export function buildDraftChanges(
  targets: TargetInfo[],
  drafts: Record<string, TargetDraft>,
): DraftChange[] {
  return targets
    .map((target) => {
      const draft = drafts[target.id]
      if (!draft || !draft.provider || !draft.model) {
        return null
      }

      const changed =
        draft.provider !== target.currentProvider ||
        draft.model !== target.currentModel ||
        (draft.strength ?? null) !== (target.currentStrength ?? null)

      if (!changed) {
        return null
      }

      return {
        targetId: target.id,
        provider: draft.provider,
        model: draft.model,
        strength: draft.strength,
      }
    })
    .filter((item): item is DraftChange => item !== null)
}
