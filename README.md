# Skills

Portable workflows for coding agents.

## Available skills

- [swarm](skills/swarm/SKILL.md): coordinate parallel workers for partitioned work or competing solutions, then return one consolidated report.
- [simulator-screenshots](skills/simulator-screenshots/SKILL.md): capture iOS Simulator screenshots for UI investigation, before-and-after comparisons, and pull request evidence.

## Use

Copy the chosen skill's complete directory from `skills/` into the skills directory supported by your agent. Keep its reference files and any license together with `SKILL.md`. Use your agent's documented skill discovery and invocation mechanism.

`swarm` uses the worker tools available in your environment. It does not require a specific editor or orchestrator. If independent workers are unavailable, it asks before switching to sequential execution.

`simulator-screenshots` requires a Mac with Xcode and an installed iOS Simulator runtime. Its description enables automatic discovery by agents that support model-invoked skills.

See the [skill's attribution](skills/swarm/SKILL.md#swarm) and [MIT license](skills/swarm/LICENSE) for its origin and terms.
