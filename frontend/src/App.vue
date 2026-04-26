<script setup lang="ts">
import { computed, ref } from 'vue'

import ModelManagementView from '@/components/ModelManagementView.vue'
import ProviderManagementView from '@/components/ProviderManagementView.vue'
import VisibilityManagementView from '@/components/VisibilityManagementView.vue'
import AgentManagementView from '@/components/AgentManagementView.vue'
import type { AppPage } from '@/types'

const activePage = ref<AppPage>('tabs')

const pages: Array<{ id: AppPage; label: string; description: string }> = [
  {
    id: 'tabs',
    label: 'Agent(Tab) 管理',
    description: '直接增加、删除或修改 OpenCode 聊天窗口里的那些 Agent Tabs。',
  },
  {
    id: 'models',
    label: '模型管理',
    description: '切换当前可见的 agent 和 subagent 所使用的 provider、model 与强度。',
  },
  {
    id: 'visibility',
    label: '显示管理',
    description: '决定哪些目标会出现在模型管理页，并修正 OMO 的 agent / subagent 分类。',
  },
  {
    id: 'providers',
    label: 'Provider 管理',
    description: '维护 opencode.json 里的 provider、model、variants 与连接配置。',
  },
]

const activePageMeta = computed(() => pages.find((page) => page.id === activePage.value) ?? pages[0])
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <h1>AGENT MANAGER</h1>
      </div>

      <nav class="page-nav" aria-label="主导航">
        <button
          v-for="page in pages"
          :key="page.id"
          type="button"
          class="page-tab"
          :class="{ active: activePage === page.id }"
          @click="activePage = page.id"
        >
          {{ page.label }}
        </button>
      </nav>

      <div class="meta-card">
        <span>当前视图</span>
        <strong>{{ activePageMeta.label }}</strong>
      </div>
    </aside>

    <main class="main-panel">
      <AgentManagementView v-if="activePage === 'tabs'" />
      <ModelManagementView v-else-if="activePage === 'models'" />
      <VisibilityManagementView v-else-if="activePage === 'visibility'" />
      <ProviderManagementView v-else />
    </main>
  </div>
</template>
