# Experiment Results

## The Question

Can AI agents optimize their own development workflow? Flowstate's hill-climbing optimizer proposes mutations to the agent's instructions (SKILL.md), waits for sprint data, and keeps or reverts based on composite score movement. But does any of this actually work -- do instruction-level changes produce measurable improvements in sprint outcomes?

Two experiments tested this. The first mutated the agent's process instructions. The second injected structural knowledge about the codebase. Both used matched-pair designs to control for product difficulty.

---

## v1.2: 2x2 Factorial

### Design

Two features crossed in a 2x2 factorial:

|  | Lessons OFF | Lessons ON |
|--|-------------|------------|
| **Lint pre-check OFF** | A: v1.1 baseline | B: lessons only |
| **Lint pre-check ON** | C: lint only | D: lint + lessons |

- **Lint pre-check**: instruction added to SKILL.md telling the agent to run the linter before gates, fixing errors proactively. Backtest ceiling of +0.40 composite score on 43 historical lint-failure sprints.
- **Cross-project lessons**: 229 lessons extracted from 130+ sprints, ranked by Bayesian confidence, injected into each sprint's context. Frozen snapshot -- no cross-build accumulation.

Five products completed all four conditions: fconv (Python CLI), presskit (TypeScript), tagvault (Go API), ledgertui (Rust TUI), pipesmith (Python ETL). Two additional replicates of condition A on fconv and presskit established the noise floor. 34 builds total.

Products were the blocking factor. Each product was built under all four conditions, so between-product variance (different stacks, different scopes) cancels out in the paired comparisons.

### Results

Main effects on token efficiency (tok/LOC, lower is better):

| Effect | Delta (tok/LOC) | Interpretation |
|--------|-----------------|----------------|
| Lint pre-check | +9.7 avg | Net negative. Overhead of running lint proactively exceeds the savings from fewer gate failures. |
| Cross-project lessons | -3.3 avg | Inside the 10-13% noise floor. Cannot distinguish from stochastic variation. |
| Lint x Lessons interaction | +18.0 avg | Condition D (both features) performs worst. Interference, not synergy. |

The noise floor, measured from the two condition-A replicates, was 10-13% on token efficiency. Any treatment effect smaller than that is indistinguishable from the variance introduced by LLM stochasticity alone.

### Conclusion

Instruction-level mutations do not move the needle. The lint pre-check is actively counterproductive -- it adds overhead on every sprint while only helping on sprints that would have had lint gate failures (a minority). Cross-project lessons show a small favorable trend but the effect is too small to detect at this sample size. The combined condition is worse than either feature alone, suggesting the two interventions interfere with each other rather than compounding.

The noise floor is the real finding. At 10-13% replicate variance, most workflow mutations will be undetectable.

---

## v1.3: Codebase Map Injection

### Design

The v1.2 results showed that instruction-level changes ("do this differently") do not help. This experiment tested a different mechanism: structural knowledge ("here is what the codebase looks like").

A codebase map -- file tree, module dependencies, key patterns, recent changes, capped at 80 lines -- was generated after each sprint and injected into the next sprint's context. The hypothesis was that this would reduce architectural mistakes and exploration overhead, especially in later sprints as the codebase grows.

Matched-pair design, 2 products:

|  | notegrep (TypeScript) | pollster (Python) |
|--|-----------------------|-------------------|
| **Control** | No map, standard context | No map, standard context |
| **Map** | Codebase map injected from sprint 2 onward | Codebase map injected from sprint 2 onward |

Each product had an extended 10-phase roadmap to give the treatment time to compound and the learning curve metric more data points. 4 builds, ~40 sprints total.

### Results

| Product | Efficiency delta | Direction |
|---------|-----------------|-----------|
| notegrep | -2.4% | Noise (inside 10-13% floor) |
| pollster | +8.0% | Map worse |

Learning curve slopes (tokens-per-LOC over time): no difference between control and treatment in either product. The map did not cause the agent to become more efficient over successive sprints compared to the control.

### Conclusion

Structural context injection does not help. The agent discovers what it needs by reading files during the planning phase, and the map does not meaningfully reduce that cost. The pollster result (map 8% worse) suggests the map may add noise to the context without providing actionable information the agent would not have found on its own.

---

## What We Learned

The noise floor from LLM stochasticity -- 10-13% between identical replicates of the same product under the same conditions -- is the dominant factor in sprint-level outcomes. Two identical builds of the same product, same instructions, same model, differ by 10-13% in token efficiency purely from randomness in the generation process.

This means:

1. **Any workflow mutation with an expected effect smaller than ~15% is undetectable** at feasible sample sizes (5-10 products).
2. **Instruction-level changes** (lint pre-check, cross-project lessons) produce effects well within the noise floor. They do not reliably improve outcomes.
3. **Structural context injection** (codebase maps) also falls within or below the noise floor.
4. **Future experiments need either much larger N** (20+ products per condition) **or mutations with >15% expected effect size** to produce detectable signal.

The honest conclusion is that the optimizer's hill-climbing loop, while well-designed mechanically, operates on a landscape where the signal-to-noise ratio is too low for gradient-based improvement to work. The agent's sprint-level performance is dominated by task difficulty and LLM stochasticity, not by the specific instructions it follows.

---

## Further Reading

- [PROTOCOL.md](PROTOCOL.md) -- full v1.2 factorial experiment design, metrics definitions, analysis plan, and limitations
- [CODEBASE-MAP.md](CODEBASE-MAP.md) -- full v1.3 codebase map experiment design, map format specification, and extended roadmaps
