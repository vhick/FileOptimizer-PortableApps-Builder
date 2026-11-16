# FileOptimizer source-level packaging audit — 2026-11-16

## Upstream identity and design

- SourceForge project: `nikkhokkho` (multiple older utilities); active SVN source: `trunk/FileOptimizer`. SVN mainline was at revisions around r1906 when checked; this changing number **is not a stable release identity** and is NOT used for packaging.
- Latest stable developer distribution observed: **FileOptimizer 18.10.2904** (18.10, 2026-11-15). Distribution files: `FileOptimizerFull.7z.exe` (~117.7 MB), `FileOptimizerSource.7z` (~5.1 MB), and separate NSIS `FileOptimizerSetup.exe` (~128.9 MB). Select Full (7z SFX), NOT Setup.
- Official SHA-256 for 18.10.2904 Full: `9813d98e5c868aadd717a487b106906064948483e9394e545fa7cc412d6f1397`.
- Official SHA-256 for 18.10.2904 source: `c05cb949700d2ab2077dd6eaea2bf9b53146366ae23623780c4ec9fb31ada676`.
- Source is Embarcadero **C++ Builder 13.2 Florence**, **VCL** Win32/Win64x, plus 32/64-bit third-party plugin executables. The main GUI project is `FileOptimizer.cbproj`. That proprietary IDE/toolchain is NOT silently installed or called by this kit: the PORTABLEAPPS branch is permitted to reuse a developer-provided official portable release. The root launcher alone is rebuilt using Microsoft's hosted Windows toolchain.
- Project is AGPL; dependencies in the Full archive have varying provenance/license. A manual complete third-party legal review is needed before community redistribution.
- Stable version resolution uses numbered SourceForge release folders; excludes beta/non-numeric labels and sorts numerically. Uses matching, hashed official source archive, not SVN HEAD.

## Findings table

Evidence labels: **SOURCE-INSPECTED** applies to pages showing actual source; **DOCUMENTATION-CONFIRMED** to author's project FAQ; **INFERRED** indicates plausible but not proven runtime behavior. No line below claims ProcMon observation.

