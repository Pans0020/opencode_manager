import type { TargetInfo, VisibilityRule } from '@/types'

export interface VisibilitySectionItem {
  target: TargetInfo
  rule: VisibilityRule | undefined
}

export interface VisibilitySections {
  opencode: VisibilitySectionItem[]
  omoAgents: VisibilitySectionItem[]
  omoSubagents: VisibilitySectionItem[]
}

export function buildVisibilitySections(
  targets: TargetInfo[],
  visibilityRules: VisibilityRule[],
): VisibilitySections {
  const ruleMap = new Map(visibilityRules.map((rule) => [rule.targetId, rule]))
  const sections: VisibilitySections = {
    opencode: [],
    omoAgents: [],
    omoSubagents: [],
  }

  for (const target of targets) {
    const item = {
      target,
      rule: ruleMap.get(target.id),
    }

    if (target.source === 'opencode') {
      sections.opencode.push(item)
      continue
    }

    const effectiveKind = item.rule?.kindOverride ?? target.kind
    if (effectiveKind === 'subagent' || effectiveKind === 'category') {
      sections.omoSubagents.push(item)
    } else {
      sections.omoAgents.push(item)
    }
  }

  return sections
}
