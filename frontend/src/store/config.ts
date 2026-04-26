import { computed, reactive, ref } from 'vue'
import { defineStore } from 'pinia'

import { applyChanges, fetchOverview, previewChanges, reloadOverview } from '@/api'
import type {
  ApplyResponse,
  ConfigSource,
  OverviewResponse,
  PreviewResponse,
  ProviderInfo,
  TargetDraft,
  TargetInfo,
} from '@/types'
import { buildDraftChanges, getProvidersForSource, mergeDraft } from '@/utils/config'

type SourceFilter = 'all' | 'opencode' | 'omo'

function createDrafts(targets: TargetInfo[]): Record<string, TargetDraft> {
  return Object.fromEntries(
    targets.map((target) => [
      target.id,
      {
        provider: target.currentProvider,
        model: target.currentModel,
        strength: target.currentStrength,
      },
    ]),
  )
}

export const useConfigStore = defineStore('config', () => {
  const overview = ref<OverviewResponse | null>(null)
  const preview = ref<PreviewResponse | null>(null)
  const applyResult = ref<ApplyResponse | null>(null)
  const loading = ref(false)
  const previewLoading = ref(false)
  const applying = ref(false)
  const error = ref<string | null>(null)

  const filters = reactive({
    source: 'all' as SourceFilter,
    keyword: '',
    changedOnly: false,
  })

  const drafts = reactive<Record<string, TargetDraft>>({})

  const providers = computed<ProviderInfo[]>(() => overview.value?.providers ?? [])
  const providersBySource = computed<Partial<Record<ConfigSource, ProviderInfo[]>>>(
    () => overview.value?.providersBySource ?? {},
  )
  const targets = computed<TargetInfo[]>(() => overview.value?.targets ?? [])
  const draftChanges = computed(() => buildDraftChanges(targets.value, drafts))

  function providersForSource(source: ConfigSource) {
    return getProvidersForSource(providersBySource.value, providers.value, source)
  }

  function providersForTarget(target: TargetInfo) {
    return providersForSource(target.source)
  }

  const filteredTargets = computed(() => {
    const keyword = filters.keyword.trim().toLowerCase()
    return targets.value.filter((target) => {
      // 只有可见的才显示在列表里
      if (!target.visible) {
        return false
      }

      if (filters.source !== 'all' && target.source !== filters.source) {
        return false
      }

      if (filters.changedOnly && !draftChanges.value.some((change) => change.targetId === target.id)) {
        return false
      }

      if (!keyword) {
        return true
      }

      const haystack = `${target.name} ${target.kind} ${target.source}`.toLowerCase()
      return haystack.includes(keyword)
    })
  })

  function hydrateDrafts(nextTargets: TargetInfo[]) {
    for (const key of Object.keys(drafts)) {
      delete drafts[key]
    }
    Object.assign(drafts, createDrafts(nextTargets))
  }

  async function load() {
    loading.value = true
    error.value = null
    try {
      const payload = await fetchOverview()
      overview.value = payload
      hydrateDrafts(payload.targets)
      preview.value = null
      applyResult.value = null
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载失败'
    } finally {
      loading.value = false
    }
  }

  function updateDraft(targetId: string, patch: Partial<TargetDraft>) {
    const current = drafts[targetId]
    const target = targets.value.find((item) => item.id === targetId)
    if (!current) {
      return
    }
    drafts[targetId] = mergeDraft(current, target ? providersForTarget(target) : providers.value, patch)
  }

  function batchUpdateDrafts(targetIds: string[], patch: Partial<TargetDraft>) {
    for (const targetId of targetIds) {
      const target = targets.value.find((t) => t.id === targetId)
      if (!target) continue

      if (patch.provider && !target.availableProviders.includes(patch.provider)) {
        continue
      }

      if (patch.provider !== undefined) {
        updateDraft(targetId, { provider: patch.provider })
      }
      if (patch.model !== undefined) {
        updateDraft(targetId, { model: patch.model })
      }
      if (patch.strength !== undefined) {
        updateDraft(targetId, { strength: patch.strength })
      }
    }
  }

  async function previewDrafts() {
    previewLoading.value = true
    error.value = null
    try {
      preview.value = await previewChanges(draftChanges.value)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '预览失败'
    } finally {
      previewLoading.value = false
    }
  }

  async function applyDrafts() {
    applying.value = true
    error.value = null
    try {
      applyResult.value = await applyChanges(draftChanges.value)
      const payload = await reloadOverview()
      overview.value = payload
      hydrateDrafts(payload.targets)
      preview.value = null
    } catch (err) {
      error.value = err instanceof Error ? err.message : '应用失败'
    } finally {
      applying.value = false
    }
  }

  async function reload() {
    loading.value = true
    error.value = null
    try {
      const payload = await reloadOverview()
      overview.value = payload
      hydrateDrafts(payload.targets)
      preview.value = null
      applyResult.value = null
    } catch (err) {
      error.value = err instanceof Error ? err.message : '刷新失败'
    } finally {
      loading.value = false
    }
  }

  return {
    applyDrafts,
    applyResult,
    applying,
    draftChanges,
    drafts,
    error,
    filteredTargets,
    filters,
    load,
    loading,
    overview,
    preview,
    previewDrafts,
    previewLoading,
    providers,
    providersBySource,
    providersForSource,
    providersForTarget,
    reload,
    targets,
    updateDraft,
    batchUpdateDrafts,
  }
})
