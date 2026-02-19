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
    <div className="overflow-x-auto">
      <div
        className="grid gap-px bg-border"
        style={{
          gridTemplateColumns: `160px repeat(${sprints.length}, minmax(56px, 1fr))`,
        }}
      >
        {/* Header row */}
        <div className="bg-bg p-2 text-xs text-gray-500" />
        {sprints.map((s) => (
          <div
            key={s.label}
            className="bg-bg p-2 text-xs text-gray-400 text-center truncate"
          >
            {s.label}
          </div>
        ))}

        {/* Hypothesis rows */}
        {displayIds.map((hId) => (
          <>
            <div key={`label-${hId}`} className="bg-card p-2 text-xs text-gray-300 truncate">
              {hId}: {hypotheses[hId]}
            </div>
            {sprints.map((s) => {
              const result = lookup[hId]?.[s.label];
              return (
                <div
                  key={`${hId}-${s.label}`}
                  className="bg-card p-2 flex items-center justify-center"
                  title={result ? resultLabel(result) : 'Not tested'}
                >
                  {result ? (
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: resultColor(result) }}
                    />
                  ) : (
                    <div className="w-3 h-3 rounded-full bg-gray-800" />
                  )}
                </div>
              );
            })}
          </>
        ))}
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
