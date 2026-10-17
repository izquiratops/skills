# Swift skill verification

## Executable checks

From the repository root, run:

```sh
python3 tests/swift-best-practices/verify.py --check-style
```

Requires Python 3.9+, a Swift 6 toolchain, SwiftLint, and SwiftFormat. Omit `--check-style` when the style tools are unavailable. The script checks local links and skill metadata, typechecks each documented Swift block in Swift 5 and Swift 6 language modes with complete concurrency checking and warnings as errors, and runs behavior checks for values, optionals/errors, decoding, ownership, structured results, stale searches, and cancellation.

Swift 5 mode on a Swift 6 compiler is not evidence of compatibility with a Swift 5 compiler. The examples target Swift 6 without extra upcoming-feature flags; they are not a deployment-target or platform test matrix. There is no application build in this documentation repository.

## Agent scenarios

Install the skill through the agent's normal skill mechanism and invoke it explicitly for Swift scenarios. Use a fresh session and isolated temporary fixtures for each scenario. Record the agent/model, tools, prompt, skill/reference reads, output, and any file changes. Check compilation and behavior independently of the agent's claims.

These are behavioral smoke tests, not a statistical evaluation or proof that the skill improves a model over its baseline. Use the same fixtures and criteria when repeating them after instruction changes.

### 1. Optional input in a Swift script

Fixture: `Port.swift` contains a function that reads `environment["PORT"]!`, converts with `UInt16(...)!`, and returns the port. Missing, zero, nonnumeric, and out-of-range ports must be errors; a valid port must succeed.

Prompt: “Invoke swift-best-practices. Fix port parsing in Port.swift. Return useful errors for missing or invalid configuration. Keep the change focused.”

Check: the agent applies the skill, handles the four invalid classes explicitly, preserves a valid value, and does not add unrelated abstractions or configuration changes. Compile and execute tests for every class.

### 2. Defects versus suggestions in review

Fixture: `Review.swift` contains `displayName(in:)` that uses `names[0]`; its documented contract permits empty input and requires `"(none)"`. Also include a presentation model with separate loading, optional results, and optional error fields, with no specified invalid-state behavior.

Prompt: “Invoke swift-best-practices. Review Review.swift for bugs and useful design improvements. Do not edit the file.”

Check: the empty-input crash is a defect with a failure condition. An enum-based model is a separate design suggestion with a benefit and trade-off, not a claimed runtime bug without evidence. The review does not turn into a formatter report or edit files.

### 3. Actor reentrancy

Fixture: `Search.swift` contains an actor that awaits an injected search operation, then stores its results without a freshness check. The contract says the most recently started search is the only request allowed to publish results. The dependency may ignore cancellation.

Prompt: “Invoke swift-best-practices. Fix overlapping searches in Search.swift so an older response cannot replace a newer search. Preserve the API and isolation settings.”

Check: the agent reads the skill and concurrency reference. It implements an ordering/freshness policy rather than rely only on cancellation or actor serialization. Use controlled completions to finish the newer request before the older one. Check that only the newer result is published. Check ordinary success and failure too.

### 4. Lifetime choices are not blanket rules

Fixture: an immutable `Sendable` struct with `let` properties is captured strongly by a finite `Task` whose caller awaits its result. There is no owner-held callback or task cycle.

Prompt: “Invoke swift-best-practices. Review Lifetime.swift for ownership and concurrency issues. Do not edit it.”

Check: the agent does not demand `[weak self]`, replace the struct with an actor, or invent a leak from a strong capture alone. It may ask for missing lifecycle context when that is actually necessary.

### 5. Unrelated documentation in a Swift repository

Fixture: `README.md` with an incorrect product name; nearby `Package.swift` and `Sources/Main.swift` indicate a Swift project.

Prompt: “In README.md, change the product name Demo to Sample. Make no other changes.”

Check: without explicit invocation, the agent does not load the Swift skill, review Swift code, run a Swift migration, or edit another file.

### 6. Existing compatibility settings

Fixture: a package manifest specifies Swift tools 5.8 and Swift 5 language mode. A Swift source file has an empty-array crash to fix. The supported compiler range is Swift 5.8 and later.

Prompt: “Invoke swift-best-practices. Make firstName(in:) return nil for an empty list. Keep support for our configured toolchains.”

Check: after invocation, the agent does not upgrade the manifest, use syntax requiring a newer compiler, change deployment targets, or weaken concurrency checks. Check the modified source against the oldest supported compiler when available; otherwise record that compatibility gap.
