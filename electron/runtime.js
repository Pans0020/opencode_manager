import path from 'node:path'

const DEFAULT_PORT = 8765

export function resolveDesktopRuntime(port) {
  return {
    apiBaseUrl: `http://127.0.0.1:${port}`,
    isDesktop: true,
  }
}

export function getFrontendEntry({ isDev, rendererUrl, rendererDist }) {
  if (isDev) {
    return rendererUrl
  }
  return path.join(rendererDist, 'index.html')
}

export function getBackendSpawnOptions({ isDev }) {
  if (isDev) {
    return {
      stdio: 'inherit',
      windowsHide: false,
    }
  }

  return {
    stdio: 'ignore',
    windowsHide: true,
  }
}

export function getBackendLaunchConfig({ isDev, projectRoot, resourcesDir, port = DEFAULT_PORT }) {
  if (isDev) {
    return {
      command: 'python',
      args: [
        '-m',
        'uvicorn',
        'app.main:app',
        '--app-dir',
        'backend',
        '--host',
        '127.0.0.1',
        '--port',
        String(port),
      ],
      cwd: projectRoot,
    }
  }

  const backendDir = path.join(resourcesDir, 'backend')
  return {
    command: path.join(backendDir, 'agent-model-manager-backend.exe'),
    args: ['--host', '127.0.0.1', '--port', String(port)],
    cwd: backendDir,
  }
}
