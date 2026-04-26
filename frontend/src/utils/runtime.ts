export interface DesktopRuntime {
  apiBaseUrl: string | null
  isDesktop: boolean
}

interface ApiBaseOptions {
  envApiBase?: string
  desktopRuntime?: DesktopRuntime
}

export function getDesktopRuntime(
  runtime: Partial<DesktopRuntime> | undefined,
): DesktopRuntime {
  return {
    apiBaseUrl: runtime?.apiBaseUrl ?? null,
    isDesktop: runtime?.isDesktop ?? false,
  }
}

export function getApiBaseUrl(options: ApiBaseOptions): string {
  if (options.desktopRuntime?.apiBaseUrl) {
    return options.desktopRuntime.apiBaseUrl
  }

  if (options.envApiBase) {
    return options.envApiBase
  }

  return 'http://127.0.0.1:8765'
}
