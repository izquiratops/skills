# Swift concurrency

Examples for the concurrency rule in [SKILL.md](../SKILL.md). Code blocks are self-contained and target Swift 6 language mode without upcoming-feature flags. Keep the project's actual isolation settings and supported features.

## Isolation and transfer

Give shared mutable state one owner. Use an actor for independently shared state and `@MainActor` for main-actor state. Respect isolation supplied by a framework, protocol, superclass, or project setting. Adding `@MainActor` everywhere to silence diagnostics can move unrelated work onto the main actor.

`Sendable` describes safe transfer across isolation boundaries. Prefer compiler-checked conformances and immutable snapshots. A struct with mutable class contents is not automatically safe, and `let` is not synchronization. The compiler can also prove safe transfer of disconnected values; where supported, `sending` can express a transfer without promising general sharing.

For each diagnostic, identify the owner, the crossing, and the values crossing it. Then isolate the operation or transfer a safe value. Use `@unchecked Sendable`, `nonisolated(unsafe)`, or `@preconcurrency` only for a narrow contract backed by a real synchronization or interoperability guarantee. Record how that guarantee is verified.

## Structured work

Await sequential work directly. Use `async let` for a fixed number of independent children. Use a task group for a dynamic set, with bounded fan-out for large inputs. Aggregate results in the parent rather than mutate a captured collection from child tasks.

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

The scope waits for its children, including on failure. Cancellation is cooperative; a child that ignores it can delay scope exit.

`Task { ... }` creates unstructured work, even inside another task. It can inherit actor context, priority, and task-local values, but not a structured parent-child lifetime or cancellation policy. Use it at a real synchronous-to-async boundary and name the owner of its result, failure, and cancellation. `Task.detached` also discards inherited actor context and task-local values; reserve it for deliberately independent work with safe captures.

## State across `await`

An actor serializes access to its state, not the whole async method. Another call can change state while a method is suspended. Reserve state before the `await` or recheck it afterward.

Here the latest *started* search alone may publish results. Cancellation alone cannot enforce this rule when a fetch ignores cancellation.

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

No `await` separates the freshness check from publication. A failed or canceled newer search leaves the last published results unchanged; it does not revive an older request.

For a deduplicating cache, install the in-flight entry before suspending. Replace or remove only the entry owned by that request. Decide whether canceling one waiter cancels shared work: awaiting an unstructured task's value does not give the waiter ownership of that task.

## Task lifetime and cancellation

Cancellation asks work to stop; it does not stop execution by force. Check at meaningful boundaries and in long loops. Propagate cancellation or handle it as an explicit outcome. APIs can report cancellation with different errors; inspect task cancellation state when it matters.

A stored task needs an owner and a stop policy. Cancel superseded work and handle failures that callers must see.

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

The callback does not retain the refresher while `load` runs. Its owner must still call `stop()` when the work is no longer needed; weak capture does not cancel it. Review the lifetime of dependencies retained by `load` too.

Binding a weak `self` strongly before a long `await` keeps it alive through the wait. That can be correct for finite work, but can keep a subscription alive indefinitely. Cleanup in `deinit` cannot break a cycle that prevents `deinit`. Provide an explicit stop boundary.

## Execution and legacy APIs

`async` means a function can suspend, not that it runs on a background thread. `Task { ... }` can inherit the main actor. Execution of nonisolated async code depends on language features and settings; inspect them before assuming an executor hop. Keep blocking I/O and expensive synchronous work off responsiveness-critical actors. Suspend for async results instead of blocking a cooperative executor thread with a semaphore.

When adapting a callback API, resume a checked continuation exactly once on every path. Specify how cancellation reaches the operation and how cancellation and completion callbacks synchronize. A checked continuation detects misuse; it does not supply cancellation or race-free ownership.

## Test concurrent behavior

Use controllable async dependencies for overlap, reversed completion order, cancellation, and failure. Synchronize tests explicitly instead of relying on sleeps. Check that canceled or superseded work cannot publish stale state and that long-lived tasks release their owners at the intended boundary. Build with the project's concurrency settings; test responsiveness on the running surface when execution placement matters.
