'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { DerivedSprint } from '@/types/sprint';

export function SessionTimeChart({ sprints }: { sprints: DerivedSprint[] }) {
  const data = sprints.map((s) => ({
    label: s.label,
    minutes: s.activeMinutes,
    fill: s.projectColor,
  }));

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <h3 className="text-sm font-semibold text-white mb-4">Active Session Time</h3>
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
            tickFormatter={(v) => `${v}m`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#13131a',
              border: '1px solid #1e1e2e',
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(v: number) => [`${v}m`, 'Active Time']}
          />
          <Bar dataKey="minutes" name="Active Time" radius={[4, 4, 0, 0]}>
            {data.map((entry, i) => (
              <rect key={i} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
