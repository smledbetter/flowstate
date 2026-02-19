import { getSprints } from '@/lib/data';
import { deriveMetrics, fmtTokens, fmtMinutes, resultColor, resultLabel } from '@/lib/compute';
import { StatCard } from '@/components/cards/StatCard';
import { ModelMixChart } from '@/components/charts/ModelMixChart';
import Link from 'next/link';

export function generateStaticParams() {
  const { sprints } = getSprints();
  return sprints.map((s) => ({ label: s.label }));
}

export default function SprintDetailPage({ params }: { params: { label: string } }) {
  const { sprints } = getSprints();
  const label = decodeURIComponent(params.label);
  const idx = sprints.findIndex((s) => s.label === label);
  const sprint = sprints[idx];
  if (!sprint) return <div className="text-white">Sprint not found</div>;

  const d = deriveMetrics(sprint);
  const m = sprint.metrics;
  const prev = idx > 0 ? sprints[idx - 1] : null;
  const next = idx < sprints.length - 1 ? sprints[idx + 1] : null;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-white">{sprint.label}</h1>
            <span
              className="px-2 py-0.5 rounded text-xs font-medium"
              style={{ backgroundColor: d.projectColor + '22', color: d.projectColor }}
            >
              {sprint.project}
            </span>
          </div>
          <p className="text-gray-500 text-sm">{sprint.phase}</p>
        </div>
        <div className="flex gap-3">
          {prev && (
            <Link
              href={`/sprint/${encodeURIComponent(prev.label)}`}
              className="text-sm text-gray-400 hover:text-white"
            >
              &larr; {prev.label}
            </Link>
          )}
          {next && (
            <Link
              href={`/sprint/${encodeURIComponent(next.label)}`}
              className="text-sm text-gray-400 hover:text-white"
            >
              {next.label} &rarr;
            </Link>
          )}
        </div>
      </div>

      {/* Metric Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard label="Tokens/LOC" value={d.newWorkTokensPerLoc} sub="new-work" />
        <StatCard label="Active Time" value={fmtMinutes(m.active_session_time_s)} />
        <StatCard label="Total Tokens" value={fmtTokens(m.total_tokens)} />
        <StatCard label="New Work" value={fmtTokens(m.new_work_tokens)} />
        <StatCard label="LOC Added" value={m.loc_added.toLocaleString()} sub={m.loc_added_approx ? 'approx' : 'exact'} />
        <StatCard label="API Calls" value={m.api_calls} />
      </div>

      {/* Model Mix + Test/Gate row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ModelMixChart sprints={[d]} />
        <div className="space-y-4">
          {/* Tests */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-sm font-semibold text-white mb-3">Tests</h3>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Total</span>
                <p className="font-mono text-white text-lg">{m.tests_total}</p>
              </div>
              <div>
                <span className="text-gray-500">Added</span>
                <p className="font-mono text-white text-lg">{m.tests_added ?? '-'}</p>
              </div>
              <div>
                <span className="text-gray-500">Coverage</span>
                <p className="font-mono text-white text-lg">
                  {m.coverage_pct !== null ? `${m.coverage_pct}%` : '-'}
                </p>
              </div>
            </div>
          </div>

          {/* Gates */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-sm font-semibold text-white mb-3">Gates</h3>
            <div className="flex items-center gap-3">
              <span
                className={`text-lg font-semibold ${m.gates_first_pass ? 'text-confirmed' : 'text-partial'}`}
              >
                {m.gates_first_pass ? 'First Pass' : 'Required Retry'}
              </span>
              {m.gates_first_pass_note && (
                <span className="text-xs text-gray-500">({m.gates_first_pass_note})</span>
              )}
            </div>
            <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Lint Errors</span>
                <p className="font-mono text-white">{m.lint_errors ?? '-'}</p>
              </div>
              <div>
                <span className="text-gray-500">Subagents</span>
                <p className="font-mono text-white">
                  {m.subagents}
                  {m.subagent_note ? ` (${m.subagent_note})` : ''}
                </p>
              </div>
            </div>
          </div>

          {/* Cache */}
          {m.cache_hit_rate_pct !== null && (
            <div className="bg-card border border-border rounded-lg p-5">
              <h3 className="text-sm font-semibold text-white mb-2">Cache Hit Rate</h3>
              <div className="flex items-center gap-3">
                <div className="flex-1 bg-gray-800 rounded-full h-3">
                  <div
                    className="h-3 rounded-full bg-uluka"
                    style={{ width: `${m.cache_hit_rate_pct}%` }}
                  />
                </div>
                <span className="font-mono text-sm text-white">{m.cache_hit_rate_pct}%</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Hypotheses */}
      {sprint.hypotheses.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-white mb-4">Hypotheses Tested</h3>
          <div className="space-y-3">
            {sprint.hypotheses.map((h) => (
              <div key={h.id} className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <span className="font-mono text-xs text-gray-400">{h.id}</span>
                  <span className="text-sm text-white font-medium">{h.name}</span>
                  <span
                    className="ml-auto px-2 py-0.5 rounded text-xs font-medium"
                    style={{
                      backgroundColor: resultColor(h.result) + '22',
                      color: resultColor(h.result),
                    }}
                  >
                    {resultLabel(h.result)}
                  </span>
                </div>
                <p className="text-xs text-gray-400">{h.evidence}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
