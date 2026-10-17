---
name: simulator-screenshots
description: "Capture the current iOS Simulator screen and report what the image shows."
---

# Simulator screenshots

Capture the visible display once, inspect the image, and report observations. Leave app state and simulator settings unchanged. The calling agent decides whether to navigate, build, launch, change settings, or request another capture outside this skill.

Run commands on the Mac that hosts the simulator, with Xcode selected and its simulator runtime installed.

## 1. Select the device

Use the target device's UDID if already known. Otherwise, list booted devices:

```sh
xcrun simctl list devices booted
```

Use the sole booted device, or ask which one to use if the target is ambiguous. If no device is booted, report that prerequisite to the calling agent.

## 2. Capture

Replace the UDID below. Run the capture and validation together; the final path is printed only after both succeed. A fresh directory preserves previous captures.

```sh
UDID='REPLACE_WITH_DEVICE_UDID'
OUT="$(mktemp -d "${TMPDIR:-/tmp}/simulator-screenshots.XXXXXX")" &&
SCREENSHOT="$OUT/screenshot.png" &&
xcrun simctl io "$UDID" screenshot --type=png "$SCREENSHOT" &&
sips -g pixelWidth -g pixelHeight "$SCREENSHOT" &&
printf 'Screenshot: %s\n' "$SCREENSHOT"
```

On failure, return the command's error as a blocker. Continue to inspection only when the PNG exists with nonzero dimensions.

## 3. Inspect and report

Read the PNG with the agent's image-reading tool. If image reading is unavailable, return the path and mark visual verification as pending.

Report:

- The image path and device UDID.
- The visible app or screen and observations relevant to the request.
- Any mismatch, loading state, or system prompt that prevents the image from showing the requested UI.

Inspect for credentials, personal data, and private notifications before attaching or sharing the image. If present, flag the privacy blocker without quoting sensitive content.

Keep the original capture unchanged. Base conclusions on visible appearance; verify behavior, accessibility semantics, and data writes separately. Finish after reporting; the calling agent chooses any next action.
