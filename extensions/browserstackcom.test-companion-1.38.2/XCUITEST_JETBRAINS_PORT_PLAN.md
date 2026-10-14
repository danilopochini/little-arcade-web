# XCUITest Support — JetBrains Port Plan (`vscode-ai-testing/jetbrains/`)

> Ports the VS Code XCUITest surface (`src/services/mobile/xcuitest-*.ts` + the generic
> native-app layer) to the JetBrains/IntelliJ surface.
> Precedent doc: `ESPRESSO_SUPPORT_PLAN.md` (the original VS Code-side build-out).
> Drafted 2026-08-25. Branch: TBD. Jira: TBD (`STM-` prefix required in the PR title).

## Status

**Layer 1 — DONE** (82 tests green, zero new Kotlin warnings):
- ✅ 1.1 `XCUITEST_SUPPORT = "xcuitestSupport"` in `FeatureFlagsKeys.kt` (camelCase, documented)
- ✅ 1.2 `services/XcuitestSupportFlag.kt` — safe-cast reader, no construction-time caching
- ✅ 1.3 `mobile.framework` threaded through `RouterApiClient` (5 touch points) + `TaskManager`
      call site; per-task memo `resolvedMobileFramework`; field omitted when undetected
- ✅ 1.4 `TestFramework` gains `ESPRESSO` / `XCUITEST` / `MAESTRO` — closed a live BigQuery
      drift against the VS Code union
- ✅ Pulled 3.4 + 3.5 forward (`DetectIosFramework.kt`, `ResolveMobileFramework.kt`) so the
      field has a real producer and Layer 1 is verifiable rather than inert

**Layer 2 + task 3.1 — DONE** (82 tests green, zero new Kotlin warnings):
- ✅ 3.1 `XcuitestInputs.kt` — `validateXcuitestProject`, `xcuitestProjectGuidance`,
      `normalizeXcuitestDevices` (device rule shared via `normalizeNativeDevices`)
- ✅ 2.5 `NativeFrameworks.kt` — `NativeFramework` enum + registry (XCUITest only; Espresso
      and Maestro deliberately absent rather than stubbed)
- ✅ 2.1 `NativeAppUpload.kt` (pure) + `MobileApiClient.uploadNativeArtifact` /
      `uploadNativeAppArtifacts` / `nativeApiPost` / `nativeApiGet` (transport)
- ✅ 2.2/2.3/2.4 `NativeAppRun.kt` — endpoint asymmetry, start, poll, `mapBuildResultToSummary`,
      verbatim zero-tests message
- ✅ 2.6/2.7 `NativeAppOrchestrator.kt` — `resolveNativeProjectName` + `runNativeAppCloudBuild`

**Layer 3 + Layer 4 — DONE** (116 tests green, zero new Kotlin warnings):
- ✅ 3.2 `XcuitestBuild.kt` — scheme resolution, conditional xcodegen, unsigned
      `build-for-testing`, `.ipa`/`tests.zip` packaging. Every command is an argv list through
      `ProcessBuilder`; output is drained on a separate thread so a chatty build cannot
      deadlock on a full pipe buffer.
- ✅ 3.3 `XcuitestProjectPicker.kt` — `FileChooser` via `invokeAndWait`, picker injectable
- ✅ 3.6 `XcuitestOrchestrator.kt` — binds upload/run to a live `MobileApiClient`
- ✅ Registry `build` leaf flipped to `buildXcuitestArtifacts`
- ✅ 4.1 `RUN_XCUITEST_BUILD("run_xcuitest_build")` on `MobileActionType`
- ✅ 4.2 handler case with the defense-in-depth flag guard; no `needsSession()` gate (this
      runs compiled tests on App Automate, it does not drive a live device)
- ✅ 4.3 project-dir resolution from the explicit param → opened project → picker
- ✅ Cancellation hook WIRED to `TaskManager.isAborted()` (Layer 2 left it defaulted off)

**The port is code-complete. Nothing below has been verified live.** Every result above is
unit-level: nothing has run against a real router, a real Xcode project, or App Automate.
Before this ships, someone needs to (1) turn `xcuitestSupport` on server-side and confirm the
router advertises `xcuitest-test-automation` to a JetBrains client, and (2) drive a real build
on a macOS host with Xcode and BrowserStack credentials. The VS Code Espresso port found two
real bugs *only* on live infra — budget for that.

**Open follow-ups:**
- R3 (no macOS gating) is unchanged in spirit but softer here than on VS Code: the default
  command runner maps a missing binary to exit 127 with the error text rather than throwing,
  so a Windows/Linux user gets a clean tool failure instead of a crash. A real "XCUITest needs
  macOS" precondition is still worth its own ticket.
