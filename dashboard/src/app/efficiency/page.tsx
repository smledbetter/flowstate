import { getSprints } from '@/lib/data';
import { deriveMetrics, aggregateStats, BENCHMARKS, fmtTokens } from '@/lib/compute';
import { BenchmarkCard } from '@/components/cards/BenchmarkCard';
import { SectionHeader } from '@/components/layout/SectionHeader';
import { TokensChart } from '@/components/charts/TokensChart';
import { CacheHitChart } from '@/components/charts/CacheHitChart';
import { TokenomicsDonut } from './TokenomicsDonut';
import { BenchmarkLadder } from './BenchmarkLadder';

export default function EfficiencyPage() {
  const { sprints } = getSprints();
  const derived = sprints.map(deriveMetrics);
  const stats = aggregateStats(sprints);

  const cacheRates = sprints
    .map((s) => s.metrics.cache_hit_rate_pct)
    .filter((v): v is number => typeof v === 'number' && !isNaN(v));
  const avgCache = cacheRates.length
    ? Math.round((cacheRates.reduce((a, b) => a + b, 0) / cacheRates.length) * 10) / 10
    : 0;

  // Compute our averages for reference
  const tokensPerLoc = derived.map((s) => s.newWorkTokensPerLoc);
  const minTokensLoc = Math.min(...tokensPerLoc);
  const maxTokensLoc = Math.max(...tokensPerLoc);
  const avgTokensLoc = stats.avgNewWorkTokensPerLoc;
  const minCache = cacheRates.length ? Math.min(...cacheRates) : 0;
  const maxCache = cacheRates.length ? Math.max(...cacheRates) : 0;
  const avgActiveMin = Math.round(stats.totalTimeMinutes / stats.totalSprints);
  const avgTotalTokens = Math.round(sprints.reduce((s, sp) => s + sp.metrics.total_tokens, 0) / sprints.length);
  const avgNewWork = Math.round(sprints.reduce((s, sp) => s + sp.metrics.new_work_tokens, 0) / sprints.length);
  const avgLoc = Math.round(stats.totalLoc / stats.totalSprints);
  const avgApiCalls = Math.round(sprints.reduce((s, sp) => s + sp.metrics.api_calls, 0) / sprints.length);
  const avgSubagents = Math.round(sprints.reduce((s, sp) => s + sp.metrics.subagents, 0) / sprints.length * 10) / 10;

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-bold text-white mb-2">Efficiency Analysis</h1>
        <p className="text-gray-500">
          Token efficiency benchmarks grounded in research from SWE-Effi and tokenomics studies
        </p>
      </div>

      {/* Benchmark Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <BenchmarkCard
          label="Avg Tokens/LOC"
          actual={stats.avgNewWorkTokensPerLoc}
          target={BENCHMARKS.tokens_per_loc_target}
          better="lower"
        />
        <BenchmarkCard
          label="Cache Hit Rate"
          actual={avgCache}
          target={BENCHMARKS.cache_hit_rate_target}
          unit="%"
          better="higher"
        />
        <BenchmarkCard
          label="Gates First Pass"
          actual={stats.gatesFirstPassRate}
          target={80}
          unit="%"
          better="higher"
        />
        <BenchmarkCard
          label="Total New-Work Tokens"
          actual={fmtTokens(stats.totalNewWork)}
          target={`for ${stats.totalLoc} LOC`}
          better="lower"
        />
      </div>

      {/* Tokenomics + Benchmark Ladder */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TokenomicsDonut />
        <BenchmarkLadder actual={stats.avgNewWorkTokensPerLoc} />
      </div>

      {/* Charts */}
      <TokensChart sprints={derived} />
      <CacheHitChart sprints={derived} />

      {/* Flowstate Averages */}
      <div>
        <SectionHeader title="Our Averages" subtitle={`Across ${stats.totalSprints} sprints, ${stats.totalLoc.toLocaleString()} LOC`} />
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-xs text-gray-500 mb-1">Avg Tokens/LOC</p>
            <p className="text-xl font-mono font-semibold text-confirmed">{avgTokensLoc}</p>
            <p className="text-xs text-gray-600 mt-1">{minTokensLoc}-{maxTokensLoc} range</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-xs text-gray-500 mb-1">Avg Cache Hit</p>
            <p className="text-xl font-mono font-semibold text-confirmed">{avgCache}%</p>
            <p className="text-xs text-gray-600 mt-1">{minCache}-{maxCache}% range</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-xs text-gray-500 mb-1">Avg Session Time</p>
            <p className="text-xl font-mono font-semibold text-white">{avgActiveMin}m</p>
            <p className="text-xs text-gray-600 mt-1">per sprint</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-xs text-gray-500 mb-1">Avg Total Tokens</p>
            <p className="text-xl font-mono font-semibold text-white">{fmtTokens(avgTotalTokens)}</p>
            <p className="text-xs text-gray-600 mt-1">per sprint</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-xs text-gray-500 mb-1">Avg New-Work</p>
            <p className="text-xl font-mono font-semibold text-white">{fmtTokens(avgNewWork)}</p>
            <p className="text-xs text-gray-600 mt-1">per sprint</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-xs text-gray-500 mb-1">Avg LOC / Sprint</p>
            <p className="text-xl font-mono font-semibold text-white">{avgLoc.toLocaleString()}</p>
            <p className="text-xs text-gray-600 mt-1">{avgSubagents} agents avg</p>
          </div>
        </div>
      </div>

      {/* Research Benchmarks */}
      <div>
        <SectionHeader title="Research Benchmarks" subtitle="How Flowstate compares to published studies" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Flowstate Actual Ranges */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Flowstate Actual vs Targets</h3>
            <div className="space-y-4 text-sm">
              {[
                { label: 'New-work tokens/LOC', actual: `${minTokensLoc}-${maxTokensLoc} (avg ${avgTokensLoc})`, target: '<300', status: 'good' as const },
                { label: 'Cache hit rate', actual: `${minCache}-${maxCache}% (avg ${avgCache}%)`, target: '>80%', status: 'good' as const },
                { label: 'Context compressions', actual: '0-1/sprint', target: '0', status: 'good' as const },
                { label: 'Delegation ratio', actual: '0.8-9.6%', target: '>30%', status: 'warn' as const },
                { label: 'Avg API calls', actual: `${avgApiCalls}/sprint`, target: '-', status: 'good' as const },
                { label: 'Avg subagents', actual: `${avgSubagents}/sprint`, target: '-', status: 'good' as const },
              ].map((row) => (
                <div key={row.label} className="flex items-center justify-between">
                  <span className="text-gray-400">{row.label}</span>
                  <div className="flex items-center gap-3">
                    <span className={`font-mono ${row.status === 'good' ? 'text-confirmed' : 'text-partial'}`}>
                      {row.actual}
                    </span>
                    {row.target !== '-' && <span className="text-gray-600 text-xs">target: {row.target}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Failure Cost */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Failure Cost (SWE-Effi)</h3>
            <p className="text-sm text-gray-400 mb-4">
              Failed attempts consume <span className="text-partial font-mono">4-5x</span> more tokens than successful ones.
            </p>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400">SWE-Agent failures</span>
                  <span className="font-mono text-falsified">8.8M tokens</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <div className="h-2 rounded-full bg-red-500" style={{ width: '100%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400">SWE-Agent successes</span>
                  <span className="font-mono text-confirmed">1.8M tokens</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <div className="h-2 rounded-full bg-green-500" style={{ width: '20.5%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-uluka">Flowstate avg sprint</span>
                  <span className="font-mono text-uluka">{fmtTokens(avgTotalTokens)} tokens</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <div className="h-2 rounded-full bg-uluka" style={{ width: `${(avgTotalTokens / 8800000) * 100}%` }} />
                </div>
              </div>
            </div>
          </div>

          {/* Multi-Agent Overhead */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Multi-Agent Overhead</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">MetaGPT (5 agents)</span>
                <span className="font-mono text-white">138K-207K tokens/task</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">ChatDev (7 agents)</span>
                <span className="font-mono text-white">184K-259K tokens/task</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Verification overhead</span>
                <span className="font-mono text-partial">72% of tokens</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Input-to-output ratio</span>
                <span className="font-mono text-white">2:1 to 3:1</span>
              </div>
            </div>
            <div className="border-t border-border mt-4 pt-3">
              <div className="flex justify-between text-sm">
                <span className="text-uluka">Flowstate avg new-work</span>
                <span className="font-mono text-uluka">{fmtTokens(avgNewWork)}/sprint</span>
              </div>
              <div className="flex justify-between text-sm mt-1">
                <span className="text-uluka">Flowstate avg agents</span>
                <span className="font-mono text-uluka">{avgSubagents}/sprint</span>
              </div>
            </div>
          </div>

          {/* Cost Per Issue */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Cost Per Issue (SWE-bench)</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Efficient (Claude/OpenHands, 27% resolve)</span>
                <span className="font-mono text-confirmed">$0.30</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Moderate (GPT-5-codex)</span>
                <span className="font-mono text-white">$0.51</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">SWE-Effi efficiency cap</span>
                <span className="font-mono text-partial">$1.00</span>
              </div>
            </div>
            <p className="text-xs text-gray-600 mt-3">
              Cache savings: 78-79% cost reduction with Claude Sonnet prompt caching.
            </p>
          </div>
        </div>
      </div>

      {/* Sources */}
      <div className="bg-card border border-border rounded-lg p-6">
        <SectionHeader title="Methodology & Sources" />
        <div className="text-sm text-gray-400 space-y-3 mb-6">
          <p>
            <strong className="text-gray-300">New-work tokens/LOC</strong> measures output + cache_creation tokens
            divided by lines of code added. This isolates the cost of generating new code from the cost of reading
            existing context (which is cache-dominated and cheap).
          </p>
          <p>
            <strong className="text-gray-300">SWE-bench benchmarks</strong> from SWE-Effi define efficient (&lt;1,000
            tokens/LOC) and moderate (1,000-5,000) ranges for general coding agents. Flowstate targets &lt;300,
            achievable through structured planning, wave parallelism, and aggressive caching.
          </p>
          <p>
            <strong className="text-gray-300">Tokenomics research</strong> shows only 8.6% of tokens in typical
            AI-assisted development are code generation. 59.4% goes to review and verification. This is expected
            and healthy -- the review overhead is what makes gates and quality checks work.
          </p>
        </div>
        <div className="border-t border-border pt-4">
          <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-3">Sources</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-gray-500">
            <span>SWE-Effi (Fan et al., Sep 2025) -- arxiv.org/html/2509.09853v2</span>
            <span>Tokenomics (Jan 2026) -- arxiv.org/html/2601.14470</span>
            <span>Don&apos;t Break the Cache (Jan 2026) -- arxiv.org/abs/2601.06007</span>
            <span>FeatBench (Sep 2025) -- arxiv.org/html/2509.22237</span>
            <span>LoCoBench-Agent -- arxiv.org/html/2511.13998</span>
            <span>OpenHands eval -- openhands.dev/blog/evaluation-of-llms-as-coding-agents-on-swe-bench-at-30x-speed</span>
          </div>
        </div>
      </div>
    </div>
  );
}
