# Swift patterns

Use these examples to resolve the corresponding rules in [SKILL.md](../SKILL.md). Each Swift block is self-contained and targets Swift 6 language mode without additional upcoming-feature flags. Adapt it to the project's supported settings; an example is not a migration instruction.

## Call-site clarity and effects

Name parameters for their role. Keep labels that disambiguate use. Mutation and a returned copy should be distinguishable without inspecting the implementation.

```swift
struct Playlist {
    private(set) var tracks: [String] = []

    mutating func append(_ track: String) {
        tracks.append(track)
    }

    func appending(_ track: String) -> Playlist {
        var result = self
        result.append(track)
        return result
    }

    mutating func remove(at index: Int) -> String {
        tracks.remove(at: index)
    }
}

func demonstratePlaylist() {
    var playlist = Playlist()
    playlist.append("Overture")
    let extended = playlist.appending("Finale")
    _ = playlist.remove(at: 0)
    _ = extended
}
```

`remove(at:)` takes an index, not a track to search for. Its caller must supply a valid index. Do not add a meaningless optional result to disguise a programming error in an API whose contract requires a valid index.

Prefer defaulted, labeled parameters over families of nearly identical overloads. Keep positional arguments where Swift's conventions make them clear; Swift argument labels already solve much of the problem that object arguments solve in TypeScript.

## Distinct states and exhaustive handling

An enum associates each state with exactly the data that belongs to it. Avoid a `loading` flag plus unrelated optional result and error fields.

```swift
struct SearchResult {
    let title: String
}

enum SearchState {
    case idle
    case loading
    case loaded([SearchResult])
    case failed(message: String)
}

func statusText(for state: SearchState) -> String {
    switch state {
    case .idle:
        "Ready"
    case .loading:
        "Searching"
    case let .loaded(results):
        "Found \(results.count) results"
    case let .failed(message):
        message
    }
}
```

The switch deliberately has no `default`: a new case must receive explicit handling. An external nonfrozen enum may gain cases without recompiling its library. Handle its known cases and add `@unknown default` with an intentional fallback; do not mechanically add that branch to every enum switch.

## Absence, failure, and the simplest useful type

Return an optional when absence is part of the answer. Use a throwing function when callers need to distinguish reasons for failure. Keep a plain collection when empty input has valid behavior.

```swift
func newestEntry(in entries: [String]) -> String? {
    entries.first
}

func total(_ amounts: [Int]) -> Int {
    amounts.reduce(0, +)
}

enum ConfigurationError: Error {
    case missingPort
    case invalidPort(String)
}

func readPort(from environment: [String: String]) throws -> UInt16 {
    guard let rawPort = environment["PORT"] else {
        throw ConfigurationError.missingPort
    }
    guard let port = UInt16(rawPort), port > 0 else {
        throw ConfigurationError.invalidPort(rawPort)
    }
    return port
}
```

An empty list has a valid total; a nonempty wrapper would add no useful guarantee here. Conversely, do not replace a required result with an optional just to avoid explaining an invariant. Strengthen the input or explicitly handle absence according to the domain.

Use `try?` when all failures genuinely mean the same thing, such as an optional best-effort cache lookup. Preserve the error when callers need to diagnose or recover. A placeholder empty string, empty collection, or zero can turn a failure into a misleading success.

A forced operation is appropriate only when its invariant is established and visible, such as a validated fixture or framework-required initialization contract. Document the reason and test that contract. External data and ordinary recoverable errors need checked handling.

## Checked conversions

`as?` checks a dynamic cast. Handle its optional result. `as` can safely bridge types or perform a compiler-checked coercion; it does not promise arbitrary data has a desired shape.

```swift
import Foundation

func textValue(from value: Any) -> String? {
    guard let text = value as? String else {
        return nil
    }
    return text
}

func boxedCount(_ count: Int) -> NSNumber {
    count as NSNumber
}

struct LayoutMetrics {
    let padding: CGFloat = 12
}
```

Use `Any` only at genuinely untyped interfaces, such as legacy interoperability. Prefer a typed interface inside Swift code. Numeric literals infer different types from context: an annotation can express the intended type without a cast.

## Typed boundaries and validated construction

