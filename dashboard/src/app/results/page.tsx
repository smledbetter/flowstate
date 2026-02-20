import Link from 'next/link';
import { getSprints, getHypotheses } from '@/lib/data';
import { deriveMetrics, resultColor, fmtTokens } from '@/lib/compute';

function Cite({ section, text }: { section: string; text?: string }) {
  return (
    <span className="citation" title={`RESULTS.md ${section}`}>
      [{text || section}]
    </span>
  );
}

function Callout({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="callout">
      <div className="callout-title">{title}</div>
      {children}
    </div>
  );
}

function Tag({ result }: { result: string }) {
  const label =
    result === 'confirmed'
      ? 'Confirmed'
      : result === 'partial'
        ? 'Partial'
        : result === 'falsified'
          ? 'Falsified'
          : 'Inconclusive';
  const cls =
    result === 'confirmed'
      ? 'tag-confirmed'
      : result === 'partial'
        ? 'tag-partial'
        : result === 'falsified'
          ? 'tag-falsified'
          : '';
  return <span className={`tag ${cls}`}>{label}</span>;
}

export default function ResultsPage() {
  const { sprints } = getSprints();
  const { hypotheses } = getHypotheses();
  const derived = sprints.map(deriveMetrics);

  const totalLoc = sprints.reduce((s, sp) => s + (sp.metrics.loc_added || 0), 0);
  const totalTests = Math.max(...sprints.map((s) => s.metrics.tests_total || 0));
  const projectCount = new Set(sprints.map((s) => s.project)).size;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Experiment Results</h1>
        <p className="text-gray-500">
          What 18 sprints across {projectCount} projects and 4 falsification experiments revealed
          about AI-assisted development workflows.
        </p>
      </div>

      <div className="prose-flowstate max-w-4xl">
        {/* ---- Overview ---- */}
        <h2>The Experiment</h2>
        <p>
          Flowstate started as a workflow copied from a single project (Weaveto.do) and tested
          across two additional projects of maximally different types: a{' '}
          <strong>TypeScript CLI tool</strong> (Uluka) and a{' '}
          <strong>Rust P2P encrypted messenger</strong> (Dappled Shade). The goal was not to
          confirm the workflow works, but to{' '}
          <strong>discover where it breaks</strong>. <Cite section="S8.0" text="RESULTS S8.0" />
        </p>

        <p>
          Twelve hypotheses (H1-H12) were defined upfront with explicit falsification criteria.
          Each sprint tested a subset. Four dedicated experiments were designed to attack Flowstate&apos;s
          value proposition under adversarial conditions.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 my-6">
          <div className="bg-card border border-border rounded-lg p-4 text-center">
            <div className="text-2xl font-mono font-bold text-white">{sprints.length}</div>
            <div className="text-xs text-gray-500 mt-1">Sprints</div>
          </div>
          <div className="bg-card border border-border rounded-lg p-4 text-center">
            <div className="text-2xl font-mono font-bold text-white">{projectCount}</div>
            <div className="text-xs text-gray-500 mt-1">Projects</div>
          </div>
          <div className="bg-card border border-border rounded-lg p-4 text-center">
            <div className="text-2xl font-mono font-bold text-white">12</div>
            <div className="text-xs text-gray-500 mt-1">Hypotheses</div>
          </div>
          <div className="bg-card border border-border rounded-lg p-4 text-center">
            <div className="text-2xl font-mono font-bold text-white">4</div>
            <div className="text-xs text-gray-500 mt-1">Experiments</div>
          </div>
        </div>

        {/* ---- Key Findings ---- */}
        <h2>Key Findings</h2>

        <h3>1. Gates are the strongest mechanism</h3>
        <p>
          Experiment 2 planted 3 bugs on a branch (unused import, wrong confidence threshold, type
          error) and ran a normal Flowstate sprint. All 3 were caught by their intended gates — test
          gate, lint gate, and type gate — all fixed in 1 cycle, all traced to the planted commit.{' '}
          <Cite section="S11.3" text="RESULTS S11.3, Exp 2" />
        </p>
        <p>
          Across all 18 sprints and 3 projects, gates caught real issues on every project: clippy
          caught 3 bugs on Dappled Shade S0, lint caught an unused import on Uluka S3, and the
          adversarial test confirmed gates under hostile conditions.
        </p>

        <Callout title="Verdict on gates">
          <p>
            H5 (gates catch real issues) is the most strongly confirmed hypothesis in Flowstate.
            Gates are non-negotiable. Everything else is optional.
          </p>
        </Callout>

        <h3>2. Sprint structure earns its keep on multi-module work</h3>
        <p>
          Experiment 4 combined two milestones (Tor spike + Matrix bridge, ~2.5x normal scope) into
          a single sprint. The 3-phase structure held: planning correctly grouped transport
          concerns, execution produced 2,652 LOC with 48 tests, gates passed first attempt.{' '}
          <Cite section="S11.3" text="RESULTS S11.3, Exp 4" />
        </p>
        <p>
          But Experiment 1 showed the opposite for simple work: no-Flowstate baselines completed{' '}
          <strong>4-8x faster</strong> with comparable quality (76-88% blind review scores) on
          well-scoped single-module tasks. The planning ceremony adds overhead that isn&apos;t justified
          when the scope is small. <Cite section="S11.3" text="RESULTS S11.3, Exp 1" />
        </p>

        <Callout title="When to use Flowstate">
          <p>
            Multi-module sprints where planning prevents wrong turns: use Flowstate. Single-file
            fixes or well-scoped features: skip the ceremony, keep the gates.
          </p>
        </Callout>

        <h3>3. Skills are marginal</h3>
        <p>
          Experiment 1 (no-Flowstate baseline) produced comparable quality without any skill files.
          Experiment 3 (blind compliance scoring) revealed that self-assessed skill compliance was
          shallow — the sprint agent caught process-level gaps but missed 6 code-level violations
          that a blind judge found. <Cite section="S11.3" text="RESULTS S11.3, Exp 1 + Exp 3" />
        </p>
        <p>
          Skill compliance (H7) improved from 3/5 to 5/5 over sprints, but this improvement was
          partially an artifact of how compliance was measured (process checks, not code inspection).
          The H7 audit methodology was upgraded to require dual verification — both process and code
          checks with file:line evidence.
        </p>

        {/* ---- Projects ---- */}
        <h2>Project Timeline</h2>

        <h3>
          Uluka <span className="text-uluka">(TypeScript CLI)</span>
        </h3>
        <p>
          9 sprints, from Phase 14 (Error Taxonomy) through Phase 22 (Crypto Library Knowledge
          Base). Reached <strong>per-project stability</strong> at Sprint 3 — 3 consecutive sprints
          with 0 skill file changes. Current state: 520 tests, 73.91% coverage.{' '}
          <Cite section="S8.1" text="RESULTS S8.1" />
        </p>

        <table>
          <thead>
            <tr>
              <th>Sprint</th>
              <th>Phase</th>
              <th>Time</th>
              <th>Tokens</th>
              <th>Tests</th>
              <th>Gates</th>
              <th>Notable</th>
            </tr>
          </thead>
          <tbody>
            {derived
              .filter((s) => s.project === 'uluka')
              .map((s) => (
                <tr key={s.label}>
                  <td>
                    <Link href={`/sprint/${s.label}`} className="text-uluka hover:underline">
                      {s.label}
                    </Link>
                  </td>
                  <td className="text-gray-400 text-xs">{s.phase || '—'}</td>
                  <td className="font-mono">
                    {s.activeMinutes > 0 ? `${s.activeMinutes}m` : '—'}
                  </td>
                  <td className="font-mono">
                    {s.metrics.new_work_tokens ? fmtTokens(s.metrics.new_work_tokens) : '—'}
                  </td>
                  <td className="font-mono">{s.metrics.tests_total || '—'}</td>
                  <td>
                    {s.metrics.gates_first_pass ? (
                      <span className="text-confirmed text-xs">Pass</span>
                    ) : (
                      <span className="text-falsified text-xs">Fail+Fix</span>
                    )}
                  </td>
                  <td className="text-gray-400 text-xs max-w-[200px]">
                    {s.label === 'uluka-s3' && 'First gate failure (lint)'}
                    {s.label === 'uluka-s8' && 'Exp 2: 3/3 planted bugs caught'}
                    {s.label === 'uluka-s2' && 'First haiku agents'}
                    {s.label === 'uluka-s1' && 'H3 control: consensus wins'}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>

        <h3>
          Dappled Shade <span className="text-ds">(Rust P2P)</span>
        </h3>
        <p>
          3 sprints (S0, S1, S6). Bootstrapped from PRD in <strong>9 minutes 10 seconds</strong>{' '}
          (success criterion required &lt;30 min). Maximally different from Uluka — Rust, crypto, P2P
          networking. Sprint 6 served as Experiment 4 (scope stress test at 2.5x).{' '}
          <Cite section="S8.2" text="RESULTS S8.2" />
        </p>

        <table>
          <thead>
            <tr>
              <th>Sprint</th>
              <th>Phase</th>
              <th>Time</th>
              <th>Tokens</th>
              <th>Tests</th>
              <th>Gates</th>
              <th>Notable</th>
            </tr>
          </thead>
          <tbody>
            {derived
              .filter((s) => s.project === 'dappled-shade')
              .map((s) => (
                <tr key={s.label}>
                  <td>
                    <Link href={`/sprint/${s.label}`} className="text-ds hover:underline">
                      {s.label}
                    </Link>
                  </td>
                  <td className="text-gray-400 text-xs">{s.phase || '—'}</td>
                  <td className="font-mono">
                    {s.activeMinutes > 0 ? `${s.activeMinutes}m` : '—'}
                  </td>
                  <td className="font-mono">
                    {s.metrics.new_work_tokens ? fmtTokens(s.metrics.new_work_tokens) : '—'}
                  </td>
                  <td className="font-mono">{s.metrics.tests_total || '—'}</td>
                  <td>
                    {s.metrics.gates_first_pass ? (
                      <span className="text-confirmed text-xs">Pass</span>
                    ) : s.metrics.gates_first_pass === false ? (
                      <span className="text-falsified text-xs">Fail+Fix</span>
                    ) : (
                      <span className="text-gray-500 text-xs">—</span>
                    )}
                  </td>
                  <td className="text-gray-400 text-xs max-w-[200px]">
                    {s.label === 'ds-s0' && 'Clippy caught 3 bugs'}
                    {s.label === 'ds-s1' && 'Olm E2E encryption'}
                    {s.label === 'ds-s6' && 'Exp 3+4: scope stress 2.5x'}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>

        <h3>
          Weaveto.do <span className="text-[#a78bfa]">(SvelteKit E2EE)</span>
        </h3>
        <p>
          2 sprints (S1, S2). The original project where Flowstate patterns were discovered. Used as
          a third validation point. 403 unit tests + 119 E2E tests.{' '}
          <Cite section="S8.3" text="RESULTS S8.3" />
        </p>

        {/* ---- Hypotheses ---- */}
        <h2>Hypothesis Results</h2>
        <p>
          12 hypotheses defined upfront, tested across 18 sprints. The hypothesis set is capped —
          no new hypotheses will be added. Future sprints re-test with better controls rather than
          expanding scope. <Cite section="S11.4" text="RESULTS S11.4" />
        </p>

        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Hypothesis</th>
              <th>Status</th>
              <th>Key Evidence</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="font-mono text-xs">H1</td>
              <td>3-phase sprint works across project types</td>
              <td><Tag result="confirmed" /></td>
              <td className="text-gray-400 text-xs">18 sprints across TS, Rust, SvelteKit. Weakened by Exp 1 for small tasks.</td>
            </tr>
            <tr>
              <td className="font-mono text-xs">H2</td>
              <td>5-skill set is right for all projects</td>
              <td><Tag result="partial" /></td>
              <td className="text-gray-400 text-xs">All 5 contributed on each project. UX least relevant on CLI. Weakened by Exp 1.</td>
            </tr>
            <tr>
              <td className="font-mono text-xs">H3</td>
              <td>Consensus agent works (skills-as-perspectives)</td>
              <td><Tag result="confirmed" /></td>
              <td className="text-gray-400 text-xs">Control experiment: consensus produced 23 scenarios + security separation vs architect-only 10.</td>
            </tr>
            <tr>
              <td className="font-mono text-xs">H4</td>
              <td>Wave parallelism helps on smaller codebases</td>
              <td><Tag result="confirmed" /></td>
              <td className="text-gray-400 text-xs">Adapts to structure: 3 agents for TS, 14 for Rust modules, 7 for SvelteKit.</td>
            </tr>
            <tr>
              <td className="font-mono text-xs">H5</td>
              <td>Gates catch real issues</td>
              <td><Tag result="confirmed" /></td>
              <td className="text-gray-400 text-xs">Strongest hypothesis. Exp 2: 3/3 planted bugs caught. Proven on all 3 projects.</td>
            </tr>
            <tr>
              <td className="font-mono text-xs">H6</td>
              <td>30-40% context budget is right</td>
              <td><Tag result="partial" /></td>
              <td className="text-gray-400 text-xs">Context never became a blocking issue. Hard to isolate as a factor.</td>
            </tr>
            <tr>
              <td className="font-mono text-xs">H7</td>
              <td>Agents follow skill instructions</td>
              <td><Tag result="partial" /></td>
              <td className="text-gray-400 text-xs">3/5 to 5/5 improvement, but Exp 3 showed process audits inflate scores.</td>
            </tr>
            <tr>
              <td className="font-mono text-xs">H8</td>
              <td>Coverage gate catches regressions</td>
              <td><Tag result="confirmed" /></td>
              <td className="text-gray-400 text-xs">Coverage floor enforced on every sprint. Exp 2: adversarial confirmation.</td>
            </tr>
            <tr>
              <td className="font-mono text-xs">H9</td>
              <td>Lint gate catches dead code</td>
              <td><Tag result="confirmed" /></td>
              <td className="text-gray-400 text-xs">Caught unused import on Uluka S3. Exp 2: caught planted unused import.</td>
            </tr>
            <tr>
              <td className="font-mono text-xs">H10</td>
              <td>Haiku viable for mechanical tasks</td>
              <td><Tag result="confirmed" /></td>
              <td className="text-gray-400 text-xs">Single-file: 5 tool uses, 13s, clean. Multi-file: better with sonnet.</td>
            </tr>
            <tr>
              <td className="font-mono text-xs">H11</td>
              <td>Works for greenfield projects</td>
              <td><Tag result="confirmed" /></td>
              <td className="text-gray-400 text-xs">DS S0: empty repo to 3,268 LOC + 57 tests, all gates passing.</td>
            </tr>
            <tr>
              <td className="font-mono text-xs">H12</td>
              <td>Skills generalize across languages</td>
              <td><Tag result="confirmed" /></td>
              <td className="text-gray-400 text-xs">TS to Rust: content adaptation only, no structural rewrites. 2 Rust-specific gaps added.</td>
            </tr>
          </tbody>
        </table>

        <p>
          Full hypothesis heatmap across all sprints is available on the{' '}
          <Link href="/hypotheses">Hypotheses page</Link>.
        </p>

        {/* ---- Experiments ---- */}
        <h2>The Four Experiments</h2>

        <h3>Experiment 1: No-Flowstate Baseline</h3>
        <p>
          Built one milestone on each project with raw Claude Code — no skills, no phases, no
          gates. Both baselines completed <strong>4-8x faster</strong> with comparable quality
          (76-88% blind review). <Cite section="S11.3" text="RESULTS S11.3" />
        </p>
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>With Flowstate</th>
              <th>Without</th>
              <th>Implication</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Speed</td>
              <td>10-22 min typical</td>
              <td>4-8x faster</td>
              <td>Overhead not justified for single-module work</td>
            </tr>
            <tr>
              <td>Quality (blind review)</td>
              <td>72-88%</td>
              <td>76-88%</td>
              <td>Comparable — skills not clearly necessary</td>
            </tr>
          </tbody>
        </table>
        <p>
          <strong>Verdict</strong>: H1 weakened for well-scoped work. H7 partially falsified
          (comparable quality without skills). This led to the &quot;light mode&quot; addition — small sprints
          skip planning ceremony, keep gates.
        </p>

        <h3>Experiment 2: Adversarial Gate Test</h3>
        <p>
          Three bugs planted on a branch: wrong threshold, type error, unused import. A normal
          Flowstate sprint ran against the branch. <Cite section="S11.3" text="RESULTS S11.3" />
        </p>

        <Callout title="Result: 3/3 caught">
          <p>
            Every planted bug was caught by its intended gate. All fixed in 1 fix cycle. All traced
            back to the planted commit. This is the strongest evidence that gates earn their keep.
          </p>
        </Callout>

        <h3>Experiment 3: Blind Compliance Scoring</h3>
        <p>
          After DS S6, code artifacts were given to a fresh agent with zero Flowstate knowledge for
          5-dimension blind scoring. The self-assessment was not inflated but was{' '}
          <strong>shallow</strong>: the sprint agent caught process-level gaps (no security audit
          wave) but missed 6 code-level violations (non-constant-time token comparison, 0.0.0.0
          bind, missing cancellation safety docs, weak hash, visibility issues, unjustified
          allow(dead_code)). <Cite section="S11.3" text="RESULTS S11.3" />
        </p>
        <p>
          <strong>Blind scores</strong>: Scope 4/5, Tests 4/5, Code quality 3/5, Convention
          compliance 3/5, Diff hygiene 4/5. Overall:{' '}
          <span className="metric-inline text-partial">18/25 (72%)</span>.
        </p>
        <p>
          <strong>Verdict</strong>: H7 audit methodology was insufficient. Upgraded to require dual
          verification (process + code with file:line evidence).
        </p>

        <h3>Experiment 4: Scope Stress Test</h3>
        <p>
          DS S6 combined M4 (Tor spike) + M5 (Matrix bridge) — ~2.5x normal scope.
          Structure held: 2,652 LOC, 48 tests, gates first pass. Planning correctly grouped
          transport concerns. <Cite section="S11.3" text="RESULTS S11.3" />
        </p>
        <p>
          <strong>Verdict</strong>: H1 confirmed under scope stress. This partially counters Exp 1
          — for multi-module work, the planning phase prevents wrong turns and wasted effort.
        </p>

        {/* ---- What It All Means ---- */}
        <h2>The Bottom Line</h2>
        <p>
          After 18 sprints, 3 projects, and 4 experiments designed to break it, two things matter:
        </p>
        <ul>
          <li>
            <strong>Gates catch real bugs</strong> — reliably, automatically, and without human
            intervention. Non-negotiable.
          </li>
          <li>
            <strong>Sprint structure prevents wrong turns on multi-module work</strong> — the
            planning phase is worth its overhead when scope crosses module boundaries.
          </li>
        </ul>
        <p>Everything else is optional:</p>
        <ul>
          <li>
            Skills produce comparable quality to no-skills (Exp 1). Keep them if you want
            consistency, but they&apos;re not the quality mechanism — gates are.
          </li>
          <li>
            The full 3-phase ceremony adds 4-8x overhead for simple tasks. Use light mode.
          </li>
          <li>
            Model mix, context management, and wave parallelism are useful optimizations but not
            load-bearing. They make sprints cheaper and faster without affecting correctness.
          </li>
        </ul>

        {/* ---- Methodology ---- */}
        <h2>Methodology and Limitations</h2>
        <p>
          Honest accounting of what this data can and cannot show:{' '}
          <Cite section="S11.2" text="RESULTS S11.2" />
        </p>
        <ul>
          <li>
            <strong>No true control</strong>: Experiment 1 provides the closest baseline, but
            projects and task difficulty varied. Causal attribution is limited.
          </li>
          <li>
            <strong>Self-assessed compliance</strong>: H7 audits were performed by the sprint
            agent, not an independent reviewer. Experiment 3 confirmed this inflates scores.
          </li>
          <li>
            <strong>Project selection bias</strong>: all projects chosen by the system&apos;s creator.
            None is a team project, legacy codebase, or data pipeline.
          </li>
          <li>
            <strong>Model versions unrecorded</strong>: sprints log model tier (opus/sonnet/haiku)
            but not specific version. Claude capability changes between sprints could confound
            comparisons.
          </li>
          <li>
            <strong>Tokens/LOC is noisy</strong>: 78-256 new-work tokens/LOC across sprints.
            Variation reflects milestone complexity, not workflow maturity. Do not compare across
            project types.
          </li>
        </ul>

        <p>
          &quot;Confirmed&quot; means the available evidence supports the hypothesis enough to continue
          relying on the pattern. All confirmations are provisional and can be overturned by future
          sprints. <Cite section="S11.1" text="RESULTS S11.1" />
        </p>
      </div>
    </div>
  );
}
