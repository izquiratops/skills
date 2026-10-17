# Swift patterns

Examples for the rules in [SKILL.md](../SKILL.md). Code blocks are self-contained and target Swift 6 language mode without upcoming-feature flags. Keep a project's existing compiler and language-mode constraints when applying them.

## Call-site clarity

Name a parameter for its role. Use labels when they make a call unambiguous. Distinguish a mutating method from one that returns a copy.

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

`remove(at:)` requires a valid index; an optional return would hide a violated precondition. Prefer labeled default parameters to a family of near-identical overloads. Swift already has argument labels: add an options type only when the arguments form a useful value of their own.

## Valid states

Don't combine a `loading` flag with optional results and an optional error. Those fields permit contradictory states. Use an enum with data attached to the case that owns it.

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

Switch over every case of an enum you own. Omit `default` so a new case requires a decision. For an external nonfrozen enum, handle known cases and give `@unknown default` an intentional fallback.

## Simplest useful type

Use an optional when absence is a valid answer. Throw when callers need the reason for failure. Keep a plain collection when empty input has valid behavior.

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

Don't wrap `total`'s input in a nonempty type: zero is the right result for an empty array. Don't make a required result optional merely to avoid enforcing its invariant. Choose an input that carries the invariant, or handle absence explicitly.

Use `try?` only when every failure has the same meaning to the caller. An empty string or zero returned after a failed parse can look like success. Force-unwrap or use `try!` only with a locally established invariant, such as a validated fixture; state and test that invariant.

## Checked conversions

Use `as?` for a cast that can fail. Swift's `as` performs compiler-checked coercion or bridging; it is not an unchecked TypeScript assertion. Use a type annotation when a literal already has the type you need.

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

Keep `Any` at genuinely untyped boundaries, such as legacy interoperability. Pass a typed value onward.

## Validate at the boundary

Decode the wire shape, then check domain invariants. `Decodable` checks the representation; it does not prove that a decoded integer is a valid identifier.

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

Keep the payload at the boundary; pass `Account` inward. A `typealias` cannot prevent mixing identifiers with other integers. Add a wrapper when it protects a real invariant. If `AccountID` becomes `Decodable`, implement decoding through its validating initializer: synthesized decoding does not call `init?(rawValue:)`.

## Values and identity

Use structs and enums for independent values. Use a class when shared identity or a reference lifetime is required. A struct that stores a class still shares that object. Mark classes `final` when subclassing is not part of the contract.

`let` prevents rebinding a class reference, not mutation of the object. Use `private(set)` to expose readable state while keeping writes inside the type. Inject dependencies through initializers when ownership or tests need it; add a protocol when callers need an interchangeable contract.

## Closure captures

Trace the retention path before choosing a capture list. Here the counter owns the source; the source owns its callback. A strong capture of the counter would complete a cycle. A weak capture lets events after release do nothing.

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

Don't add `[weak self]` to every closure. A strong capture can be correct when work must retain its owner. Use `unowned` only when every access has a lifetime guarantee; otherwise it can trap. For retained tasks, see [task lifetime and cancellation](concurrency.md#task-lifetime-and-cancellation).

## API contracts

Document public behavior, meaningful absence, errors, side effects, and nonobvious costs with `///`. Explain the complexity of a computed property that is not O(1). Internal comments explain decisions and invariants.

## Collection indices

Iterate elements when you need elements. Use `indices` when you need valid indices. `enumerated()` gives ordinals, not indices into an arbitrary collection or slice. Use `first` for an optional first element; use `String.Index` rather than integer offsets for strings.
