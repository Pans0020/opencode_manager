/// <reference types="vite/client" />

interface DesktopRuntime {
  apiBaseUrl: string | null
  isDesktop: boolean
}

interface Window {
  __AGENT_MODEL_MANAGER__?: DesktopRuntime
}
