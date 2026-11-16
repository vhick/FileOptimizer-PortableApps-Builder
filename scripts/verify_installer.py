#!/usr/bin/env python3
"""Check a real installer output path/PE and hash against the shared action outputs.
This does NOT claim a GUI install/upgrade was exercised by hosted CI.
"""
import argparse
import hashlib
from pathlib import Path
import sys
import os
p=argparse.ArgumentParser();p.add_argument('--file',required=True);p.add_argument('--sha256',required=True);p.add_argument('--dist',required=True)
a=p.parse_args()
try:
 f=Path(a.file).resolve();out=Path(a.dist).resolve()
 if f.parent!=out or not f.name.lower().endswith('.paf.exe'):raise RuntimeError('Wrong installer location or filename')
 if f.stat().st_size<50000:raise RuntimeError('Installer too small')
 with f.open('rb') as stream:
  if stream.read(2)!=b'MZ':raise RuntimeError('Not a Windows PE')
  stream.seek(60);offset=int.from_bytes(stream.read(4),'little')
  if offset>1048576:raise RuntimeError('Invalid PE offset')
  stream.seek(offset)
  if stream.read(4)!=b'PE\0\0':raise RuntimeError('Invalid PE signature')
 h=hashlib.sha256()
 with f.open('rb') as stream:
  for b in iter(lambda:stream.read(1048576),b''):h.update(b)
 if h.hexdigest()!=a.sha256.lower():raise RuntimeError('Installer SHA-256 differs from action output')
 print(f'Installer structure/hash validated: {f.name}, SHA256={h.hexdigest()}')
except Exception as err:
 print('INSTALLER VALIDATION FAILED:',err,file=sys.stderr);sys.exit(1)
