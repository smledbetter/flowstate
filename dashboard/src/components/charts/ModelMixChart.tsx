'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import type { DerivedSprint } from '@/types/sprint';

export function ModelMixChart({ sprints }: { sprints: DerivedSprint[] }) {
  const data = sprints.map((s) => ({
    label: s.label,
    Opus: s.metrics.opus_pct,
    Sonnet: s.metrics.sonnet_pct,
    Haiku: s.metrics.haiku_pct,
  }));

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <h3 className="text-sm font-semibold text-white mb-4">Model Mix</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
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
            domain={[0, 100]}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#13131a',
              border: '1px solid #1e1e2e',
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(v: number) => `${v}%`}
          />
          <Legend wrapperStyle={{ fontSize: 11, color: '#6b7280' }} />
          <Bar dataKey="Opus" stackId="a" fill="#a78bfa" radius={[0, 0, 0, 0]} />
          <Bar dataKey="Sonnet" stackId="a" fill="#60a5fa" />
          <Bar dataKey="Haiku" stackId="a" fill="#34d399" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
