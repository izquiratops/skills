# Variants and UI tests

## Appearance and text size

Read the current settings before changing them:

```sh
ORIGINAL_APPEARANCE="$(xcrun simctl ui "$UDID" appearance)"
ORIGINAL_CONTENT_SIZE="$(xcrun simctl ui "$UDID" content_size)"
printf 'Restore appearance=%s content_size=%s\n' "$ORIGINAL_APPEARANCE" "$ORIGINAL_CONTENT_SIZE"
```

Proceed only if appearance is `light` or `dark` and content size is a supported category. For `unknown` or `unsupported`, capture the current settings without changing them. Keep the original values in the same shell or record them so restoration survives separate tool calls.

```sh
xcrun simctl ui "$UDID" appearance dark
xcrun simctl ui "$UDID" content_size accessibility-extra-extra-extra-large
```

Inspect each variant after capture. Restore the saved values after success, error, or interruption, and query them again to confirm restoration:

```sh
xcrun simctl ui "$UDID" appearance "$ORIGINAL_APPEARANCE"
xcrun simctl ui "$UDID" content_size "$ORIGINAL_CONTENT_SIZE"
xcrun simctl ui "$UDID" appearance
xcrun simctl ui "$UDID" content_size
```

Use launch-time language and locale arguments only if supported by the app. Record them for comparisons. Keep the existing status bar by default; clearing an override does not restore someone else's prior override.

## UI-test attachments

Use this branch when evidence requires taps, scrolling, confirmation dialogs, or state transitions. Prefer an existing synthetic UI test. Read its data setup before running it: a screenshot attachment can contain whatever the test puts on screen.

If a test needs a screenshot, attach it after an assertion or explicit wait for the intended state, rather than after a fixed sleep:

```swift
XCTAssertTrue(app.buttons["EXPECTED_ACCESSIBILITY_IDENTIFIER"].waitForExistence(timeout: 10))
let attachment = XCTAttachment(screenshot: app.screenshot())
attachment.name = "login-after"
attachment.lifetime = .keepAlways
add(attachment)
```

Replace the identifier and attachment name with the test's actual state. A screenshot is evidence, not a substitute for the test's assertions.

Run the project's existing test command with a fresh result bundle, or adapt this template to its workspace, scheme, and synthetic test:

```sh
RESULT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/simulator-test.XXXXXX")"
xcodebuild test \
  -project 'PATH_TO_APP.xcodeproj' \
  -scheme 'APP_SCHEME' \
  -destination "platform=iOS Simulator,id=$UDID" \
  -only-testing:'UI_TEST_TARGET/TEST_CLASS/TEST_METHOD' \
  -resultBundlePath "$RESULT_DIR/UI.xcresult"
```

The `.xcresult` destination must not already exist. Test execution can restart the app and change its state. Export screenshots only from a result bundle known to use safe data:

```sh
ATTACHMENTS="$RESULT_DIR/attachments"
xcrun xcresulttool export attachments \
  --path "$RESULT_DIR/UI.xcresult" \
  --output-path "$ATTACHMENTS" \
  --filter '*.png'
```

Read the generated `manifest.json` to map exported filenames to tests and attachment names. Preserve that mapping in captions. Inspect the PNGs before sharing them. A failed test can still have useful attachments; report the failure separately from the image evidence.

If the installed Xcode rejects these options, consult `xcrun xcresulttool export attachments --help` and use that version's supported syntax. Return to the skill's inspection and publication steps after export.
