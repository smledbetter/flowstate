'use client';

import { BENCHMARKS } from '@/lib/compute';

const tiers = [
  { label: 'SWE-bench Moderate', value: BENCHMARKS.tokens_per_loc_swebench_moderate, color: '#ef4444' },
  { label: 'SWE-bench Efficient', value: BENCHMARKS.tokens_per_loc_swebench_efficient, color: '#eab308' },
  { label: 'Flowstate Target', value: BENCHMARKS.tokens_per_loc_target, color: '#22c55e' },
];

export function BenchmarkLadder({ actual }: { actual: number }) {
  const max = BENCHMARKS.tokens_per_loc_swebench_moderate;

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <h3 className="text-sm font-semibold text-white mb-4">Tokens/LOC Benchmark Ladder</h3>
      <div className="space-y-5">
        {/* Actual */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-white font-semibold">Flowstate Actual</span>
            <span className="font-mono text-sm text-uluka">{actual}</span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-4">
            <div
              className="h-4 rounded-full bg-uluka"
              style={{ width: `${Math.min((actual / max) * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* Benchmarks */}
        {tiers.map((tier) => (
          <div key={tier.label}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-400">{tier.label}</span>
              <span className="font-mono text-xs text-gray-500">{tier.value.toLocaleString()}</span>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-2">
              <div
                className="h-2 rounded-full"
                style={{
                  width: `${Math.min((tier.value / max) * 100, 100)}%`,
                  backgroundColor: tier.color,
                }}
              />
            </div>
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-500 mt-4">
        Lower is better. Flowstate achieves 3-17x better efficiency than SWE-bench efficient range.
      </p>
    </div>
  );
}
