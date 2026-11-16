#!/usr/bin/env python3
"""Resolve FileOptimizer stable releases safely despite SourceForge HTML 403s.

Prefer SourceForge file metadata. If SourceForge HTML blocks CI, cross-check the
DEVELOPER'S OFFICIAL release history with an exact pinned, checked SHA-256 pair.
Never guess build numbers, switch to SVN trunk, or accept unchecked assets.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request

BASE = 'https://sourceforge.net/projects/nikkhokkho/files/FileOptimizer'
VENDOR_HISTORY = 'https://nikkhokkho.sourceforge.io/?page=FileOptimizer'
FILES = ('FileOptimizerFull.7z.exe', 'FileOptimizerSource.7z')
# Vendor-displayed SHA-256 at the time this builder was authored. An exact-version
# fallback only, never treated as an assurance for a DIFFERENT release.
VERIFIED = {
    '18.10.2904': {
        'FileOptimizerFull.7z.exe': '9813d98e5c868aadd717a487b106906064948483e9394e545fa7cc412d6f1397',
        'FileOptimizerSource.7z': 'c05cb949700d2ab2077dd6eaea2bf9b53146366ae23623780c4ec9fb31ada676',
    }
}
VERSION = re.compile(r'^\d+\.\d+\.\d+$')
AGENT = 'FileOptimizerCommunityPortableBuilder/1.1 (+https://sourceforge.net/projects/nikkhokkho/)'
# All endpoints below are SourceForge-controlled download services; final bytes MUST
# match the exact-source SHA-256. Mirrors are for availability, not provenance.
OFFICIAL_DOWNLOAD_HOSTS = (
    'https://downloads.sourceforge.net/project',
    'https://netix.dl.sourceforge.net/project',
    'https://phoenixnap.dl.sourceforge.net/project',
)



def fetch(url: str, size_limit: int = 20_000_000) -> bytes:
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': AGENT, 'Accept': 'text/html,application/xhtml+xml'})
            with urllib.request.urlopen(req, timeout=45) as response:
                data = response.read(size_limit + 1)
                if len(data) > size_limit:
                    raise RuntimeError('Unexpectedly large metadata page')
                return data
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 403, 404):
                raise RuntimeError(f'SourceForge metadata error {exc.code}: {url}') from exc
            if i == 2:
                raise RuntimeError(f'Metadata request failed: {url} ({exc})') from exc
            time.sleep(i + 1)
    raise AssertionError('unreachable')


def available_versions(page: str) -> list[str]:
    page = html.unescape(page)
    versions = set(re.findall(r'(?:/FileOptimizer/)(\d+\.\d+\.\d+)(?:/|["?])', page))
    return sorted((v for v in versions if VERSION.fullmatch(v)), key=lambda v: tuple(int(x) for x in v.split('.')), reverse=True)


def official_history_versions(page: str) -> list[str]:
    """Read the developer's CHANGELOG heading, never pretend this gives build number.

    Major/minor versions appear like "18.10 - 2026/11/15". Only the release
    prefix is derivable here. The checked mapping provides the exact build ID.
    """
    clean = re.sub(r'<[^>]*>', ' ', html.unescape(page))
    matches = re.findall(r'(?<!\d)(\d+\.\d+)\s*[-–]\s*20\d\d[/-]\d\d[/-]\d\d', clean)
    return sorted(set(matches), key=lambda v: tuple(map(int, v.split('.'))), reverse=True)


def choose_verified_from_history(page: str) -> str:
    versions = official_history_versions(page)
    if not versions:
        raise RuntimeError('Official developer history could not be parsed: refusing unverified latest')
    newest = versions[0]
    pinned = sorted((v for v in VERIFIED if v.rsplit('.', 1)[0] == newest),
                    key=lambda v: tuple(map(int, v.split('.'))), reverse=True)
    if not pinned:
        raise RuntimeError(
            f'Developer lists newer version {newest}, but there is no exact verified '
            'SourceForge release folder and checksum pair in this kit. '
            'Update and audit the manifest; refusing an older release.')
    print(f'NOTICE: SourceForge directory inaccessible; developer history shows {newest}. '
          f'Using exact SHA-256-pinned release {pinned[0]}. '
          'A newer build within the same major/minor cannot be ruled out.', file=sys.stderr)
    return pinned[0]


def discover_latest() -> tuple[str, str]:
    """Try original official folder listing; fallback only after HTTP 403.

    Other HTTP errors (401/429/5xx) are not treated as an invitation to silently
    ignore source failures. Explicit versions do not depend on HTML discovery.
    """
    try:
        listing = fetch(BASE + '/').decode('utf-8', 'replace')
    except RuntimeError as exc:
        if 'metadata error 403:' not in str(exc):
            raise
        print('NOTICE: SourceForge HTML returned 403; checking the independent '
              'official developer release-history page.', file=sys.stderr)
        vendor = fetch(VENDOR_HISTORY, size_limit=4_000_000).decode('utf-8', 'replace')
        return choose_verified_from_history(vendor), 'developer-history-sha256-pinned-403-fallback'
    options = available_versions(listing)
    if not options:
        raise RuntimeError('No stable SourceForge folders found: refusing unverified latest')
    return options[0], 'sourceforge-release-directory'


def sourceforge_checksum(version: str, name: str) -> str:
    # Exact trusted SHA-256 pinned for the audited official distribution.
    # SourceForge /download can return 100+ MB binary (NOT an HTML checksum
    # page), so never fetch it as metadata. Unknown versions fail closed.
    if version in VERIFIED and name in VERIFIED[version]:
        return VERIFIED[version][name]
    raise RuntimeError(
        f'No independently audited SHA-256 for {version}/{name}. '
        'Refusing to download unknown release bytes. Update verified release manifest.')


def download(version: str, name: str, expected_sha: str, target: Path) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_suffix(target.suffix + '.download')
    # All hosts are SourceForge project distribution endpoints, not external mirrors.
    # A source is accepted ONLY if its full SHA-256 equals the audited expected digest.
    errors = []
    for host in OFFICIAL_DOWNLOAD_HOSTS:
        url = f'{host}/nikkhokkho/FileOptimizer/{version}/{name}'
        if part.exists():
            part.unlink()
        for attempt in range(2):
            digest = hashlib.sha256()
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': AGENT, 'Accept': 'application/octet-stream'})
                with urllib.request.urlopen(req, timeout=120) as response, part.open('wb') as out:
                    final_url = response.geturl()
                    if not final_url.startswith('https://'):
                        raise RuntimeError('Insecure SourceForge redirect rejected')
                    while True:
                        block = response.read(1024 * 1024)
                        if not block:
                            break
                        digest.update(block)
                        out.write(block)
                actual = digest.hexdigest()
                if actual != expected_sha:
                    raise RuntimeError(f'Checksum mismatch for {name} via {url}: '
                                       f'expected {expected_sha}, got {actual}')
                part.replace(target)
                print(f'Validated official release archive: {name}, SHA-256 {actual}')
                return url
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
                errors.append(f'{url}: {exc}')
                # 401 and 429 require immediate stop (authorization / rate limiting).
                if isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 429):
                    raise RuntimeError(f'SourceForge download denied ({exc.code}); '
                                       'stop, do not retry alternate hosts') from exc
                # 403/404 can indicate blocked or unsynchronized CDN endpoint; try
                # a different SourceForge-operated download endpoint only.
                if isinstance(exc, urllib.error.HTTPError) and exc.code in (403, 404):
                    break
                if attempt == 0:
                    time.sleep(2)
            except RuntimeError:
                # Critical security error: never try another mirror after mismatch.
                raise
            finally:
                if part.exists():
                    part.unlink()
    raise RuntimeError('All official SourceForge download endpoints failed for '
                       f'{name}: ' + ' | '.join(errors))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', default='latest')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--builder-revision', default='b1r2')
    args = parser.parse_args()
    if args.version == 'latest':
        version, discovery_method = discover_latest()
    else:
        if not VERSION.fullmatch(args.version):
            raise RuntimeError('Explicit version must be a stable numeric version, e.g. 18.10.2904')
        version = args.version
        discovery_method = 'explicit-stable-verified-version'
    hashes = {name: sourceforge_checksum(version, name) for name in FILES}
    download_urls = {}
    for name, sha in hashes.items():
        download_urls[name] = download(version, name, sha, args.out / 'downloads' / name)
    identity = {
        'application': 'FileOptimizer', 'upstream': 'https://sourceforge.net/p/nikkhokkho/code/HEAD/tree/',
        'version': version, 'discovery_method': discovery_method,
        'official_download_endpoints': download_urls, 'source_identity': 'FileOptimizerSource.7z SHA-256 (release snapshot; SVN SHA is not applicable)',
        'source_sha256': hashes['FileOptimizerSource.7z'],
        'official_portable_sha256': hashes['FileOptimizerFull.7z.exe'],
        'builder_revision': args.builder_revision, 'package_revision': 'r1',
        'architecture': 'x64', 'mode': 'PORTABLEAPPS',
        'installer_engine': 'custom-nsis',
        'package_builder': 'vhick/Portable-Package-Builder@v1.0.0',
        'publisher': 'vhick/portable-release-publisher@v1.1.1',
        'release_tag': f'portable-fileoptimizer-{version}-{args.builder_revision}',
    }
    (args.out / 'identity.json').write_text(json.dumps(identity, indent=2) + '\n', encoding='utf-8')
    gh = os.environ.get('GITHUB_OUTPUT')
    if gh:
        with open(gh, 'a', encoding='utf-8') as out:
            out.write(f'version={version}\ntag={identity["release_tag"]}\n')
    print(json.dumps(identity, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('ERROR:', error, file=sys.stderr)
        sys.exit(1)