`JSONDecoder` checks the decoded representation. Domain validation is a separate step. This example requires a positive identifier; a syntactically valid JSON integer can still violate that requirement.

```swift
import Foundation

struct AccountID: Hashable {
    let rawValue: Int

    init?(rawValue: Int) {
        guard rawValue > 0 else {
            return nil
        }
        self.rawValue = rawValue
    }
}

struct Account {
    let id: AccountID
    let name: String
}

enum AccountInputError: Error {
    case invalidID
    case emptyName
}

private struct AccountPayload: Decodable {
    let id: Int
    let name: String
}

func decodeAccount(from data: Data) throws -> Account {
    let payload = try JSONDecoder().decode(AccountPayload.self, from: data)
    guard let id = AccountID(rawValue: payload.id) else {
        throw AccountInputError.invalidID
    }
    let name = payload.name.trimmingCharacters(in: .whitespacesAndNewlines)
    guard !name.isEmpty else {
        throw AccountInputError.emptyName
    }
    return Account(id: id, name: name)
}
```

Give a domain wrapper validated construction when its invariant matters. A `typealias` names a type but does not distinguish identifiers from other values of that type. Do not add wrappers without a concrete benefit.

Keep the payload private to the boundary. Pass the validated domain value onward instead of repeatedly decoding or checking the same identifier. Do not add synthesized `Decodable` conformance to `AccountID` without preserving its validation in `init(from:)`: synthesized decoding would bypass `init?(rawValue:)`.

## Values, identity, and mutation

Choose structs/enums for independent values. A struct containing a class reference still shares the referenced object unless its design provides value semantics. Choose a class when identity or a reference lifetime is part of the requirement; use `final` when subclassing is not intended.

`let` prevents rebinding a class reference, not changes to the referenced object. `private(set)` can expose readable state while restricting mutation to the type's implementation. A read-only reference property alone does not make the referenced object read-only.

Inject dependencies through initializers when that makes ownership and tests explicit. Prefer a concrete dependency until callers need an interchangeable contract. A protocol for every class or a singleton for every service adds abstraction without establishing a useful boundary.

## Ownership and closure captures

Draw the retention path before choosing a capture list. Here, the owner retains the event source, the source retains the callback, and a strong callback capture would retain the owner. A weak capture breaks that cycle; events after the owner disappears can legitimately do nothing.

```swift
@MainActor
final class EventSource {
    var onEvent: (() -> Void)?

    func emit() {
        onEvent?()
    }
}

@MainActor
final class EventCounter {
    private let source: EventSource
    private(set) var count = 0

    init(source: EventSource) {
        self.source = source
        source.onEvent = { [weak self] in
            self?.count += 1
        }
    }
}
```

`[weak self]` is not a default for every closure. Strong capture can be correct when work must retain its owner until completion. Nonescaping closures usually do not create a lasting ownership cycle. `unowned` requires a lifetime guarantee on every access; it traps if the referent has already been destroyed.

An owner that retains a task can participate in a similar cycle. For task captures and cancellation, also read [concurrency](concurrency.md#task-lifetime-and-cancellation).

## Contracts and collection costs

Use `///` for public API contracts: behavior, meaningful absence, errors, side effects, and performance callers cannot infer. An internal comment should explain a decision or invariant. Prefer methods for substantial work; if a computed property is not O(1), document its complexity.

Iterate elements directly when you need elements. Use a collection's `indices` when you need valid indices. Use `enumerated()` for an ordinal plus an element, not as a source of indices into arbitrary collections or slices. Avoid integer arithmetic on `String.Index` and assumptions that a slice starts at zero.

## Sources

- [Swift API Design Guidelines](https://www.swift.org/documentation/api-design-guidelines/): naming, argument labels, documentation, and complexity.
- [Enumerations](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/enumerations/), [Error Handling](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/errorhandling/), and [Type Casting](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/typecasting/).
- [Structures and Classes](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/classesandstructures/) and [Automatic Reference Counting](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/automaticreferencecounting/).
- [Encoding and Decoding Custom Types](https://developer.apple.com/documentation/foundation/archives_and_serialization/encoding_and_decoding_custom_types).
- [Microsoft's Swift guide](https://github.com/microsoft/swift-guide): additional input on early exits, immutability, documentation, and dependency injection. Examples and rules here are independently written.
