# Flowstate Sanitized Sprint Export

> Fill this out after a sprint on a project where source code and architecture details must not leave the environment. The retro agent produces a full retrospective locally -- you read it and transcribe ONLY the numbers and process observations below. Redact or generalize anything project-specific before bringing this file back to the Flowstate repo.

## Sprint Identity
- **Project codename**: (a name that does not reveal the real project, e.g., "WorkProject-A")
- **Sprint number**: 
- **Language/framework**: (e.g., "TypeScript/React", "Python/FastAPI")
- **Sprint scope**: (generalized, e.g., "added caching layer" not "added Redis caching to FooCorp payment service")

## Metrics
- **Active session time**: ___m ___s
- **Total tokens**: ___
- **Model mix**: ___% opus / ___% sonnet / ___% haiku
- **Subagents spawned**: ___
- **API calls**: ___
- **Tests added**: ___ (total: ___)
- **Gates first pass**: yes / no
- **Fix cycles needed**: ___

## Hypothesis Results

| # | Hypothesis | Result | Safe-to-share evidence |
|---|-----------|--------|----------------------|
| H1 | 3-phase works | | |
| H4 | Wave parallelism helps | | Waves: ___, max parallel: ___ |
| H5 | Gates catch real issues | | Gate that caught it: ___ (e.g., "lint", "type check") |
| H7 | Skills are followed | /5 | Which failed (by number, not content): |
| H8 | Coverage gate works | | Coverage: ___% -> ___% |
| H9 | Lint gate works | | Errors: ___ -> ___ |

## Skill Change Proposals

> Copy proposals from the full retro. REDACT project-specific content. Generalize patterns.
> Example: "Add guidance about [internal framework]'s middleware" becomes "Add guidance about framework-specific middleware patterns"
> If a proposal cannot be generalized without losing its meaning, note "REDACTED -- too project-specific" and describe the category (e.g., "architecture pattern", "testing approach", "security rule").

### Proposal 1
- **Skill file**: 
- **Category**: (architecture / testing / security / process / other)
- **Generalized description**: 
- **Safe to apply to generic skills?**: yes / no / needs-generalization

### Proposal 2 (copy as needed)

## Process Observations

> These are safe to share because they describe the workflow, not the project.

- **Did Phase 1+2 single prompt work?**: yes / no / partially
- **Did the agent stop and ask for approval?**: yes / no
- **Biggest friction point**: 
- **What would you change about the sprint prompt?**: 
- **Human idle time** (if available from collect.sh): ___m ___s
- **Anything surprising?**: 
