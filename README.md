# Skills

Portable workflows for coding agents.

## Available skills

- [swarm](skills/swarm/SKILL.md): coordinate parallel workers for partitioned work or competing solutions, then return one consolidated report.
- [swift-best-practices](skills/swift-best-practices/SKILL.md): language-level guardrails for Swift implementation and review, with examples for API design, safety, ownership, and concurrency.

## Use

Copy a complete skill directory from `skills/` into the skills directory supported by your agent. Keep its references and any license files together.

Invoke `swift-best-practices` for Swift coding and review tasks. Its examples target Swift 6 language mode; keep each project's supported compiler and language-mode settings. It leaves framework-specific design and mechanical formatting to other guidance and your configured tools.

Use your agent's documented skill invocation mechanism to run `swarm`. It uses the worker tools available in your environment and does not require a specific editor or orchestrator. If independent workers are unavailable, it asks before switching to sequential execution.

See the [swarm attribution](skills/swarm/SKILL.md#swarm) and [MIT license](skills/swarm/LICENSE) for its origin and terms. The Swift skill includes [patterns](skills/swift-best-practices/references/patterns.md) and [concurrency](skills/swift-best-practices/references/concurrency.md) references.

## Verification

For Swift examples, links, and skill metadata, run:

```sh
python3 tests/swift-best-practices/verify.py --check-style
```

See the [verification scenarios](tests/swift-best-practices/scenarios.md) for requirements, limitations, and agent-behavior checks.
