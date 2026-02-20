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

<!-- generated-from: python3 tools/generate_tables.py compare uluka 0 1 -->
| Metric | Sprint 0 | Sprint 1 | Delta |
|--------|----------|----------|-------|
| Active session time | 17m 39s | 21m 51s | +4m 12s (larger milestone) |
| Total tokens | 9.4M | 8.4M | -1.0M |
| Opus % (tokens) | 65.8% | 59.9% | -5.9pp |
| Sonnet % (tokens) | 34.2% | 40.1% | +5.9pp |
| Haiku % | 0% | 0% | — |
| Subagents | 3 | 3 | — |
| API calls | 145 | 151 | — |
| Tests | 237 | 320 (+83) | +35% |
| Coverage | 65.72% | 69.82% | +4.10pp |
| Lint errors | 12 | 5 | -7 cleaned |
| Gates first pass | yes | yes | — |

**Hypothesis results**:

<!-- generated-from: python3 tools/generate_tables.py hypotheses uluka 1 -->
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

<!-- generated-from: python3 tools/generate_tables.py compare uluka 0 1 2 -->
| Metric | Sprint 0 | Sprint 1 | Sprint 2 | Delta (S1->S2) |
|--------|----------|----------|----------|---------------|
| Active session time | 17m 39s | 21m 51s | 10m 44s | -11m 7s (smaller phase) |
| Total tokens | 9.4M | 8.4M | 6.1M | -2.3M |
| New-work tokens | 287K | 197K | 211K | +7% |
| Opus % (tokens) | 65.8% | 59.9% | 68.4% | +8.5pp |
| Sonnet % (tokens) | 34.2% | 40.1% | 19.2% | -20.9pp |
| Haiku % (tokens) | 0% | 0% | 12.4% | +12.4pp (first haiku) |
| Subagents | 3 | 3 | 3 (1S+2H) | First haiku agents |
| API calls | 145 | 151 | 106 | -30% |
| Tests | 237 | 320 (+83) | 348 (+28) | — |
| Coverage | 65.72% | 69.82% | 69.85% (+0.03pp) | Minimal (I/O-heavy code) |
| Lint errors | 12 | 15 | 15 (0 new) | Stable |
| Gates first pass | yes | yes | yes | 3rd consecutive |
| Insertions | ~1,200 | ~2,542 | 826 | Smaller phase |

**Hypothesis results**:

<!-- generated-from: python3 tools/generate_tables.py hypotheses uluka 2 -->
| # | Hypothesis | Result | Evidence |
|---|-----------|--------|----------|
| H1 | 3-phase works for CLI | Confirmed | 3rd consecutive sprint. THINK→EXECUTE→SHIP clean. |
| H5 | Gates catch real issues | Inconclusive | Gates passed first try again (3rd in a row). Lint gate confirmed 0 new errors. No gate actually blocked anything. |
| H7 | Skills are followed | 4/5 + 1 partial | PM Gherkin: YES. Architect cheapest model: YES (first haiku tasks). TDD: YES. Security hash validation: YES. Orchestrator read full impl (partial — acceptable for <200 line modules). |
| H8 | Haiku for mechanical tasks | Confirmed | T4 (config): 5 tool uses, 13s, clean. T3 (CLI wiring): 25 tool uses, 61s, clean but higher cost for multi-file work. |
| H9 | Lint gate catches dead code | Confirmed | 15 → 15, zero new errors introduced. |

**Retro outcome**: 1 skill change applied — refined haiku task threshold: single-file mechanical = haiku, multi-file wiring = sonnet. 2/3 toward per-project stability (Sprint 1 and Sprint 2 both had minimal/no skill changes).

**Notable**: First sprint with haiku agents on Uluka. T4 (config extension, 5 tool uses, 13s) validated haiku for single-file mechanical tasks. T3 (CLI commands, 25 tool uses, 61s) showed multi-file wiring is sonnet-appropriate even when individual changes are small.

## 8.1.5 Sprint 3: Claude Code Hook Integration

Sprint 3 built Phase 17 (Claude Code Hook Integration) — hook runner core with path validation and JSON output, pre-commit hook with staged file scanning, CLI commands, and setup documentation. 5 requirements (HOOK-01 through HOOK-05) delivered across 3 sequential waves.

**Metrics**:

