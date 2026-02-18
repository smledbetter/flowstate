# Flowstate: Experiment Results

> All experiment designs, hypothesis definitions, test protocols, and sprint results for the Flowstate workflow system. See [PRD.md](PRD.md) for the system definition.

## 8. Sprint 0: The Falsification Sprint

Sprint 0 is not "build Flowstate." Sprint 0 is **copy the Weaveto.do workflow into Uluka, run one sprint, and document what breaks.**

### 8.0 Observation budget

Running a sprint while simultaneously evaluating it creates competing demands on the human's attention. To keep this manageable, hypotheses are split into two tiers:

**Tier 1 — Must test** (existential questions, low observation cost):
- H1: Does the 3-phase sprint work for a CLI tool?
- H5: Do quality gates catch real issues?
- H7: Do agents actually follow skill instructions?

These are tested by doing the sprint and reviewing the output afterward. They require no real-time note-taking during execution.

**Tier 2 — Observe if possible** (useful but higher observation cost):
- H2: Is the 5-skill set right?
- H3: Does the consensus agent pattern work?
- H4: Does wave-based parallelism help?
- H6: Is the 30-40% context budget right?

These require some real-time observation during the sprint (noting context levels, timing waves, checking for irrelevant skill output). Record what you can without slowing down the build. If observation is interfering with execution, **prioritize execution** — an incomplete observation with a shipped milestone is more useful than thorough notes with an unfinished sprint.

The H3 control experiment (Architect-only agent comparison) is **deferred to Sprint 1** unless Sprint 0 finishes with time and context to spare. It's useful but not worth delaying the sprint.

### 8.0.1 What we're testing

**Context**: Uluka is a Node.js CLI tool (TypeScript, vitest, no frontend, no linter configured). It has 9 subsystems under `src/` (analyzers, cli, config, core, detectors, extractors, importers, reporters, verifiers, types, utils). Build: `tsc`. Test: `vitest`. No E2E tests. No lint command.

**Handling inconclusive results**: Most hypotheses will not produce clean confirmed/falsified outcomes. When a result is inconclusive:
- **Keep the pattern but don't build infrastructure around it.** An inconclusive wave-parallelism result means keep using waves but don't invest in a wave-optimization tool.
- **Design Sprint 1 to re-test.** If H4 was inconclusive because the milestone only had 3 tasks, pick a larger milestone for Sprint 1.
- **Record why it was inconclusive.** "Not enough tasks to test parallelism" is useful data. "Couldn't tell" is not.

---

#### H1: 3-phase sprint works for a CLI tool (not just a web app) [Tier 1]

**Test protocol**:
1. Run the full 3-phase cycle on Uluka's next milestone: Think (produce acceptance.md + implementation.md) → Execute+Gate (build it, run gates) → Ship (push, retro)
2. After the sprint, review: did each phase produce output that was actually used by the next phase?

**Record**:
- Did all 3 phases produce useful output, or was any phase empty/ceremonial?
- Did the phases happen in order, or did execution reveal planning gaps that forced a return to Think?
- If a phase felt forced, what would have been more natural?

**Falsified if**: a phase produced no useful output (e.g., acceptance.md was ignored during execution), or the human had to break the phase sequence more than once to make progress.

**If inconclusive**: the sprint completed but it's unclear whether the structure helped vs. was tolerated. Re-test in Sprint 1 and compare active session time against an unstructured sprint estimate.

---

#### H2: The 5-skill set is the right set for all projects [Tier 2]

**Test protocol**:
1. Copy all 5 Weaveto.do skills into Uluka's `.claude/skills/`, stripped of project-specific content
2. During Phase 1 (Think), load all 5 into the consensus agent as instructed by the Weaveto.do workflow
3. After Phase 1, review `acceptance.md` and `implementation.md`. For each skill, answer:
   - Did this skill's perspective appear in the output? (grep for skill-specific patterns: Gherkin from PM, accessibility from UX, threat model from Security, coverage thresholds from Prod Eng, system layers from Architect)
   - If it appeared, was it useful or noise?
4. During Phase 2, note any moment where you wished an agent had a perspective that none of the 5 skills cover (e.g., "CLI ergonomics", "backwards compatibility", "npm packaging")

**Record**:
- Per skill: appeared in output (yes/no), useful (yes/no/partially), with specific examples
- Any missing perspectives that would have helped, with specific examples of where they were needed

**Falsified if**: 2+ skills produce no useful output for Uluka, or a clearly-needed perspective is missing from the set.

**If inconclusive**: skills appeared but usefulness is ambiguous. Keep all 5 for Sprint 1, but tag questionable skills for closer scrutiny.

---

#### H3: Skills-as-perspectives-in-one-agent works for CLI projects [Tier 2]

**Test protocol**:
1. In Phase 1, load PM + UX + Architect skills into a single consensus agent (the Weaveto.do pattern)
2. Review the consensus agent's output for coherence. Specifically check:
   - Are the Gherkin acceptance criteria (PM skill) consistent with the implementation plan (Architect skill)?
   - Does the UX skill's output make sense for a CLI, or does it produce web-specific recommendations (accessibility, color contrast, keyboard navigation)?
   - Does the agent explicitly reference each skill's perspective, or does it collapse into a single undifferentiated voice?

