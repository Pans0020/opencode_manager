<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'

import { useConfigStore } from '@/store/config'
import type { TargetInfo } from '@/types'
import {
  getBatchProviderTargetIds,
  getModelOptions,
  getStrengthOptions,
  getValidProviderIdForSource,
} from '@/utils/config'
import { getDefaultSourceTab, getVisibleTargetsBySource, type SourceTab } from '@/utils/source-tabs'
import { getTargetKindLabel, groupTargetsByTab } from '@/utils/target-groups'

const store = useConfigStore()
const {
  applyResult,
  applying,
  draftChanges,
  drafts,
  error,
  filteredTargets,
  filters,
  loading,
  overview,
  preview,
  previewLoading,
  targets,
} = storeToRefs(store)

const activeSource = ref<SourceTab>(getDefaultSourceTab())

const batchProviderId = ref<string | null>(null)
const activeProviders = computed(() => store.providersForSource(activeSource.value))

function targetProviders(target: TargetInfo) {
  return store.providersForTarget(target)
}

function handleBatchApply() {
  if (!batchProviderId.value) return

  const targetIds = getBatchProviderTargetIds(targets.value, activeSource.value)

  store.batchUpdateDrafts(targetIds, {
    provider: batchProviderId.value,
  })

  ElMessage.success(`已将 ${sourceMeta[activeSource.value].title} 供应商切换为 ${batchProviderId.value}`)
}

const sourceMeta: Record<SourceTab, { title: string; tone: string; description: string }> = {
  opencode: {
    title: 'OpenCode',
    tone: 'control',
    description: '统一切换当前可见的 OpenCode agent 模型配置。',
  },
  omo: {
    title: 'OMO',
    tone: 'orchestration',
    description: '区分主 agent 和 subagent，分别管理 oh-my-openagent 的模型配置。',
  },
}

const visibleTargets = computed(() => getVisibleTargetsBySource(filteredTargets.value, activeSource.value))
const omoTabs = computed(() => groupTargetsByTab(visibleTargets.value, overview.value?.customTabs ?? []))

const previewVisible = computed({
  get: () => Boolean(preview.value),
  set: (value: boolean) => {
    if (!value) {
      store.preview = null
    }
  },
})

function switchSource(next: SourceTab) {
  activeSource.value = next
  filters.value.source = next
}

watch(activeProviders, (providers) => {
  batchProviderId.value = getValidProviderIdForSource(batchProviderId.value, providers)
})

async function handlePreview() {
  await store.previewDrafts()
  if (!preview.value?.files.length) {
    ElMessage.info('当前没有需要应用的改动')
  }
}

async function handleApply() {
  await store.applyDrafts()
  if (applyResult.value) {
    ElMessage.success('配置已写回文件')
  }
}

onMounted(async () => {
  filters.value.source = activeSource.value
  if (!overview.value) {
    await store.load()
  }
})
</script>

