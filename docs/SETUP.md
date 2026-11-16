# Beginner-friendly GitHub Desktop guide

## A. Make a separate builder repository

1. Open **GitHub Desktop** and log into your GitHub account.
2. Go to **File → New repository**. Name it `FileOptimizer-PortableApps-Builder` and choose a local folder.
3. Click **Create Repository**. Do not fork the upstream SourceForge project, do not use any other existing portable builder folder and do not run `git init`.
4. Choose **Repository → Show in Explorer**. This is your new repository's top-level folder.
5. Extract all folders and files **inside** this kit ZIP into that folder. You should see `README.md`, `scripts`, `launcher`, `docs`, `tests`, and **.github/workflows/build.yml**. In Explorer, enable **View → Show → Hidden items** if you cannot see `.github`.
6. Back in GitHub Desktop, type a short commit message (e.g. `FileOptimizer PortableApps builder b1r1`), click **Commit to main**, then **Publish repository**. Public is usually appropriate for builder source and hosted runner access, but it does **not** grant permission to redistribute any third-party plugin.

## B. First validation build, without a public release

7. Open your repository on github.com. Click **Actions**. If GitHub asks to enable workflows, enable them for this repository.
8. Select **FileOptimizer PortableApps - Verified Build** on the left. Click **Run workflow**.
9. Enter `18.10.2904` in version (known official baseline), and leave **publish** unchecked/false. Click the green Run workflow button.
10. Open the newest workflow run. The steps show checks for SourceForge checksum, matched source, launcher compilation, ZIP, installer and publisher dry-run. A successful ZIP build is not proof that FileOptimizer really works until you test on your PC.
11. If it fails, click the red step and expand the error log. Use `docs/OPEN-ISSUES.md`. Do not delete a failing log to 'fix' a problem.
12. If it succeeds, run `latest` with publish still false to test automatic stable-version discovery. For a real release, run again with `publish=true` after licensing and Windows acceptance review.

## C. Download / install

13. In the repository click **Releases** (right side on GitHub). Open the release called **FileOptimizer Portable ...** (there is no public release if publish stayed false).
14. Download the ZIP or the `.paf.exe` and verify its SHA-256 using PowerShell: `Get-FileHash -Algorithm SHA256 "C:\path\to\download.zip"`. Compare with the `SHA256SUMS.txt` file on the same GitHub release.
15. **ZIP option:** right-click ZIP → Extract All → choose a folder. Keep the extracted `FileOptimizerCommunityPortable` folder intact. Start `FileOptimizerPortable.exe` at the top level.
16. **PortableApps-style installer option:** run the community `.paf.exe`, select the desired PortableApps folder and follow its prompts. This is not a certified official PortableApps.com installer. Refresh the PortableApps Platform menu if it does not appear automatically.
17. Do **not** start the internal `App\FileOptimizer\FileOptimizer64.exe` directly when using the packaged version. That bypasses the data and registry safeguards.

## D. Data, upgrades and rollback

18. Portable settings live in `Data\Settings\FileOptimizer.ini`. Launcher log lives in `Data\Logs\launcher.log`; temporary/browser data may remain in `Data\RuntimeTemp` and `Data\WebView2`. `Data\Backups` contains earlier copies. `Data\Control` stores locks and recovery journals.
19. Before any update, **exit FileOptimizer and every plugin**, then confirm `Data\Control\active.run` is absent. If present, start/close the root launcher once to complete recovery, after ensuring no other FileOptimizer process is running. Do not update first.
20. Copy the **entire** `Data` folder to a separate backup drive. If a pending recovery exists, also back up `App\FileOptimizer\FileOptimizer.ini`/`.log` before changing binaries. Only then run a newer package/installer; never delete Data.
21. If the upgrade breaks, close the app, restore the last known-good root launcher and `App`/`Other` application files, keep `Data`, and retry. If an old program cannot read new settings, restore the **matching version** Data backup instead.
22. If a crash or registry conflict leaves a journal, keep it and use `docs/OPEN-ISSUES.md`. Do not manually delete shared registry trees, Windows user profiles, shortcuts or Windows system caches.

## E. Safe initial application test

Create copies of nonimportant PNG/JPG/PDF test files. Launch FileOptimizer from the root executable, change one setting and exit, restart, and verify the setting stays. Check that the originals or Recycle Bin behavior match FileOptimizer's options. Test one plugin at a time. Because FileOptimizer can rewrite files, do not begin with your only copy of important documents.
