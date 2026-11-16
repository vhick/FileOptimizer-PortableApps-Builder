# b1r4 fix — Portable-Package-Builder running-exe path

The 2026-11-16 b1r2 hosted Windows runner **successfully** downloaded and SHA-256 verified official release 18.10.2904, verified the matching source archive, compiled the launcher, and validated a real ZIP. It stopped when pinned `Portable-Package-Builder@v1.0.0` rejected `running-exe: App/FileOptimizer/FileOptimizer64.exe` because that action explicitly requires a Windows relative path with backslashes. b1r4 passes `running-exe: 'App\FileOptimizer\FileOptimizer64.exe'`. A regression test now guards this exact action contract. This fixes the *observed argument failure*; installer creation, installation/upgrade behavior, and interactive Windows portability remain unverified until the b1r4 workflow is run and acceptance tests pass.

In the failed b1r2 run, the ZIP was uploaded as the workflow artifact `FileOptimizer-Validated-ZIP-InstallerOrReleaseFailed`, artifact ID 14204413716, run 43822539246. The archive upload SHA-256 is NOT the same as the inner FileOptimizer portable ZIP SHA-256. The user can download that ZIP from the GitHub run's **Artifacts** panel; it has not been runtime-tested.

Full application recompilation from source is **not needed** for the selected PORTABLEAPPS mode: the original developer supplies a portable full archive and a matching source snapshot. The main GUI source requires Embarcadero C++ Builder 13.2 Florence and many third-party optimization tools. Continue using hash-verified official binaries unless a source patch proves necessary to satisfy a particular functional/portability requirement.

---

# SourceForge HTTP 403 handling (verified in b1r2 Windows build)

The first GitHub Actions run failed before application downloads when the HTML file-listing endpoint returned **HTTP 403**. For `version=latest`, b1r4 checks the official developer history (`nikkhokkho.sourceforge.io`) if that specific endpoint fails with 403, and selects only an exact previously SHA-256-pinned SourceForge release whose developer major/minor version matches. It never silently uses an older major/minor release or SVN HEAD. Official SourceForge CDN endpoints are used for downloads, and each file must exactly match an audited SHA-256. If an endpoint blocks CI, another SourceForge-operated CDN endpoint is tried; checksum mismatch stops immediately.

**Practical first rerun:** the workflow now defaults to `version=18.10.2904`, which bypasses HTML release discovery entirely. Use `latest` only to exercise the live discovery path. The developer-history fallback succeeded in the uploaded b1r2 GitHub Windows build, but in the uploaded b1r3 run the developer site returned HTTP 500. The new default avoids both metadata dependencies for the already-audited release. SHA-256-pinned archives are still mandatory, so a future unknown release will fail safely until audited.

Pinned shared actions are now referenced by immutable SHA values observed in the user's successful runner-action-resolution log while preserving v1.0.0 and v1.1.1 identities.

---

# FileOptimizer Community PortableApps Builder — b1r4

**Selected product:** PORTABLEAPPS only; Windows x64. This is an independent community build of **FileOptimizer**, not an official PortableApps.com release. The upstream SourceForge project `nikkhokkho` contains several programs, but its actively maintained SVN `trunk/FileOptimizer` tree matches the current official FileOptimizer portable distribution.

**What the kit does:** An unattended GitHub Actions job resolves a verified stable SourceForge **FileOptimizerFull.7z.exe** plus matching **FileOptimizerSource.7z**, verifies vendor-published SHA-256 values, extracts without running either archive, examines the release source for the audited storage/shell patterns, stages the developer's authentic 64-bit executable and complete `Plugins64`, compiles a genuine community `FileOptimizerPortable.exe` launcher using MSVC, builds and tests an independent ZIP, builds a PortableApps-style `.paf.exe` using **vhick/Portable-Package-Builder@v1.0.0** (`custom-nsis`), validates the installer PE/hash, and previews (or explicitly publishes) the two files using **vhick/portable-release-publisher@v1.1.1**.

**Never** mistake a successful CI build for real Windows GUI or install/upgrade testing. The launcher compiled and its ZIP passed CI validation in b1r2; the b1r4 installer workflow and real Windows runtime remain unverified. It is a **test candidate**, not a certified PortableApps.com package. See `docs/VALIDATION.md` and `docs/OPEN-ISSUES.md`.

## Contents

```text
.github/workflows/build.yml       Windows hosted build, installer, release
scripts/resolve.py               SourceForge stable version + official SHA256 resolver
scripts/verify_actions.py        Checks exact published pinned action.yml interfaces and commits
scripts/build.ps1                Full Windows compilation and staging orchestration
scripts/stage.py                 FileOptimizer-specific source-check, plugin and original icon staging
scripts/package.py               Validated root layout, compiled PE and independent ZIP
scripts/verify_installer.py      Separate custom-NSIS installer PE/hash checks
launcher/FileOptimizerPortable.cpp  REAL native Win64 launcher source
LICENSE-LAUNCHER.txt            Independent launcher MIT; upstream remains AGPL
tests/test_static.py             16 executable static unit tests
docs/AUDIT.md                    Upstream findings and bounded storage decisions
docs/VALIDATION.md               Honest evidence matrix, live Windows acceptance steps
docs/OPEN-ISSUES.md              Unverified behavior and fail-safe limitations
docs/SETUP.md                    GitHub Desktop + first release + data-safe upgrades
```

## How it works