- Multi-scheme Xcode workspaces still resolve to the FIRST scheme — same documented limitation
  as VS Code.
- Espresso and Maestro remain unregistered; Layer 2's generic spine is ready for them.

## 1. Context & goal

XCUITest (native iOS test authoring: Swift, compiled into a `*-Runner.app`, run on
BrowserStack App Automate) works today **only on the VS Code surface**. The JetBrains
surface has none of it.

**What JetBrains has today:** live Appium mobile sessions only. The `"XCUITest"` strings
already in `jetbrains/` are Appium's iOS `automationName` capability
([MobileTypes.kt:70](jetbrains/src/main/kotlin/com/browserstack/testcompanion/mobile/MobileTypes.kt),
[MobileSession.kt:242](jetbrains/src/main/kotlin/com/browserstack/testcompanion/mobile/MobileSession.kt))
and page-source parsing comments. They are **not** native XCUITest authoring — do not
mistake them for partial coverage.

**Scope note — this is not an XCUITest-only gap.** Espresso and Maestro are absent from
JetBrains too. The entire native build → upload → run → poll layer is missing. Roughly
60% of the port (Layer 2 below) is framework-generic and pays for all three.

**No `llm_router` changes are needed.** The router side is complete and surface-agnostic:
`xcuitest-test-automation` (`src/prompts/skills/workflows/`), `xcuitest-scripting`
(`.../workflows/components/`), and the `framework?: "appium" | "espresso" | "xcuitest" |
"maestro"` field at `llm_router/src/shared/types.ts:265`. It gates on that field plus the
`xcuitestSupport` flag. This is single-repo work.

## 2. The blocker — read this first

[RouterApiClient.kt:581](jetbrains/src/main/kotlin/com/browserstack/testcompanion/api/RouterApiClient.kt)
builds the router mobile context with `appId`, `platform`, `appName`, and
`enableCameraMediaInjection` — **no `framework` field**.

The router only advertises the XCUITest skill and the `run_xcuitest_build` action when it
receives `mobile.framework === "xcuitest"`. JetBrains never sends it. Until Layer 1 lands,
every other layer is unreachable code: the model is never told the tool exists, so it never
calls it.

Ship Layer 1 as its own PR and verify the router starts advertising the skill before
committing to the rest.

## 3. The pipeline — reuse vs new

| Stage | JetBrains today | XCUITest needs | Port work? |
|---|---|---|---|
| 1 Detect | none — `framework` never set | read Xcode project + UI-test signal from disk | 🔴 new |
| 2 Observe | live Appium session (`get_page_source`) | **identical — reuse** | 🟢 none |
| 3 Authoring prompt | router-driven | **already exists router-side** | 🟢 none |
| 4 Validate inputs | none | Xcode project check + device-id normalization | 🔴 new |
| 5 Build | none | `xcodebuild build-for-testing` → `.ipa` + `tests.zip` | 🔴 new |
| 6 Upload | Appium single binary (`/app-automate/upload`) | `xcuitest/v2/{app,test-suite}` | 🔴 new |
| 7 Run | live WebDriver | submit-and-poll `xcuitest/v2/build` → `builds/{id}` | 🔴 new |
| 8 Fix loop | exists (`TestRunSummary` seam) | map build result into the same seam | 🟡 small |

**Design principles** (carried over from the Espresso plan — they still hold):

- **Additive, framework-routed.** Do not change the Appium path. Branch on framework.
- **XCUITest is still `testingPlatform: "app"`** → still routes to the router's mobile agent.
- **The run-result seam is sacred.** Downstream (fix loop, completion gate, telemetry) only
  needs `{ framework, passed, failed, outcome }`. Every new run path produces exactly that.
- **Port Layer 2 generic, not xcuitest-specific.** Same cost now, saves redoing it for
  Espresso and Maestro.

## 4. Layer 1 — Contract (unblocks everything)

**Est. 0.5 day.** Independently shippable and verifiable.

