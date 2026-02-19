import { getSprints, getHypotheses } from '@/lib/data';
import { deriveMetrics, aggregateStats, fmtTokens } from '@/lib/compute';
import { StatCard } from '@/components/cards/StatCard';
import { SprintCard } from '@/components/cards/SprintCard';
import { SectionHeader } from '@/components/layout/SectionHeader';
import { TokensChart } from '@/components/charts/TokensChart';
import { EfficiencyChart } from '@/components/charts/EfficiencyChart';
import { HypothesisHeatmap } from '@/components/charts/HypothesisHeatmap';
import Link from 'next/link';

export default function OverviewPage() {
  const { sprints } = getSprints();
  const { hypotheses } = getHypotheses();
  const derived = sprints.map(deriveMetrics);
  const stats = aggregateStats(sprints);

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Flowstate</h1>
        <p className="text-gray-500">
          Sprint efficiency metrics for AI-assisted development across {stats.totalSprints} sprints
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Avg Tokens/LOC"
          value={stats.avgNewWorkTokensPerLoc}
          sub="new-work tokens per line"
          accent="#22c55e"
        />
        <StatCard
          label="Total LOC"
          value={stats.totalLoc.toLocaleString()}
          sub={`across ${stats.totalSprints} sprints`}
        />
        <StatCard
          label="Gates First Pass"
          value={`${stats.gatesFirstPassRate}%`}
          sub={`${sprints.filter((s) => s.metrics.gates_first_pass).length}/${stats.totalSprints} sprints`}
        />
        <StatCard
          label="Active Time"
          value={`${stats.totalTimeMinutes}m`}
          sub="total active session time"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TokensChart sprints={derived} />
        <EfficiencyChart sprints={derived} />
      </div>

      {/* Sprint Grid */}
      <div>
        <SectionHeader title="All Sprints" subtitle="Click a sprint for details" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {derived.map((s) => (
            <SprintCard key={s.label} sprint={s} />
          ))}
        </div>
      </div>

      {/* Hypothesis Teaser */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <SectionHeader title="Hypothesis Tracking" subtitle="H1-H12 across all sprints" />
          <Link href="/hypotheses" className="text-sm text-uluka hover:underline">
            View all
          </Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-5">
          <HypothesisHeatmap sprints={derived} hypotheses={hypotheses} compact />
        </div>
      </div>
    </div>
  );
}
