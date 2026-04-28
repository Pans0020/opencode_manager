<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage, ElMessageBox } from 'element-plus'

import { useAgentStore } from '@/store/agent'
import type { AgentDraft, ConfigSource } from '@/types'
import {
  createEmptyAgentDraft,
  duplicateAgentDraft,
  getDisplayAgents,
  getHiddenAgents,
  hasAgentIdInSource,
  isValidAgentId,
  shouldShowAgentSourceTabs,
} from '@/utils/agent-form'

const store = useAgentStore()
const {
  agents,
  availableSources,
  configPaths,
  error,
  loading,
  preview,
  previewLoading,
  applying,
  applyResult,
} = storeToRefs(store)

const activeSource = ref<ConfigSource>('opencode')
const activeAgentKey = ref<string | null>(null)

const sourceLabels: Record<ConfigSource, string> = {
  opencode: 'OpenCode',
  omo: 'OMO',
}

const showSourceTabs = computed(() => shouldShowAgentSourceTabs(availableSources.value))
const activeConfigPath = computed(() => {
  return activeSource.value === 'omo' ? configPaths.value.omoOpencode : configPaths.value.opencode
})
const displayAgents = computed(() => getDisplayAgents(agents.value, activeSource.value))

const hiddenAgents = computed(() => {
  return getHiddenAgents(agents.value, activeSource.value)
})

const activeAgent = computed(() => {
  return agents.value.find(a => a.clientKey === activeAgentKey.value) || null
})

const previewVisible = computed({
  get: () => Boolean(preview.value),
  set: (value: boolean) => {
    if (!value) {
      store.preview = null
    }
  },
})

// 添加 Agent 相关的弹窗状态
const addDialogVisible = ref(false)
const addMethod = ref<'restore' | 'duplicate' | 'new'>('restore')
const addSelectedHidden = ref<string>('')
const addDuplicateFrom = ref<string>('')
const addNewId = ref<string>('')

function selectFirstVisibleAgent() {
  activeAgentKey.value = displayAgents.value[0]?.clientKey ?? null
}

function ensureActiveSourceAndSelection() {
  if (!availableSources.value.includes(activeSource.value)) {
    activeSource.value = availableSources.value[0] ?? 'opencode'
  }
  if (!activeAgent.value || activeAgent.value.source !== activeSource.value) {
    selectFirstVisibleAgent()
  }
}

function switchSource(source: ConfigSource) {
  activeSource.value = source
  selectFirstVisibleAgent()
}

async function handleReload() {
  await store.load()
  ensureActiveSourceAndSelection()
}

function openAddDialog() {
  addMethod.value = hiddenAgents.value.length > 0 ? 'restore' : 'duplicate'
  addSelectedHidden.value = hiddenAgents.value.length > 0 ? hiddenAgents.value[0].clientKey : ''
  addDuplicateFrom.value = displayAgents.value.length > 0 ? displayAgents.value[0].clientKey : ''
  addNewId.value = ''
  addDialogVisible.value = true
}

function handleConfirmAdd() {
  let newId = ''
  let newRecord: AgentDraft | null = null

  if (addMethod.value === 'restore') {
    if (!addSelectedHidden.value) {
      ElMessage.warning('请选择一个被隐藏的 Agent')
      return
    }
    const target = agents.value.find(a => a.clientKey === addSelectedHidden.value && a.source === activeSource.value)
    if (target) {
      target.payload = { ...(target.payload ?? {}), mode: 'primary' }
      activeAgentKey.value = target.clientKey
      addDialogVisible.value = false
      return
    }
  } else if (addMethod.value === 'duplicate') {
    if (!addDuplicateFrom.value || !addNewId.value.trim()) {
      ElMessage.warning('请选择来源并输入新的 ID')
      return
    }
    newId = addNewId.value.trim()
    const source = agents.value.find(a => a.clientKey === addDuplicateFrom.value && a.source === activeSource.value)
    if (source) {
      newRecord = duplicateAgentDraft(source, newId, store.createClientKey(activeSource.value))
    }
  } else {
    if (!addNewId.value.trim()) {
      ElMessage.warning('请输入新的 ID')
      return
    }
    newId = addNewId.value.trim()
    newRecord = createEmptyAgentDraft(activeSource.value, store.createClientKey(activeSource.value))
    newRecord.id = newId
  }

  if (newRecord && newId) {
    if (hasAgentIdInSource(agents.value, activeSource.value, newId)) {
      ElMessage.warning('该 Agent ID 已存在')
      return
    }
    if (!isValidAgentId(newId)) {
      ElMessage.warning('Agent ID 只能包含字母、数字、冒号、下划线和连字符')
      return
    }
    agents.value.push(newRecord)
    activeAgentKey.value = newRecord.clientKey
    addDialogVisible.value = false
  }
}

