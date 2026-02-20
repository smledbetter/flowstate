'use client';

import { resultColor, resultLabel } from '@/lib/compute';
import type { DerivedSprint } from '@/types/sprint';

interface Props {
  sprints: DerivedSprint[];
  hypotheses: Record<string, string>;
  compact?: boolean;
}

export function HypothesisHeatmap({ sprints, hypotheses, compact }: Props) {
  const hIds = Object.keys(hypotheses);

  // Build lookup: hId -> sprintLabel -> result
  const lookup: Record<string, Record<string, string>> = {};
  for (const s of sprints) {
    for (const h of s.hypotheses) {
      const hId = h.id.replace('_control', '');
      if (!lookup[hId]) lookup[hId] = {};
      lookup[hId][s.label] = h.result;
    }
  }

  const displayIds = compact ? hIds.filter((id) => lookup[id]) : hIds;

  return (
    <div className="relative">
      {/* Scrollable container — labels stick left, data scrolls */}
      <div className="overflow-x-auto">
        <table className="border-separate" style={{ borderSpacing: '1px' }}>
          <thead>
            <tr>
              <th
                className="sticky left-0 z-10 bg-bg p-2 text-xs text-gray-500 text-left font-normal"
                style={{ minWidth: '340px', maxWidth: '400px' }}
              />
              {sprints.map((s) => (
                <th
                  key={s.label}
                  className="bg-bg p-2 text-xs text-gray-400 text-center font-normal whitespace-nowrap"
                  style={{ minWidth: '48px' }}
                >
                  {s.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayIds.map((hId) => (
              <tr key={hId}>
                <td
                  className="sticky left-0 z-10 bg-card p-2 text-xs text-gray-300"
                  style={{ minWidth: '340px', maxWidth: '400px' }}
                >
                  <span className="text-gray-500">{hId}:</span> {hypotheses[hId]}
                </td>
                {sprints.map((s) => {
                  const result = lookup[hId]?.[s.label];
                  return (
                    <td
                      key={`${hId}-${s.label}`}
                      className="bg-card p-2 text-center"
                      title={result ? resultLabel(result) : 'Not tested'}
                    >
                      <div
                        className={`w-3 h-3 rounded-full mx-auto ${!result ? 'bg-gray-800' : ''}`}
                        style={result ? { backgroundColor: resultColor(result) } : undefined}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex gap-4 mt-3 text-xs text-gray-500">
        {['confirmed', 'partially_confirmed', 'inconclusive', 'falsified'].map((r) => (
          <div key={r} className="flex items-center gap-1.5">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: resultColor(r) }}
            />
            {resultLabel(r)}
          </div>
        ))}
      </div>
    </div>
  );
}