<template>
  <section class="content-shell">
    <header class="toolbar">
      <div class="toolbar-copy">
        <h2>{{ sourceMeta[activeSource].title }}</h2>
      </div>

      <div class="toolbar-group">
        <div class="inline-tabs">
          <button type="button" class="mini-tab" :class="{ active: activeSource === 'opencode' }" @click="switchSource('opencode')">
            OpenCode
          </button>
          <button type="button" class="mini-tab" :class="{ active: activeSource === 'omo' }" @click="switchSource('omo')">
            OMO
          </button>
        </div>
        <el-input v-model="filters.keyword" placeholder="搜索 agent" clearable style="width: 140px" />
        <el-switch v-model="filters.changedOnly" inline-prompt active-text="已改" inactive-text="全部" />
        <el-button :loading="loading" @click="store.reload">重读</el-button>
        <el-button type="primary" :disabled="draftChanges.length === 0" :loading="previewLoading" @click="handlePreview">
          应用
        </el-button>
      </div>
    </header>

    <div class="board-wrapper">
      <div class="meta-strip" v-if="overview">
        <div class="meta-pill">
          <span>OpenCode</span>
          <strong>{{ overview.configPaths.opencode }}</strong>
        </div>
        <div class="meta-pill">
          <span>OMO</span>
          <strong>{{ overview.configPaths.omo }}</strong>
        </div>
      </div>

      <div
        class="batch-bar"
        style="
          margin-bottom: 24px;
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          background: var(--bg-card);
          border: 1px solid var(--border);
          border-radius: 12px;
        "
      >
        <span style="font-size: 13px; color: var(--text-dim); font-weight: 500">一键设置 {{ sourceMeta[activeSource].title }} 供应商:</span>
        <el-select v-model="batchProviderId" placeholder="选择供应商" style="width: 150px">
          <el-option v-for="p in activeProviders" :key="p.id" :label="p.label" :value="p.id" />
        </el-select>
        <el-button type="primary" @click="handleBatchApply" :disabled="!batchProviderId">
          {{ activeSource === 'opencode' ? '应用到当前可见 OpenCode' : '应用到所有 OMO Agent' }}
        </el-button>
        <div style="font-size: 12px; color: var(--text-dim); margin-left: auto">
          {{ activeSource === 'opencode' ? '此操作只更新当前可见的 OpenCode 项' : '此操作将更新所有 OMO Agent (包括 Atlas/Sisyphus 等)' }}
        </div>
      </div>

      <el-alert v-if="error" :title="error" type="error" show-icon class="alert" style="margin-bottom: 12px;" />

      <section class="board">
        <div class="section" v-if="activeSource === 'omo'" style="padding: 0; background: transparent; border: none;">
          <el-tabs type="border-card" tab-position="left">
            <template v-for="(targets, tabName) in omoTabs" :key="tabName">
              <el-tab-pane v-if="targets.length > 0" :label="`${tabName} (${targets.length})`">
                <div class="target-grid" style="padding: 12px 0;">
                  <article v-for="target in targets" :key="target.id" class="target-card">
                    <div class="target-header">
                      <div>
                        <h4>{{ target.name }}</h4>
                        <p>{{ getTargetKindLabel(target) }}</p>
                      </div>
                    </div>

                    <div class="field-grid">
                      <label>
                        <span>Provider</span>
                        <el-select :model-value="drafts[target.id]?.provider" @update:model-value="(value: string) => store.updateDraft(target.id, { provider: value })">
                          <el-option v-for="provider in targetProviders(target)" :key="provider.id" :label="provider.label" :value="provider.id" />
                        </el-select>
                      </label>
                      <label>
                        <span>Model</span>
                        <el-select :model-value="drafts[target.id]?.model" @update:model-value="(value: string) => store.updateDraft(target.id, { model: value })">
                          <el-option
                            v-for="model in getModelOptions(targetProviders(target), drafts[target.id]?.provider ?? null)"
                            :key="model.id"
                            :label="model.label"
                            :value="model.id"
                          />
                        </el-select>
                      </label>
                      <label v-if="getStrengthOptions(targetProviders(target), drafts[target.id]?.provider ?? null, drafts[target.id]?.model ?? null).length > 0">
                        <span>Strength</span>
                        <el-select :model-value="drafts[target.id]?.strength" @update:model-value="(value: string) => store.updateDraft(target.id, { strength: value })">
                          <el-option
                            v-for="strength in getStrengthOptions(targetProviders(target), drafts[target.id]?.provider ?? null, drafts[target.id]?.model ?? null)"
                            :key="strength"
                            :label="strength.toLowerCase() === 'none' ? 'Default' : strength"
                            :value="strength"
                          />
                        </el-select>
                      </label>
                    </div>
                  </article>
                </div>
              </el-tab-pane>
            </template>
          </el-tabs>
        </div>

        <div class="section" v-else>
          <div class="target-grid">
            <article v-for="target in visibleTargets" :key="target.id" class="target-card">
              <div class="target-header">
                <div>
                  <h4>{{ target.name }}</h4>
                  <p>{{ getTargetKindLabel(target) }}</p>
                </div>
              </div>
              <div class="field-grid">
                <label>
                  <span>Provider</span>
                  <el-select :model-value="drafts[target.id]?.provider" @update:model-value="(value: string) => store.updateDraft(target.id, { provider: value })">
                    <el-option v-for="provider in targetProviders(target)" :key="provider.id" :label="provider.label" :value="provider.id" />
                  </el-select>
                </label>
                <label>
                  <span>Model</span>
                  <el-select :model-value="drafts[target.id]?.model" @update:model-value="(value: string) => store.updateDraft(target.id, { model: value })">
                    <el-option
                      v-for="model in getModelOptions(targetProviders(target), drafts[target.id]?.provider ?? null)"
                      :key="model.id"
                      :label="model.label"
                      :value="model.id"
                    />
                  </el-select>
                </label>
                <label v-if="getStrengthOptions(targetProviders(target), drafts[target.id]?.provider ?? null, drafts[target.id]?.model ?? null).length > 0">
                  <span>Strength</span>
                  <el-select :model-value="drafts[target.id]?.strength" @update:model-value="(value: string) => store.updateDraft(target.id, { strength: value })">
                    <el-option
                      v-for="strength in getStrengthOptions(targetProviders(target), drafts[target.id]?.provider ?? null, drafts[target.id]?.model ?? null)"
                      :key="strength"
                      :label="strength.toLowerCase() === 'none' ? 'Default' : strength"
                      :value="strength"
                    />
                  </el-select>
                </label>
              </div>
            </article>
          </div>
        </div>
      </section>
    </div>

    <el-dialog v-model="previewVisible" width="600px" title="改动预览">
      <template v-if="preview">
        <div v-for="file in preview.files" :key="file.filePath" class="diff-file">
          <div class="diff-list">
            <div v-for="item in file.items" :key="`${file.filePath}-${item.path}`" class="diff-row">
              <strong>{{ item.path }}</strong>
              <span>{{ item.oldValue ?? '-' }} → {{ item.newValue ?? '-' }}</span>
            </div>
          </div>
        </div>
      </template>

      <template #footer>
        <el-button @click="previewVisible = false">取消</el-button>
        <el-button type="primary" :loading="applying" @click="handleApply">确认</el-button>
      </template>
    </el-dialog>
  </section>
</template>
