# Known blockers, risks and next tests

## Blockers to calling b1r2 production-ready

1. **No hosted Windows build or manual runtime evidence yet.** The kit is downloadable source, not a guaranteed successful CI product. MSVC compilation, 7-Zip SFX extraction, asset layout, original icon extraction, installer action behavior, and publisher dry-run must all be checked on the first workflow run.
2. **Crash immediately followed by a PAF installer update without recovery:** FileOptimizer may have recently changed `App/FileOptimizer/FileOptimizer.ini` or `.log`, while `Data/Settings` has an older copy. The root launcher normally recovers those private files on its next run; the shared installer may replace the old App directory *before* that next run. The pending marker survives in `Data`, but old App-side files might be removed. **Do not upgrade while `Data/Control/active.run` exists.** This is a real unfinished contract requirement. It may need a narrowly scoped new pre-install recovery/abort feature in the shared Package Builder rather than duplicating installer code in this kit.
3. **Registry restoration concurrency:** Upstream always writes `FileOptimizer64.exe=11001` to HKCU Internet Explorer browser-emulation feature controls. Launcher restores only if the value still exactly matches that write, preserving unexpected edits. Duplicate installed-app detection uses a source-confirmed named mutex, but unexpected concurrent software edits remain a tradeoff. When conflict is detected, launcher leaves a journal and refuses further unsafe cleanup.
4. **Full plugin audit:** FileOptimizer ships many third-party tools; not every child writeset, programmatic error behavior, and redistribution obligation has been audited. The upstream developer's official distribution is retained, but this does not prove every third-party license permits independent republishing. Release after confirming bundled notices and legal obligations.
5. **Immutable shared action references:** Both pinned shared action versions use immutable SHA references proven in the uploaded GitHub Actions runner log; separate verification still checks their published tag and action.yml. If the action owner retags a version, the verifier fails safely.
6. **External Windows activity:** Recycle Bin, Windows shell caches, Windows WebView2/IE/notifications and plugin subprocesses can create Windows-managed or intentional host traces. There is no defensible claim of zero traces. Do not delete unknown data or disable notifications just to reduce trace counts.
7. **Target platform:** This kit intentionally packages only x64 Windows (`FileOptimizer64.exe`, `Plugins64`). A separate proven x86 workflow would be needed for legacy 32-bit Windows, rather than mislabeling this x64 compiled root launcher.
8. **Interactive installer test missing:** CI validates a real `.paf.exe` PE and SHA-256, but that is not proof that installation, upgrade, rollback, and Data preservation work. Run the documented Windows acceptance plan.

## SourceForge retrieval policy

- The SourceForge project files page is the **preferred** stable release discovery source, not SVN trunk `HEAD`. GitHub-hosted HTML requests may receive HTTP 403; b1r2 instead checks the official developer release history against the exact-version, SHA-256-pinned manifest. An unknown version or unavailable developer history fails closed.
- Download exactly two developer files for the same stable folder: Full SFX, and Source 7z.
- Use audited exact-release SHA-256 values pinned for **18.10.2904**. The SourceForge `/download` page streams a large archive, not a reliable HTML checksum API. All unknown versions fail closed until independently audited manifest hashes are added.
- Do not trust a SourceForge folder label by itself; compute the full download digest and compare it. Do not execute the SFX or upstream installer.
- Record source archive SHA, binary archive SHA, actual main EXE SHA, builder revision, package revision, shared action refs and their dynamically resolved commits.
- SourceForge official portable releases use numeric versions such as 18.10.2904; no SVN commit SHA corresponds to the uploaded binary without additional upstream evidence.

## Troubleshooting by error

| Error in workflow | Meaning and safe action |
|---|---|
| `SourceForge metadata error 403` | b1r2 checks the official developer release history and exact SHA-256-pinned version; if that page is blocked, use explicit `18.10.2904` until access is restored. Do not use SVN HEAD. |
| `Unable to verify official SHA-256` | New release's hash page could not be verified. Stop; inspect the developer page before extending trusted hash mapping. |
| `Source storage/shell assumptions changed` | Upstream changed audited code; investigate current `cppMain.cpp` and adapt the launcher rather than bypassing the check. |
| `Expected one vendor FileOptimizer64.exe alongside Plugins64` | Archive structure changed; inspect with 7-Zip and update application-specific staging. |
| `Genuine original FileOptimizer.ico was not found` | Original author icon source unavailable; do not invent a replacement or steal an unrelated icon. |
| `Native PE root launcher compilation failed` | Inspect MSVC output; do not publish ZIP/installer. |
| `Independent ZIP validation failed` | Read package validator output; do not build or publish installer. |
| `Installer validation failed` | PAF action produced no valid `.paf.exe` or mismatched checksum; stop publication. |
| `Registry recovery is unresolved` | Launcher deliberately retained unexpected host state. Inspect `Data/Control/registry.journal` and registry manually; never delete unknown values. |
| `A plugin or browser process has not exited` | Leave session files intact, close plugins safely, then retry the launcher. |

## Update/rollback limits

**Never erase Data.** For recovery, preserve the entire `Data/` tree including empty folders, temp/browser caches, `Backups`, `Control` and `Settings`, and preserve any still-live private files under `App/FileOptimizer` if `active.run` exists. Do not upgrade during a running operation. The shared custom NSIS installer is pinned and its actual cross-version behavior must be validated; if upgrade reconciliation is not supported, safely use ZIP extraction after backing up data and completing recovery.

## Actual uploaded-run evidence (2026-11-16)
- GitHub runner completed checkout, Python setup, 8 static tests and shared-action verification.
- **Failure:** HTTP 403 from `https://sourceforge.net/projects/nikkhokkho/files/FileOptimizer/` in `resolve.py` while `version=latest`. No binary download or launcher compilation occurred.
- b1r2 adds a developer-history-verified exact-release fallback for HTTP 403, plus SourceForge-operated CDN failover and SHA-256 enforcement.
- This is **not yet confirmed** on the hosted Windows runner. If all official download endpoints fail, there is no safe magic workaround; further SourceForge access investigation is required.
