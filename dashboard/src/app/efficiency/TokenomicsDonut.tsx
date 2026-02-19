'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { BENCHMARKS } from '@/lib/compute';

const data = [
  { name: 'Code Generation', value: BENCHMARKS.code_generation_pct, color: '#38bdf8' },
  { name: 'Review & Verification', value: BENCHMARKS.review_pct, color: '#a78bfa' },
  { name: 'Other', value: 100 - BENCHMARKS.code_generation_pct - BENCHMARKS.review_pct, color: '#374151' },
];

export function TokenomicsDonut() {
  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <h3 className="text-sm font-semibold text-white mb-4">Where Tokens Go (Industry Average)</h3>
      <div className="flex items-center">
        <ResponsiveContainer width="50%" height={200}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#13131a',
                border: '1px solid #1e1e2e',
                borderRadius: 8,
                fontSize: 12,
              }}
              formatter={(v: number) => `${v}%`}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="space-y-3 text-sm">
          {data.map((d) => (
            <div key={d.name} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: d.color }} />
              <span className="text-gray-400">{d.name}</span>
              <span className="font-mono text-white ml-auto">{d.value}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
