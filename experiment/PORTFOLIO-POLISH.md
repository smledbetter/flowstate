# Portfolio Polish: Making Flowstate Presentation-Ready

## Status: PROPOSED — run after v1.3 (codebase map) experiment completes

## Goal

Make the Flowstate repo communicate its value in 90 seconds to a hiring manager who lands on the GitHub page. The substance already exists (130+ sprints, 16 projects, a controlled experiment with honest results). The presentation doesn't match the substance.

## What Makes This Repo Impressive

Most portfolio projects are "I built a thing." This one is:

1. A self-optimizing development workflow that ran 130+ autonomous AI sprints across 16 real projects
2. A hill-climbing optimizer that proposes, tests, and reverts process mutations based on empirical data
3. A controlled 2x2 factorial experiment testing whether AI agents can optimize their own workflow
4. Honest null/small results published transparently — more rigorous than most AI benchmarking content

That story isn't visible today. It needs to be.

## Work Items

### 1. Rewrite the README (highest impact)

Replace the current setup-oriented README with a narrative structure:

- **Lead with the pitch:** "I built a system that ran 130+ autonomous AI agent sprints across 16 projects, then designed and ran a controlled experiment to test whether it could optimize itself."
- **What Flowstate is:** 3-4 sentences. Sprint-based workflow for Claude Code. Automated metrics, cross-project learning, hill-climbing optimizer.
- **What the experiment found:** Brief summary of v1.2 results (lint negative, lessons inconclusive, noise floor is the real finding) and v1.3 results (fill in after experiment completes). Link to blog post when it exists.
- **Architecture diagram:** Mermaid diagram showing how the pieces connect — sprint workflow, metrics collection, DuckDB, optimizer loop, experiment framework.
- **Key numbers:** 130+ sprints, 16 projects, 229 cross-project lessons, 66 classified gate failures, 34 experiment builds.
- **Setup instructions:** Move to a separate SETUP.md or a collapsed section at the bottom. Important but not the opener.

### 2. Experiment Results Summary

Write `experiment/README.md` as a standalone 2-minute read:

- The question (can AI agents optimize their own workflow?)
- The design (2x2 factorial, why these two features, how the controls work)
- The results (effect sizes, noise floor, what we learned)
- The honest conclusion (instruction-level mutations don't move the needle at feasible sample sizes; the noise floor from LLM stochasticity is the real finding)
- v1.3 results (codebase map — fill in after experiment)
- Link to PROTOCOL.md for full design details

This file should be linkable from the main README and from the blog post.

### 3. Code Quality Pass on Visible Files

Nobody will audit every file, but someone might click into the 3-4 most prominent ones. Clean up the ones most likely to be opened:

**optimize.py:**
- Replace `except Exception: pass` with logged warnings
- Extract VPS config (IP, SSH key path) to env vars with defaults
- Add docstrings to `propose_mutation`, `evaluate_experiment`, `deploy_skill`

**mcp_server.py:**
- Extract `FLOWSTATE_API` URL to env var (already partially done with PIN, finish the job)
- Replace bare except blocks with specific exception types
- Add a comment block at the top explaining what this server does and how it fits

**import_sprint.py:**
- Add a warning when DuckDB write fails (currently silent)
- Add a brief module docstring

**backtest.py:**
- Fix the Mann-Whitney U rank assignment bug or add scipy.stats as optional dependency with fallback
- Add a note about the Abramowitz-Stegun approximation limitations

Don't rewrite anything. Just raise the floor on what someone sees if they click in.

### 4. Add pyproject.toml and Tests

**pyproject.toml:**
- Pin duckdb version
- Define the project metadata (name, version, description, author, license)
- No need to make it pip-installable — just show that dependencies are managed

**Test suite (15-20 tests, focused on the contract):**
- Composite score calculation (5-6 cases: all gates pass, gates fail, missing fields, edge cases)
- Import validation logic (valid input, missing required fields, out-of-range values, type coercion)
- Mutation generators (each returns None when already applied, returns modified text when applicable)
- Backtest composite_score function matches migrate_to_duckdb calculation

These tests serve two purposes: they catch regressions, and they signal "this person tests their code" to anyone browsing the repo.

### 5. One Architecture Diagram

Mermaid diagram in the README showing:

```
PRD.md --> init.py --> Project Setup
                          |
                    Sprint Loop (SKILL.md)
                     /    |    \
                Phase 1  Phase 2  Phase 3
                (Think)  (Execute) (Ship)
                                    |
                              MCP collect_metrics
                                    |
                              DuckDB / sprints.json
                                    |
                        optimize.py (hill-climbing)
                           /              \
                     propose             evaluate
                    (mutate SKILL.md)   (keep/revert)
                                    |
                        backtest.py (validation)
                                    |
                        experiment/ (controlled tests)
```

Actual Mermaid syntax to be written at implementation time. The point is: one image that shows the feedback loop.

## What NOT to Do

- Don't add multi-user support, plugin architecture, or auth. This is a portfolio piece, not a SaaS product.
- Don't rewrite tools from scratch. The code works. Polish, don't rebuild.
- Don't add features. The experiment results and the honest narrative are the differentiator, not more functionality.
- Don't over-document. A good README + experiment summary + clean visible code beats comprehensive docs that nobody reads.

## Estimated Effort

- README rewrite: 1-2 hours
- experiment/README.md: 1-2 hours
- Code quality pass (4 files): 2-3 hours
- pyproject.toml + test suite: 3-4 hours
- Architecture diagram: 30 minutes

Total: ~1-2 focused days. Could be a single Flowstate sprint if scoped tightly.

## Dependencies

- v1.3 (codebase map) experiment results — needed for the experiment summary
- Blog post draft (optional) — the README can link to it, but the repo should stand alone without it
