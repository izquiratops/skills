# Prepare the app

Use this branch only when a suitable simulator or app is not already running. Follow the project's build and signing instructions first. Run repository commands from its dedicated task worktree when required.

## Boot a device

List installed, available devices and select a model and runtime that meet the task's requirements:

```sh
xcrun simctl list devices available
UDID='REPLACE_WITH_DEVICE_UDID'
xcrun simctl boot "$UDID"
xcrun simctl bootstatus "$UDID" -b
```

Run `boot` only for a shut-down device. Use `bootstatus` to wait for startup. If no suitable runtime is installed, report the missing prerequisite. Preserve other devices and their data.

The Simulator window is optional for `simctl` captures. For manual interaction, open the Simulator app supplied with the selected Xcode installation. Do not assume a fixed Xcode installation path.

## Build and install

Discover the project's workspace or project and shared scheme from its instructions or `xcodebuild -list`. The following is a template: replace the project and scheme before running it. Use `-workspace PATH` instead of `-project PATH` when the project requires a workspace.

```sh
BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/simulator-build.XXXXXX")"
xcodebuild build \
  -project 'PATH_TO_APP.xcodeproj' \
  -scheme 'APP_SCHEME' \
  -configuration Debug \
  -destination "platform=iOS Simulator,id=$UDID" \
  -derivedDataPath "$BUILD_DIR"
```

Use the resulting simulator `.app`, usually under `$BUILD_DIR/Build/Products/Debug-iphonesimulator/`. Check the build log for its actual location; an iPhone device build cannot run in Simulator. Follow the project's simulator signing settings if needed rather than changing the project's signing configuration.

```sh
APP='REPLACE_WITH_BUILT_SIMULATOR_APP_PATH'
BUNDLE_ID="$(/usr/libexec/PlistBuddy -c 'Print CFBundleIdentifier' "$APP/Info.plist")"
xcrun simctl install "$UDID" "$APP"
```

Installing can replace an existing app. Use a dedicated simulator when the current installation or its state must be preserved. To identify an already installed app bundle without reinstalling it:

```sh
xcrun simctl get_app_container "$UDID" "$BUNDLE_ID" app
```

## Launch safely

Read the project's fixture implementation and build guards before choosing arguments. Set the scenario and screen using that project's documented mechanism. There is no universal simulator fixture flag.

The launch template below restarts the app and discards its current in-memory state. Use it only when a fresh launch is intended, and append the project's verified fixture arguments before executing it:

```sh
xcrun simctl launch --terminate-running-process "$UDID" "$BUNDLE_ID" PROJECT_FIXTURE_ARGUMENTS
```

If investigating the current running state, return to the capture steps without restarting. Continue only after the intended screen is visible; inspect an initial capture if necessary.