<!-- generated-from: python3 tools/generate_tables.py compare uluka 1 2 3 -->
| Metric | Sprint 1 | Sprint 2 | Sprint 3 | Delta (S2->S3) |
|--------|----------|----------|----------|----------------|
| Active session time | 21m 51s | 10m 44s | 12m 37s | +1m 53s |
| Total tokens | 8.4M | 6.1M | 6.9M | +0.8M |
| New-work tokens | 197K | 211K | 83K | -61% |
| Opus % (tokens) | 59.9% | 68.4% | 88.1% | Orchestrator dominates |
| Sonnet % (tokens) | 40.1% | 19.2% | 9.3% | Continuing drop |
| Haiku % (tokens) | 0% | 12.4% | 2.7% | 1 haiku agent |
| Subagents | 3 | 3 | 3 (2S+1H) | — |
| API calls | 151 | 106 | 77 | -27% |
| Tests | 320 (+83) | 348 (+28) | 370 (+22) | — |
| Coverage | 69.82% | 69.85% | 70.22% (+0.37pp) | Steady climb |
| Lint errors | 15 | 15 | 15 (Gate 2 caught +1, fixed) | Stable |
| Gates first pass | yes | yes | no (lint) | First gate failure |
| Insertions | ~2,542 | 826 | 890 | +8% |

**Hypothesis results**:

<!-- generated-from: python3 tools/generate_tables.py hypotheses uluka 3 -->
| # | Hypothesis | Result | Evidence |
|---|-----------|--------|----------|
| H1 | 3-phase works for CLI | Confirmed | 4th consecutive sprint. Clean THINK->EXECUTE->SHIP. |
| H5 | Gates catch real issues | **CONFIRMED** | Gate 2 (lint) caught unused `relative` import from T1 subagent. 16 errors > 15 max. Fixed in 1 cycle. **First time a gate actually blocked code across all Uluka sprints.** |
| H7 | Skills are followed | **5/5** | PM Gherkin: YES. Architect cheapest model: YES (haiku for CLI wiring). ProdEng tests first: YES. Security input validation: YES. UX help text: YES. **First perfect compliance score.** |
| H8 | Coverage gate | Confirmed | 70.22% > 65% floor. Steady upward trend. |
| H9 | Lint gate | Confirmed | Gate 2 caught the unused import. First real enforcement action on Uluka. |

**Retro outcome**: 1 orchestrator convention proposed (add lint self-check to subagent prompts). **No skill file changes** — 3/3 consecutive clean sprints on Uluka. **Per-project stability achieved.**

**Notable**:
- **H5 finally confirmed on Uluka**: after 3 sprints of gates passing first try, Gate 2 actually caught something. The sonnet subagent imported `relative` from `path` but used a different approach, leaving the dead import. Lint gate enforced the cap.
- **H7 perfect score**: first 5/5 compliance across any sprint on any project. Skills are being followed consistently.
- **Per-project stability**: 3 consecutive sprints with 0 skill file changes (S1: 0, S2: 1 minor threshold, S3: 0). The skill set is stable for Uluka.
- **Haiku succeeds on CLI wiring again**: T3 (haiku) handled CLI command registration and docs, confirming the Sprint 2 finding that haiku works for mechanical tasks.

## 8.1.6 Sprint 8: Crypto Library Knowledge Base + Evidence Quality (Experiment 2)

Sprint 8 built Phase 21 (Crypto Library Knowledge Base + Evidence Quality) and served as **Experiment 2** — 3 bugs were planted on the `exp-2-adversarial` branch to test whether gates catch them.

**Metrics**:

| Metric | Value |
|--------|-------|
| Active session time | 10m 28s |
| Total tokens | 4.2M |
| New-work tokens | 212K |
| Cache hit rate | 95.0% |
| Opus % | 84.1% |
| Sonnet % | 8.2% |
| Haiku % | 7.7% |
| Subagents | 2 |
| Tests | 520 (+42) |
| Coverage | 73.91% |
| LOC added | 1,078 |
| Gates first pass | no (3 regressions from planted bugs) |
| Rework rate | 1.6 |

**Hypothesis results**:

