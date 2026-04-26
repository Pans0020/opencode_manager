<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'

import { useConfigStore } from '@/store/config'
import { useVisibilityStore } from '@/store/visibility'
import { buildVisibilitySections } from '@/utils/visibility'

const configStore = useConfigStore()
const visibilityStore = useVisibilityStore()

const { error, loading, saving, targets, visibilityRules } = storeToRefs(visibilityStore)
const sections = computed(() => buildVisibilitySections(targets.value, visibilityRules.value))

function getKindLabel(kind: string) {
  if (kind === 'category') {
    return 'sub'
  }
  return kind
}

async function handleSave() {
  await visibilityStore.save()
  await configStore.reload()
  ElMessage.success('显示规则已更新')
}

onMounted(async () => {
  if (!visibilityStore.settings) {
    await visibilityStore.load()
  }
})
</script>

<template>
  <section class="content-shell">
    <header class="toolbar">
      <div class="toolbar-copy">
        <h2>显示管理</h2>
      </div>

      <div class="toolbar-group">
        <el-button :loading="loading" @click="visibilityStore.load">重读</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存规则</el-button>
      </div>
    </header>

    <div class="board-wrapper">
      <el-alert v-if="error" :title="error" type="error" show-icon class="alert" style="margin-bottom: 20px;" />

      <section class="board">
        <div class="section" style="padding: 0; background: transparent; border: none; box-shadow: none;">
          <el-tabs type="border-card">
            <el-tab-pane :label="`OpenCode (${sections.opencode.length})`">
              <div class="visibility-grid">
                <div v-for="item in sections.opencode" :key="item.target.id" class="visibility-card">
                  <div class="vis-header">
                    <strong :title="item.target.id">{{ item.target.name }}</strong>
                    <el-switch
                      size="small"
                      :model-value="visibilityStore.drafts[item.target.id]?.visible ?? true"
                      @update:model-value="(value: boolean) => visibilityStore.updateRule(item.target.id, { visible: value })"
                    />
                  </div>
                  <div class="vis-meta">
                    <span>{{ getKindLabel(item.target.kind) }}</span>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane :label="`OMO Agents (${sections.omoAgents.length})`">
              <div class="visibility-grid">
                <div v-for="item in sections.omoAgents" :key="item.target.id" class="visibility-card-extended">
                  <div class="vis-header">
                    <strong :title="item.target.id">{{ item.target.name }}</strong>
                    <el-switch
                      size="small"
                      :model-value="visibilityStore.drafts[item.target.id]?.visible ?? true"
                      @update:model-value="(value: boolean) => visibilityStore.updateRule(item.target.id, { visible: value })"
                    />
                  </div>
                  <div class="vis-actions-row">
                    <el-select
                      size="small"
                      class="kind-select"
                      :model-value="visibilityStore.drafts[item.target.id]?.kindOverride ?? 'agent'"
                      @update:model-value="(value: 'agent' | 'subagent') => visibilityStore.updateRule(item.target.id, { kindOverride: value })"
                    >
                      <el-option label="agent" value="agent" />
                      <el-option label="subagent" value="subagent" />
                    </el-select>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane :label="`OMO Subagents (${sections.omoSubagents.length})`">
              <div class="visibility-grid">
                <div v-for="item in sections.omoSubagents" :key="item.target.id" class="visibility-card-extended">
                  <div class="vis-header">
                    <strong :title="item.target.id">{{ item.target.name }}</strong>
                    <el-switch
                      size="small"
                      :model-value="visibilityStore.drafts[item.target.id]?.visible ?? true"
                      @update:model-value="(value: boolean) => visibilityStore.updateRule(item.target.id, { visible: value })"
                    />
                  </div>
                  <div class="vis-actions-row">
                    <el-select
                      size="small"
                      class="kind-select"
                      :model-value="visibilityStore.drafts[item.target.id]?.kindOverride ?? 'subagent'"
                      @update:model-value="(value: 'agent' | 'subagent') => visibilityStore.updateRule(item.target.id, { kindOverride: value })"
                    >
                      <el-option label="agent" value="agent" />
                      <el-option label="subagent" value="subagent" />
                    </el-select>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </section>
    </div>
  </section>
</template>
