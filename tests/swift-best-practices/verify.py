#!/usr/bin/env python3
"""Check the portable skill, compile its examples, and run focused smoke tests.

Run from any directory with Python 3.9+ and a Swift 6 toolchain:
    python3 tests/swift-best-practices/verify.py
Add --check-style to also require SwiftLint and SwiftFormat.
"""

import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/swift-best-practices"


def run(command, cwd=None):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError(f"{' '.join(map(str, command))}\n{result.stdout}{result.stderr}")
    return result.stdout.strip()


def check_documents():
    docs = [ROOT / "README.md", Path(__file__).with_name("scenarios.md"),
            *sorted(SKILL.rglob("*.md"))]
    assert len(list(SKILL.rglob("*.md"))) == 3, "Expected a main file and two references"
    for doc in docs:
        text = doc.read_text()
        assert text.endswith("\n"), f"Missing final newline: {doc}"
        assert all(line == line.rstrip() for line in text.splitlines()), doc
        assert len(re.findall(r"^```", text, re.M)) % 2 == 0, doc
        for target in re.findall(r"\[[^\]]+\]\(([^\s)]+)\)", text):
            if target.startswith(("https://", "http://")):
                continue
            relative, _, anchor = target.partition("#")
            destination = doc.parent / relative if relative else doc
            assert destination.is_file(), f"Missing link: {doc}: {target}"
            if anchor and destination.suffix == ".md":
                headings = re.findall(r"^#+ (.+)$", destination.read_text(), re.M)
                slugs = {
                    re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-")
                    for h in headings
                }
                assert anchor in slugs, f"Missing anchor: {doc}: {target}"
    main = (SKILL / "SKILL.md").read_text()
    frontmatter = main.split("---", 2)[1]
    assert "name: swift-best-practices" in frontmatter
    assert "disable-model-invocation" not in frontmatter
    assert "paths:" not in frontmatter, "Keep editor-specific metadata out"
    description = re.search(r'^description: "(.+)"$', frontmatter, re.M).group(1)
    assert len(description) <= 1024
    assert "projects or scripts" in description
    print(f"PASS: {len(docs)} documents, local links, anchors, and discovery metadata")


# Appended to individual examples, not shipped as part of the skill's guidance.
SMOKE_TESTS = {
    "patterns-1": """
var original = Playlist()
original.append("One")
let copy = original.appending("Two")
precondition(original.tracks == ["One"])
precondition(copy.tracks == ["One", "Two"])
precondition(original.remove(at: 0) == "One")
""",
    "patterns-3": """
precondition(newestEntry(in: []) == nil)
precondition(total([]) == 0)
let port = try readPort(from: ["PORT": "8080"])
precondition(port == 8080)
for environment in [[:], ["PORT": "0"], ["PORT": "65536"], ["PORT": "bad"]] {
    do {
        _ = try readPort(from: environment)
        preconditionFailure("Invalid port accepted")
    } catch is ConfigurationError {}
}
""",
    "patterns-5": """
let account = try decodeAccount(from: Data(#"{"id":1,"name":" Ada "}"#.utf8))
precondition(account.id.rawValue == 1 && account.name == "Ada")
for json in [#"{"id":0,"name":"Ada"}"#, #"{"id":1,"name":" "}"#,
             #"{"id":"bad","name":"Ada"}"#, "not json"] {
    do {
        _ = try decodeAccount(from: Data(json.utf8))
        preconditionFailure("Invalid account accepted")
    } catch {}
}
""",
    "patterns-6": """
@MainActor final class WeakOwner {
    weak var value: EventCounter?
    init(_ value: EventCounter?) { self.value = value }
}
let source = EventSource()
var owner: EventCounter? = EventCounter(source: source)
let releasedOwner = WeakOwner(owner)
source.emit()
precondition(owner?.count == 1)
owner = nil
precondition(releasedOwner.value == nil)
source.emit()
""",
    "concurrency-1": """
struct Prices: PriceSource {
    func subtotal() async throws -> Int { 100 }
    func shipping() async throws -> Int { 20 }
}
let total = try await checkoutTotal(from: Prices())
precondition(total == 120)
""",
    "concurrency-2": """
actor Gate {
    private var continuation: CheckedContinuation<[String], Never>?
    private var startedWaiter: CheckedContinuation<Void, Never>?
    private var started = false

    func fetch() async -> [String] {
        await withCheckedContinuation { continuation in
            self.continuation = continuation
            started = true
            startedWaiter?.resume()
            startedWaiter = nil
        }
    }

    func waitUntilStarted() async {
        if started { return }
        await withCheckedContinuation { startedWaiter = $0 }
    }

    func finish() {
        continuation?.resume(returning: ["old"])
        continuation = nil
    }
}
let store = SearchStore()
let gate = Gate()
let old = Task { try await store.search(for: "old") { _ in await gate.fetch() } }
await gate.waitUntilStarted()
try await store.search(for: "new") { _ in ["new"] }
await gate.finish()
do {
    try await old.value
    preconditionFailure("Superseded request succeeded")
} catch SearchUpdateError.superseded {}
let results = await store.results
precondition(results == ["new"])
let canceled = Task {
    withUnsafeCurrentTask { $0?.cancel() }
    try await store.search(for: "canceled") { _ in ["unwanted"] }
}
do {
    try await canceled.value
    preconditionFailure("Canceled request succeeded")
} catch is CancellationError {}
let afterCancellation = await store.results
precondition(afterCancellation == ["new"])
""",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-style", action="store_true")
    args = parser.parse_args()
    check_documents()
    assert shutil.which("swiftc"), "A Swift 6 toolchain is required"
    print(run(["swiftc", "--version"]))
    with tempfile.TemporaryDirectory(prefix="swift-skill-check-") as temporary:
        directory = Path(temporary)
        examples = {}
        for doc in sorted(SKILL.rglob("*.md")):
            blocks = re.findall(r"^```swift\n(.*?)^```$", doc.read_text(), re.M | re.S)
            for number, block in enumerate(blocks, 1):
                name = f"{doc.stem}-{number}"
                source = directory / f"{name}.swift"
                source.write_text(block)
                examples[name] = source
                for mode in ("5", "6"):
                    run(["swiftc", "-swift-version", mode, "-strict-concurrency=complete",
                         "-warnings-as-errors", "-parse-as-library", "-typecheck", str(source)])
        assert len(examples) == 9, "Update checks when examples change"
        print("PASS: 9 examples typechecked in Swift 5 and 6 modes (18 checks)")
        if args.check_style:
            for tool in ("swiftformat", "swiftlint"):
                assert shutil.which(tool), f"{tool} is required with --check-style"
            run(["swiftformat", "--lint", "--swiftversion", "6", str(directory)])
            run(["swiftlint", "lint", "--quiet", "--strict", str(directory)])
            print("PASS: SwiftFormat and SwiftLint on all 9 examples")
        for name, body in SMOKE_TESTS.items():
            source = directory / f"{name}-smoke.swift"
            source.write_text(examples[name].read_text() +
                              "\n@main struct SmokeTest {\n"
                              "    @MainActor static func main() async throws {\n" + body +
                              "\n    }\n}\n")
            binary = directory / f"{name}-smoke"
            run(["swiftc", "-swift-version", "6", "-strict-concurrency=complete",
                 "-warnings-as-errors", "-parse-as-library", str(source), "-o", str(binary)])
            run([str(binary)])
            print(f"PASS: {name} runtime smoke test")
    print("External links and agent behavior need separate checks; see scenarios.md.")


if __name__ == "__main__":
    main()