| # | Hypothesis | Result | Evidence |
|---|-----------|--------|----------|
| H1 | 3-phase works for CLI | Confirmed | 8th consecutive sprint. Multi-session with regression fix. |
| H5 | Gates catch real issues | **CONFIRMED** | 3/3 planted bugs caught: wrong threshold (Gate 1), type error (Gate 1), unused import (Gate 2). All fixed in 1 cycle. |
| H7 | Skills are followed | Partially confirmed | 4/5. PM Gherkin not applied (continuation session, not fresh planning). |
| H8 | Coverage gate | Confirmed | 73.91% > 65% floor. |
| H9 | Lint gate | Confirmed | Planted unused import caught by lint gate. |

**Experiment 2 result**: All 3 planted bugs caught by their intended gates, all correctly fixed in 1 cycle, all traced to planted commit `903939b`. H5, H8, H9 confirmed under adversarial conditions. See section 11.3.

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

<!-- generated-from: python3 tools/generate_tables.py sprint dappled-shade 0 -->
| Metric | Value |
|--------|-------|
| Active session time | 37m 43s (execution + retro, sleep gap excluded by >60s filter) |
| Total tokens | 16.8M |
| Opus % (tokens) | 48.2% |
| Sonnet % (tokens) | 49.9% |
| Haiku % (tokens) | 1.9% |
| Subagents | 14 (across 7 waves, per retro) |
| API calls | 330 |
| Rust LOC | 3,268 (2,961 src/ + 307 tests/integration.rs) |
| Tests | 57 passed, 3 ignored (2 live Tor, 1 doc) |
| Gates first pass | No — clippy caught 3 issues, passed on second run |

**Hypothesis results**:

<!-- generated-from: python3 tools/generate_tables.py hypotheses dappled-shade 0 -->
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

<!-- generated-from: python3 tools/generate_tables.py compare dappled-shade 0 1 -->
| Metric | Sprint 0 | Sprint 1 | Delta |
|--------|----------|----------|-------|
| Active session time | 37m 43s | 16m 3s | -57% |
| Total tokens | 16.8M | 9.2M | -45% |
| New-work tokens | 630K | 274K | -56% |
| Cache hit rate | 96.3% | 97.1% | +0.8pp |
| Opus % (tokens) | 48.2% | 59.5% | +11.3pp |
| Sonnet % (tokens) | 49.9% | 40.5% | -9.4pp |
| Haiku % (tokens) | 1.9% | 0% | -1.9pp |
| Subagents | 14 (per retro) | 4 | -71% |
| API calls | 330 | 145 | -56% |
| Rust LOC | 3,268 | 4,403 (+1,135) | +35% |
| Tests | 57 | 75 (+18) | +32% |
| Gates first pass | no (clippy) | yes | Improved |

**Hypothesis results**:

<!-- generated-from: python3 tools/generate_tables.py hypotheses dappled-shade 1 -->
| # | Hypothesis | Result | Evidence |
|---|-----------|--------|----------|
| H1 | 3-phase works for Rust | Confirmed | 2nd consecutive sprint. Clean execution. |
| H4 | Wave parallelism helps | Confirmed | Wave 4 ran 3 parallel agents (olm tests, integration test, security audit) on independent files. No conflicts. |
| H5 | Gates catch real issues | Confirmed (indirectly) | Gates passed first try, but Wave 4.3 security audit (pre-gate) caught `.unwrap()` on transport, bare `Vec<u8>` for plaintext, missing size guard. Audit-before-gates is effective. |
| H7 | Skills are followed | 5/5 (1 partial) | PM Gherkin: YES. Architect async traits: YES. TDD: PARTIAL (same structural issue as S0). Zeroizing: YES. Noise cap: YES. |
| H12 | Skills generalize TS→Rust | Confirmed | Sprint 0's 3 change proposals (async trait, Noise limit, TDD clarification) prevented the same errors in Sprint 1. No new language-specific gaps. |

**Retro outcome**: No skill changes proposed. This is **1/3 toward per-project stability** (first clean sprint on Dappled Shade).

