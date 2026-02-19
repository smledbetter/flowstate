import { getSprints, getHypotheses } from '@/lib/data';
import { deriveMetrics, resultColor, resultLabel } from '@/lib/compute';
import { SectionHeader } from '@/components/layout/SectionHeader';
import { HypothesisHeatmap } from '@/components/charts/HypothesisHeatmap';

export default function HypothesesPage() {
  const { sprints } = getSprints();
  const { hypotheses } = getHypotheses();
  const derived = sprints.map(deriveMetrics);
  const hIds = Object.keys(hypotheses);

  // Aggregate results per hypothesis
  const rollup: Record<
    string,
    { confirmed: number; partial: number; inconclusive: number; falsified: number; total: number }
  > = {};
  for (const id of hIds) {
    rollup[id] = { confirmed: 0, partial: 0, inconclusive: 0, falsified: 0, total: 0 };
  }
  for (const s of sprints) {
    for (const h of s.hypotheses) {
      const id = h.id.replace('_control', '');
      if (!rollup[id]) continue;
      rollup[id].total++;
      if (h.result === 'confirmed') rollup[id].confirmed++;
      else if (h.result === 'partially_confirmed') rollup[id].partial++;
      else if (h.result === 'inconclusive') rollup[id].inconclusive++;
      else if (h.result === 'falsified') rollup[id].falsified++;
    }
  }

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-bold text-white mb-2">Hypothesis Tracking</h1>
        <p className="text-gray-500">
          12 hypotheses tracked across {sprints.length} sprints. None falsified.
        </p>
      </div>

      {/* Full Heatmap */}
      <div className="bg-card border border-border rounded-lg p-5">
        <HypothesisHeatmap sprints={derived} hypotheses={hypotheses} />
      </div>

      {/* Per-hypothesis rollup */}
      <div>
        <SectionHeader title="Hypothesis Summary" subtitle="Aggregated results across all sprints" />
        <div className="space-y-3">
          {hIds.map((id) => {
            const r = rollup[id];
            const status =
              r.confirmed > 0 && r.falsified === 0
                ? 'confirmed'
                : r.falsified > 0
                  ? 'falsified'
                  : r.total > 0
                    ? 'partially_confirmed'
                    : 'inconclusive';

            return (
              <div key={id} className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-gray-400 w-8">{id}</span>
                    <span className="text-sm text-white">{hypotheses[id]}</span>
                  </div>
                  <span
                    className="px-2 py-0.5 rounded text-xs font-medium"
                    style={{
                      backgroundColor: resultColor(status) + '22',
                      color: resultColor(status),
                    }}
                  >
                    {r.total > 0 ? `${r.confirmed}/${r.total} confirmed` : 'Not tested'}
                  </span>
                </div>
                {r.total > 0 && (
                  <div className="flex gap-4 text-xs text-gray-500">
                    {r.confirmed > 0 && (
                      <span className="text-confirmed">{r.confirmed} confirmed</span>
                    )}
                    {r.partial > 0 && <span className="text-partial">{r.partial} partial</span>}
                    {r.inconclusive > 0 && (
                      <span className="text-inconclusive">{r.inconclusive} inconclusive</span>
                    )}
                    {r.falsified > 0 && (
                      <span className="text-falsified">{r.falsified} falsified</span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
