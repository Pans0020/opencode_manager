import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

describe('vite desktop build config', () => {
  it('uses relative asset base for file protocol', () => {
    const configSource = fs.readFileSync(path.resolve(__dirname, '../vite.config.ts'), 'utf-8')
    expect(configSource).toContain("base: './'")
  })
})
