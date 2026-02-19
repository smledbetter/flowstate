export function BenchmarkCard({
  label,
  actual,
  target,
  unit,
  better,
}: {
  label: string;
  actual: number | string;
  target: number | string;
  unit?: string;
  better: 'lower' | 'higher';
}) {
  const numActual = typeof actual === 'number' ? actual : parseFloat(actual);
  const numTarget = typeof target === 'number' ? target : parseFloat(target);
  const isGood = better === 'lower' ? numActual <= numTarget : numActual >= numTarget;

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">{label}</p>
      <div className="flex items-baseline gap-2">
        <span className={`text-2xl font-mono font-semibold ${isGood ? 'text-confirmed' : 'text-partial'}`}>
          {actual}
          {unit}
        </span>
        <span className="text-xs text-gray-500">
          target: {target}
          {unit}
        </span>
      </div>
    </div>
  );
}
