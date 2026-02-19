'use client';

import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from 'recharts';
import type { DerivedSprint } from '@/types/sprint';
import { BENCHMARKS, movingAverage } from '@/lib/compute';

export function TokensChart({ sprints }: { sprints: DerivedSprint[] }) {
  const values = sprints.map((s) => s.newWorkTokensPerLoc);
  const ma = movingAverage(values, 3);

  const data = sprints.map((s, i) => ({
    label: s.label,
    newWorkTokensPerLoc: s.newWorkTokensPerLoc,
    movingAvg: ma[i],
    project: s.project,
    fill: s.projectColor,
  }));

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <h3 className="text-sm font-semibold text-white mb-4">New-Work Tokens / LOC</h3>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <XAxis
            dataKey="label"
            tick={{ fill: '#6b7280', fontSize: 11 }}
            axisLine={{ stroke: '#1e1e2e' }}
            tickLine={false}
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
              name === 'movingAvg' ? '3-sprint avg' : 'Tokens/LOC',
            ]}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, color: '#6b7280' }}
            formatter={(value) => (value === 'movingAvg' ? '3-sprint moving avg' : 'Tokens/LOC')}
          />
          <ReferenceLine
            y={BENCHMARKS.tokens_per_loc_target}
            stroke="#22c55e"
            strokeDasharray="4 4"
            label={{ value: 'Target: 300', fill: '#22c55e', fontSize: 10, position: 'right' }}
          />
          <ReferenceLine
            y={BENCHMARKS.tokens_per_loc_swebench_efficient}
            stroke="#6b7280"
            strokeDasharray="4 4"
            label={{
              value: 'SWE-bench efficient: 1K',
              fill: '#6b7280',
              fontSize: 10,
              position: 'right',
            }}
          />
          <Bar dataKey="newWorkTokensPerLoc" name="newWorkTokensPerLoc" radius={[4, 4, 0, 0]}>
            {data.map((entry, i) => (
              <rect key={i} fill={entry.fill} />
            ))}
          </Bar>
          <Line
            dataKey="movingAvg"
            name="movingAvg"
            stroke="#38bdf8"
            strokeWidth={2}
            dot={{ r: 3, fill: '#38bdf8' }}
            connectNulls
            type="monotone"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
