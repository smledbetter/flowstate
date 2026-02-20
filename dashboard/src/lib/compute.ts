import type { Sprint, DerivedSprint } from '@/types/sprint';

export const BENCHMARKS = {
  tokens_per_loc_target: 300,
  tokens_per_loc_swebench_efficient: 1_000,
  tokens_per_loc_swebench_moderate: 5_000,
  cache_hit_rate_target: 80,
  delegation_ratio_target: 30,
  context_compressions_target: 0,
  code_generation_pct: 8.6,
  review_pct: 59.4,
} as const;

export const PROJECT_COLORS: Record<string, string> = {
  uluka: '#38bdf8',
  'dappled-shade': '#fb923c',
  'weaveto-do': '#a78bfa',
};

export function deriveMetrics(sprint: Sprint): DerivedSprint {
  const loc = sprint.metrics.loc_added || 1;
  return {
    ...sprint,
    newWorkTokensPerLoc: Math.round((sprint.metrics.new_work_tokens || 0) / loc),
    totalTokensPerLoc: Math.round((sprint.metrics.total_tokens || 0) / loc),
    activeMinutes: Math.round((sprint.metrics.active_session_time_s || 0) / 60),
    projectColor: PROJECT_COLORS[sprint.project] || '#888',
  };
}

export function aggregateStats(sprints: Sprint[]) {
  const total = sprints.length;
  const totalTokens = sprints.reduce((s, sp) => s + (sp.metrics.total_tokens || 0), 0);
  const totalNewWork = sprints.reduce((s, sp) => s + (sp.metrics.new_work_tokens || 0), 0);
  const totalLoc = sprints.reduce((s, sp) => s + (sp.metrics.loc_added || 0), 0);
  const totalTime = sprints.reduce((s, sp) => s + (sp.metrics.active_session_time_s || 0), 0);
  const gatesFirstPass = sprints.filter((sp) => sp.metrics.gates_first_pass).length;
  const cacheRates = sprints
    .map((sp) => sp.metrics.cache_hit_rate_pct)
    .filter((v): v is number => typeof v === 'number' && !isNaN(v));
  const avgCache = cacheRates.length
    ? Math.round((cacheRates.reduce((a, b) => a + b, 0) / cacheRates.length) * 10) / 10
    : null;

  return {
    totalSprints: total,
    totalTokens,
    totalNewWork,
    totalLoc,
    totalTimeMinutes: Math.round(totalTime / 60),
    avgNewWorkTokensPerLoc: totalLoc ? Math.round(totalNewWork / totalLoc) : 0,
    gatesFirstPassRate: Math.round((gatesFirstPass / total) * 100),
    avgCacheHitPct: avgCache,
  };
}

export function fmtTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${Math.round(n / 1_000)}K`;
  return String(n);
}

export function fmtMinutes(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s`;
}

/**
 * Compute a simple moving average over an array of numbers.
 * Window defaults to 3. Nulls are skipped (output is null at that index).
 * For the first (window-1) points, uses all available prior values (expanding window).
 */
export function movingAverage(values: (number | null)[], window = 3): (number | null)[] {
  return values.map((_, i) => {
    const slice: number[] = [];
    for (let j = Math.max(0, i - window + 1); j <= i; j++) {
      if (values[j] !== null && values[j] !== undefined) {
        slice.push(values[j] as number);
      }
    }
    if (slice.length === 0) return null;
    return Math.round((slice.reduce((a, b) => a + b, 0) / slice.length) * 10) / 10;
  });
}

export function resultColor(result: string): string {
  switch (result) {
    case 'confirmed':
      return '#22c55e';
    case 'partially_confirmed':
      return '#eab308';
    case 'inconclusive':
      return '#6b7280';
    case 'falsified':
      return '#ef4444';
    default:
      return '#6b7280';
  }
}

export function resultLabel(result: string): string {
  switch (result) {
    case 'partially_confirmed':
      return 'Partial';
    case 'confirmed':
      return 'Confirmed';
    case 'inconclusive':
      return 'Inconclusive';
    case 'falsified':
      return 'Falsified';
    default:
      return result;
  }
}
