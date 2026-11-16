# FileOptimizer Community PortableApps Builder — b1r1

**Selected product:** PORTABLEAPPS only; Windows x64. This is an independent community build of **FileOptimizer**, not an official PortableApps.com release. The upstream SourceForge project `nikkhokkho` contains several programs, but its actively maintained SVN `trunk/FileOptimizer` tree matches the current official FileOptimizer portable distribution.

**What the kit does:** An unattended GitHub Actions job downloads the most recent stable SourceForge **FileOptimizerFull.7z.exe** plus matching **FileOptimizerSource.7z**, verifies vendor-published SHA-256 values, extracts without running either archive, examines the release source for the audited storage/shell patterns, stages the developer's authentic 64-bit executable and complete `Plugins64`, compiles a genuine community `FileOptimizerPortable.exe` launcher using MSVC, builds and tests an independent ZIP, builds a PortableApps-style `.paf.exe` using **vhick/Portable-Package-Builder@v1.0.0** (`custom-nsis`), validates the installer PE/hash, and previews (or explicitly publishes) the two files using **vhick/portable-release-publisher@v1.1.1**.

**Never** mistake a successful CI build for real Windows GUI or install/upgrade testing. b1r1 has static tests but no verified Windows builds yet. It is a **test candidate**, not a certified PortableApps.com package. See `docs/VALIDATION.md` and `docs/OPEN-ISSUES.md`.

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
tests/test_static.py             8 executable static unit tests
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
5. GitHub website → repository **Actions** → **FileOptimizer PortableApps - Verified Build** → **Run workflow**. First run: `version=18.10.2904` and `publish=false`. If successful, try `version=latest`.
6. In the first run, study the `Verify SourceForge assets...`, `Build independent PortableApps-style installer`, `Publisher dry-run` stages.
7. Run again with `publish=true` **only after reviewing the static provenance and licensing assumptions**. The validated files appear in the calling repository's **Releases**, together with publisher-generated checksums.
8. Extract the ZIP as its own `FileOptimizerCommunityPortable` folder or use the community `.paf.exe` installer. Run the root **FileOptimizerPortable.exe**, not the upstream internal EXE.
9. To upgrade, exit FileOptimizer and all plugins; confirm `Data/Control/active.run` and `Data/Control/registry.journal` are absent. Make a full copy of `Data` and any private `App/FileOptimizer/FileOptimizer.ini`/`.log` recovery files **before** installing a new version. Never overwrite or delete `Data`.
10. To roll back, close the app, back up `Data`, restore the previous `App`/`Other`/launcher binaries, and keep Data unchanged. Older upstream versions may not read newer INI settings; restore the matching Data backup if needed.

Detailed beginner instructions: `docs/SETUP.md`.

## Revision identity

Builder b1r1, portable package revision r1. Stable versions use **numeric** three-component SourceForge folder versions (e.g. `18.10.2904`). An exact release source-archive SHA-256 is recorded as the source identity instead of inventing a Git SHA for SourceForge's SVN/release snapshot. Every package also includes the original version-matched 7z source archive, launcher source, package identity JSON and developer icon.

Pinned actions: `vhick/Portable-Package-Builder@v1.0.0` and `vhick/portable-release-publisher@v1.1.1`. Exact `action.yml` interfaces were inspected for the pinned tags as of the build-kit creation date; CI also resolves and records tag commits. Their references remain **mutable tags**, not immutable SHAs. See `docs/OPEN-ISSUES.md`.

## Source and licenses

Upstream: https://sourceforge.net/p/nikkhokkho/code/HEAD/tree/  
Official distribution: https://sourceforge.net/projects/nikkhokkho/files/FileOptimizer/  
Author documentation: https://nikkhokkho.sourceforge.io/?page=FileOptimizer  
Official PortableApps format: https://portableapps.com/development/portableapps.com_format

FileOptimizer: **AGPL** (see upstream author). The developer's full binary archive contains third-party compression programs whose licenses may differ. The pinned official package is reused without patching vendor binaries; complete independent audit of all plugin redistribution terms remains an open issue. The independently compiled launcher and builder scripts are MIT-licensed, not the upstream app. Do not imply the program is code signed or officially certified.

**No app binaries, installer, ZIP package or public release has been generated by this chat.** This ZIP is the actual downloadable source builder kit; the GitHub workflow is the first possible Windows compilation and distribution test.
