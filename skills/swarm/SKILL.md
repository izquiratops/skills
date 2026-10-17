---
name: swarm
description: "Coordinate parallel workers for partitioned work or competing solutions, then return one consolidated report."
disable-model-invocation: true
---

# Swarm

Fan out independent workers, validate their results, and return one report. Workers can cover distinct slices, race the same brief, or mix both.

Originally created by [Lauren Tan (poteto)](https://github.com/poteto). Forked from [backnotprop/pstack's Swarm](https://github.com/backnotprop/pstack/blob/6f131f137de64fdaf928278c0fd9ecec520ccbee/skills/swarm/SKILL.md). Distributed under the [MIT license](LICENSE).

## Start

Use the current environment's supported worker mechanism: native subagents, background agent processes, or an available terminal orchestrator. Inspect the available tools and their documented options before dispatch. Use only mechanisms that expose worker identity, completion state, and retrievable output. This workflow is self-contained; no particular editor, agent CLI, or orchestrator is required.

If independent workers are unavailable, explain the limitation and ask whether to proceed sequentially or move to an environment with worker support. Label an agreed sequential run as sequential, not parallel.

Track four phases before launching anything: **Frame → Fan out → Aggregate → Report**. Use a task-list tool if available; otherwise keep a compact checklist in the conversation.

## A. Frame

1. State the done predicate and the artifact or report to return.
2. Choose **partition** (distinct slices), **race** (identical briefs), or **mixed**. For races, declare **first pass**, **rank all**, or **best-of**, with selection criteria, before launch. Set N from the user or derive it from the required slices; explain the count. N is the total worker count. Launch all N before waiting for results. If capacity requires waves, agree on the concurrency limit first.
3. Select the execution mechanism and working locations. Prefer local workers when the task needs local files, credentials, or services. Use remote workers only when permitted and when their required context is available there. Follow the environment's approval and data-access rules.
4. Honor requested models, reasoning levels, and speed settings through supported options. Otherwise use the worker mechanism's configured defaults and report that choice. Verify model inheritance rather than assuming it. If a requested setting is unavailable, report the blocker and ask before substituting. A model race names every arm's model up front.
5. Isolate writes. Follow repository instructions for worktrees, including read-only reviews where required. Give independent repository tasks or competing implementations separate worktrees and task branches at the intended base commit. Keep non-repository outputs in distinct worker-owned paths. Record ownership in the briefs. Workers must not overwrite another worker's files or integrate competing branches. Delegate commit, push, or PR authority explicitly; the parent owns final integration and publication by default.
6. Record each worker's name, scope, working location, verification criteria, and finite time budget. When workers verify commits, name the exact SHAs. For measurements, specify sample count, what one sample means, and execution order. Decide which slices are required for coverage.

**Frame is complete when every worker has a standalone brief and an owned location, and the completion rule is explicit.**

## B. Fan out

Keep a ledger using the identifiers returned by the execution mechanism:

| Worker | Scope / race arm | Model / settings | Worker handle | Location / branch / SHA | State / result |
| --- | --- | --- | --- | --- | --- |

Dispatch all workers without blocking on individual results, subject to any agreed waves. Use the mechanism's supported asynchronous or batched calls; translate the workflow into actual tool options rather than assuming a shared API across environments. Record launch failures individually and keep every missing required slice as a gap.

Every brief includes:

- Worker identity, goal, scope or race arm, and done predicate.
- Absolute working directory or remote workspace, owned paths or worktree, base SHA where relevant, and allowed side effects.
- Required verification, including exact SHAs and measurement method when specified.
- Enough context to work independently: assume a fresh conversation without the parent's history.
- A request to return **PASS**, **ISSUES**, or **BLOCKED**, with evidence, checks actually run, changed paths or commit IDs, and gaps. Ask for all provable issues, not only the first.
- A result destination the parent can retrieve: the worker's response, captured process output, or a unique report path accessible to the parent.
- A boundary: perform only this brief; let the parent launch additional workers, handle integration, and publish unless explicitly delegated.

A launch acknowledgement is not proof that work began. Confirm activity or a matching completed response through the mechanism's state and output tools. Inspect failed or stalled launches before recovery so a delivered brief is not submitted twice. Leave approval decisions to the user when required.

**Fan out is complete when all N workers have been dispatched or have a recorded launch failure.**

## C. Aggregate

Wait only after fan-out, using finite waits within each worker's remaining budget. Retrieve both lifecycle state and output. A settled state or process exit is a signal to inspect, not proof that the brief is complete. Require a response matching the brief and containing the requested evidence. A timeout, unknown state, or missing response remains unresolved, not PASS. Account for background jobs that can outlive the worker's response.

On timeout or blockage, inspect state and output before recovery. Ask the user before answering an approval or question dialog. Record a dropout or gap when recovery cannot finish within the budget; continue collecting other workers.

If output is truncated or unavailable, retrieve a larger capture or ask the worker to write its report to a unique accessible path. Transfer remote reports through the supported mechanism before reading them locally.

Validate every result against its brief. When required SHAs, measurement method, or evidence are missing, request one correction from that worker, or replace it once if it exited. After another miss, record a gap. A gap never counts as a pass. Inspect artifacts and rerun decisive checks before accepting or integrating changes; a worker's PASS label alone is not verification.

For partitions, account for every required slice. For races, apply the declared rule:

- **First pass:** accept the first result that satisfies all criteria. Request that remaining workers stop at a safe point, then collect their state and any partial work. Stop them only after verifying the selected result, not merely because it claims PASS.
- **Rank all:** collect every arm or an explicit gap, then rank by the declared criteria.
- **Best-of:** select the strongest qualifying result against the declared criteria; explain trade-offs and missing arms.

Keep a compact result table, one-line evidenced issues, and explicit gaps or dropouts. Reconcile conflicts instead of pasting raw worker transcripts.

**Aggregate is complete when each worker has a validated result, a known safe stopped state, or an explicit unresolved gap, and every required slice is accounted for.**

## D. Report

Return one consolidated in-chat report with:

- Overall outcome against the done predicate.
- Worker result table, with handles or output locations the user can inspect.
- Evidence-backed issues, selected artifacts or commits, and checks actually run.
- Gaps, dropouts, blocked or skipped checks, and any workers still running.
- The selection rule and chosen arm for a race.

Keep worker outputs and visible terminals available for inspection by default. Close only resources this swarm created, only when cleanup is requested and the workers are safely stopped. Retain uncommitted work until it is safely preserved. Follow repository rules for worktree cleanup separately; ending a worker does not preserve its work.
