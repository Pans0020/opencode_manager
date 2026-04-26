import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const projectRoot = path.resolve(import.meta.dirname, '..', '..')

function readText(relativePath) {
  return fs.readFileSync(path.join(projectRoot, relativePath), 'utf8')
}

test('desktop build is configured for an unpacked folder package', () => {
  const pkg = JSON.parse(readText('package.json'))

  assert.equal(pkg.scripts['build:desktop'], 'electron-builder --win')
  assert.deepEqual(pkg.build.win.target, [
    {
      target: 'dir',
      arch: ['x64'],
    },
  ])
  assert.equal(pkg.build.portable, undefined)
})

test('one-click build script reports the folder output', () => {
  const script = readText('build-portable.cmd')

  assert.match(script, /Building folder package/)
  assert.match(script, /dist\\win-unpacked\\Agent Model Manager\.exe/)
  assert.match(script, /dist\\Agent-Model-Manager-\*-portable\.exe/)
})