function handleRemoveAgent(clientKey: string) {
  ElMessageBox.confirm('确定要删除或隐藏此 Agent 吗？', '警告', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    const target = agents.value.find(a => a.clientKey === clientKey)
    if (target && target.source === 'opencode' && target.payload?.mode === 'primary') {
        // 如果是 opencode 的 primary agent，可以只变成 subagent 来隐藏，也可以彻底删除
        // 这里直接删除
        const idx = agents.value.findIndex(a => a.clientKey === clientKey)
        if (idx !== -1) {
          agents.value.splice(idx, 1)
          if (activeAgentKey.value === clientKey) {
            selectFirstVisibleAgent()
          }
        }
    } else {
        const idx = agents.value.findIndex(a => a.clientKey === clientKey)
        if (idx !== -1) {
          agents.value.splice(idx, 1)
          if (activeAgentKey.value === clientKey) {
            selectFirstVisibleAgent()
          }
        }
    }
  }).catch(() => {})
}

async function handlePreview() {
  await store.previewDrafts()
  if (!preview.value?.files.length) {
    ElMessage.info('当前没有需要应用的改动')
  }
}

async function handleApply() {
  await store.applyDrafts()
  if (applyResult.value) {
    ElMessage.success('Agent 配置已保存')
    ensureActiveSourceAndSelection()
  }
}

onMounted(async () => {
  if (agents.value.length === 0) {
    await store.load()
  }
  ensureActiveSourceAndSelection()
})
</script>

