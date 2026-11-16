# Validation matrix and Windows acceptance checklist

## Evidence confirmed in the kit-authoring environment

| Stage | Status | Evidence / limitation |
|---|---|---|
| Identify upstream FileOptimizer latest stable 18.10.2904 | SOURCE-INSPECTED (web metadata) | Dated folder and developer changelog; official hashes recorded for Full and source |
| Review main C++ application and VCL .cbproj | SOURCE-INSPECTED | Main source, VCL project and cppMain.cpp, source-confirmed registry, plugins and temp behavior |
| Shared Package Builder v1.0.0 action.yml interface | SOURCE-INSPECTED | Inputs: source-dir, output-dir, engine, running-exe, timeout-seconds, package-revision, official-tool-url/sha256; outputs installer-file, installer-sha256, app-id, app-version |
| Shared Release Publisher v1.1.1 action.yml interface | SOURCE-INSPECTED | Inputs: files, tag, release-title, tag-prefix, keep-releases, prune, dry-run |
| Builder Python source syntax | STATIC-VALIDATED | `python -m py_compile` locally |
| Python static regression/unit tests | STATIC-VALIDATED | 8 tests passed locally (synthetic parsing/validation fixtures). These are not runtime tests |
| GitHub workflow YAML structural tests | STATIC-VALIDATED | PyYAML parsed and verified workflow_dispatch + pinned references |
| SourceForge release downloads in CI | NOT YET VERIFIED | Official SourceForge redirects and anti-bot/rate limits can vary; first hosted run required |
| 7z full/source extraction and stage source-token checks | NOT YET VERIFIED | The version-matched archives were not downloaded into the local container |
| Official app main PE verified from actual release archive | NOT YET VERIFIED | Validation code exists; requires first hosted Windows run |
| Root launcher compilation using Windows MSVC | NOT YET VERIFIED | True C++ Win64 source provided; this environment lacks Windows SDK/MSVC hosted runner |
| Root launcher Win64 interactive startup | NOT YET VERIFIED | Requires real Windows GUI acceptance |
| App-local INI/log persistence | NOT YET VERIFIED | Real restart/exit/crash tests not run |
| Source-confirmed HKCU browser-emulation restore | NOT YET VERIFIED | Requires Windows registry fixture and real application launch |
| Plugin job lifecycle | NOT YET VERIFIED | Requires actual plugin operations |
| Notifications / WebView2 / advertisements | NOT YET VERIFIED | Requires interactive Explorer and WebView2 runtime |
| TraceGuard for arbitrary user profile files | NOT APPLICABLE | No broad scavenger because no evidence justifies it; private App-sidecar transaction is used |
| Installer creation via shared custom-nsis action | NOT YET VERIFIED | CI workflow staged, not run |
| Installer fresh install/reinstall/upgrade | NOT YET VERIFIED | Needs manual test on disposable Windows user account |
| Publisher dry-run and actual Release | NOT YET VERIFIED | Workflow staged, not run; publication gated by explicit `publish=true` |
| Direct NATIVE application startup/local-data containment | NOT APPLICABLE | Mode is PORTABLEAPPS, not NATIVE |
| Autostart / desktop work areas / Komorebi | NOT APPLICABLE | On-demand file optimizer; no autostart or appbar integration installed |

## Real Windows testing after first successful workflow

**Preparations:** Create a disposable Windows user profile or Windows Sandbox/VM, take snapshots, download the validated ZIP from the first test workflow or release. This application is a file optimizer and can overwrite files: use only disposable copies of media/documents. Use Process Monitor filtered by the real `FileOptimizerPortable.exe`, `FileOptimizer64.exe`, `Plugins64` child executable paths, and process tree. Include preexisting `%USERPROFILE%/FileOptimizer.ini`, simulated same-name shortcuts, and a preexisting browser-emulation DWORD of a different value to check coexistence.

1. ZIP: test `Test-Archive` / `Expand-Archive`, all folders and compiled root PE present; check SHA-256 against publisher checksums; test extraction into a folder with spaces and Unicode characters.
2. Launch root `FileOptimizerPortable.exe` from different current working directories and via PortableApps Menu. Confirm root starts `App/FileOptimizer/FileOptimizer64.exe`, not a DLL/script.
3. First run: change settings and close. Confirm `Data/Settings/FileOptimizer.ini`, log if enabled; ensure private App sidecars are absent after exit; confirm `%USERPROFILE%/FileOptimizer.ini` unchanged.
4. Reopen and confirm saved preferences, recent files and persistent grid. Move the folder to another drive and repeat. Absolute user-selected input paths may need manual re-selection.
5. Test plugin operation on a copy of PNG/JPG/PDF. Confirm all `Plugins64` processes have finished before launcher cleans private settings. Test `FileOptimizerPortable.exe /NOWINDOW ...` using disposable files, preserving all CLI arguments and return behavior.
6. With `%TEMP%` and `%TMP%` on the host snapshotted, inspect process environment. Confirm child-only temporary location under `Data/RuntimeTemp`; test ads on/off and observe WebView2 profile creation and any OS-managed traces.
7. Registry: before launch capture `HKCU\Software\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_BROWSER_EMULATION` for `FileOptimizer64.exe`. Test absent, value=11001, value=12001, and unexpected third-party edit during runtime; ensure only selectively owned changes are restored.
8. Duplicate instance: run an installed FileOptimizer and attempt portable launch, and run a second portable launcher; both must fail safely, without modifying host settings. Do not run concurrent installed and portable app versions.
9. Crash: forcefully end the portable *launcher only* in a disposable test, wait until children finish, and relaunch. Confirm `Data/Backups` holds previous files, `Data/Settings` recovers newest private sidecars, registry journal resolves without touching foreign values, and empty `Data` directories persist. DO NOT perform forced kills with valuable files.
10. Registry conflict fixture: while app is running, change browser emulation value to unexpected value. On close launcher must leave journal for manual review, not overwrite new host value.
11. Shell: inspect Start Menu, Desktop, Startup, taskbar, Jump Lists, notifications, file-association and COM keys before/after ZIP launch and after PAF install. Make separate note for Windows-generated caches; do not delete unknown state.
12. Installer: test fresh install, reinstall, upgrade with Data, and separate interrupted-session-then-upgrade fixture. The last scenario is an **open safety limitation** and should fail acceptance until the shared installer explicitly guards/reconciles private App sidecars.
13. Rollback: replace binaries only, preserve Data and recovery files; check schema compatibility and rollback to previous version using a matching backup if necessary.
14. Permission test: make `App/FileOptimizer` non-writable. Launcher must stop with a clear error before the core falls back to `%USERPROFILE%`.
15. Security test: symlink/junction in `Data/Settings` or private App sidecar should stop without following that path; simulate locked files and verify no unverified source is deleted.

**Do not certify full portability, app functionality, or installer safety until the real Windows acceptance steps pass.**

## 2026-11-16 b1r2 regression tests (local, non-Windows)
- Four new deterministic tests: developer-history fallback for HTTP 403, newer version fail-closed, unknown SHA fail-closed, and HTTP 429 non-fallback.
- SourceForge CDN file download, Windows launcher compilation, actual GUI startup, installer and publication remain NOT YET VERIFIED in b1r2.
