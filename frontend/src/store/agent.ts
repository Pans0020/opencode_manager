import { ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchAgentSettings, previewAgentSettings, applyAgentSettings } from '@/api'
import type { AgentDraft, ApplyResponse, ConfigSource, PreviewResponse } from '@/types'
import { createAgentDrafts, serializeAgentDrafts } from '@/utils/agent-form'

export const useAgentStore = defineStore('agent', () => {
  const loading = ref(false)
  const previewLoading = ref(false)
  const applying = ref(false)
  const error = ref<string | null>(null)
  
  const agents = ref<AgentDraft[]>([])
  const availableSources = ref<ConfigSource[]>(['opencode'])
  const configPaths = ref<Record<string, string>>({})
  const preview = ref<PreviewResponse | null>(null)
  const applyResult = ref<ApplyResponse | null>(null)
  const nextDraftId = ref(1)

  async function load() {
    loading.value = true
    error.value = null
    try {
      const payload = await fetchAgentSettings()
      agents.value = createAgentDrafts(payload.agents)
      availableSources.value = payload.availableSources
      configPaths.value = payload.configPaths
      preview.value = null
      applyResult.value = null
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载失败'
    } finally {
      loading.value = false
    }
  }

  async function previewDrafts() {
    previewLoading.value = true
    error.value = null
    try {
      preview.value = await previewAgentSettings(serializeAgentDrafts(agents.value))
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
      applyResult.value = await applyAgentSettings(serializeAgentDrafts(agents.value))
      await load()
    } catch (err) {
      error.value = err instanceof Error ? err.message : '应用失败'
    } finally {
      applying.value = false
    }
  }

  function createClientKey(source: ConfigSource) {
    const key = `${source}:new:${nextDraftId.value}`
    nextDraftId.value += 1
    return key
  }

  return {
    agents,
    availableSources,
    configPaths,
    loading,
    error,
    preview,
    applyResult,
    previewLoading,
    applying,
    load,
    previewDrafts,
    applyDrafts,
    createClientKey,
  }
})
