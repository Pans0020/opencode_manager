import { describe, expect, it } from 'vitest'

import { getApiBaseUrl, getDesktopRuntime } from '@/utils/runtime'

describe('runtime helpers', () => {
  it('prefers desktop injected api base when present', () => {
    expect(
      getApiBaseUrl({
        envApiBase: 'http://127.0.0.1:8765',
        desktopRuntime: {
          apiBaseUrl: 'http://127.0.0.1:9901',
          isDesktop: true,
        },
      }),
    ).toBe('http://127.0.0.1:9901')
  })

  it('falls back to env api base and default', () => {
    expect(getApiBaseUrl({ envApiBase: 'http://127.0.0.1:9000' })).toBe('http://127.0.0.1:9000')
    expect(getApiBaseUrl({})).toBe('http://127.0.0.1:8765')
  })

  it('normalizes missing desktop runtime', () => {
    expect(getDesktopRuntime(undefined)).toEqual({
      apiBaseUrl: null,
      isDesktop: false,
    })
  })
})
