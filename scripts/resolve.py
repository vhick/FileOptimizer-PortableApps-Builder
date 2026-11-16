#!/usr/bin/env python3
"""Resolve FileOptimizer stable SourceForge folder and verify OFFICIAL full/source archives.

A source-archive SHA-256 is the stable source identity; SVN trunk is intentionally NOT
compiled or claimed to match a release. No unverified 'latest' or mirror substitution.
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
AGENT = 'FileOptimizerCommunityPortableBuilder/1.0 (+https://sourceforge.net/projects/nikkhokkho/)'


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


def sourceforge_checksum(version: str, name: str) -> str:
    # This page is rendered by SourceForge and displays the vendor's published
    # SHA-256. If SourceForge redirects to binary bytes / blocks us, fail closed
    # unless the exact release is included in VERIFIED above.
    url = f'{BASE}/{version}/{name}/download'
    try:
        page = fetch(url, size_limit=2_000_000).decode('utf-8', 'replace')
        match = re.search(r'SHA-256\s*:\s*(?:<[^>]*>\s*)*([a-fA-F0-9]{64})', page, flags=re.I)
        if match:
            return match.group(1).lower()
    except RuntimeError:
        pass
    if version in VERIFIED and name in VERIFIED[version]:
        return VERIFIED[version][name]
    raise RuntimeError(f'Unable to verify official SHA-256 for {version}/{name}. No download accepted.')


def download(version: str, name: str, expected_sha: str, target: Path) -> None:
    url = f'https://downloads.sourceforge.net/project/nikkhokkho/FileOptimizer/{version}/{name}'
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_suffix(target.suffix + '.download')
    if part.exists():
        part.unlink()
    for attempt in range(3):
        digest = hashlib.sha256()
        try:
            req = urllib.request.Request(url, headers={'User-Agent': AGENT, 'Accept': 'application/octet-stream'})
            with urllib.request.urlopen(req, timeout=90) as response, part.open('wb') as out:
                final_url = response.geturl()
                if not final_url.startswith('https://'):
                    raise RuntimeError('Insecure SourceForge download redirect')
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    digest.update(block)
                    out.write(block)
            if digest.hexdigest() != expected_sha:
                raise RuntimeError(f'{name} checksum mismatch: got {digest.hexdigest()}, expected {expected_sha}')
            part.replace(target)
            return
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 403, 404):
                raise RuntimeError(f'Official download error {exc.code}: {url}') from exc
            if attempt == 2:
                raise RuntimeError(f'Download failed: {name} ({exc})') from exc
            time.sleep(2 + attempt)
        except Exception:
            raise
        finally:
            if part.exists():
                part.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', default='latest')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--builder-revision', default='b1r1')
    args = parser.parse_args()
    if args.version == 'latest':
        page = fetch(BASE + '/').decode('utf-8', 'replace')
        options = available_versions(page)
        if not options:
            raise RuntimeError('No stable SourceForge release folders discovered; refusing unverified main/trunk')
        version = options[0]
    else:
        if not VERSION.fullmatch(args.version):
            raise RuntimeError('Explicit version must be a stable numeric version, e.g. 18.10.2904')
        version = args.version
    hashes = {name: sourceforge_checksum(version, name) for name in FILES}
    for name, sha in hashes.items():
        download(version, name, sha, args.out / 'downloads' / name)
    identity = {
        'application': 'FileOptimizer', 'upstream': 'https://sourceforge.net/p/nikkhokkho/code/HEAD/tree/',
        'version': version, 'source_identity': 'FileOptimizerSource.7z SHA-256 (release snapshot; SVN SHA is not applicable)',
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
