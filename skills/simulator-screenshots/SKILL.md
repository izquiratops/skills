---
name: simulator-screenshots
description: "Capture iOS Simulator screenshots to investigate UI, compare before and after states, or provide pull request evidence."
---

# Simulator screenshots

Run commands on the Mac that hosts the simulator, with Xcode selected and its simulator runtime installed.

## 1. Select the device and evidence

Identify the screen, state, and UI claim to show. For comparisons, use the same device, locale, appearance, text size, and app state before and after the change.

```sh
xcode-select -p
xcrun simctl list devices booted
```

Use the requested device's UDID in all later commands. When several devices are booted and the target is unclear, ask which one to use. An explicit UDID prevents a capture from the wrong device.

```sh
UDID='REPLACE_WITH_DEVICE_UDID'
```

If no suitable device is booted, or the app needs a build, follow [Prepare the app](references/prepare.md). Continue when the selected device is booted and the intended app is installed.

## 2. Reach the intended state

For an app that is already running, preserve its current state. For a reproducible launch, inspect the project's launch arguments, deep links, and UI tests. Prefer synthetic fixtures for screenshots that will leave the machine. Confirm that the installed build supports those fixtures before launching; a flag that a Release build ignores is not a privacy safeguard.

`simctl io` captures the visible display, not off-screen scroll content. It does not tap, type, scroll, or identify the foreground app. Use an available UI automation tool or the project's XCTest UI tests for interactions. If neither can reach the required state, ask the user to navigate there. See [UI-test attachments](references/variants-and-tests.md#ui-test-attachments) for interaction evidence.

Continue when the intended state is visible. A successful launch only means a process started; it does not prove that loading or animation finished.

## 3. Capture

Create a separate output directory for this run. Keep evidence outside tracked source files unless the project stores screenshots in Git by convention.

```sh
OUT="$(mktemp -d "${TMPDIR:-/tmp}/simulator-screenshots.XXXXXX")"
SCREENSHOT="$OUT/before.png"
xcrun simctl io "$UDID" screenshot --type=png "$SCREENSHOT"
file "$SCREENSHOT"
sips -g pixelWidth -g pixelHeight "$SCREENSHOT"
printf 'Screenshot: %s\n' "$SCREENSHOT"
```

Give subsequent captures distinct names such as `after.png` or `login-dark.png`. Reusing a destination can overwrite evidence. Use [Appearance and text size](references/variants-and-tests.md#appearance-and-text-size) only when those variants are relevant.

Record the app revision and build configuration, device model and runtime, launch scenario or interaction steps, locale, appearance, and text size with the evidence. These commands supply device and UI settings:

```sh
xcrun simctl list devices booted
xcrun simctl ui "$UDID" appearance
xcrun simctl ui "$UDID" content_size
```

Continue only after the capture command succeeds and the PNG exists with nonzero dimensions. On failure, read the command's error and recheck the selected device. Report tool or runtime blockers instead of claiming a capture succeeded.

## 4. Inspect the image

Open the PNG with the agent's image-reading tool. `open "$SCREENSHOT"` opens Preview for a human, but does not let an agent inspect the pixels. If image reading is unavailable, return the file for human inspection and label visual verification as pending.

Check that the image shows:

- The intended app, screen, and state, rather than the Home Screen, an unrelated app, or a system prompt.
- The UI detail under discussion, with loading and transitions complete.
- Safe content: no real credentials, tokens, personal health data, account details, or private notifications.

If a capture is wrong or premature, reach the state again and capture to a new filename. Use synthetic data for replacement evidence. Keep original captures unchanged; label crops or annotations as derivatives.

A screenshot proves visible appearance, not tap behavior, accessibility semantics, network success, or HealthKit writes. Verify those claims separately.

## 5. Return or publish evidence

Return the inspected image paths and a short caption for each. Include the relevant capture conditions and any unverified claims. Preserve required files in the project's approved artifact location before temporary storage is removed.

For pull requests, use the repository's existing artifact or image-hosting process. Publish only inspected, safe images. A local path is not a GitHub attachment, and `gh pr create` or `gh pr edit` does not upload an image referenced by that path.

Use `gh` for GitHub operations. For an existing Actions artifact, retrieve its actual run link with `gh run view RUN_ID --json url` and name the artifact in the caption. An Actions artifact link is not a direct image URL. If inline images are needed, use an approved hosted image URL, or ask the user to attach the PNG through GitHub's editor. Do not create a public release or commit screenshots merely to host them.

When a hosted image URL is available, include it only where the project's PR policy permits evidence:

```markdown
![Login screen after the fix](HOSTED_IMAGE_URL)
```

Finish when the images have been inspected or explicitly marked for human inspection, the recipient has usable paths or links, and temporary simulator-setting changes have been restored.
