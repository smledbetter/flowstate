import Link from 'next/link';

function Cite({ section, text }: { section: string; text?: string }) {
  return (
    <span className="citation" title={`PRD.md ${section}`}>
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

export default function PrdPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">System Design</h1>
        <p className="text-gray-500">
          A written summary of the Flowstate PRD — what it is, how it works, and why it was built
          this way.
        </p>
      </div>

      <div className="prose-flowstate max-w-4xl">
        {/* ---- What Flowstate Is ---- */}
        <h2>What Flowstate Is</h2>
        <p>
          Flowstate is a <strong>set of markdown files and Claude Code skills</strong> for
          sprint-based, multi-agent software development. It sits on top of Claude Code — it is not
          a SaaS product, a CLI tool, or a framework. You own the files, version control them, and
          evolve them with your project. <Cite section="S2" text="PRD S2" />
        </p>

        <Callout title="Design priorities (in order)">
          <p>
            1. <strong>Code quality</strong> — correct, tested, reviewed code ships. Gates are the
            hard constraint.
          </p>
          <p>
            2. <strong>Wall time</strong> — parallelism and smart delegation minimize calendar time.
          </p>
          <p>
            3. <strong>Token efficiency</strong> — model mix, caching, and context management
            minimize cost per unit of accepted work.
          </p>
        </Callout>

        <p>
          The system is <strong>PRD-first</strong> (every project starts from a specification),{' '}
          <strong>sprint-structured</strong> (work happens in phases with gates),{' '}
          <strong>empirical</strong> (patterns are hypotheses tested across projects, not axioms),
          and <strong>human-steered</strong> (the human reviews plans, approves gates, and decides
          which retrospective changes to adopt). <Cite section="S2" text="PRD S2" />
        </p>

        {/* ---- The Sprint ---- */}
        <h2>The Sprint</h2>
        <p>
          A sprint is the atomic unit of work. Every sprint follows three phases:{' '}
          <Cite section="S4.1" text="PRD S4.1" />
        </p>

        <div className="bg-card border border-border rounded-lg p-5 my-6 font-mono text-sm text-gray-300 overflow-x-auto">
          <div className="grid grid-cols-3 gap-6">
            <div>
              <div className="text-white font-semibold mb-2">Phase 1: THINK</div>
              <div className="text-gray-400 text-xs leading-relaxed">
                PRD/milestone loaded
                <br />
                Consensus agent (PM + UX + Arch)
                <br />
                Produces acceptance.md
                <br />
                Produces implementation.md
              </div>
            </div>
            <div>
              <div className="text-white font-semibold mb-2">Phase 2: EXECUTE + GATE</div>
              <div className="text-gray-400 text-xs leading-relaxed">
                Wave-based parallel execution
                <br />
                Subagents with fresh context
                <br />
                Ship-readiness gate
                <br />
                PASS or fix + re-gate (max 3)
              </div>
            </div>
            <div>
              <div className="text-white font-semibold mb-2">Phase 3: SHIP</div>
              <div className="text-gray-400 text-xs leading-relaxed">
                Metrics collection
                <br />
                Doc sync + roadmap update
                <br />
                Retrospective with diffs
                <br />
                Next sprint baseline
              </div>
            </div>
          </div>
        </div>

        <p>
          Phase 1 and 2 are combined into a single prompt — the agent plans and immediately
          executes without a human approval break. Only Phase 3 (Ship) has a checkpoint. This was a
          deliberate design choice to minimize human idle time.{' '}
          <Cite section="S5.4" text="PRD S5.4" />
        </p>

        <p>
          <strong>Light mode</strong>: Experiment 1 showed the full planning ceremony adds ~4x
          overhead for small, well-scoped tasks (3 files or fewer, no new dependencies). Small
          sprints skip planning and go straight to implementation. Gates are mandatory regardless.{' '}
          <Cite section="S4.8" text="PRD S4.8" />
        </p>

        {/* ---- Skills vs Gates ---- */}
        <h2>Skills vs Gates</h2>
        <p>
          This distinction is <strong>load-bearing</strong>.{' '}
          <Cite section="S4.2" text="PRD S4.2" />
        </p>

        <table>
          <thead>
            <tr>
              <th>Layer</th>
              <th>Nature</th>
              <th>Examples</th>
              <th>Enforced by</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>
                <span className="text-confirmed font-semibold">Gate</span> (hard)
              </td>
              <td>Enforcement</td>
              <td>Tests pass, types check, lint clean, coverage threshold</td>
              <td>Automated commands returning pass/fail</td>
            </tr>
            <tr>
              <td>
                <span className="text-partial font-semibold">Skill</span> (soft)
              </td>
              <td>Advisory</td>
              <td>&quot;No plaintext logging&quot;, &quot;use pure functions&quot;, &quot;write Gherkin criteria&quot;</td>
              <td>Agent following instructions (unverifiable without a gate)</td>
            </tr>
          </tbody>
        </table>

        <Callout title="The rule">
          <p>
            Any skill instruction that matters enough to block shipping must have a corresponding
            gate. If you can&apos;t automate the check, the skill is aspirational, not operational.
          </p>
        </Callout>

        <p>
          Experiment 2 validated this hierarchy decisively: all 3 planted bugs were caught by gates,
          not by skill instructions. Experiment 1 showed comparable code quality{' '}
          <em>without skills at all</em> — but gates remained essential. Gates are the strongest
          mechanism in Flowstate.{' '}
          <Link href="/results">See Results</Link>
        </p>

        {/* ---- Quality Gates ---- */}
        <h2>Quality Gates</h2>
        <p>
          Gates are non-negotiable. A sprint cannot ship unless all enabled gates pass:{' '}
          <Cite section="S4.6" text="PRD S4.6" />
        </p>

        <table>
          <thead>
            <tr>
              <th>Gate</th>
              <th>Default</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Tests pass</td>
              <td>Required</td>
              <td>Command configurable per project</td>
            </tr>
            <tr>
              <td>Type check</td>
              <td>Required</td>
              <td><code>tsc --noEmit</code>, <code>cargo check</code>, etc.</td>
            </tr>
            <tr>
              <td>Coverage threshold</td>
              <td>75% lines</td>
              <td>Configurable percentage</td>
            </tr>
            <tr>
              <td>Lint clean</td>
              <td>Required</td>
              <td>Formatter + linter required at bootstrap</td>
            </tr>
            <tr>
              <td>No regressions</td>
              <td>Required</td>
              <td>Classify failures as regression vs feature</td>
            </tr>
            <tr>
              <td>Smoke test</td>
              <td>Optional</td>
              <td>One real end-to-end exercise, not mocks</td>
            </tr>
            <tr>
              <td>Custom gates</td>
              <td>None</td>
              <td>Turn skill instructions into enforceable checks</td>
            </tr>
          </tbody>
        </table>

        <p>
          When gates fail, findings include <strong>specific file paths and line numbers</strong>,
          not just pass/fail. Each test failure is classified as a <strong>regression</strong>{' '}
          (existing test now fails — agent damaged code) or <strong>feature failure</strong> (new
          test doesn&apos;t pass — implementation incomplete). This distinction drives different fix
          strategies. <Cite section="S4.6" text="PRD S4.6" />
        </p>

        {/* ---- The Architect ---- */}
        <h2>The Architect</h2>
        <p>
          The architect is the lead agent. It reads the PRD, plans each sprint, decides the agent
          strategy, manages the orchestration budget, runs the retrospective, and proposes process
          improvements. It <strong>never writes feature code directly</strong> — it operates in
          delegate mode. <Cite section="S4.3" text="PRD S4.3" />
        </p>

        <h3>Agent Strategy Selection</h3>
        <table>
          <thead>
            <tr>
              <th>Signal</th>
              <th>Strategy</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>1 file, simple fix</td>
              <td>Solo haiku subagent</td>
              <td><span className="tag tag-confirmed">Proven</span></td>
            </tr>
            <tr>
              <td>1 subsystem, moderate</td>
              <td>Solo sonnet subagent</td>
              <td><span className="tag tag-confirmed">Proven</span></td>
            </tr>
            <tr>
              <td>2-3 independent subsystems</td>
              <td>Parallel subagents (wave-based)</td>
              <td><span className="tag tag-confirmed">Proven</span></td>
            </tr>
            <tr>
              <td>3+ needing coordination</td>
              <td>Agent team with shared task list</td>
              <td><span className="tag tag-partial">Unvalidated</span></td>
            </tr>
            <tr>
              <td>Security-critical</td>
              <td>Opus-led with plan approval</td>
              <td><span className="tag tag-confirmed">Proven</span></td>
            </tr>
          </tbody>
        </table>

        {/* ---- Context Management ---- */}
        <h2>Context Management</h2>
        <p>
          Context rot is the primary enemy of code quality. The system enforces several rules to
          keep context healthy: <Cite section="S4.5" text="PRD S4.5" />
        </p>
        <ul>
          <li>
            <strong>Orchestrator stays thin</strong> — target 30-40% context usage. Delegates, doesn&apos;t
            accumulate.
          </li>
          <li>
            <strong>Fresh context per worker</strong> — each subagent gets a clean 200K window.
          </li>
          <li>
            <strong>File references, not content</strong> — pass <code>@file-path</code>, let
            workers read what they need.
          </li>
          <li>
            <strong>Collect summaries, not raw output</strong> — workers report results; orchestrator
            doesn&apos;t re-read files.
          </li>
          <li>
            <strong>Commit per wave</strong> — atomic commits create durable checkpoints.
          </li>
          <li>
            <strong>Session breaks at 50%</strong> — if context exceeds 50%, commit and start fresh.
          </li>
        </ul>

        {/* ---- The Retrospective ---- */}
        <h2>The Retrospective</h2>
        <p>
          Every sprint ends with a structured retrospective that produces two outputs:{' '}
          <Cite section="S4.8" text="PRD S4.8" />
        </p>

        <h3>1. The Report (informational)</h3>
        <p>
          What was built, primary metrics vs previous sprint, what worked and what failed — with
          specific evidence, not vibes.
        </p>

        <h3>2. The Change Proposal (actionable)</h3>
        <p>
          Each proposed change is a <strong>diff</strong> — the literal before/after edit to a skill
          file or process document. The retro format gate enforces this: a retrospective without at
          least one diff block is rejected automatically.
        </p>

        <Callout title="Simplification bias">
          <p>
            When proposing skill changes, prefer removing or simplifying instructions over adding
            new ones. Research shows compliance drops ~6 percentage points per additional
            instruction, falling below 50% at 3+ simultaneous instructions. Every new instruction
            must justify the compliance cost to existing ones.
          </p>
        </Callout>

        <p>
          The human reviews retrospective proposals <strong>after the sprint session ends</strong>,
          not mid-session. Each change is individually approve/modify/reject. Rejected changes
          include a reason that feeds into the next retro.
        </p>

        {/* ---- Metrics ---- */}
        <h2>Metrics</h2>
        <p>
          Metrics are organized into <strong>primary</strong> (drive decisions every sprint) and{' '}
          <strong>diagnostic</strong> (investigated when a primary metric goes wrong).{' '}
          <Cite section="S4.7" text="PRD S4.7" />
        </p>

        <h3>Primary Metrics</h3>
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>What it measures</th>
              <th>Decision it drives</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>First-pass gate success</td>
              <td>Did code pass gates before fixes?</td>
              <td>Skill quality — are agents writing correct code?</td>
            </tr>
            <tr>
              <td>Active session time</td>
              <td>Sum of active session durations</td>
              <td>Parallelism effectiveness</td>
            </tr>
            <tr>
              <td>Total new-work tokens</td>
              <td>Non-cache tokens consumed</td>
              <td>Raw cost of the sprint</td>
            </tr>
          </tbody>
        </table>

        <h3>Diagnostic Metrics</h3>
        <p>
          Model mix, cache hit rate, meta overhead ratio, tokens per accepted LOC, agent spawn
          count, test count, coverage delta, defects found by gate, delegation ratio, and context
          compressions. These are only investigated when primary metrics go wrong.
        </p>
        <p>
          All metrics are parsed automatically from Claude Code&apos;s JSONL session logs by{' '}
          <code>collect.sh</code>. No manual tracking of any kind.{' '}
          <Cite section="S4.7" text="PRD S4.7" />
        </p>

        {/* ---- Tiered Portability ---- */}
        <h2>Tiered Portability</h2>
        <p>
          Flowstate runs in environments with different levels of tooling access:{' '}
          <Cite section="S9" text="PRD S9" />
        </p>

        <table>
          <thead>
            <tr>
              <th>Tier</th>
              <th>Environment</th>
              <th>What works</th>
              <th>Feedback mechanism</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Tier 1: Full</strong></td>
              <td>Personal machine, Claude Code + bash</td>
              <td>Skills, gates, automated metrics, full retros</td>
              <td>Automated via <code>collect.sh</code></td>
            </tr>
            <tr>
              <td><strong>Tier 2: Skills + Structure</strong></td>
              <td>Work laptop, restricted bash</td>
              <td>Skills, sprint structure, manual gates</td>
              <td>Sanitized export (human-redacted)</td>
            </tr>
            <tr>
              <td><strong>Tier 3: Prompt-only</strong></td>
              <td>Any LLM interface</td>
              <td>Sprint structure as a prompting pattern</td>
              <td>Manual observation</td>
            </tr>
          </tbody>
        </table>

        <p>
          Tier 2 exists specifically for environments where source code must not leave the machine.
          The human is the firewall — the retro agent produces a full local retrospective AND a
          sanitized export. Nothing project-specific crosses the boundary.
        </p>

        {/* ---- Stability and Exit ---- */}
        <h2>Stability and Exit Criteria</h2>
        <p>
          Flowstate is not meant to be perpetually evolving. The goal is to reach a{' '}
          <strong>stable state</strong> where the system works reliably and changes are rare.{' '}
          <Cite section="S12" text="PRD S12" />
        </p>

        <Callout title="Stable state definition">
          <p>
            When 3 consecutive sprints on the same project produce no human-approved retrospective
            changes to core skill files, Flowstate is stable for that project type. Cross-project
            stability requires stable state on 3+ different project types.
          </p>
        </Callout>

        <p>
          Current stability status: <strong>Uluka is STABLE</strong> (3/3 consecutive clean
          sprints), Dappled Shade is at 2/3, Weaveto.do is at 2/2.{' '}
          <Link href="/results">See full results</Link>
        </p>

        <p>
          This prevents Flowstate from becoming a permanent hobby project disguised as productivity
          tooling. <Cite section="S12" text="PRD S12" />
        </p>
      </div>
    </div>
  );
}