<template>
  <section class="content-shell" style="height: 100%; display: flex; flex-direction: column;">
    <header class="toolbar">
      <div class="toolbar-copy">
        <h2>Agent(Tab) 管理</h2>
      </div>

      <div class="toolbar-group">
        <div v-if="showSourceTabs" class="inline-tabs">
          <button
            v-for="source in availableSources"
            :key="source"
            type="button"
            class="mini-tab"
            :class="{ active: activeSource === source }"
            @click="switchSource(source)"
          >
            {{ sourceLabels[source] }}
          </button>
        </div>
        <el-button :loading="loading" @click="handleReload">重读</el-button>
        <el-button type="primary" :loading="previewLoading" @click="handlePreview">应用改动</el-button>
      </div>
    </header>

    <div class="board-wrapper" style="display: flex; flex-direction: column; gap: 12px; flex: 1; min-height: 0;">
      <div class="meta-strip" v-if="activeConfigPath">
        <div class="meta-pill">
          <span>{{ sourceLabels[activeSource] }}</span>
          <strong>{{ activeConfigPath }}</strong>
        </div>
      </div>

      <el-alert v-if="error" :title="error" type="error" show-icon class="alert" />

      <div class="provider-layout">
        
        <div class="provider-list">
          <div class="section-head mini">
            <h3>Agent Tabs</h3>
            <el-button size="small" type="primary" link @click="openAddDialog">+ 添加</el-button>
          </div>
          <div class="provider-list-body">
            <div
              v-for="agent in displayAgents"
              :key="agent.clientKey"
              class="provider-list-item"
              :class="{ active: activeAgentKey === agent.clientKey }"
              @click="activeAgentKey = agent.clientKey"
            >
              <strong>{{ agent.id }}</strong>
              <el-button size="small" type="danger" link @click.stop="handleRemoveAgent(agent.clientKey)">删除</el-button>
            </div>
          </div>
        </div>

        <div class="provider-editor" v-if="activeAgent">
          <div class="section-head">
            <h3>编辑 Agent: {{ activeAgent.id }}</h3>
          </div>

          <el-form label-width="120px" label-position="top" size="large" style="max-width: 600px;">
            <el-form-item label="Agent ID (标识)">
              <el-input v-model="activeAgent.id" placeholder="如: Fast, Ordinary" />
              <div style="font-size: 12px; color: var(--text-dim); margin-top: 4px;">修改 ID 将会在保存时重命名此 Agent，这将改变其在 OpenCode 中的 Tab 名字。</div>
            </el-form-item>
            
            <el-form-item label="描述 (Description)">
              <el-input v-model="activeAgent.description" type="textarea" :rows="3" placeholder="描述此 Agent 的用途" />
            </el-form-item>

            <el-form-item label="主题色 (Color)">
              <el-color-picker v-model="activeAgent.color" />
            </el-form-item>

            <el-form-item label="提示词 (Prompt)">
              <el-input v-model="activeAgent.prompt" type="textarea" :rows="6" placeholder="输入提示词，或使用 {file:./prompts/xxx.txt} 引用外部文件" />
              <div style="font-size: 12px; color: var(--text-dim); margin-top: 4px;">您可以直接输入提示词内容，或引用外部文件。</div>
            </el-form-item>
          </el-form>
        </div>
        <div v-else class="provider-editor" style="display: flex; align-items: center; justify-content: center; color: var(--text-dim); font-size: 16px;">
          请在左侧选择或添加一个 Agent
        </div>
      </div>
    </div>

    <!-- 新增 Agent 弹窗 -->
    <el-dialog v-model="addDialogVisible" title="添加 Agent 到 Tab" width="500px">
      <el-form label-width="100px" label-position="top">
        <el-form-item label="添加方式">
          <el-radio-group v-model="addMethod">
            <el-radio value="restore" :disabled="hiddenAgents.length === 0">显示隐藏的内置 Agent</el-radio>
            <el-radio value="duplicate">复制已有的 Agent</el-radio>
            <el-radio value="new">创建全新空白 Agent</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="addMethod === 'restore'" label="选择要显示的内置 Agent">
          <el-select v-model="addSelectedHidden" placeholder="请选择">
            <el-option v-for="a in hiddenAgents" :key="a.clientKey" :label="a.id" :value="a.clientKey" />
          </el-select>
          <div style="font-size: 12px; color: var(--text-dim); margin-top: 4px;">
            这些是配置文件中作为子助手 (subagent) 或被默认隐藏的 Agent，选择后会将其提拔为独立的 Tab。
          </div>
        </el-form-item>

        <template v-else-if="addMethod === 'duplicate'">
          <el-form-item label="选择要复制的来源">
            <el-select v-model="addDuplicateFrom" placeholder="请选择">
              <el-option v-for="a in displayAgents" :key="a.clientKey" :label="a.id" :value="a.clientKey" />
            </el-select>
          </el-form-item>
          <el-form-item label="新的 Agent ID">
            <el-input v-model="addNewId" placeholder="输入只包含字母、数字、冒号、连字符的 ID" />
          </el-form-item>
        </template>

        <template v-else>
          <el-form-item label="全新的 Agent ID">
            <el-input v-model="addNewId" placeholder="输入只包含字母、数字、冒号、连字符的 ID" />
          </el-form-item>
        </template>
      </el-form>

      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmAdd">确定添加</el-button>
      </template>
    </el-dialog>

    <!-- 改动预览弹窗 -->
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
        <el-button type="primary" :loading="applying" @click="handleApply">确认保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>
