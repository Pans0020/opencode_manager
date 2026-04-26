import test from 'node:test'
import assert from 'node:assert/strict'
import path from 'node:path'

import {
  getBackendLaunchConfig,
  getBackendSpawnOptions,
  getFrontendEntry,
  resolveDesktopRuntime,
} from '../runtime.js'

test('resolveDesktopRuntime returns desktop flags and api url', () => {
  assert.deepEqual(resolveDesktopRuntime(8877), {
    apiBaseUrl: 'http://127.0.0.1:8877',
    isDesktop: true,
  })
})

test('getFrontendEntry uses dev server in development mode', () => {
  assert.equal(
    getFrontendEntry({ isDev: true, rendererUrl: 'http://localhost:5173' }),
    'http://localhost:5173',
  )
})

test('getFrontendEntry resolves built index in production mode', () => {
  const result = getFrontendEntry({
    isDev: false,
    rendererDist: 'C:/app/frontend/dist',
  })
  assert.equal(result, path.join('C:/app/frontend/dist', 'index.html'))
})

test('getBackendLaunchConfig uses uvicorn in development mode', () => {
  const result = getBackendLaunchConfig({
    isDev: true,
    projectRoot: 'C:/workspace/omo_ca',
    port: 8765,
  })

  assert.equal(result.command, 'python')
  assert.deepEqual(result.args, [
    '-m',
    'uvicorn',
    'app.main:app',
    '--app-dir',
    'backend',
    '--host',
    '127.0.0.1',
    '--port',
    '8765',
  ])
  assert.equal(result.cwd, 'C:/workspace/omo_ca')
})

test('getBackendLaunchConfig uses packaged backend exe in production mode', () => {
  const result = getBackendLaunchConfig({
    isDev: false,
    resourcesDir: 'C:/app/resources',
    port: 9001,
  })

  assert.equal(result.command, path.join('C:/app/resources', 'backend', 'agent-model-manager-backend.exe'))
  assert.deepEqual(result.args, ['--host', '127.0.0.1', '--port', '9001'])
  assert.equal(result.cwd, path.join('C:/app/resources', 'backend'))
})

test('getBackendSpawnOptions hides backend console in production mode', () => {
  assert.deepEqual(getBackendSpawnOptions({ isDev: false }), {
    stdio: 'ignore',
    windowsHide: true,
  })
})