| Finding | Source evidence | File/registry path | Component | NATIVE remedy | PORTABLEAPPS remedy | Data safety | Functionality tradeoff | Acceptance test | Limitation |
|---|---|---|---|---|---|---|---|---|---|---|
| Settings/local log | Author FAQ; `cppMain.cpp` GetIni/SetIni | `FileOptimizer.ini`, `FileOptimizer.log` beside FileOptimizer64.exe; if unwritable fallback `%USERPROFILE%` | Application | N/A (not selected) | Write probe then private App-sidecar transaction mirrored to `Data/Settings`; backup and recovery marker | No installed profile touched | App dir must be writable | Change settings and verify Data after exit/crash | Crash+upgrade before recovery can lose App-side changes |
| Browser emulation registry | `cppMain.cpp`, `LoadOptions`, call `clsUtil::SetRegistry` | `HKCU\Software\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_BROWSER_EMULATION` / `FileOptimizer64.exe` DWORD 11001 | Application | N/A | Snapshot original value, restore selectively after last tracked child or on next run | Never remove registry tree, only specifically observed value if still equals 11001 | External ad WebBrowser compatibility retained | Compare pre/during/after registry value | Installed concurrent process/external changes cause conservative unresolved journal |
| WebView2 profile temp path | `cppMain.cpp`, `GetTempPath` → `WEBVIEW2_USER_DATA_FOLDER` | User temporary path by default | Application + framework | N/A | Child-only `TEMP/TMP` → `Data/RuntimeTemp`; reserve Data/WebView2 | No shared system TEMP edits | Temporary data may accumulate | ProcMon on ads on/off, check profile persistence | Additional WebView2/cache paths not verified |
| Optimization plugin executables | `cppMain.cpp`, `Plugins64` and worker shutdown | `App/FileOptimizer/Plugins64` and application chosen output directories | Application + plugin children | N/A | Keep complete vendor `Plugins64`; track descendants in Windows Job; do not delete user inputs | User paths excluded from any cleanup | Can delay shutdown while plugins remain open | Optimize sample files, observe children | Standalone helpers may escape Job or write other host state |
| Persistent recent-files grid | `cppMain.cpp` `grdFiles` INI sections | Same INI under App while running, `Data/Settings` between runs | Application | N/A | The same INI transaction | Backed-up Data | None intended | Close/reopen with PersistentGrid true | INI can include absolute user file paths, not auto-rewritten |
| Recycle Bin and backup files | `cppMain.cpp` optimizer code (`CopyToRecycleBin`, `.bak`) | User-selected files, user's Recycle Bin | Application/Windows shell | N/A | **No cleanup.** User files intentionally optimized | Preserves normal user decisions | User must test on copies | Use a disposable test file | True zero-OS-trace is impossible |
| Optional advertisement/browser | `cppMain.cpp` HideAds handling | Internet Explorer feature key and WebView2 temp cache | Application + Windows | N/A | Maintain upstream optional ads and browser state; do not forcibly disable | Only one confirmed registry entry restored | Ads require supported system/browser runtimes | Test displaying, closing ad view | WebView2 runtime may be external OS dependency |
| Windows notifications and shortcuts | No observed upstream auto-registration in inspected paths; full runtime not audited | Unknown | Windows / app / installer | N/A | No broad ShellGuard action absent evidence; manual observation required | Never touch existing shortcuts/CLSID | None | Before/after with real Explorer session | Not yet verified |
| Setup integration | Official `FileOptimizerSetup.exe` is a separate installer | Start Menu, shell registration if installer used | Official installer | N/A | NEVER run vendor Setup; only extract vendor 7z full archive; shared custom-NSIS independently installs staged app | Prevents intentional upstream Setup registrations | Community installer lacks upstream context-menu integration | Compare fresh portable ZIP vs shared PAF | Shared installer upgrade behavior requires real Windows testing |
| Source/provenance | Official versioned developer archive, checksums, C++Builder project | SourceForge versioned files | SourceForge/author | N/A | Verify official SHA-256 of Full and Source; include version-matched source | Protects provenance, not antivirus immunity | Does not rebuild vendor binaries | Validate downloaded files, application PE | No independent vendor code signature verified |

## Source links

- Source tree: https://sourceforge.net/p/nikkhokkho/code/HEAD/tree/trunk/FileOptimizer/
- Main project: https://sourceforge.net/p/nikkhokkho/code/HEAD/tree/trunk/FileOptimizer/FileOptimizer.cpp
- VCL project: https://sourceforge.net/p/nikkhokkho/code/HEAD/tree/trunk/FileOptimizer/FileOptimizer.cbproj
- Options, registry, plugin/worker logic: https://sourceforge.net/p/nikkhokkho/code/HEAD/tree/trunk/FileOptimizer/Source/cppMain.cpp
- Developer's portable/log FAQ: https://nikkhokkho.sourceforge.io/?page=FileOptimizer
- Official files: https://sourceforge.net/projects/nikkhokkho/files/FileOptimizer/18.10.2904/
- Shared builder action: https://raw.githubusercontent.com/vhick/Portable-Package-Builder/v1.0.0/action.yml
- Shared publisher action: https://raw.githubusercontent.com/vhick/portable-release-publisher/v1.1.1/action.yml

## Data and shell policy

The compiled launcher does not harvest a Windows user's shared AppData, HKLM keys, Start Menu trees, Desktop shortcuts or browser caches. It manages only its own private App sidecars and one identified HKCU value. If an unexpected action changes the registry value or a symlink/junction appears, it fails conservatively and preserves records. Its child process environment changes TEMP/TMP; it does not call Windows system-wide SetEnvironmentVariable / global environment APIs for other programs. The `Data` folder remains the user's persistent source of truth, and may contain empty directories and cache data.

**Audit scope:** source-inspected and static only. It is NOT a substitute for ProcMon traces of an actual 18.10.2904 run on a disposable Windows profile, actual Toast/AUMID verification, or tests with every plugin. This kit does not claim those were performed.
