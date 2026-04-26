import { app, BrowserWindow, nativeTheme } from 'electron'
import { spawn } from 'node:child_process'
import net from 'node:net'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  getBackendLaunchConfig,
  getBackendSpawnOptions,
  getFrontendEntry,
  resolveDesktopRuntime,
} from './runtime.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const projectRoot = path.resolve(__dirname, '..')
const isDev = process.env.ELECTRON_DEV === '1' || !app.isPackaged
const rendererUrl = process.env.ELECTRON_RENDERER_URL || 'http://localhost:5173'
const rendererDist = path.join(projectRoot, 'frontend', 'dist')

let backendProcess = null

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function isPortAvailable(port) {
  return new Promise((resolve) => {
    const server = net.createServer()
    server.once('error', () => resolve(false))
    server.once('listening', () => {
      server.close(() => resolve(true))
    })
    server.listen(port, '127.0.0.1')
  })
}

async function findAvailablePort(startPort) {
  for (let port = startPort; port < startPort + 20; port += 1) {
    if (await isPortAvailable(port)) {
      return port
    }
  }
  throw new Error('No available backend port found')
}

async function waitForHttp(url, attempts = 80) {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      const response = await fetch(url)
      if (response.ok) {
        return
      }
    } catch {
      // keep polling until timeout
    }
    await wait(500)
  }
  throw new Error(`Timed out waiting for ${url}`)
}

async function startBackend(port) {
  const launchConfig = getBackendLaunchConfig({
    isDev,
    projectRoot,
    resourcesDir: process.resourcesPath,
    port,
  })

  backendProcess = spawn(launchConfig.command, launchConfig.args, {
    cwd: launchConfig.cwd,
    ...getBackendSpawnOptions({ isDev }),
  })

  backendProcess.once('exit', (code) => {
    backendProcess = null
    if (code && code !== 0) {
      console.error(`Backend exited with code ${code}`)
    }
  })

  await waitForHttp(`http://127.0.0.1:${port}/api/health`)
}

async function createMainWindow() {
  const port = await findAvailablePort(8765)
  const desktopRuntime = resolveDesktopRuntime(port)

  process.env.AGENT_MODEL_MANAGER_API_BASE_URL = desktopRuntime.apiBaseUrl
  process.env.AGENT_MODEL_MANAGER_IS_DESKTOP = '1'

  await startBackend(port)

  nativeTheme.themeSource = 'dark'

  const window = new BrowserWindow({
    width: 1440,
    height: 960,
    show: false,
    autoHideMenuBar: true,
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#1e1e20',
      symbolColor: '#ffffff',
      height: 32,
    },
    webPreferences: {
      preload: path.join(__dirname, 'preload.mjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  window.once('ready-to-show', () => {
    window.show()
  })

  const entry = getFrontendEntry({
    isDev,
    rendererUrl,
    rendererDist,
  })

  if (isDev) {
    await waitForHttp(entry)
    await window.loadURL(entry)
    window.webContents.openDevTools({ mode: 'detach' })
  } else {
    await window.loadFile(entry)
  }
}

app.whenReady().then(async () => {
  await createMainWindow()

  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      await createMainWindow()
    }
  })
})

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill()
  }
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
