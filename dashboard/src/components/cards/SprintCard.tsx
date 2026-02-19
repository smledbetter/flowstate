import Link from 'next/link';
import type { DerivedSprint } from '@/types/sprint';

export function SprintCard({ sprint }: { sprint: DerivedSprint }) {
  const m = sprint.metrics;
  return (
    <Link
      href={`/sprint/${encodeURIComponent(sprint.label)}`}
      className="block bg-card border border-border rounded-lg p-4 hover:border-gray-600 transition-colors"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold text-white text-sm">{sprint.label}</span>
        <span
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: sprint.projectColor }}
        />
      </div>
      <p className="text-xs text-gray-500 mb-3 line-clamp-1">{sprint.phase}</p>
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div>
          <span className="text-gray-500">Tokens/LOC</span>
          <p className="font-mono text-white">{sprint.newWorkTokensPerLoc}</p>
        </div>
        <div>
          <span className="text-gray-500">Time</span>
          <p className="font-mono text-white">{sprint.activeMinutes}m</p>
        </div>
        <div>
          <span className="text-gray-500">Gates</span>
          <p className={m.gates_first_pass ? 'text-confirmed' : 'text-partial'}>
            {m.gates_first_pass ? 'Pass' : 'Retry'}
          </p>
        </div>
      </div>
    </Link>
  );
}
