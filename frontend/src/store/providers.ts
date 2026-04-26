import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { applyProviderSettings, fetchProviderSettings, previewProviderSettings } from '@/api'
import type { ApplyResponse, ConfigSource, PreviewResponse, ProviderDraft } from '@/types'
import {
  createEmptyModelDraft,
  createEmptyProviderDraft,
  createEmptyVariantDraft,
  createProviderDrafts,
  serializeProviderDrafts,
} from '@/utils/provider-form'

export const useProviderStore = defineStore('providers', () => {
  const drafts = ref<ProviderDraft[]>([])
  const selectedProviderIndex = ref(0)
  const loading = ref(false)
  const previewLoading = ref(false)
  const applying = ref(false)
  const preview = ref<PreviewResponse | null>(null)
  const applyResult = ref<ApplyResponse | null>(null)
  const error = ref<string | null>(null)
  const selectedSource = ref<ConfigSource>('opencode')
  const availableSources = ref<ConfigSource[]>(['opencode'])
  const configPath = ref<string | null>(null)

  const selectedProvider = computed(
    () => drafts.value[selectedProviderIndex.value] ?? drafts.value[0] ?? null,
  )

  async function load(source: ConfigSource = selectedSource.value) {
    loading.value = true
    error.value = null
    try {
      const payload = await fetchProviderSettings(source)
      selectedSource.value = payload.source
      availableSources.value = payload.availableSources
      configPath.value = payload.configPath
      drafts.value = createProviderDrafts(payload.providers)
      selectedProviderIndex.value = 0
      preview.value = null
      applyResult.value = null
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载 Provider 配置失败'
    } finally {
      loading.value = false
    }
  }

  function selectProvider(providerId: string) {
    const nextIndex = drafts.value.findIndex((provider) => provider.id === providerId)
    selectedProviderIndex.value = nextIndex >= 0 ? nextIndex : 0
  }

  function selectProviderIndex(index: number) {
    selectedProviderIndex.value = index >= 0 && index < drafts.value.length ? index : 0
  }

  async function selectSource(source: ConfigSource) {
    if (source === selectedSource.value) return
    await load(source)
  }

  function addProvider() {
    const provider = createEmptyProviderDraft()
    provider.id = `new-provider-${drafts.value.length + 1}`
    drafts.value.push(provider)
    selectedProviderIndex.value = drafts.value.length - 1
  }

  function removeProvider(providerId: string) {
    const removedIndex = drafts.value.findIndex((provider) => provider.id === providerId)
    drafts.value = drafts.value.filter((provider) => provider.id !== providerId)
    if (drafts.value.length === 0) {
      selectedProviderIndex.value = 0
      return
    }
    selectedProviderIndex.value = Math.min(
      removedIndex >= 0 ? removedIndex : selectedProviderIndex.value,
      drafts.value.length - 1,
    )
  }

  function addModel(providerId: string) {
    const provider = drafts.value.find((item) => item.id === providerId)
    if (!provider) return
    const model = createEmptyModelDraft()
    model.id = `new-model-${provider.models.length + 1}`
    provider.models.push(model)
  }

  function removeModel(providerId: string, modelId: string) {
    const provider = drafts.value.find((item) => item.id === providerId)
    if (!provider) return
    provider.models = provider.models.filter((model) => model.id !== modelId)
  }

  function addVariant(providerId: string, modelId: string) {
    const model = drafts.value
      .find((item) => item.id === providerId)
      ?.models.find((item) => item.id === modelId)
    if (!model) return
    const variant = createEmptyVariantDraft()
    variant.id = `variant-${model.variants.length + 1}`
    model.variants.push(variant)
  }

  function removeVariant(providerId: string, modelId: string, variantId: string) {
    const model = drafts.value
      .find((item) => item.id === providerId)
      ?.models.find((item) => item.id === modelId)
    if (!model) return
    model.variants = model.variants.filter((variant) => variant.id !== variantId)
  }

  async function previewDrafts() {
    previewLoading.value = true
    error.value = null
    try {
      preview.value = await previewProviderSettings(serializeProviderDrafts(drafts.value), selectedSource.value)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '预览 Provider 配置失败'
      throw err
    } finally {
      previewLoading.value = false
    }
  }

  async function applyDrafts() {
    applying.value = true
    error.value = null
    try {
      applyResult.value = await applyProviderSettings(serializeProviderDrafts(drafts.value), selectedSource.value)
      await load(selectedSource.value)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '写回 Provider 配置失败'
      throw err
    } finally {
      applying.value = false
    }
  }

  return {
    addModel,
    addProvider,
    addVariant,
    applyDrafts,
    applyResult,
    applying,
    availableSources,
    configPath,
    drafts,
    error,
    load,
    loading,
    preview,
    previewDrafts,
    previewLoading,
    removeModel,
    removeProvider,
    removeVariant,
    selectProvider,
    selectProviderIndex,
    selectSource,
    selectedProvider,
    selectedProviderIndex,
    selectedSource,
  }
})
