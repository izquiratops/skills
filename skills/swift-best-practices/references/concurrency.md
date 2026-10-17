# Swift concurrency

Read this reference for asynchronous or concurrent work covered by [SKILL.md](../SKILL.md). Each example is self-contained and targets Swift 6 language mode without additional upcoming-feature flags. Preserve the project's actual isolation settings and supported features.

## Establish the contract

Before editing or reviewing concurrent code, identify:

1. **Isolation:** which actor or synchronization mechanism owns each piece of shared mutable state?
2. **Transfer:** which values cross isolation boundaries, and why is that transfer safe?
3. **Lifetime:** who waits for work, observes failure, and cancels work that is no longer needed?
4. **Suspension:** which assumptions can become invalid while an `await` suspends?

The compiler checks data-race safety, not the application's ordering or freshness requirements. A compile is necessary evidence, not proof that the operation is logically correct.

## Isolation and value transfer

Keep related state and operations in one isolation domain. Use an actor for independently shared mutable state and `@MainActor` for state that belongs to the main actor, such as UI state. Respect isolation already supplied by a framework, superclass, protocol, or project setting; do not annotate every type with `@MainActor` to make diagnostics disappear.

`Sendable` describes values that can safely cross isolation boundaries. Prefer compiler-checked conformances and immutable snapshots for shared results. A struct with mutable reference-type contents is not automatically safe just because it is a struct. A `let` binding is not a concurrency mechanism.

Not every transfer requires adding `Sendable` to a type: the compiler can also prove safe transfers of disconnected values. Where supported and appropriate, `sending` expresses transfer rather than arbitrary sharing. Choose the intended ownership and isolation contract before adding annotations.

For a concurrency diagnostic, first identify the crossing, shared state, and intended owner. Adjust the boundary, isolate the operation, or pass a safe snapshot. `@unchecked Sendable`, `nonisolated(unsafe)`, and `@preconcurrency` are escape hatches for specific interoperability or synchronization contracts, not routine fixes. If required, keep the escape hatch narrow and document the external guarantee and how it is verified. An annotation cannot make an unsafe implementation safe.

## Structured work first

Call an async operation directly when work is sequential. Use `async let` for a fixed number of independent child operations. Use a task group for a dynamic set, and bound fan-out for large inputs. Keep result aggregation in the parent rather than mutate a captured collection from concurrent children.

```swift
protocol PriceSource: Sendable {
    func subtotal() async throws -> Int
    func shipping() async throws -> Int
}

func checkoutTotal(from source: some PriceSource) async throws -> Int {
    async let subtotal = source.subtotal()
    async let shipping = source.shipping()
    return try await subtotal + shipping
}
```

The children belong to the function's scope. The scope waits for them before it exits, including on failure. Cancellation is cooperative: a child that ignores cancellation can delay scope exit.

`Task { ... }` creates **unstructured** work even when written inside another task. It inherits actor context, priority, and task-local values in the supported context, but does not gain structured parent-child lifetime or cancellation propagation. Use it when a real boundary needs independently managed work, such as starting async work from a synchronous event callback. Name the owner and failure/cancellation policy.

`Task.detached` also discards inherited actor context and task-local values. Use it only for deliberately independent work with safe captures and an explicit lifetime. It is not a general-purpose fix for isolation errors or a substitute for structured concurrency.

## State across suspension

Actors serialize access to their state, but do not make an entire async method atomic. At an `await`, another call can change the actor's state. Keep invariant-sensitive transitions synchronous, reserve state before suspending when appropriate, or recheck assumptions afterward.

Here the latest *started* search owns the right to publish results. A previous search can finish later, but cannot overwrite those results. Cancellation alone would not enforce this policy if the underlying operation ignored cancellation.

```swift
import Foundation

enum SearchUpdateError: Error {
    case superseded
}

actor SearchStore {
    private var latestRequest: UUID?
    private(set) var results: [String] = []

    func search(
        for query: String,
        fetch: @Sendable (String) async throws -> [String]
    ) async throws {
        let request = UUID()
        latestRequest = request
        let updated = try await fetch(query)
        try Task.checkCancellation()
        guard latestRequest == request else {
            throw SearchUpdateError.superseded
        }
        results = updated
    }
}
```