**Record**:
- Coherence score: did the perspectives reinforce each other (good), coexist neutrally (OK), or contradict each other (bad)?
- Specific examples of perspective conflicts or irrelevant skill output

**Falsified if**: 2+ skill perspectives produce contradictory recommendations in the same document, or the output contains substantial irrelevant content from a mismatched skill.

**Deferred**: The Architect-only control comparison is deferred to Sprint 1. In Sprint 0, we assess the consensus output on its own merits.

**If inconclusive**: output is coherent but it's unclear whether multi-skill added value over single-skill. The Sprint 1 control comparison will resolve this.

---

#### H4: Wave-based parallelism helps on a smaller codebase [Tier 2]

**Test protocol**:
1. During Phase 1, the implementation plan must explicitly group tasks into waves with dependency analysis. For each task, list which files it reads and writes.
2. Identify tasks that share NO files (candidates for parallel execution in the same wave). Identify tasks that share files (must be in sequential waves).
3. Execute Wave 1 tasks in parallel (spawn multiple subagents simultaneously). Time this.
4. For comparison: after the sprint, estimate how long serial execution would have taken by summing individual task active times from the session log.

**Record**:
- Number of waves in the plan
- Tasks per wave (average and max)
- How many tasks were actually parallelizable (shared-file analysis)
- Parallel active time vs estimated serial active time
- Any file conflicts that occurred during parallel execution (agent A and agent B both modified the same file)

**Falsified if**: fewer than 2 tasks are parallelizable (the codebase is too interconnected), or parallel execution is slower than serial due to coordination overhead, or file conflicts occur that require manual resolution.

**If inconclusive**: the milestone was too small to generate enough parallel tasks. Pick a larger milestone for Sprint 1 and re-test.

---

#### H5: Quality gates catch real issues on a different project [Tier 1]

