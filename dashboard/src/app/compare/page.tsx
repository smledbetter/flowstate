import { getSprints } from '@/lib/data';
import { deriveMetrics, aggregateStats, fmtTokens, PROJECT_COLORS } from '@/lib/compute';
import { StatCard } from '@/components/cards/StatCard';
import { SectionHeader } from '@/components/layout/SectionHeader';
import { EfficiencyChart } from '@/components/charts/EfficiencyChart';
import { ModelMixChart } from '@/components/charts/ModelMixChart';
import { SessionTimeChart } from './SessionTimeChart';

export default function ComparePage() {
  const { sprints } = getSprints();
  const derived = sprints.map(deriveMetrics);

  const uluka = sprints.filter((s) => s.project === 'uluka');
  const ds = sprints.filter((s) => s.project === 'dappled-shade');
  const ulukaStats = aggregateStats(uluka);
  const dsStats = aggregateStats(ds);

  const uDerived = derived.filter((s) => s.project === 'uluka');
  const dDerived = derived.filter((s) => s.project === 'dappled-shade');

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-bold text-white mb-2">Project Comparison</h1>
        <p className="text-gray-500">Uluka (TypeScript CLI) vs Dappled Shade (Rust P2P)</p>
      </div>

      {/* Side by side stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: PROJECT_COLORS.uluka }} />
            <span className="text-sm font-semibold text-white">Uluka</span>
            <span className="text-xs text-gray-500">TypeScript</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <StatCard label="Sprints" value={ulukaStats.totalSprints} />
            <StatCard label="Avg Tokens/LOC" value={ulukaStats.avgNewWorkTokensPerLoc} accent={PROJECT_COLORS.uluka} />
            <StatCard label="Total LOC" value={ulukaStats.totalLoc.toLocaleString()} />
            <StatCard label="Gates Pass Rate" value={`${ulukaStats.gatesFirstPassRate}%`} />
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2 mb-4">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: PROJECT_COLORS['dappled-shade'] }} />
            <span className="text-sm font-semibold text-white">Dappled Shade</span>
            <span className="text-xs text-gray-500">Rust</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <StatCard label="Sprints" value={dsStats.totalSprints} />
            <StatCard label="Avg Tokens/LOC" value={dsStats.avgNewWorkTokensPerLoc} accent={PROJECT_COLORS['dappled-shade']} />
            <StatCard label="Total LOC" value={dsStats.totalLoc.toLocaleString()} />
            <StatCard label="Gates Pass Rate" value={`${dsStats.gatesFirstPassRate}%`} />
          </div>
        </div>
      </div>

      {/* Charts */}
      <EfficiencyChart sprints={derived} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SessionTimeChart sprints={derived} />
        <ModelMixChart sprints={derived} />
      </div>
    </div>
  );
}
