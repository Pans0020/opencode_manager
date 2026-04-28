import type { TargetInfo } from '@/types'

export interface TargetGroups {
  agents: TargetInfo[]
  subagents: TargetInfo[]
  others: TargetInfo[]
}

export function splitTargetsByKind(targets: TargetInfo[]): TargetGroups {
  return targets.reduce<TargetGroups>(
    (groups, target) => {
      if (target.kind === 'agent') {
        groups.agents.push(target)
      } else if (target.kind === 'subagent' || target.kind === 'category') {
        groups.subagents.push(target)
      } else {
        groups.others.push(target)
      }

      return groups
    },
    { agents: [], subagents: [], others: [] },
  )
}

export function getTargetKindLabel(target: TargetInfo): string {
  if (target.source !== 'omo') {
    return target.kind
  }

  const [, rawKind, ...nameParts] = target.id.split(':')
  const rawName = nameParts.join(':')
  const groupName = rawKind === 'category' ? 'categories' : 'agents'
  return `${rawKind} · ${groupName}.${rawName}`
}

export function groupTargetsByTab(targets: TargetInfo[], customTabs: string[]): Record<string, TargetInfo[]> {
  const groups: Record<string, TargetInfo[]> = {
    Agents: [],
    Subagents: [],
  }

  for (const tab of customTabs) {
    groups[tab] = []
  }

  for (const target of targets) {
    if (target.customTab && groups[target.customTab] !== undefined) {
      groups[target.customTab].push(target)
    } else if (target.kind === 'agent') {
      groups.Agents.push(target)
    } else if (target.kind === 'subagent' || target.kind === 'category') {
      groups.Subagents.push(target)
    } else {
      groups.Agents.push(target) // Fallback for others if any
    }
  }

  // Remove empty default tabs if not needed, but keep custom ones? 
  // Let's just return all of them and filter in Vue.
  return groups
}