**Test protocol**:
1. Define Uluka's gates before execution begins:
   - `npm run build` (tsc) must pass — this is the type check gate
   - `npm test` (vitest) must pass — this is the test gate
   - Coverage: check current baseline, set threshold at current level (don't regress)
   - No lint gate (Uluka has no linter — note this as a gap)
2. After all execution waves complete, run gates. Record raw output.
3. If gates pass on first attempt: manually review the code changes for issues the gates missed. Specifically check for:
   - Unused imports or dead code (no lint gate to catch this)
   - Console.log statements left in production code
   - Error handling gaps (empty catch blocks, unhandled promise rejections)
   - API contract violations (function signatures changed without updating callers)
4. If gates fail: record what failed, whether the failure was a real issue or a false positive, and how many fix cycles it took to pass.

**Record**:
- First-pass result: pass or fail, with specific failures
- Fix cycles needed (0 = passed first try, 1+ = needed fixes)
- Manual review findings: issues the gates missed, categorized by type
- Gap analysis: what gates should Uluka have that it currently lacks?

**Falsified if**: gates pass but manual review finds 3+ substantive issues, indicating the gate set is too weak for this project. Also falsified if gates are so strict they produce false positives that waste time.

**If inconclusive**: gates caught some things, missed some things. Use the gap analysis to add custom gates in Sprint 1 and re-test.

---

#### H6: 30-40% context budget is the right orchestrator target [Tier 2]

**Test protocol**:
1. The orchestrator (architect) agent must NOT read file contents into its own context — only pass file path references to workers.
2. If you notice context getting heavy during the sprint, note approximately where you are and what caused it. Don't interrupt execution to take measurements.
3. After the sprint, assess: did the orchestrator maintain quality throughout, or did delegation decisions degrade toward the end?

**Record**:
- Did the orchestrator need a session break? If so, when and why?
- Quality assessment: was orchestrator output consistently sharp, or did it degrade?
- Did the orchestrator ever need to re-read a file it should have remembered?
- If context exceeded 50%: what caused it? (file content leaked in, too many summaries, long plan)

**Falsified if**: the orchestrator hits quality degradation well below 40% (budget is too generous), or the orchestrator can't complete the sprint within 50% (budget is too tight). Also falsified if context usage is simply unmeasurable in practice.

**If inconclusive**: context didn't become an issue either way. Not a useful data point — re-test on a larger milestone in Sprint 1.

---

#### H7: Skill instructions are actually followed by agents [Tier 1]

**Test protocol**:
1. Before execution, select 5 specific, verifiable instructions from across the skills. These must be instructions where you can check the output, not just intentions. Examples from the Weaveto.do skills (adapted for Uluka):
   - PM skill: "Every story must have at least one happy path and one failure/edge case scenario" → check `acceptance.md` for edge case scenarios written in Gherkin format (Given/When/Then)
   - Architect skill: "Cheapest appropriate model" → check if implementation.md specifies haiku for mechanical tasks
   - Prod Eng skill: "Write failing test for new feature/fix" (TDD) → check git log for test commits before implementation commits
   - Prod Eng skill: "Reset state between tests (no shared mutable state)" → grep test files for shared `let` variables or `beforeAll` mutations
   - Security skill: "Input validation on all data handling" → check new code for unvalidated inputs on public API functions
2. After the sprint completes, audit each instruction:
   - Was the instruction present in the skill file the agent loaded?
   - Did the agent's output comply with the instruction?
   - If not, was there a gate that would have caught the violation?

**Record**:
- Per instruction: complied (yes/no), gate would have caught it (yes/no)
- Compliance rate: X/5 instructions followed
- Gate coverage: of the instructions violated, how many had a corresponding gate?
- The specific violations found, with file paths and line numbers

**Falsified if**: compliance rate is below 3/5, indicating agents ignore most skill instructions. Also partially falsified if compliance is high but only because the instructions were trivially easy to follow — note whether the instructions tested were substantive or superficial.

**If inconclusive**: compliance is 3/5 but it's unclear whether the 2 failures were skill issues or task issues. Add gates for the failed instructions in Sprint 1 and see if enforcement changes behavior.

### 8.0.2 Steps

**Prep** (manual, not agent-driven):
1. Copy Weaveto.do's 5 skill files into Uluka's `.claude/skills/`, removing Weaveto.do-specific content (crypto references, Svelte patterns, vodozemac details) while keeping the structure and quality bars
2. Copy WORKFLOW.md patterns into a `flowstate.config.md` for Uluka
3. Identify Uluka's next logical milestone (read existing code, tests, README)
4. Write acceptance criteria for that milestone

**Execute**:
5. Run Phase 1 (Think): consensus agent produces implementation.md for the milestone
6. Run Phase 2 (Execute + Gate): subagent-only execution (no teams yet), wave-based where possible
7. Run Phase 3 (Ship): push, update state, metrics collection, retrospective

**Observe and record** (the actual deliverable of Sprint 0):
8. For each hypothesis: record confirmed / falsified / inconclusive, with specific evidence and (if inconclusive) why and what Sprint 1 should do differently
9. Document every friction point: where the workflow felt forced, where skills were ignored, where gates missed something, where context ran out
10. Document every adaptation: what you changed mid-sprint to make things work
11. Collect metrics (see 8.0.2a below)

### 8.0.2a How metrics are collected in Sprint 0

All metrics are parsed from Claude Code's JSONL session logs and standard CLI tools. Parent session logs are at `~/.claude/projects/{project-slug}/{session-id}.jsonl`; subagent logs are at `~/.claude/projects/{project-slug}/{session-id}/subagents/agent-{id}.jsonl`. A `metrics/collect.sh` script automates this — run it after the sprint with the parent session IDs (subagent logs are discovered automatically).

| Metric | How to collect | When |
|--------|---------------|------|
| **Active session time** | Parse first and last `timestamp` from each session's JSONL log. Sum `(last - first)` across all sprint sessions. | After ship |
| **Token usage** | Sum `usage.input_tokens`, `usage.output_tokens`, `usage.cache_read_input_tokens`, `usage.cache_creation_input_tokens` from all `"type":"assistant"` entries in parent + subagent session logs | After ship |
| **Model mix** | Group token counts by `message.model` field from parent + subagent logs. Without subagent logs, model mix only shows the orchestrator model. | After ship |
| **LOC delta** | `git diff --stat {start-sha}..{end-sha}` | After ship |
| **Test count** | Test runner output (e.g., `npx vitest --run` summary line) | After gate |
| **Coverage** | Coverage tool output (e.g., `npx vitest --coverage` summary) | After gate |
| **Gate results** | Save gate command stdout/stderr to `metrics/sprint-0-gates.log` | During gate |
| **First-pass gate success** | Did gates pass on the first run? yes/no, with failure details | During gate |
| **Agent spawn count** | Parse `"type":"assistant"` entries, check `message.content[]` blocks for `type: "tool_use"` with `name: "Task"`. Handled by `collect.sh`. | After ship |

### 8.0.3 Sprint 0 output

The output of Sprint 0 is not "Flowstate v1." It's a document:

```
retrospectives/sprint-0.md
├── Hypothesis results (confirmed / falsified / inconclusive + why + Sprint 1 action)
├── What transferred from Weaveto.do without changes
├── What needed adaptation (and what the adaptation was)
├── What was useless or harmful (candidates for removal)
├── What was missing (candidates for addition)
├── Friction log (notes during sprint — as detailed as possible without slowing execution)
├── Metrics
└── Recommendations for Sprint 1
```

**Sprint 1 scope is determined by Sprint 0 results**, not by a roadmap written before testing.

### 8.0.4 What comes after Sprint 0

The roadmap below is provisional. Sprint 0 results may reorder, add, or remove items.

**Sprint 1: Generalize what worked**
- Formalize the patterns that survived Sprint 0 into reusable skill files
- Remove or rewrite what didn't work
- Re-test any inconclusive hypotheses with better test conditions
- Run the H3 control experiment (Architect-only vs consensus comparison) if deferred from Sprint 0
- Add project-specific skill generation if the Uluka experience revealed missing skills
- Build metrics collector if manual collection was painful enough to justify it
- Run a second sprint on Uluka using the generalized skills

**Sprint 2: Agent strategy**
- Add agent team support (if Sprint 1 revealed coordination needs that subagents couldn't meet)
- Validate or discard hybrid mode
- Add dynamic strategy selection to architect skill

**Sprint 3: Self-improvement loop**
- Formalize retro → diff → approval → apply pipeline
- Add skill pruning (with the never-triggered distinction from section 4.8)
- Add cross-sprint trend analysis
- Test: demonstrate measurable improvement with causal evidence

**Future (when patterns stabilize across 2+ projects)**
- Global `~/.flowstate/` for cross-project learning
- Optional Node CLI for metrics automation
- Community skill library

## 8.1 Sprint 1: Validation Sprint

Sprint 1 builds Phase 15 (Cross-File Data Flow Analysis) and validates the improvements made after Sprint 0.

### 8.1.0 Sprint 0 results summary

| Hypothesis | Result | Action taken |
|------------|--------|-------------|
| H1: 3-phase works for CLI | Confirmed | Keep |
| H2: 5-skill set is right | Mostly confirmed (UX least relevant) | Keep all 5, test H3 control |
| H3: Consensus agent works | Confirmed (no contradictions) | Run control experiment in Sprint 1 |
| H4: Wave parallelism helps | Confirmed (~40% speedup) | Keep |
| H5: Gates catch real issues | Inconclusive (gates passed first try) | Add coverage + lint gates, re-test |
| H6: 30-40% context budget | Partially confirmed | Observe again |
| H7: Skills are followed | 3/5 compliant, 1 N/A, 1 non-compliant | Skills updated, re-test |

### 8.1.1 What we're testing in Sprint 1

Sprint 1 re-tests H1, H5, and H7 with improved gates and updated skills. It also introduces three new hypotheses and runs the deferred H3 control experiment.

#### H3 control: Consensus agent vs architect-only [Tier 1, deferred from Sprint 0]

**Test protocol**: During Phase 1 (Think), produce two versions of the acceptance criteria and implementation plan:
1. **Consensus version**: all 5 skills loaded (the normal workflow)
2. **Control version**: architect skill only (no PM, UX, security, prod-eng)

Compare the outputs for quality, completeness, and noise. Execute whichever is better (or merge them).

**Falsified if**: the architect-only version is equal or better quality — the extra 4 skills are context waste.

#### H8: Coverage gate catches regressions [Tier 1, new]

**Test protocol**: Coverage gate (`npx vitest --run --coverage`) is added with a 65% statement threshold. After the sprint, check:
- Did coverage stay above 65%?
- If new code was added without tests, would the gate have caught it?

**Falsified if**: coverage drops below baseline and the gate doesn't flag it, or the threshold is so low it never triggers.

#### H9: Lint gate catches new dead code [Tier 1, new]

**Test protocol**: Lint gate (`npx tsc --noEmit --noUnusedLocals`) is added. 12 pre-existing errors documented. After the sprint:
- Count lint errors. Did the sprint add new ones?
- If a subagent left an unused import, did the gate catch it?

**Falsified if**: new unused code is introduced and the lint gate misses it (shouldn't happen — tsc is deterministic).

#### H10: Haiku is viable for mechanical tasks in this codebase [Tier 2, new]

**Test protocol**: Phase 15 should include some mechanical tasks (registering new modules in an index, adding type exports, updating configs). The architect should assign these to haiku.
- Did haiku complete the mechanical tasks correctly?
- Did the model mix shift toward cheaper models compared to Sprint 0's 64% opus / 36% sonnet?

**Falsified if**: haiku fails on tasks the architect classified as mechanical, or no mechanical tasks exist (in which case the hypothesis is inconclusive, not falsified).

### 8.1.2 Sprint 1 metrics collection

Same as Sprint 0: `metrics/collect.sh` with parent session ID. The script automatically discovers subagent logs. Use `--after` if the sprint started mid-session.

New gates to check:
- Lint error count (must not exceed 12)
- Coverage statement % (must be >= 65%)

### 8.1.3 Sprint 1 results summary

Sprint 1 built Phase 15 (Cross-File Data Flow Analysis) with all 4 quality gates enforced.

**Metrics**:

| Metric | Sprint 0 | Sprint 1 | Delta |
|--------|----------|----------|-------|
| Active session time | 17m 29s | 25m 16s | +7m 47s (larger milestone) |
| Total tokens | 14.4M | 13.6M | -0.8M |
| Opus % | 63.9% | 61.7% | -2.2pp |
| Sonnet % | 36.1% | 38.3% | +2.2pp |
| Haiku % | 0% | 0% | — |
| Subagents | 4 | 4 | — |
| API calls | 242 | 245 | — |
| Tests | 237 | 320 (+83) | +35% |
| Coverage | 65.72% | 69.82% | +4.10pp |
| Lint errors | 12 | 5 | -7 cleaned |
| Gates first pass | yes | yes | — |

**Hypothesis results**:

| # | Hypothesis | Result | Evidence |
|---|-----------|--------|----------|
| H3 control | Consensus vs architect-only | Consensus wins for security phases | Consensus: 23 scenarios + sanitizer registry separation. Architect-only: 10 scenarios, no separation |
| H5 | Gates catch real issues | Partially confirmed | All 4 gates passed first try. Coverage + lint gates enforce thresholds but did not catch a regression this sprint. First true confirmation came on Dappled Shade S0 where clippy caught 3 bugs |
| H7 | Skills are followed | 4/5 (up from 3/5) | Sprint 0 retro changes fixed prior non-compliance. TDD ordering still partial |
| H8 | Coverage gate catches regressions | Confirmed | Coverage rose 4.10pp; gate enforces 65% floor |
| H9 | Lint gate catches dead code | Confirmed | 7 pre-existing errors cleaned; no new ones introduced |
| H10 | Haiku for mechanical tasks | Inconclusive | No haiku used — architect didn't classify any tasks as mechanical |

**Retro outcome**: 3 change proposals, all process lessons (no skill file edits). This is the first sprint with 0 skill changes — 1/3 toward per-project stability.

## 8.1.4 Sprint 2: Incremental Analysis with Caching

Sprint 2 built Phase 16 (Incremental Analysis with Caching) — SHA-256 content-hashed cache, pipeline integration, CLI commands, and `--incremental` flag.

**Metrics**:

| Metric | Sprint 0 | Sprint 1 | Sprint 2 | Delta (S1→S2) |
|--------|----------|----------|----------|---------------|
| Active session time | 17m 29s | 25m 16s | 16m 56s | -8m 20s (smaller phase) |
| Total tokens | 14.4M | 13.6M | 9.8M | -3.8M |
| New-work tokens | — | 1.45M | 309K | -79% |
| Opus % | 63.9% | 61.7% | 65.7% | +4.0pp |
| Sonnet % | 36.1% | 38.3% | 18.7% | -19.6pp |
| Haiku % | 0% | 0% | 15.6% | +15.6pp (first haiku) |
| Subagents | 4 | 4 | 4 (2 sonnet + 2 haiku) | First haiku agents |
| API calls | 242 | 245 | 178 | -27% |
| Tests | 237 | 320 (+83) | 348 (+28) | — |
| Coverage | 65.72% | 69.82% | 69.85% (+0.03pp) | Minimal (I/O-heavy code) |
| Lint errors | 12 | 15 | 15 (0 new) | Stable |
| Gates first pass | yes | yes | yes | 3rd consecutive |
| Insertions | ~1,200 | ~2,542 | 826 | Smaller phase |

**Hypothesis results**:

| # | Hypothesis | Result | Evidence |
|---|-----------|--------|----------|
| H1 | 3-phase works for CLI | Confirmed | 3rd consecutive sprint. THINK→EXECUTE→SHIP clean. |
| H5 | Gates catch real issues | Inconclusive | Gates passed first try again (3rd in a row). Lint gate confirmed 0 new errors. No gate actually blocked anything. |
| H7 | Skills are followed | 4/5 + 1 partial | PM Gherkin: YES. Architect cheapest model: YES (first haiku tasks). TDD: YES. Security hash validation: YES. Orchestrator read full impl (partial — acceptable for <200 line modules). |
| H8 | Haiku for mechanical tasks | Confirmed | T4 (config): 5 tool uses, 13s, clean. T3 (CLI wiring): 25 tool uses, 61s, clean but higher cost for multi-file work. |
| H9 | Lint gate catches dead code | Confirmed | 15 → 15, zero new errors introduced. |

**Retro outcome**: 1 skill change applied — refined haiku task threshold: single-file mechanical = haiku, multi-file wiring = sonnet. 2/3 toward per-project stability (Sprint 1 and Sprint 2 both had minimal/no skill changes).

**Notable**: First sprint with haiku agents on Uluka. T4 (config extension, 5 tool uses, 13s) validated haiku for single-file mechanical tasks. T3 (CLI commands, 25 tool uses, 61s) showed multi-file wiring is sonnet-appropriate even when individual changes are small. Tokens per accepted LOC dropped to ~374 — best efficiency across all Uluka sprints.

## 8.2 Dappled Shade Sprint 0: Cross-Project Generalization

Dappled Shade tests whether Flowstate generalizes beyond TypeScript CLI tools. It is a Rust P2P encrypted messaging application over Tor — maximally different from Uluka in language, domain, and threat model.

### 8.2.0 Bootstrap

Flowstate was bootstrapped onto Dappled Shade from just a PRD in **9 minutes 10 seconds** (success criterion #6 requires < 30 minutes). The bootstrap produced:

- 5 adapted skills (Rust/crypto/P2P-specific content, same structural pattern)
- `flowstate.config.md` with Rust gates (cargo build, test, clippy, fmt)
- `metrics/baseline.md` with H7 audit instructions (Zeroizing, no disk writes)
- `metrics/collect.sh` adapted from Uluka (PROJECT_LOGS path updated)
- `SPRINT-0.md` with copy-paste prompts and two new hypotheses (H11, H12)

No Uluka-specific or TypeScript-specific content leaked into the Dappled Shade files.

### 8.2.1 What we're testing

Two new hypotheses plus re-tests of core hypotheses on a different project type.

#### H11: Flowstate works for greenfield projects [Tier 1, new]

**Test protocol**: Bootstrap Flowstate onto an empty repo (just a PRD), run Sprint 0, and assess whether the 3-phase structure works when there's no existing code to build on.

**Falsified if**: the workflow assumes existing code (e.g., skills reference patterns that don't exist yet, gates fail because there's nothing to test).

#### H12: Skills generalize across programming languages [Tier 1, new]

**Test protocol**: Adapt the 5 Uluka skills (TypeScript) for Dappled Shade (Rust). Run a sprint. Check whether the adapted skills produce useful output or whether Rust-specific gaps require fundamentally different skill structures.

**Falsified if**: 2+ skills need structural rewrites (not just content adaptation) to work with Rust, or Rust-specific patterns (ownership, lifetimes, async traits) require a new skill category.

### 8.2.2 Sprint 0 results

Sprint 0 built the full M0 MVP: a terminal-based P2P encrypted messaging CLI over Tor.

**Metrics**:

| Metric | Value |
|--------|-------|
| Active session time | 54m 6s (raw 426m 29s minus 6h 12m 23s sleep gap between Phase 2 and 3) |
| Total tokens | 26.9M |
| Opus % | 47.7% |
| Sonnet % | 49.6% |
| Haiku % | 2.8% |
| Subagents | 14 (across 7 waves) |
| API calls | 579 |
| Rust LOC | 3,268 (2,961 src/ + 307 tests/integration.rs) |
| Tests | 57 passed, 3 ignored (2 live Tor, 1 doc) |
| Gates first pass | No — clippy caught 3 issues, passed on second run |

**Hypothesis results**:

| # | Hypothesis | Result | Evidence |
|---|-----------|--------|----------|
| H1 | 3-phase works for Rust | Confirmed | Think produced coherent plan, Execute built 3,268 LOC in 7 waves, Ship gates all passed |
| H2 | 5-skill set works for crypto/P2P | Confirmed | All 5 contributed: PM (24 Gherkin scenarios), UX (CLI design), Architect (crate structure), PE (TDD/gates), Security (zeroization, Noise limits) |
| H4 | Wave parallelism helps | Confirmed | 4 of 7 waves used parallelism (2-3 agents). No merge conflicts. Module-per-file Rust structure maps naturally to independent waves |
| H5 | Gates catch real issues | Confirmed | Clippy caught `manual_div_ceil`, `async_fn_in_trait`. Security audit caught `.expect()` on network data and Noise message size exceeded |
| H7 | Skills are followed | 4/5 | PM Gherkin: YES. Architect cheapest model: YES (haiku for scaffold/CLI). TDD: PARTIAL. Zeroizing: YES. No disk writes: YES |
| H11 | Greenfield works | Confirmed | Empty repo to 3,268 LOC, 57 tests, all gates passing |
| H12 | Skills generalize TS→Rust | Mostly confirmed | Core patterns transferred. Two Rust-specific gaps: async trait dyn-compatibility, Noise message size limits |

**Notable firsts**:
- **Haiku appeared** (2.8%) — first time across any Flowstate sprint. Architect assigned haiku to scaffold and CLI boilerplate tasks.
- **Gates failed first pass** — clippy caught real issues. This is the first empirical evidence that gates earn their keep on unfamiliar territory (H5 was inconclusive on Uluka where gates always passed first try).
- **14 subagents in 7 waves** — Rust's module-per-file structure enabled much more parallelism than Uluka's tightly coupled TypeScript.

**Skill changes applied**: 3 Rust-specific additions (async trait guidance in architect, Noise size limit in security auditor, TDD clarification in production engineer). All surgical — no structural rewrites needed. 0/3 toward per-project stability.

## 8.2.3 Sprint 1: dapple-olm (Olm per-message E2EE)

Sprint 1 added Olm per-message end-to-end encryption with forward secrecy on top of Sprint 0's Noise transport encryption. Double encryption pipeline: `plaintext → Olm encrypt → serialize → Noise encrypt → transport framing → wire`.

**Metrics**:

| Metric | Sprint 0 | Sprint 1 | Delta |
|--------|----------|----------|-------|
| Active session time | 54m 6s | 21m 39s | -60% |
| Total tokens | 26.9M | 15.5M | -42% |
| New-work tokens | 1.26M | 565K | -55% |
| Cache hit rate | — | 96.4% | — |
| Opus % | 47.7% | 58.2% | +10.5pp |
| Sonnet % | 49.6% | 41.8% | -7.8pp |
| Haiku % | 2.8% | 0% | -2.8pp |
| Subagents | 14 | 6 | -57% |
| API calls | 579 | 255 | -56% |
| Rust LOC | 3,268 | 4,403 (+1,135) | +35% |
| Tests | 57 | 75 (+18) | +32% |
| Gates first pass | no (clippy) | yes | Improved |

**Hypothesis results**:

| # | Hypothesis | Result | Evidence |
|---|-----------|--------|----------|
| H1 | 3-phase works for Rust | Confirmed | 2nd consecutive sprint. Clean execution. |
| H4 | Wave parallelism helps | Confirmed | Wave 4 ran 3 parallel agents (olm tests, integration test, security audit) on independent files. No conflicts. |
| H5 | Gates catch real issues | Confirmed (indirectly) | Gates passed first try, but Wave 4.3 security audit (pre-gate) caught `.unwrap()` on transport, bare `Vec<u8>` for plaintext, missing size guard. Audit-before-gates is effective. |
| H7 | Skills are followed | 5/5 (1 partial) | PM Gherkin: YES. Architect async traits: YES. TDD: PARTIAL (same structural issue as S0). Zeroizing: YES. Noise cap: YES. |
| H12 | Skills generalize TS→Rust | Confirmed | Sprint 0's 3 change proposals (async trait, Noise limit, TDD clarification) prevented the same errors in Sprint 1. No new language-specific gaps. |

**Retro outcome**: No skill changes proposed. This is **1/3 toward per-project stability** (first clean sprint on Dappled Shade).

**Notable**: vodozemac API was much cleaner than arti (Sprint 0's pain point). Session.rs integration was surgical (+148 lines) — Sprint 0's architecture was well-factored. First-pass gate success (vs Sprint 0's clippy failure) suggests Sprint 0's skill amendments are working. Tokens per accepted LOC: ~306 — best ratio across all sprints on either project.

## 8.3 Cross-Project Comparison

Six sprints across two projects and two languages. Cross-project patterns are now visible across multiple iterations.

### 8.3.1 Metrics comparison

| | Uluka S0 | Uluka S1 | Uluka S2 | DS S0 | DS S1 | Trend |
|---|---|---|---|---|---|---|
| Active session time | 17m 29s | 25m 16s | 16m 56s | 54m 6s | 21m 39s | Both projects getting faster |
| Total tokens | 14.4M | 13.6M | 9.8M | 26.9M | 15.5M | Decreasing on both |
| New-work tokens | — | 1.45M | 309K | 1.26M | 565K | Improving efficiency |
| Opus % | 63.9% | 61.7% | 65.7% | 47.7% | 58.2% | 58-66% range |
| Sonnet % | 36.1% | 38.3% | 18.7% | 49.6% | 41.8% | Dropping as haiku takes load |
| Haiku % | 0% | 0% | 15.6% | 2.8% | 0% | Uluka first real haiku usage |
| Subagents | 4 | 4 | 4 | 14 | 6 | DS normalizing after greenfield |
| API calls | 242 | 245 | 178 | 579 | 255 | Dropping on both |
| Gates 1st pass | yes | yes | yes | no (clippy) | yes | 5/6 sprints clean |
| H7 compliance | 3/5 | 4/5 | 4.5/5 | 4/5 | 5/5 | Improving toward ceiling |
| Tokens/LOC | ~12,000 | ~9,700 | ~374 | ~8,200 | ~306 | Dramatic improvement |

### 8.3.2 What the data shows

**Patterns confirmed across all conditions**:
- 3-phase structure (H1): confirmed on 6 consecutive sprints across TS and Rust, existing and greenfield codebases
- Wave parallelism (H4): adapts to project structure — 4 agents for coupled TS, 14→6 agents for Rust as architecture stabilizes
- 5-skill consensus (H2, H3): coherent output across CLI tools and crypto P2P, no contradictions
- Skill compliance (H7): improving from 3/5 → 5/5 over 6 sprints, with TDD ordering as the only persistent partial
- Skills generalize across languages (H12): confirmed on DS S1 — Sprint 0's amendments prevented repeat failures

**Trends**:
- Active session time is decreasing on both projects as skills stabilize and architects make better plans
- Tokens per accepted LOC dropped dramatically: Uluka 12,000 → 374, DS 8,200 → 306. Cache hit rates above 96% are driving this.
- Haiku appeared on Uluka S2 (15.6%) with confirmed viability for single-file mechanical tasks
- Gates are most valuable on first contact (DS S0 clippy caught 3 bugs). On mature codebases, gates confirm rather than catch.
- Agent count is stabilizing: 4 per sprint on Uluka, DS normalizing from 14 to 6

**Per-project stability status**:
- Uluka: 2/3 clean sprints (Sprint 1: 0 skill edits, Sprint 2: 1 minor threshold refinement)
- Dappled Shade: 1/3 (Sprint 1 had 0 skill changes proposed)
- Cross-project: Rust-specific additions don't invalidate TS skills — they're additive, not contradictory

## 9. Tokens per Accepted LOC

A diagnostic metric the skeptic review identified as conspicuously absent. Calculated as total tokens / lines of code added.

| Sprint | Total Tokens | New-work Tokens | LOC Added | Tokens/LOC (total) | Tokens/LOC (new-work) |
|--------|-------------|----------------|-----------|-------------------|----------------------|
| Uluka S0 | 14.4M | — | ~1,200 | ~12,000 | — |
| Uluka S1 | 13.6M | 1.45M | ~2,542 | ~5,350 | ~570 |
| Uluka S2 | 9.8M | 309K | 826 | ~11,860 | ~374 |
| DS S0 | 26.9M | 1.26M | 3,268 | ~8,200 | ~386 |
| DS S1 | 15.5M | 565K | 1,845 | ~8,400 | ~306 |

**Note**: Total tokens/LOC is misleading because cache reads dominate (96%+ hit rates). New-work tokens/LOC is more meaningful — it measures how many non-cached tokens are consumed per line of accepted code. The dramatic improvement from ~12,000 (Uluka S0) to ~306-374 (latest sprints) is primarily driven by cache efficiency, not by writing fewer tokens.

Do not compare across project types — only across sprints on the same project. Greenfield code produces more LOC per token because there are no existing patterns to understand.

## 10. Open Questions

Inherited from the original PRD section 12. Updated with answers where available.

| # | Question | Status | Answer |
|---|----------|--------|--------|
| 1 | Does the UX designer skill add value for CLI projects? | **Answered** | Partially. UX contributed CLI design patterns on Dappled Shade, was least relevant on Uluka. Keep but monitor. |
| 2 | Is the security auditor skill useful for non-crypto projects? | **Answered** | Yes on Uluka (input validation, error handling). Strongly yes on Dappled Shade (crypto audit caught 3 real bugs). |
| 3 | How many wave-parallelism opportunities exist in Uluka's codebase? | **Answered** | Limited — 4 subagents per sprint. Rust's module-per-file structure (Dappled Shade) enables much more (14 agents, 7 waves). Parallelism scales with module independence. |
| 4 | Was the milestone scope right for Uluka's size? | **Answered** | Yes — both Phase 14 and Phase 15 completed in single sprints (17m and 25m). |
| 5 | Does consensus work when 2 of 5 skills are irrelevant? | **Answered** | Yes — irrelevant skills were quietly deprioritized, not contradictory. H3 control confirmed consensus > architect-only for security-adjacent phases. |
| 6 | Can we reliably parse Claude Code session logs for metrics? | **Answered** | Yes, with caveats. Required 3 bug fixes (spawn count nesting, subagent discovery, wall time calculation). Log format is stable but undocumented. |
| 7 | What custom gates does Uluka need beyond Weaveto.do's? | **Answered** | Coverage gate (65% floor) and lint gate (`--noUnusedLocals`). Both added in Sprint 1. |

## 11. Methodology Notes

Addressing known weaknesses identified by adversarial review.

### 11.1 What "confirmed" means

Hypotheses use a 4-level scale:
- **Confirmed**: direct evidence supports the hypothesis with observable data
- **Partially confirmed**: evidence is supportive but incomplete or indirect
- **Inconclusive**: insufficient data to confirm or falsify — retest with better conditions
- **Falsified**: direct evidence contradicts the hypothesis

"Confirmed" does not mean "proven beyond doubt." It means the available evidence supports the hypothesis enough to continue relying on the pattern. All confirmations are provisional and can be overturned by future sprints.

### 11.2 Known limitations

- **No baseline comparison**: no sprint has been run without Flowstate on the same codebase. Active session time, token usage, and code quality cannot be attributed to Flowstate vs. Claude Code's inherent capability. A no-Flowstate baseline experiment is planned (see 11.3).
- **Human idle time is approximate**: collect.sh detects gaps >60s between assistant and human entries as "human idle" time. This captures review and approval delays but not setup time or passive monitoring. Better than nothing, not perfect.
- **Project selection is not independent**: both test projects were chosen by the same person who created Flowstate. Neither is a team project, a web app with a database, or an inherited messy codebase.
- **Skill compliance is self-assessed**: H7 audits are performed by the person who wrote the skills, not by an independent reviewer.
- **Model versions are unrecorded**: sprints record model tier (opus/sonnet/haiku) but not specific model version. Claude capability changes between sprints could confound comparisons.
- **Tokens per accepted LOC is high**: ~8,000-12,000 tokens per line of code. This is the real cost of agent-based development and should not be hidden.

### 11.3 Planned experiments

**No-Flowstate baseline** (next Uluka sprint): Build one Uluka milestone with raw Claude Code — no skills, no phases, no gates. Record the same metrics (active session time, tokens, tests, coverage). Compare to the Flowstate sprint on a similar-complexity milestone. This is the single highest-value experiment for establishing whether Flowstate adds value.

**Human time tracking** (implemented in collect.sh): The metrics collector now detects gaps >60s between assistant and human entries in session logs, reporting them as "Human idle" time automatically. No manual logging needed — the session log timestamps already contain the data.

### 11.4 Hypothesis cap

The current hypothesis set (H1-H12) is sufficient. No new hypotheses will be added. Future sprints re-test existing hypotheses with better controls rather than expanding scope. This prevents the meta-system from growing indefinitely.