Upstream's official portable application already writes `FileOptimizer.ini`/`.log` near its own EXE when its directory is writable. Rather than redirect every Windows profile folder, the compiled launcher temporarily stages these two known files under `App/FileOptimizer`, saves them back to `Data/Settings` after complete application-and-plugin shutdown, and retains verified backups. If an interrupted run is detected, it recovers private sidecars before the next launch. For child processes only, `TEMP`/`TMP` point to `Data/RuntimeTemp` (which also controls FileOptimizer's source-confirmed WebView2 temp setting). The launcher snapshots/restores exactly one source-confirmed HKCU browser-emulation value, conditioned on the value matching the version written by upstream. It never deletes arbitrary AppData, user files, or shell trees.

**Important limitations:** An interrupted run followed by an installer upgrade **before a recovery launch** could strand settings under the previous App folder. This must be tested and may need a protective installer change in the shared Package Builder. Other plugins may make incidental Windows/OS-managed writes that have not been runtime observed. See `docs/OPEN-ISSUES.md`. Keep backups of Data and do not upgrade while a recovery marker is present.

## Quick start

1. Use GitHub Desktop to create a separate public repository named `FileOptimizer-PortableApps-Builder` (or choose private for a specific legal/licensing reason). **Do not fork SourceForge or the two shared builder actions.**
2. Use **Repository → Show in Explorer** to open your local GitHub repo directory.
3. Extract the **contents** of this kit ZIP to the repository root, including hidden `.github`.
4. Commit the files and **Publish repository** in GitHub Desktop.
5. GitHub website → repository **Actions** → **FileOptimizer PortableApps - Verified Build** → **Run workflow**. First run: leave `version=18.10.2904` (now the prefilled default) and `publish=false`. Use `version=latest` only when you want a live stable-release check; that check may fail safely if SourceForge metadata is unavailable.
6. In the first run, study the `Verify SourceForge assets...`, `Build independent PortableApps-style installer`, `Publisher dry-run` stages.
7. Run again with `publish=true` **only after reviewing the static provenance and licensing assumptions**. The validated files appear in the calling repository's **Releases**, together with publisher-generated checksums.
8. Extract the ZIP as its own `FileOptimizerCommunityPortable` folder or use the community `.paf.exe` installer. Run the root **FileOptimizerPortable.exe**, not the upstream internal EXE.
9. To upgrade, exit FileOptimizer and all plugins; confirm `Data/Control/active.run` and `Data/Control/registry.journal` are absent. Make a full copy of `Data` and any private `App/FileOptimizer/FileOptimizer.ini`/`.log` recovery files **before** installing a new version. Never overwrite or delete `Data`.
10. To roll back, close the app, back up `Data`, restore the previous `App`/`Other`/launcher binaries, and keep Data unchanged. Older upstream versions may not read newer INI settings; restore the matching Data backup if needed.

Detailed beginner instructions: `docs/SETUP.md`.

## Revision identity

Builder b1r4, portable package revision r1. Stable versions use **numeric** three-component SourceForge folder versions (e.g. `18.10.2904`). An exact release source-archive SHA-256 is recorded as the source identity instead of inventing a Git SHA for SourceForge's SVN/release snapshot. Every package also includes the original version-matched 7z source archive, launcher source, package identity JSON and developer icon.

Pinned actions: `vhick/Portable-Package-Builder@v1.0.0` and `vhick/portable-release-publisher@v1.1.1`. Exact `action.yml` interfaces were inspected for the pinned tags as of the build-kit creation date; CI also resolves and records tag commits. The workflow uses the verified **immutable commit SHA** for each action; the verification script also ensures neither pinned tag has moved. See `docs/OPEN-ISSUES.md`.

## Source and licenses

Upstream: https://sourceforge.net/p/nikkhokkho/code/HEAD/tree/  
Official distribution: https://sourceforge.net/projects/nikkhokkho/files/FileOptimizer/  
Author documentation: https://nikkhokkho.sourceforge.io/?page=FileOptimizer  
Official PortableApps format: https://portableapps.com/development/portableapps.com_format

FileOptimizer: **AGPL** (see upstream author). The developer's full binary archive contains third-party compression programs whose licenses may differ. The pinned official package is reused without patching vendor binaries; complete independent audit of all plugin redistribution terms remains an open issue. The independently compiled launcher and builder scripts are MIT-licensed, not the upstream app. Do not imply the program is code signed or officially certified.

**The uploaded b1r2 runner produced a compiled application package ZIP and preserved it as a workflow artifact, but did not generate an installer or release. This chat creates only the revised builder kit; b1r4 still needs a new hosted Windows workflow run.** This ZIP is the updated source builder kit; the next GitHub run must validate the corrected installer configuration.

## b1r4 resolver incident / safe first-run change (November 16, 2026)

Uploaded b1r3 run `logs_118678794995.zip` requested `latest`. The SourceForge HTML listing returned HTTP 403 and the developer-history fallback returned HTTP 500, so the build stopped before downloading assets. This is NOT a launcher or NSIS compiler error. b1r4 sets the GitHub workflow's default `version` to the independently SHA-256-pinned stable `18.10.2904`; there is no network metadata lookup for explicit versions. `latest` remains available and continues to fail closed if both official metadata sources are inaccessible. No invented alternate API endpoints, mirror identities or weaker hashes were introduced. Binaries are still obtained solely from controlled SourceForge download endpoints and checked against the pinned SHA-256.

On the next run, leave `version=18.10.2904`, set `publish=false`, and inspect whether the b1r3 installer-path correction now permits shared `custom-nsis` generation. **Neither b1r4 GitHub execution nor Windows runtime portability has been tested here.**