The freshness check and publication have no intervening `await`. Decide the policy for failed or canceled newer requests too: this example leaves the previous published results unchanged and does not revive an older request.

For a cache that coalesces duplicate requests, install an in-flight entry before suspending. On completion or failure, only replace/remove the entry owned by that request. Specify whether canceling one waiter should cancel shared work; callers awaiting an unstructured task's value do not automatically own its cancellation.

## Task lifetime and cancellation

Cancellation requests work to stop; it does not forcibly terminate execution. Check it at meaningful boundaries and in long-running loops. Propagate cancellation or handle it as an explicit outcome. Some APIs use their own cancellation errors, so do not rely only on catching `CancellationError` when the task's cancellation state matters.

A stored task needs an explicit lifecycle. Cancel superseded work and provide a stop operation for its owner to call. Preserve failures that need attention instead of discarding a throwing task's handle.

```swift
@MainActor
final class Refresher {
    private var task: Task<Void, Never>?
    private(set) var values: [String] = []
    private(set) var lastError: String?

    func start(load: @escaping @Sendable () async throws -> [String]) {
        stop()
        lastError = nil
        task = Task { [weak self] in
            do {
                let updated = try await load()
                try Task.checkCancellation()
                self?.values = updated
            } catch {
                guard !Task.isCancelled else {
                    return
                }
                self?.lastError = String(describing: error)
            }
        }
    }

    func stop() {
        task?.cancel()
        task = nil
    }
}
```

The callback retains its dependencies but not the refresher while waiting. The owner must call `stop()` when work is no longer needed; weak capture alone does not stop the operation. Dependencies captured by `load` need their own lifetime review.

Capturing `[weak self]` and then binding `self` strongly before a long `await` keeps it alive across that wait. This may be correct for finite work, but can keep a long-running subscription alive indefinitely. Cleanup only in `deinit` cannot break a cycle that prevents `deinit` from running. Prefer an explicit stop/cancel boundary and test release of the owner.

## Execution and legacy boundaries

`async` means a function can suspend, not that it runs on a background thread. `Task { ... }` can inherit the main actor. Executor behavior of nonisolated async functions depends on language features and settings; inspect the project before assuming execution moves away from the caller. Use supported explicit execution controls when needed, and measure responsiveness under real workloads.

Keep blocking I/O and expensive synchronous work off responsiveness-critical actors. Use an appropriate asynchronous API or an explicitly managed execution boundary for blocking work. A semaphore wait for future async work can deadlock or exhaust cooperative executor threads; suspend instead of blocking for a task result.

When adapting a callback API, use checked continuations where appropriate. Resume exactly once on every completion path. Define how cancellation reaches the underlying operation and how competing cancellation/completion callbacks are synchronized. A checked continuation detects misuse; it does not supply cancellation handling or race-free ownership.

## Verification

Test the contract, not scheduling luck. Use controllable async dependencies to exercise overlapping requests, reversed completion order, cancellation, and failure. Prefer explicit synchronization in tests over arbitrary sleeps. Check that canceled/superseded work cannot publish stale state and that long-lived tasks release their owners at the intended lifecycle boundary.

Use the project's supported concurrency settings during builds. Do not weaken them to make a test pass. Test UI responsiveness on the actual running surface when execution placement is relevant.

## Sources

- [The Swift Programming Language: Concurrency](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/): structured and unstructured tasks, cancellation, actors, and sendable values.
- [Swift concurrency migration guide](https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/): language-mode configuration, isolation, safe transfers, and interoperability. If the rendered guide is unavailable, its [source](https://github.com/swiftlang/swift-migration-guide/tree/main/Guide.docc) contains the same topics.
- [Task](https://developer.apple.com/documentation/swift/task) and [withCheckedThrowingContinuation](https://developer.apple.com/documentation/swift/withcheckedthrowingcontinuation(isolation:function:_:)): lifetime, execution, and continuation contracts.
- [Microsoft's concurrency example](https://github.com/microsoft/swift-guide/blob/gh-pages/Concurrency.md): additional input on actor reentrancy and in-flight request caching. The examples here use original, framework-independent types.
