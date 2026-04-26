import type { TargetInfo } from '@/types'

export type SourceTab = 'opencode' | 'omo'

export function getDefaultSourceTab(): SourceTab {
  return 'opencode'
}

export function getVisibleTargetsBySource(targets: TargetInfo[], source: SourceTab): TargetInfo[] {
  return targets.filter((target) => target.source === source)
}
