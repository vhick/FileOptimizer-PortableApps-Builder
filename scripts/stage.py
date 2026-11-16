#!/usr/bin/env python3
"""Stage a real FileOptimizer 64-bit PortableApps distribution from verified vendor SFX.
Never run the vendor SFX or setup program. It is extracted with 7-Zip only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile
from PIL import Image

NAME = 'FileOptimizerCommunityPortable'
FOLDERS = ['Settings','RuntimeTemp','WebView2','Logs','Backups','Control']

def reject_links(root):
    for p in root.rglob('*'):
        if p.is_symlink():raise RuntimeError(f'Unexpected symbolic link in upstream archive: {p}')

def pe_machine(p):
    with p.open('rb') as f:
        if f.read(2)!=b'MZ':return None
        f.seek(60);off=int.from_bytes(f.read(4),'little');f.seek(off)
        if f.read(4)!=b'PE\0\0':return None
        return int.from_bytes(f.read(2),'little')

def find_binary(root):
    choices=[]
    for f in root.rglob('FileOptimizer64.exe'):
        if f.is_file() and (f.parent/'Plugins64').is_dir():choices.append(f.parent)
    if len(choices)!=1:raise RuntimeError(f'Expected one vendor FileOptimizer64.exe alongside Plugins64, found {len(choices)}')
    return choices[0]

def source_checks(src):
    # Source archive is included in the package; static checks make upstream
    # changes visible rather than silently retaining assumptions about paths.
    allcpp=list(src.rglob('cppMain.cpp'))
    if len(allcpp)!=1:raise RuntimeError('Source archive missing unique cppMain.cpp')
    data=allcpp[0].read_bytes().decode('utf-8','replace')
    required=['FEATURE_BROWSER_EMULATION','WEBVIEW2_USER_DATA_FOLDER','Plugins64','GetOption','SetEnvironmentVariable']
    absent=[s for s in required if s not in data]
    if absent:raise RuntimeError(f'Source storage/shell assumptions changed: missing {absent}; re-audit required')
    main=list(src.rglob('FileOptimizer.cpp'))
    if len(main)!=1 or 'CreateForm' not in main[0].read_bytes().decode('utf-8','replace'):
        raise RuntimeError('Source archive does not resemble audited VCL FileOptimizer')
    return {'cppMain':str(allcpp[0].relative_to(src)),'FileOptimizer':str(main[0].relative_to(src)),'static_tokens':required}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--full',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--kit',type=Path,required=True)
    args=p.parse_args()
    identity=json.loads((args.work/'identity.json').read_text(encoding='utf-8'))
    if identity['mode']!='PORTABLEAPPS':raise RuntimeError('Wrong-mode identity')
    reject_links(args.full);reject_links(args.source)
    src_find=source_checks(args.source)
    vendor=find_binary(args.full)
    app=args.work/'stage'/NAME
    if app.exists():raise RuntimeError('Staging folder already exists; choose a clean workspace')
    destination=app/'App'/'FileOptimizer'
    shutil.copytree(vendor,destination)
    # 64-bit build only; do not confuse architecture with an x86 launcher.
    for item in (destination/'Plugins32',destination/'FileOptimizer32.exe'):
        if item.is_dir():shutil.rmtree(item)
        elif item.is_file():item.unlink()
    if pe_machine(destination/'FileOptimizer64.exe') != 0x8664:raise RuntimeError('Vendor main executable is not a Win64 PE')
    if not any((destination/'Plugins64').rglob('*.exe')):raise RuntimeError('Missing vendor optimization plugins')
    for folder in FOLDERS:(app/'Data'/folder).mkdir(parents=True,exist_ok=True)
    for basename in ('FileOptimizer.ini','FileOptimizer.log'):
        f=destination/basename
        if f.exists():
            if not f.is_file():raise RuntimeError(f'Non-file sidecar in vendor archive: {f}')
            shutil.move(str(f),str(app/'Data'/'Settings'/basename))
    (app/'App'/'AppInfo').mkdir(parents=True,exist_ok=True)
    (app/'Other'/'Source').mkdir(parents=True,exist_ok=True)
    # Genuine original developer ICO, not a guessed/generated branding icon.
    # Prefer the icon beside the exact archived FileOptimizer.cpp project file.
    main_src=next(args.source.rglob('FileOptimizer.cpp'))
    preferred=main_src.parent/'FileOptimizer.ico'
    icons=[preferred] if preferred.is_file() else (list(args.source.rglob('FileOptimizer.ico')) or list(args.full.rglob('FileOptimizer.ico')))
    if len(icons)!=1:raise RuntimeError('Genuine original FileOptimizer.ico was not found unambiguously')
    ico=app/'App'/'AppInfo'/'appicon.ico';shutil.copy2(icons[0],ico)
    with Image.open(ico) as icon:
        for size in (16,32):
            try:frame=icon.ico.getimage((size,size))
            except Exception:frame=icon.copy().convert('RGBA').resize((size,size),Image.Resampling.LANCZOS)
            frame.save(app/'App'/'AppInfo'/f'appicon_{size}.png','PNG')
    (app/'App'/'AppInfo'/'appinfo.ini').write_text(f'''[Format]
Type=PortableApps.comFormat
Version=3.8

[Details]
Name=FileOptimizer Portable (Community)
AppID=FileOptimizerCommunityPortable
Publisher=Javier Gutiérrez Chamorro (Guti)
Homepage=https://sourceforge.net/projects/nikkhokkho/
Category=Utilities
Description=Portable file optimizer using the official FileOptimizer portable distribution
Language=Multilingual

[License]
Shareable=true
OpenSource=true
Freeware=true
CommercialUse=true

[Version]
PackageVersion={identity['version']}.0
DisplayVersion={identity['version']} Community {identity['package_revision']}

[Control]
Icons=1
Start=FileOptimizerPortable.exe
''',encoding='utf-8',newline='\n')
    shutil.copy2(args.work/'downloads'/'FileOptimizerSource.7z',app/'Other'/'Source'/'FileOptimizerSource.7z')
    shutil.copy2(args.kit/'launcher'/'FileOptimizerPortable.cpp',app/'Other'/'Source'/'FileOptimizerPortable.cpp')
    shutil.copy2(args.kit/'LICENSE-LAUNCHER.txt',app/'Other'/'Source'/'LICENSE-LAUNCHER.txt')
    (app/'Other'/'Source'/'README-SOURCE.txt').write_text('FileOptimizer official version-matched source archive retained alongside its binaries.\nThe independently built portable launcher source is also included.\nFileOptimizer licensing: AGPL. Third-party plugin licensing may differ; consult vendor distribution.\n',encoding='utf-8')
    identity['source_audit']=src_find
    identity['app_binary_sha256']=hashlib.sha256((destination/'FileOptimizer64.exe').read_bytes()).hexdigest()
    (app/'Other'/'Source'/'build-identity.json').write_text(json.dumps(identity,indent=2)+'\n',encoding='utf-8')
    print('Staging complete:',app)

if __name__=='__main__':
    try:main()
    except Exception as e:print('STAGE ERROR:',e,file=sys.stderr);sys.exit(1)
