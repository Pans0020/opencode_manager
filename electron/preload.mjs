import { contextBridge } from 'electron'

contextBridge.exposeInMainWorld('__AGENT_MODEL_MANAGER__', {
  apiBaseUrl: process.env.AGENT_MODEL_MANAGER_API_BASE_URL ?? null,
  isDesktop: process.env.AGENT_MODEL_MANAGER_IS_DESKTOP === '1',
})
