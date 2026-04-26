<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'

import { useProviderStore } from '@/store/providers'
import type { ConfigSource } from '@/types'

const providerStore = useProviderStore()
const {
  applyResult,
  applying,
  availableSources,
  configPath,
  drafts,
  error,
  loading,
  preview,
  previewLoading,
  selectedProvider,
  selectedProviderIndex,
  selectedSource,
} = storeToRefs(providerStore)

const previewVisible = computed({
  get: () => Boolean(preview.value),
  set: (value: boolean) => {
    if (!value) {
      providerStore.preview = null
    }
  },
})

async function handlePreview() {
  await providerStore.previewDrafts()
  if (!preview.value?.files.length) {
    ElMessage.info('当前没有需要应用的 Provider 改动')
  }
}

async function handleApply() {
  await providerStore.applyDrafts()
  if (applyResult.value) {
    ElMessage.success('Provider 配置已写回文件')
  }
}

const activeModelTab = ref<string | null>(null)

const sourceLabels = {
  opencode: 'OpenCode',
  omo: 'OMO',
}

function syncActiveModelTab() {
  activeModelTab.value = selectedProvider.value?.models[0]?.id ?? null
}

function handleSelectProvider(index: number) {
  providerStore.selectProviderIndex(index)
  syncActiveModelTab()
}

async function handleSelectSource(source: ConfigSource) {
  await providerStore.selectSource(source)
  syncActiveModelTab()
}

async function handleReload() {
  await providerStore.load()
  syncActiveModelTab()
}

function handleAddModel(providerId: string) {
  providerStore.addModel(providerId)
  const models = selectedProvider.value?.models
  if (models?.length) {
    activeModelTab.value = models[models.length - 1].id
  }
}

onMounted(async () => {
  if (!drafts.value.length) {
    await providerStore.load()
  }
  if (selectedProvider.value?.models.length) {
    activeModelTab.value = selectedProvider.value.models[0].id
  }
})
</script>

<template>
  <section class="content-shell">
    <header class="toolbar">
      <div class="toolbar-copy">
        <h2>Provider 管理</h2>
      </div>

      <div class="toolbar-group">
        <div v-if="availableSources.length > 1" class="inline-tabs">
          <button
            v-for="source in availableSources"
            :key="source"
            type="button"
            class="mini-tab"
            :class="{ active: selectedSource === source }"
            @click="handleSelectSource(source)"
          >
            {{ sourceLabels[source] }}
          </button>
        </div>
        <el-button :loading="loading" @click="handleReload">重读</el-button>
        <el-button @click="providerStore.addProvider">新增 Provider</el-button>
        <el-button type="primary" :loading="previewLoading" @click="handlePreview">预览写回</el-button>
      </div>
    </header>

    <div class="board-wrapper">
      <div class="meta-strip" v-if="configPath" style="margin-bottom: 12px;">
        <div class="meta-pill">
          <span>{{ sourceLabels[selectedSource] }}</span>
          <strong>{{ configPath }}</strong>
        </div>
      </div>

      <el-alert v-if="error" :title="error" type="error" show-icon class="alert" style="margin-bottom: 20px;" />

      <section class="provider-layout">
        <aside class="provider-list section">
          <div class="section-head">
            <h3>Providers</h3>
          </div>
          <div class="provider-list-body">
            <button
              v-for="(provider, index) in drafts"
              :key="index"
              type="button"
              class="provider-list-item"
              :class="{ active: selectedProviderIndex === index }"
              @click="handleSelectProvider(index)"
            >
              <strong>{{ provider.id }}</strong>
              <span>{{ provider.models.length }} models</span>
            </button>
          </div>
        </aside>

        <section class="section provider-editor" v-if="selectedProvider">
          <div class="section-head">
            <h3>配置：{{ selectedProvider.id || '新项' }}</h3>
            <div class="inline-actions">
              <el-button @click="handleAddModel(selectedProvider.id)">新增 Model</el-button>
              <el-popconfirm title="确定删除这个 Provider 吗？" @confirm="providerStore.removeProvider(selectedProvider.id)">
                <template #reference>
                  <el-button type="danger" plain>删除 Provider</el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>

          <div class="provider-form-grid">
            <label>
              <span>ID</span>
              <el-input v-model="selectedProvider.id" />
            </label>
            <label>
              <span>NPM</span>
              <el-input v-model="selectedProvider.npm" />
            </label>
            <label>
              <span>Base URL</span>
              <el-input v-model="selectedProvider.baseURL" />
            </label>
            <label>
              <span>API Key</span>
              <el-input v-model="selectedProvider.apiKey" />
            </label>
          </div>

          <el-tabs v-model="activeModelTab" type="border-card" class="model-stack" v-if="selectedProvider.models.length > 0">
            <el-tab-pane v-for="model in selectedProvider.models" :key="model.id" :label="model.id || '新 Model'" :name="model.id">
              <div class="model-inner-editor">
                <div class="section-head mini">
                  <h3>Model 详情</h3>
                  <div class="inline-actions">
                    <el-button size="small" @click="providerStore.addVariant(selectedProvider.id, model.id)">新增 Variant</el-button>
                    <el-popconfirm title="确定删除这个 Model 吗？" @confirm="providerStore.removeModel(selectedProvider.id, model.id)">
                      <template #reference>
                        <el-button type="danger" size="small" plain>删除 Model</el-button>
                      </template>
                    </el-popconfirm>
                  </div>
                </div>

                <div class="provider-form-grid tight">
                  <label><span>Model ID</span><el-input v-model="model.id" /></label>
                  <label><span>Name</span><el-input v-model="model.name" /></label>
                </div>

                <div class="provider-json-grid">
                  <label><span>Limit(JSON)</span><el-input v-model="model.limitText" type="textarea" :rows="3" /></label>
                  <label><span>Cost(JSON)</span><el-input v-model="model.costText" type="textarea" :rows="3" /></label>
                  <label><span>Options(JSON)</span><el-input v-model="model.optionsText" type="textarea" :rows="3" /></label>
                </div>

                <div class="variant-stack">
                  <div class="section-head mini">
                    <h3>Variants ({{ model.variants.length }})</h3>
                  </div>
                  <div v-for="variant in model.variants" :key="variant.id" class="variant-row-tight">
                    <el-input v-model="variant.id" placeholder="ID" style="width: 120px" />
                    <el-input v-model="variant.valueText" placeholder="Config (JSON)" />
                    <el-popconfirm title="删除变体？" @confirm="providerStore.removeVariant(selectedProvider.id, model.id, variant.id)">
                      <template #reference>
                        <el-button type="danger" size="small" plain>删除</el-button>
                      </template>
                    </el-popconfirm>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </section>
      </section>
    </div>

    <el-dialog v-model="previewVisible" width="920px" title="预览改动">
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
