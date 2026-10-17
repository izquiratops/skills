# Skills

Portable workflows for coding agents.

## Available skills

- [swarm](skills/swarm/SKILL.md): coordinate parallel workers for partitioned work or competing solutions, then return one consolidated report.

## Use

Copy the complete `skills/swarm/` directory into the skills directory supported by your agent. Keep `SKILL.md` and `LICENSE` together. Use your agent's documented skill invocation mechanism to run `swarm`.

The skill uses the worker tools available in your environment. It does not require a specific editor or orchestrator. If independent workers are unavailable, it asks before switching to sequential execution.

See the [skill's attribution](skills/swarm/SKILL.md#swarm) and [MIT license](skills/swarm/LICENSE) for its origin and terms.
