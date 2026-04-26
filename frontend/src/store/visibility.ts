import { computed, reactive, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchVisibilitySettings, saveVisibilitySettings } from '@/api'
import type { TargetInfo, VisibilityRule, VisibilitySettingsResponse } from '@/types'

function createRulesMap(rules: VisibilityRule[]) {
  return Object.fromEntries(
    rules.map((rule) => [
      rule.targetId,
      {
        visible: rule.visible,
        kindOverride: rule.kindOverride,
      },
    ]),
  )
}

export const useVisibilityStore = defineStore('visibility', () => {
  const settings = ref<VisibilitySettingsResponse | null>(null)
  const loading = ref(false)
  const saving = ref(false)
  const error = ref<string | null>(null)
  const drafts = reactive<Record<string, { visible: boolean; kindOverride: 'agent' | 'subagent' | null; tabOverride: string | null }>>({})
  const customTabs = ref<string[]>([])

  const targets = computed<TargetInfo[]>(() => settings.value?.targets ?? [])
  const visibilityRules = computed<VisibilityRule[]>(() =>
    targets.value.map((target) => ({
      targetId: target.id,
      visible: drafts[target.id]?.visible ?? true,
      kindOverride: drafts[target.id]?.kindOverride ?? null,
      tabOverride: drafts[target.id]?.tabOverride ?? null,
    })),
  )

  function hydrate(payload: VisibilitySettingsResponse) {
    settings.value = payload
    for (const key of Object.keys(drafts)) {
      delete drafts[key]
    }
    const map = Object.fromEntries(
      payload.visibilityRules.map((rule) => [
        rule.targetId,
        {
          visible: rule.visible,
          kindOverride: rule.kindOverride,
          tabOverride: rule.tabOverride ?? null,
        },
      ]),
    )
    Object.assign(drafts, map)
    customTabs.value = [...(payload.customTabs || [])]
  }

  async function load() {
    loading.value = true
    error.value = null
    try {
      hydrate(await fetchVisibilitySettings())
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载显示配置失败'
    } finally {
      loading.value = false
    }
  }

  async function save() {
    saving.value = true
    error.value = null
    try {
      hydrate(await saveVisibilitySettings(visibilityRules.value, customTabs.value))
    } catch (err) {
      error.value = err instanceof Error ? err.message : '保存显示配置失败'
      throw err
    } finally {
      saving.value = false
    }
  }

  function updateRule(targetId: string, patch: Partial<{ visible: boolean; kindOverride: 'agent' | 'subagent' | null; tabOverride: string | null }>) {
    drafts[targetId] = {
      visible: patch.visible ?? drafts[targetId]?.visible ?? true,
      kindOverride: patch.kindOverride !== undefined ? patch.kindOverride : (drafts[targetId]?.kindOverride ?? null),
      tabOverride: patch.tabOverride !== undefined ? patch.tabOverride : (drafts[targetId]?.tabOverride ?? null),
    }
  }

  return {
    drafts,
    customTabs,
    error,
    load,
    loading,
    save,
    saving,
    settings,
    targets,
    updateRule,
    visibilityRules,
  }
})
