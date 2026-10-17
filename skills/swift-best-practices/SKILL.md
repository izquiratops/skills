---
name: swift-best-practices
description: "Swift correctness and API design guardrails. Use when implementing, debugging, refactoring, or reviewing Swift code in projects or scripts. Not for unrelated work in a repository that contains Swift."
paths: ["**/*.swift"]
disable-model-invocation: true
---

# Swift best practices

Target Swift 6 by default; keep an existing project's supported compiler and language-mode settings.

## Rules

| Rule | Guidance |
| --- | --- |
| Call-site clarity | Read a realistic call before settling a name. Use role-based names and meaningful argument labels. Follow Swift's API naming conventions; clarity takes priority over brevity. |
| Effects in names | Distinguish mutation from a returned value (`sort`/`sorted`, `formUnion`/`union`). Boolean queries read as assertions. |
| Valid states | Model distinct states with enums and associated values instead of correlated flags and optionals. Use a domain type when it prevents a concrete invalid value or mix-up, not for every primitive. |
| Exhaustive handling | List the cases of owned enums explicitly so additions require a decision. For nonfrozen external enums, use `@unknown default` with deliberate fallback behavior. |
| Meaningful absence | Use an optional for legitimate absence. Unwrap with binding, pattern matching, or a meaningful default; use early `guard` exits for prerequisites. Keep a value nonoptional when the domain requires it. |
| Explicit failure | Use `throws` for failures that need an explanation. Recover where a policy exists; otherwise propagate. Use `try?` only when discarding the error is intentional. Forced unwraps, `try!`, and `as!` need a locally justified invariant, not optimism about external input. |
| Checked conversions | Use `as?` for a dynamic cast that can fail and handle the result. Swift's `as` supports safe coercion and bridging; it is not a TypeScript-style unchecked assertion. Prefer a type annotation when it expresses the intended numeric type directly. |
| Mutation and identity | Prefer `let` when a binding need not change. Prefer structs/enums for values; use classes for shared identity, reference lifetimes, inheritance, or framework requirements. A `let` class reference does not make its object immutable. |
| Deliberate ownership | Trace who retains each object and escaping closure. Choose strong, weak, or unowned references from required lifetimes. Use weak references for nonownership when the referent can disappear; use unowned only with a proven lifetime guarantee. |
| Typed boundaries | Decode external representations into typed values, then validate domain constraints. `Decodable` verifies representation, not every invariant. Keep raw dictionaries and repeated validation at the boundary. |
| Small API surface | Expose only what callers need. Prefer private implementation details, controlled mutation, and injected dependencies over hidden mutable global state. Use protocols when an actual abstraction needs them. |
| Useful contracts | Document public API semantics, invariants, errors, and nonobvious costs with `///`. Explain nonconstant computed-property complexity. Internal comments explain decisions rather than narrate syntax. |
| Safe collection access | Iterate elements, `indices`, or `enumerated()` as appropriate; enumeration offsets are not general collection indices. Use `first` for an optional first element. Use ranges that express the actual endpoints. |
| Concurrency contracts | Identify isolation, value-transfer safety, task ownership, cancellation, and state assumptions across `await`. Read the concurrency reference before changing or reviewing concurrent code. |

## References

- Read [patterns](references/patterns.md) when applying or reviewing API design, state modeling, absence/failure handling, conversions, ownership, or boundary validation and the rule's application is not straightforward.
- Read [concurrency](references/concurrency.md) when implementing or reviewing async functions, tasks, actors, shared mutable state, cancellation, or concurrency diagnostics.
