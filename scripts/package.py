#!/usr/bin/env python3
"""Independently validate complete staging, ZIP contents and copied PE binaries."""
import argparse
import hashlib
from pathlib import Path
import json
import sys
import tempfile
import zipfile
import shutil
import configparser

NAME='FileOptimizerCommunityPortable'

def machine(p):
    with open(p,'rb') as f:
        assert f.read(2)==b'MZ','Not a PE executable'
        f.seek(60);offset=int.from_bytes(f.read(4),'little');assert offset<1024*1024
        f.seek(offset);assert f.read(4)==b'PE\0\0','Not a PE signature'
        return int.from_bytes(f.read(2),'little')

def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def validate(root):
    assert root.name==NAME
    launcher=root/'FileOptimizerPortable.exe';exe=root/'App'/'FileOptimizer'/'FileOptimizer64.exe'
    assert launcher.is_file() and machine(launcher)==0x8664,'Launcher must be a real Win64 PE'
    assert exe.is_file() and machine(exe)==0x8664,'Upstream app must be a real Win64 PE'
    assert (root/'App'/'FileOptimizer'/'Plugins64').is_dir(),'Missing plugin directory'
    assert list((root/'App'/'FileOptimizer'/'Plugins64').rglob('*.exe')),'Missing vendor plugin binaries'
    ini=configparser.ConfigParser();ini.optionxform=str
    with (root/'App'/'AppInfo'/'appinfo.ini').open(encoding='utf-8') as f:ini.read_file(f)
    assert ini['Format']['Type']=='PortableApps.comFormat'
    assert ini['Details']['AppID']=='FileOptimizerCommunityPortable'
    assert ini['Control']['Start']=='FileOptimizerPortable.exe'
    for n in (16,32):
        png=root/'App'/'AppInfo'/f'appicon_{n}.png'
        assert png.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n',f'Missing PNG icon {n}'
    assert (root/'App'/'AppInfo'/'appicon.ico').read_bytes()[:4]==b'\x00\x00\x01\x00'
    for n in ('Settings','RuntimeTemp','WebView2','Logs','Backups','Control'):
        assert (root/'Data'/n).is_dir(),f'Missing persistent Data/{n}'
    assert not (root/'App'/'FileOptimizer'/'FileOptimizer.ini').exists(),'App shipped with unowned live INI'
    assert (root/'Other'/'Source'/'FileOptimizerSource.7z').stat().st_size>100_000
    assert (root/'Other'/'Source'/'FileOptimizerPortable.cpp').is_file()
    assert (root/'Other'/'Source'/'build-identity.json').is_file()
    for entry in root.rglob('*'):
        assert not entry.is_symlink(),f'Symlink in staged payload: {entry}'


def main():
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--dist',type=Path,required=True)
    args=p.parse_args()
    root=args.work/'stage'/NAME;validate(root)
    identity=json.loads((args.work/'identity.json').read_text(encoding='utf-8'))
    dest=args.dist/f'{NAME}-{identity["version"]}-{identity["builder_revision"]}.zip'
    args.dist.mkdir(parents=True,exist_ok=True)
    if dest.exists():raise RuntimeError('Refusing to overwrite existing validated ZIP')
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for f in sorted(root.rglob('*')):
            n=(Path(NAME)/f.relative_to(root)).as_posix()
            if f.is_dir():z.writestr(n+'/',b'')
            elif f.is_file():z.write(f,n)
            else:raise RuntimeError(f'Unexpected entry {f}')
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None,'ZIP CRC validation failed'
        names=z.namelist();assert all(x.startswith(NAME+'/') and '..' not in Path(x).parts for x in names)
        with tempfile.TemporaryDirectory() as temp:
            z.extractall(temp)
            unpacked=Path(temp)/NAME
            validate(unpacked)
            assert digest(unpacked/'FileOptimizerPortable.exe')==digest(root/'FileOptimizerPortable.exe')
            assert digest(unpacked/'App'/'FileOptimizer'/'FileOptimizer64.exe')==digest(root/'App'/'FileOptimizer'/'FileOptimizer64.exe')
    sha=digest(dest)
    (args.dist/'ZIP-SHA256SUMS.txt').write_text(f'{sha}  {dest.name}\n',encoding='utf-8')
    print(f'ZIP VALIDATED: {dest}\nSHA256: {sha}')

if __name__=='__main__':
    try:main()
    except Exception as exc:print('PACKAGE ERROR:',exc,file=sys.stderr);sys.exit(1)
