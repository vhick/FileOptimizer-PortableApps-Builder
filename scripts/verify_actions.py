#!/usr/bin/env python3
"""Read pinned published action.yml files and verify their required interfaces.
Note: static workflow 'uses: @tag' cannot eliminate mutable-tag risk; record SHAs.
"""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request
import yaml

ACTIONS = [
 ('vhick', 'Portable-Package-Builder', 'v1.0.0',
  {'source-dir','output-dir','engine','running-exe','timeout-seconds','package-revision','official-tool-url','official-tool-sha256'},
  {'installer-file','installer-sha256','app-id','app-version'}),
 ('vhick', 'portable-release-publisher', 'v1.1.1',
  {'files','tag','release-title','tag-prefix','keep-releases','prune','dry-run'},set()),
]
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'FileOptimizerCommunityPortableBuilder/1.0','Accept':'application/vnd.github+json'})
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