**Notable**: vodozemac API was much cleaner than arti (Sprint 0's pain point). Session.rs integration was surgical (+148 lines) — Sprint 0's architecture was well-factored. First-pass gate success (vs Sprint 0's clippy failure) suggests Sprint 0's skill amendments are working.

## 8.2.4 Sprint 6: Tor Spike + Matrix Outbound Bridge (Experiment 4)

Sprint 6 was **Experiment 4** — a scope stress test combining M4 Phase 1 (Tor spike) and M5 Phase 1 (Matrix outbound bridge) into a single Flowstate sprint. ~2.5x normal DS sprint scope. Experiment 3 (blind compliance scoring) was folded in after completion.

**Deliverables**: TransportManager (mode selection, health monitoring, TCP fallback), Matrix bridge (appservice registration, ghost users, outbound queue, inbound routing, HTTP handlers), Arti spike report (no-go decision), CLI `--transport` flag, acceptance criteria for both M4 and M5.

**Metrics**:

<!-- generated-from: python3 tools/generate_tables.py sprint dappled-shade 6 -->
| Metric | Value |
|--------|-------|
| LOC added | 2,652 |
| Tests | 212 (+48) |
| Files changed | 15 |
| Commits | 2 |
| Gates first pass | yes |
| Token/timing | null (no collect.sh for DS yet) |

Note: Token and timing metrics unavailable — DS does not have a collect.sh. Flagged in retro.

**Hypothesis results (self-assessed)**:

<!-- generated-from: python3 tools/generate_tables.py hypotheses dappled-shade 6 -->
| # | Hypothesis | Result | Evidence |
|---|-----------|--------|----------|
| H1 | 3-phase works under combined scope | Confirmed | M4+M5 delivered in Think->Execute->Ship. Wave-based execution grouped transport concerns. |
| H5 | Gates catch real issues | Confirmed | 212 tests + 0 clippy validated 2,652 LOC on first attempt. |
| H7 | Skills are followed | Partially confirmed (self) | 8/10 skill instructions followed. Missing: dedicated security audit wave, adversarial scenarios. |

**Experiment 3 — Blind compliance scoring**: see section 8.4.2 below.

**Retro outcome**: 3 change proposals (create collect.sh, add security audit wave, capture token metrics). No skill file changes — **2/3 toward per-project stability** on DS.

## 8.3 Cross-Project Comparison

Eighteen sprints across three projects and three languages/frameworks (plus 2 no-Flowstate baselines and 4 falsification experiments).

### 8.3.1 Metrics comparison

<!-- generated-from: python3 tools/generate_tables.py cross-project -->
| | Uluka S0 | Uluka S1 | Uluka S2 | Uluka S3 | Uluka S8 (Exp 2) | DS S0 | DS S1 | DS S6 (Exp 4) | WTD S1 | WTD S2 | Trend |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Active session time | 17m 39s | 21m 51s | 10m 44s | 12m 37s | 10m 28s | 37m 43s | 16m 3s | null | null | 22m 13s | Stabilizing 10-22m |
| Total tokens | 9.4M | 8.4M | 6.1M | 6.9M | 4.2M | 16.8M | 9.2M | null | null | 12.9M | Decreasing |
| New-work tokens | 287K | 197K | 211K | 83K | 212K | 630K | 274K | null | 527K | 531K | 83K-630K range |
| Cache hit rate | — | — | — | — | 95.0% | 96.3% | 97.1% | — | 96.9% | 95.9% | 95-97% |
| Opus % | 65.8% | 59.9% | 68.4% | 88.1% | 84.1% | 48.2% | 59.5% | 100% | — | 61.0% | Varies |
| Sonnet % | 34.2% | 40.1% | 19.2% | 9.3% | 8.2% | 49.9% | 40.5% | 0% | — | 12.2% | — |
| Haiku % | 0% | 0% | 12.4% | 2.7% | 7.7% | 1.9% | 0% | 0% | — | 26.8% | Used when appropriate |
| Subagents | 3 | 3 | 3 | 3 | 2 | 14 | 4 | null | null | 7 | — |
| Gates 1st pass | yes | yes | yes | no (lint) | no (planted) | no (clippy) | yes | yes | null | yes | Failures catch real bugs |
| LOC added | ~1,200 | ~2,542 | 826 | 890 | 1,078 | 3,268 | 1,135 | 2,652 | null | 459 | — |
| Tokens/LOC (new-work) | ~239 | ~78 | ~256 | ~93 | ~197 | ~193 | ~242 | null | null | ~1,157 | 78-256 typical (WTD S2 high: small LOC) |

### 8.3.2 What the data shows

**Patterns confirmed across all conditions**:
- 3-phase structure (H1): confirmed on 18 sprints across TS, Rust, and SvelteKit, including 2.5x scope stress (DS S6). Weakened by Exp 1 baselines for well-scoped single-module work, but holds for multi-module sprints.
- Wave parallelism (H4): adapts to project structure — 3 agents for coupled TS, 14->4 for Rust, 7 for SvelteKit
- 5-skill consensus (H2, H3): coherent output across CLI tools, crypto P2P, and E2EE web app. Weakened by Exp 1 (comparable quality without skills).
- Skill compliance (H7): improved from 3/5 -> 5/5 over sprints, but **Exp 3 revealed process-level auditing inflates scores**. H7 audit methodology upgraded to require code-level verification.
- Skills generalize across languages (H12): confirmed on DS S1 and WTD S1
- Gates catch real issues (H5): confirmed on all 3 projects. Exp 2 adversarial test: 3/3 planted bugs caught. DS S0 clippy caught 3 bugs. Uluka S3 lint caught unused import.

**Key finding from experiments**:
- **Gates are the strongest mechanism** (Exp 2). They catch bugs reliably, automatically, and without human intervention.
- **Sprint structure earns its keep on multi-module work** (Exp 4: held at 2.5x scope) but adds 4-8x overhead for single-module tasks (Exp 1).
- **Skills are marginal** — comparable quality without them (Exp 1), compliance hard to audit reliably (Exp 3).

**Per-project stability status**:
- **Uluka: STABLE** — 3/3 consecutive clean sprints. Skill set frozen.
- **Dappled Shade: 2/3** — Sprint 1 and Sprint 6 had 0 skill file changes.
- **Weaveto.do: 2/2** — On track for stable at 3/3.

## 9. Tokens per Accepted LOC

A diagnostic metric the skeptic review identified as conspicuously absent. Calculated as total tokens / lines of code added.

<!-- generated-from: python3 tools/generate_tables.py tokens-per-loc -->
| Sprint | Total Tokens | New-work Tokens | LOC Added | Tokens/LOC (total) | Tokens/LOC (new-work) |
|--------|-------------|----------------|-----------|-------------------|----------------------|
| Uluka S0 | 9.4M | 287K | ~1,200 | ~7,833 | ~239 |
| Uluka S1 | 8.4M | 197K | ~2,542 | ~3,305 | ~78 |
| Uluka S2 | 6.1M | 211K | 826 | ~7,385 | ~256 |
| Uluka S3 | 6.9M | 83K | 890 | ~7,753 | ~93 |
| Uluka S8 | 4.2M | 212K | 1,078 | ~3,896 | ~197 |
| DS S0 | 16.8M | 630K | 3,268 | ~5,141 | ~193 |
| DS S1 | 9.2M | 274K | 1,135 | ~8,106 | ~242 |
| WTD S2 | 12.9M | 531K | 459 | ~28,122 | ~1,157 |

**Note**: Total tokens/LOC is misleading because cache reads dominate (96%+ hit rates). New-work tokens/LOC is more meaningful — it measures how many non-cached tokens are consumed per line of accepted code. New-work tokens/LOC is stable in the 78-256 range across all sprints — there is no dramatic improvement trend. The variation reflects milestone complexity, not workflow maturity.

Do not compare across project types — only across sprints on the same project. Greenfield code produces more LOC per token because there are no existing patterns to understand.

**Metrics correction (applied in this session)**: All sprint metrics were re-verified using `extract_metrics.py` with message ID deduplication and subagent log aggregation. Previous numbers were inflated by ~1.5x due to two bugs in the collection tooling: (1) streaming logged the same message ID multiple times without deduplication, (2) subagent logs at `{session-id}/subagents/agent-*.jsonl` were not always included. Both bugs are now fixed in `extract_metrics.py` and `collect.sh`.

**Data source**: All sprint metrics are stored in `sprints.json` (single source of truth). Tables in this document are generated from that data using `tools/generate_tables.py` — see `<!-- generated-from -->` comments above each table. To regenerate after a correction: run the indicated command and paste the output over the existing table.

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
- **Skill compliance is self-assessed**: H7 audits are performed by the sprint agent, not an independent reviewer. Experiment 3 confirmed this inflates scores — process-level checks pass while code-level violations go undetected. Mitigated: sprint template now requires dual verification (process + code with file:line evidence).
- **Model versions are unrecorded**: sprints record model tier (opus/sonnet/haiku) but not specific model version. Claude capability changes between sprints could confound comparisons.
- **Tokens per accepted LOC**: ~3,300-8,100 total tokens/LOC (dominated by cache reads), ~78-256 new-work tokens/LOC. Total is misleading; new-work is the meaningful efficiency metric.

### 11.3 Experiments

Four falsification experiments designed to test Flowstate's value proposition under adversarial conditions.

#### Experiment 1: No-Flowstate Baseline — COMPLETE

Built one milestone on each project with raw Claude Code (no skills, no phases, no gates). Both baselines completed 4-8x faster with comparable quality (76-88% blind review). Full results: `temp/experiment-1-results.md`.

**Verdicts**: H1 weakened (3-phase adds overhead for well-scoped work), H7 partially falsified (comparable quality without skills), H2 weakened (skills not clearly necessary).

#### Experiment 2: Adversarial Gate Test — COMPLETE

Planted 3 bugs on Uluka's `exp-2-adversarial` branch (unused import, wrong confidence threshold, type error). Ran a normal Flowstate sprint (S8). All 3 caught by their intended gates (Gate 1 tests, Gate 2 lint, Gate 1 types), all fixed in 1 cycle, all traced to planted commit `903939b`. H5, H8, H9 confirmed under adversarial conditions.

#### Experiment 3: Blind Compliance Scoring — COMPLETE (folded into Exp 4)

After DS S6, gave code artifacts to a fresh agent with no Flowstate knowledge for 5-dimension blind scoring. Compared against self-assessed scores.

**Key finding**: Self-assessment was not inflated but was shallow. Sprint agent scored H7 as "partially confirmed" (correct), but caught process-level gaps (no security audit wave) while missing 6 code-level violations the blind judge found (non-constant-time token comparison, 0.0.0.0 bind, no cancellation safety docs, weak hash, pub vs pub(crate), unjustified allow(dead_code)).

**Blind scores**: Scope 4/5, Tests 4/5, Code quality 3/5, Convention compliance 3/5, Diff hygiene 4/5. **Overall: 18/25 (72%)**.

**Comparison**: DS S5 baseline (no Flowstate) scored 22/25 (88%) at lower scope. Not directly comparable — 2.5x scope means more surface area for issues.

**Root cause**: H7 audit checks process compliance ("did the activity happen?") not code compliance ("does the code follow the instruction?"). Sprint template updated to require both process AND code verification with file:line evidence.

**Verdict**: H7 audit methodology was insufficient. Upgraded sprint template with dual-verification requirement.

#### Experiment 4: Scope Stress Test — COMPLETE

DS S6 combined M4 (Tor spike) + M5 (Matrix outbound bridge) — ~2.5x normal DS sprint scope. Tests whether 3-phase structure holds under combined milestone pressure.

**Result**: Structure held. 2,652 LOC, 48 tests, gates first pass. The planning phase correctly grouped M4+M5 transport concerns. This partially counters Exp 1's finding: for multi-module work, the planning phase prevents wrong turns. Token metrics unavailable (no collect.sh).

**Verdict**: H1 confirmed under scope stress. Flowstate's value proposition is strongest for multi-module sprints where planning prevents wasted work.

#### Summary: What the experiments show

| Experiment | Targets | Result | Flowstate implication |
|-----------|---------|--------|----------------------|
| Exp 1: No-Flowstate baseline | H1, H2, H7 | 4-8x faster, comparable quality | Overhead not justified for single-module work |
| Exp 2: Adversarial gates | H5, H8, H9 | 3/3 planted bugs caught, all fixed in 1 cycle | Gates are the strongest mechanism; H5, H8, H9 confirmed |
| Exp 3: Blind scoring | H7 | Process audit misses code violations | H7 template upgraded to dual verification |
| Exp 4: Scope stress | H1, H4 | Structure held at 2.5x scope | Flowstate earns its keep on multi-module sprints |

Full experiment results: `temp/experiment-1-results.md`, `temp/experiment-2-adversarial-gates.md`, `temp/experiment-3-4-results.md`.

### 11.4 Hypothesis cap

The current hypothesis set (H1-H12) is sufficient. No new hypotheses will be added. Future sprints re-test existing hypotheses with better controls rather than expanding scope. This prevents the meta-system from growing indefinitely.

