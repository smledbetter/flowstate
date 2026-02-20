'use client';

import {
  ComposedChart,
  Area,
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

export function CacheHitChart({ sprints }: { sprints: DerivedSprint[] }) {
  const filtered = sprints.filter((s) => typeof s.metrics.cache_hit_rate_pct === 'number');
  const values = filtered.map((s) => s.metrics.cache_hit_rate_pct);
  const ma = movingAverage(values, 3);

  const data = filtered.map((s, i) => ({
    label: s.label,
    cache: s.metrics.cache_hit_rate_pct,
    movingAvg: ma[i],
    fill: s.projectColor,
  }));

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <h3 className="text-sm font-semibold text-white mb-4">Cache Hit Rate</h3>
      <ResponsiveContainer width="100%" height={250}>
        <ComposedChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <XAxis
            dataKey="label"
            tick={{ fill: '#6b7280', fontSize: 11 }}
            axisLine={{ stroke: '#1e1e2e' }}
            tickLine={false}
          />
          <YAxis
            domain={[90, 100]}
            tick={{ fill: '#6b7280', fontSize: 11 }}
            axisLine={{ stroke: '#1e1e2e' }}
            tickLine={false}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#13131a',
              border: '1px solid #1e1e2e',
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(v: number, name: string) => [
              `${v}%`,
              name === 'movingAvg' ? '3-sprint avg' : 'Cache Hit',
            ]}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, color: '#6b7280' }}
            formatter={(value) => (value === 'movingAvg' ? '3-sprint moving avg' : 'Cache Hit Rate')}
          />
          <ReferenceLine
            y={BENCHMARKS.cache_hit_rate_target}
            stroke="#22c55e33"
            strokeDasharray="4 4"
            label={{ value: `Target: ${BENCHMARKS.cache_hit_rate_target}%`, fill: '#22c55e', fontSize: 10, position: 'right' }}
          />
          <Area
            dataKey="cache"
            name="cache"
            stroke="#38bdf8"
            fill="#38bdf822"
            strokeWidth={2}
            dot={{ r: 4, fill: '#38bdf8' }}
          />
          <Line
            dataKey="movingAvg"
            name="movingAvg"
            stroke="#fb923c"
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={{ r: 3, fill: '#fb923c' }}
            connectNulls
            type="monotone"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