| # | Task | File (verified anchor) | Change | Acceptance |
|---|---|---|---|---|
| 1.1 | Flag key | [FeatureFlagsKeys.kt:162](jetbrains/src/main/kotlin/com/browserstack/testcompanion/services/FeatureFlagsKeys.kt) (append after `GATE_TEST_CASE_TAG_ADVISORY`) | Add `const val XCUITEST_SUPPORT: String = "xcuitestSupport"`. **camelCase wire key** — must equal `feature-flags.ts:52`, not snake_case. | Key present; matches the VS Code constant byte-for-byte. |
| 1.2 | Flag reader | new `services/XcuitestSupportFlag.kt`, mirroring [ParallelSessionsFlag.kt:24](jetbrains/src/main/kotlin/com/browserstack/testcompanion/services/ParallelSessionsFlag.kt) | `fun isXcuitestSupportEnabled(): Boolean` reading `ServiceHandlers.cachedFeatureFlags` via the safe-cast idiom (`as? JsonPrimitive`, never `jsonPrimitive` — it throws on a malformed backend value). Read at each decision point, never cached at construction, so a mid-session rollback takes effect without an IDE restart. | Returns `false` pre-`getAgents`; flips without restart. |
| 1.3 | Router contract field | [RouterApiClient.kt:581](jetbrains/src/main/kotlin/com/browserstack/testcompanion/api/RouterApiClient.kt) | Inside the `put("mobile", buildJsonObject { … })` block, emit `framework` when resolved. Omit when unset (non-breaking — the router defaults to `"appium"`). | Router receives `mobile.framework`; skill catalog includes `xcuitest-test-automation`. |
| 1.4 | Telemetry enum drift | [TestRunSummary.kt:11](jetbrains/src/main/kotlin/com/browserstack/testcompanion/terminal/TestRunSummary.kt) | JetBrains `TestFramework` stops at `JUNIT`; VS Code's union ([parse-test-run-summary.ts:4](src/services/test-run/parse-test-run-summary.ts)) already carries `espresso`, `xcuitest`, `maestro`. Add all three. The file's own docstring promises wire strings are byte-identical with VS Code "so the two clients land the same values in BigQuery" — this is a live drift, not new scope. | Enum matches the VS Code union; wire strings identical. |

## 5. Layer 2 — Generic native layer

**Est. 1 week.** Framework-parameterized; Espresso and Maestro reuse all of it.

| # | Task | Source (LOC) | Target | Notes |
|---|---|---|---|---|
| 2.1 | Artifact upload | [native-app-upload.ts](src/services/mobile/native-app-upload.ts) (170) | extend [MobileApiClient.kt:84](jetbrains/src/main/kotlin/com/browserstack/testcompanion/mobile/MobileApiClient.kt) | POST `/app-automate/{framework}/v2/{app,test-suite}`, parse `app_url` / `test_suite_url` (`bs://` prefix check). **Extend the existing client** — it already does OkHttp multipart + basic auth at line 152. Do not write a second HTTP client. **Surface the API error body**: an opaque "upload failed" on a 422 with a real reason cost a full debugging session on the VS Code side (see the comment at `native-app-upload.ts:123`). |
| 2.2 | Build run + poll | [native-app-run.ts](src/services/mobile/native-app-run.ts) (361) | new `mobile/NativeAppRun.kt` | POST `{framework}/v2/build` → `build_id`; poll `GET {framework}/v2/builds/{id}` (5s interval, 30min timeout) to terminal status; map to `TestRunSummary`. **Port the endpoint asymmetry verbatim** (`native-app-run.ts:28-43`): Espresso/XCUITest take no platform segment on the build POST, Maestro does — and the build-status GET takes none for any of them. Verified live under STM-1404; the spec says otherwise. Do not "symmetrize" it. |
| 2.3 | Result → seam mapping | `mapBuildResultToSummary` (`native-app-run.ts:190`) | same file as 2.2 | Prefer per-testcase counts nested at `sessions[].testcases.status.{passed,failed,error,timedout}`; fall back to session status, then top-level build status. Pure — unit-test it. |
| 2.4 | `no_tests_detected` messaging | `native-app-run.ts:332-338` | same file as 2.2 | Port the long "ran ZERO tests" message verbatim. It exists because the model read `no_tests_detected` as an ordinary test failure and burned six real device builds editing selectors on a suite that could never execute. Do not shorten it. |
| 2.5 | Framework registry | [native-frameworks.ts](src/services/mobile/native-frameworks.ts) (123) | new `mobile/NativeFrameworks.kt` | Per-framework leaves: `build`, `validate`, `defaultDevice`, `label`, `projectNameFallback`, `projectGuidance`, `normalizeDevices`, `extractArtifacts`. Kotlin sealed class or enum-with-fields. |
| 2.6 | Orchestrator | [native-app-orchestrator.ts](src/services/mobile/native-app-orchestrator.ts) (118) | new `mobile/NativeAppOrchestrator.kt` | validate → build → upload → run+poll. **Both fail-fast gates are load-bearing**: an invalid device id must be rejected *before* building and uploading, or App Automate 422s after all that work is already spent. Keep every stage injectable for tests. |
| 2.7 | Project name resolution | `resolveNativeProjectName` (`native-app-orchestrator.ts:32`) | same file as 2.6 | Always send a **named** project. Omitting it files the build under the account default, which 422s for project-scoped/RBAC accounts — common in enterprise orgs. |

