#!/usr/bin/env python3
"""Verify published shared action interfaces AND their immutable approved commits."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request
import yaml

APPROVED_COMMITS = {
  'vhick/Portable-Package-Builder': '0112c35580e83b37eb8757ebcb949274e1631a04',
  'vhick/portable-release-publisher': 'cb64f86ac2d8c67506db5832de07f9ff58cbeaeb',
}

ACTIONS = [
 ('vhick', 'Portable-Package-Builder', 'v1.0.0',
  {'source-dir','output-dir','engine','running-exe','timeout-seconds','package-revision','official-tool-url','official-tool-sha256'},
  {'installer-file','installer-sha256','app-id','app-version'}),
 ('vhick', 'portable-release-publisher', 'v1.1.1',
  {'files','tag','release-title','tag-prefix','keep-releases','prune','dry-run'},set()),
]
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'FileOptimizerCommunityPortableBuilder/1.1','Accept':'application/vnd.github+json'})
 with urllib.request.urlopen(req,timeout=40) as f: return f.read()
def main(out):
 results=[]
 for owner,repo,tag,inputs,outputs in ACTIONS:
  ref=json.loads(get(f'https://api.github.com/repos/{owner}/{repo}/git/ref/tags/{tag}'))
  item=ref['object'];sha=item['sha']
  if item['type']=='tag':
   tagobj=json.loads(get(item['url']))
   item=tagobj['object'];sha=item['sha']
  if item['type']!='commit' or len(sha)!=40:raise RuntimeError(f'Unresolved immutable SHA: {repo}')
  approved=APPROVED_COMMITS[f'{owner}/{repo}']
  if sha.lower() != approved:
   raise RuntimeError(f'Pinned action tag moved: {owner}/{repo}@{tag} resolved to {sha}; expected {approved}')
  raw=get(f'https://raw.githubusercontent.com/{owner}/{repo}/{sha}/action.yml')
  action=yaml.safe_load(raw)
  if not inputs.issubset(action.get('inputs',{})):raise RuntimeError(f'Inputs have changed: {repo}')
  if not outputs.issubset(action.get('outputs',{})):raise RuntimeError(f'Outputs have changed: {repo}')
  if action.get('runs',{}).get('using')!='composite':raise RuntimeError(f'Unexpected action type: {repo}')
  results.append({'repository':f'{owner}/{repo}','tag':tag,'resolved_commit':sha,'action_yaml_sha256':hashlib.sha256(raw).hexdigest()})
 Path(out).parent.mkdir(parents=True,exist_ok=True)
 Path(out).write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(results,indent=2))
if __name__=='__main__':
 try:main(sys.argv[1])
 except Exception as exc:print(f'FAILED verifying shared actions: {exc}',file=sys.stderr);sys.exit(1)
