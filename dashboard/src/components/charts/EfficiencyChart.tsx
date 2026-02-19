'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { DerivedSprint } from '@/types/sprint';
import { BENCHMARKS, PROJECT_COLORS } from '@/lib/compute';

export function EfficiencyChart({ sprints }: { sprints: DerivedSprint[] }) {
  const uluka = sprints.filter((s) => s.project === 'uluka');
  const ds = sprints.filter((s) => s.project === 'dappled-shade');

  const maxLen = Math.max(uluka.length, ds.length);
  const data = Array.from({ length: maxLen }, (_, i) => ({
    index: i,
    uluka: uluka[i]?.newWorkTokensPerLoc ?? null,
    ulukaLabel: uluka[i]?.label ?? null,
    ds: ds[i]?.newWorkTokensPerLoc ?? null,
    dsLabel: ds[i]?.label ?? null,
  }));

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <h3 className="text-sm font-semibold text-white mb-4">Efficiency Trend by Sprint</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <XAxis
            dataKey="index"
            tick={{ fill: '#6b7280', fontSize: 11 }}
            axisLine={{ stroke: '#1e1e2e' }}
            tickLine={false}
            label={{ value: 'Sprint #', fill: '#6b7280', fontSize: 11, position: 'insideBottom', offset: -2 }}
          />
          <YAxis
            tick={{ fill: '#6b7280', fontSize: 11 }}
            axisLine={{ stroke: '#1e1e2e' }}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#13131a',
              border: '1px solid #1e1e2e',
              borderRadius: 8,
              fontSize: 12,
            }}
            labelStyle={{ color: '#e2e8f0' }}
            formatter={(value: number, name: string) => [
              value,
              name === 'uluka' ? 'Uluka' : 'Dappled Shade',
            ]}
          />
          <ReferenceLine
            y={BENCHMARKS.tokens_per_loc_target}
            stroke="#22c55e33"
            strokeDasharray="4 4"
          />
          <Line
            dataKey="uluka"
            stroke={PROJECT_COLORS.uluka}
            strokeWidth={2}
            dot={{ r: 4, fill: PROJECT_COLORS.uluka }}
            connectNulls={false}
            name="uluka"
          />
          <Line
            dataKey="ds"
            stroke={PROJECT_COLORS['dappled-shade']}
            strokeWidth={2}
            dot={{ r: 4, fill: PROJECT_COLORS['dappled-shade'] }}
            connectNulls={false}
            name="ds"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