## 6. Layer 3 — XCUITest leaves

**Est. 1 week.** 3.2 carries the risk.

| # | Task | Source (LOC) | Target | Notes |
|---|---|---|---|---|
| 3.1 | Input validation | [xcuitest-inputs.ts](src/services/mobile/xcuitest-inputs.ts) (158) | new `mobile/XcuitestInputs.kt` | `validateXcuitestProject` (needs a `.xcodeproj`/`project.yml` **and** a UI-test signal), `xcuitestProjectGuidance`, `normalizeXcuitestDevices` (`"<Device Name>-<osVersion>"`, version must be numeric). Pure — port the unit tests alongside. Easiest item here; do it first to establish the Kotlin idiom. |
| 3.2 | Build + package | [xcuitest-build.ts](src/services/mobile/xcuitest-build.ts) (409) | new `mobile/XcuitestBuild.kt` | **The hard one.** `xcodebuild -list -json` → scheme + `*UITests` target; conditional `xcodegen generate` (only when `project.yml` is newer than the `.xcodeproj`, or it's missing); unsigned `build-for-testing`; package `.app` → `app.ipa` via `Payload/`, `*-Runner.app` → `tests.zip`. See §8 R1 for the argv constraint. |
| 3.3 | Project picker | [xcuitest-project-picker.ts](src/services/mobile/xcuitest-project-picker.ts) (69) | new `mobile/XcuitestProjectPicker.kt` | Use the workspace if it validates, else prompt. [ReportImportHandler.kt](jetbrains/src/main/kotlin/com/browserstack/testcompanion/services/ReportImportHandler.kt) already has the exact `FileChooserDescriptorFactory.createSingleFolderDescriptor()` idiom that replaces `vscode.window.showOpenDialog` — copy it, including its off-EDT handling. |
| 3.4 | iOS detection | [detect-ios-framework.ts](src/services/mobile/detect-ios-framework.ts) (82) | new `mobile/DetectIosFramework.kt` | Returns `"xcuitest"` when an Xcode project **and** a UI-test signal (a `*UITests` dir, or a source that `import XCTest`) are present. Note the deliberate `looksLikeFile` filter when scanning one level deep — a legit directory named `App.UITests` carries a dot and must still be scanned. |
| 3.5 | Framework resolution order | [resolve-mobile-framework.ts](src/services/mobile/resolve-mobile-framework.ts) (135) | new `mobile/ResolveMobileFramework.kt` | Native-first ordering. XCUITest-only today, but port the full ordered chain — the ordering is exactly what broke under STM-1404 when a Maestro seed pre-empted the native detectors it documented itself as deferring to. Feeds Layer 1's `framework` field. |
| 3.6 | XCUITest wrapper | [xcuitest-orchestrator.ts](src/services/mobile/xcuitest-orchestrator.ts) (59) | new `mobile/XcuitestOrchestrator.kt` | Thin — fixes framework to `"xcuitest"` and delegates to 2.6. |

## 7. Layer 4 — Tool wiring

**Est. 2 days.**

| # | Task | File (verified anchor) | Change | Acceptance |
|---|---|---|---|---|
| 4.1 | Action enum | [MobileActionType.kt:52](jetbrains/src/main/kotlin/com/browserstack/testcompanion/mobile/MobileActionType.kt) (append after `INJECT_MEDIA`) | `RUN_XCUITEST_BUILD("run_xcuitest_build")` — wire string must match `src/shared/mobile-action-types.ts`. | Action parses from a router tool call. |
| 4.2 | Handler case | [MobileActionHandler.kt:180](jetbrains/src/main/kotlin/com/browserstack/testcompanion/mobile/MobileActionHandler.kt) (1556 LOC; follow the `UPLOAD_APP` dispatch shape) | Port [mobile-action-handler.ts:648](src/core/task/tool-handlers/mobile-action-handler.ts). **Keep the defense-in-depth flag guard** — the router only advertises the action when the flag is on, but a stale or forged call must not run a build for an un-rolled-out user. Then: resolve project dir → parse `devices` (comma-split, default to the registry's `defaultDevice`) → call 3.6. | Flag off ⇒ refusal, no build. Flag on ⇒ full run. |
| 4.3 | Workspace dir threading | `MobileActionHandler` context | JetBrains equivalent of VS Code's `requireWorkspaceProjectDir(params.project_dir, context.cwd)` — the project dir must reach the handler. | Handler resolves the Xcode project without an explicit param. |

## 8. Risks & open questions

- **R1 — argv, never a shell string.** Every `xcodebuild` / `xcodegen` / packaging step in
  `xcuitest-build.ts` runs as an argv array through `execFile` with **no shell**, so scheme,
  target, and app names can never be interpreted as shell syntax. Kotlin's `ProcessBuilder`
  gives this naturally (`ProcessBuilder(listOf(...))`) — but the packaging step in particular
  was deliberately de-`&&`-chained into sequenced argv steps. Do not collapse it back into a
  shell string. Existing `ProcessBuilder` usage lives in `checkpoints/ShadowGitTracker.kt` and
  `terminal/StandaloneTerminalProcess.kt`.
- **R2 — `MAX_BUFFER` / chatty output.** `xcodebuild` is extremely verbose (VS Code allows 20 MB
  so failure classification isn't truncated). JetBrains' `StandaloneTerminalProcess` uses reader
  threads; confirm nothing caps output below that before relying on `isXcodebuildBuildFailure`.
- **R3 — no macOS gating anywhere.** Neither surface guards on `process.platform` / OS. On
  Windows or Linux, `xcodebuild` simply fails with a non-zero exit. This is a **pre-existing
  VS Code gap**, not something the port introduces. Match current behaviour for parity and
  file the graceful-failure fix as its own ticket — JetBrains has proportionally more
  Windows users, so it will surface more often here.
- **R4 — Surface Parity Gate.** A PR touching only `jetbrains/` host logic trips
  `.github/workflows/surface-parity-gate.yml`, which wants `vs` and `cli` too. This port needs
  `Parity-Skip: vs cli STM-XXXX` on **its own bare line** — per the repo CLAUDE.md, the gate
  matches surface names word-wise against the same line, so justification prose containing
  another surface's name silently over-waives. Put explanations on separate lines.
- **R5 — do not re-derive the build recipe.** The unsigned-build pipeline
  (`CODE_SIGNING_ALLOWED=NO` / `CODE_SIGNING_REQUIRED=NO` / empty `CODE_SIGN_IDENTITY`,
  BrowserStack resigns on upload) is already proven end-to-end on the VS Code side. Port it
  verbatim; re-deriving code signing from scratch is a multi-day detour.
- **Open — multi-scheme workspaces.** `resolveXcuitestScheme` picks the *first* scheme and the
  first `*UITests` target. VS Code documents non-standard multi-scheme workspaces as an
  unhandled follow-up. Inherit the same limitation; don't try to solve it during the port.
- **Open — E2E hardware.** A real verification run needs macOS + Xcode + BrowserStack creds.
  The Espresso port found two real bugs *only* on live infra (a dependency-parsing miss and the
  nested per-testcase count shape) — budget for a live run, don't stop at unit tests.

## 9. Testing

- JetBrains unit tests live in `jetbrains/src/test/kotlin/…` (see the existing
  `mobile/PageSourceCompressorTest.kt`, `mobile/MobileSelectorParserTest.kt`).
- Port the pure logic **with** its VS Code test cases: device normalization (3.1), project
  validation (3.1), scheme resolution + `isXcodebuildBuildFailure` (3.2), detection (3.4),
  resolution ordering (3.5), result→seam mapping (2.3), endpoint derivation incl. the Maestro
  asymmetry (2.2).
- Keep IO in thin shells and unit-test the pure core — that's what makes the VS Code modules
  testable without a real Xcode toolchain, and it's the property most easily lost in a port.
- Use `/jetbrains-verify` for plugin-level E2E once wired.

## 10. Execution order

1. **Layer 1 as its own PR** (1.1 → 1.2 → 1.3 → 1.4). Verify the router advertises
   `xcuitest-test-automation` to a JetBrains client. **Stop and confirm before continuing.**
2. Layer 3.1 (pure, establishes the Kotlin porting idiom) → 3.4 → 3.5.
3. Layer 2 (2.1 → 2.2/2.3/2.4 → 2.5 → 2.6/2.7).
4. Layer 3.2 (the risky one) → 3.3 → 3.6.
5. Layer 4 (4.1 → 4.2 → 4.3).
6. Live E2E on real hardware + a real App Automate run.

**Total est. ~2.5–3 engineer-weeks**, excluding live-hardware debugging. Layer 2 is ~60% of
the work and is fully reusable for the Espresso and Maestro ports.
