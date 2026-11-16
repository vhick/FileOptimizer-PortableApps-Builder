"""Real deterministic logic/regression tests. Not a substitute for Windows GUI testing."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
import yaml
import zipfile
import sys

ROOT=Path(__file__).resolve().parents[1]
def mod(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
resolver=mod('resolve');stage=mod('stage');package=mod('package')

class KitTests(unittest.TestCase):
 def test_semver_is_numeric_not_string(self):
  sample=''.join(f'<a href="/projects/nikkhokkho/files/FileOptimizer/{x}/">{x}</a>'
                 for x in ['9.90.1844','18.00.2889','18.10.2904','18.02.2000','19.00.1'])
  self.assertEqual(resolver.available_versions(sample)[:3],['19.00.1','18.10.2904','18.02.2000'])
 def test_vendor_history_403_fallback_selects_known_release(self):
  official_html="""<html><h2>History</h2><p>18.10 - 2026/11/15</p><p>18.00 - 2026/10/25</p></html>"""
  self.assertEqual(resolver.choose_verified_from_history(official_html),'18.10.2904')

 def test_vendor_history_newer_version_fails_closed(self):
  with self.assertRaisesRegex(RuntimeError, 'newer version 18.20'):
   resolver.choose_verified_from_history('<html>History 18.20 - 2026/12/15</html>')

 def test_unverified_sha256_fails_closed(self):
  with self.assertRaisesRegex(RuntimeError, 'No independently audited SHA-256'):
   resolver.sourceforge_checksum('19.00.1000','FileOptimizerFull.7z.exe')

 def test_403_discovers_vendor_only_and_not_other_http_errors(self):
  old=resolver.fetch
  calls=[]
  try:
   def mock403(url, *args, **kwargs):
    calls.append(url)
    if url==resolver.BASE+'/':
     raise RuntimeError('SourceForge metadata error 403: '+url)
    return b'<html>History 18.10 - 2026/11/15</html>'
   resolver.fetch=mock403
   ver,source=resolver.discover_latest()
   self.assertEqual(ver,'18.10.2904')
   self.assertIn('403',source)
   self.assertEqual(calls,[resolver.BASE+'/',resolver.VENDOR_HISTORY])
   def mock429(url, *args, **kwargs):
    raise RuntimeError('SourceForge metadata error 429: '+url)
   resolver.fetch=mock429
   with self.assertRaisesRegex(RuntimeError,'429'):
    resolver.discover_latest()
  finally:
   resolver.fetch=old

 def test_reject_prerelease_as_version(self):
  self.assertFalse(resolver.VERSION.fullmatch('19.00.22-beta'))
  self.assertFalse(resolver.VERSION.fullmatch('master'))
 def test_verified_official_hashes_are_sha256(self):
  values=resolver.VERIFIED['18.10.2904']
  self.assertEqual(set(values),set(resolver.FILES))
  for sha in values.values():self.assertEqual(len(bytes.fromhex(sha)),32)
 def test_source_scan_real_application_paths(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'Source').mkdir();(root/'FileOptimizer.cpp').write_text('Application->CreateForm',encoding='utf-8')
   (root/'Source'/'cppMain.cpp').write_text('FEATURE_BROWSER_EMULATION WEBVIEW2_USER_DATA_FOLDER Plugins64 GetOption SetEnvironmentVariable',encoding='utf-8')
   self.assertIn('cppMain',stage.source_checks(root))
   (root/'Source'/'cppMain.cpp').write_text('unexpected new source layout',encoding='utf-8')
   with self.assertRaises(RuntimeError):stage.source_checks(root)
 def test_invalid_pe_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'not-an-exe';f.write_bytes(b'MZ'+bytes(100))
   with self.assertRaises(AssertionError):package.machine(f)
 def test_workflow_dispatch_and_shared_action_version(self):
  flow=yaml.load((ROOT/'.github/workflows/build.yml').read_text(encoding='utf-8'),Loader=yaml.BaseLoader)
  self.assertIn('workflow_dispatch',flow['on'])
  steps=flow['jobs']['package']['steps']
  uses=[s.get('uses','') for s in steps]
  self.assertIn('vhick/Portable-Package-Builder@0112c35580e83b37eb8757ebcb949274e1631a04', uses)
  self.assertEqual(uses.count('vhick/portable-release-publisher@cb64f86ac2d8c67506db5832de07f9ff58cbeaeb'), 2)
  self.assertEqual(flow['concurrency']['cancel-in-progress'],'false')
 def test_approved_action_sha_matches_workflow(self):
  verifier=mod('verify_actions')
  workflow=(ROOT/'.github/workflows/build.yml').read_text(encoding='utf-8')
  for name, sha in verifier.APPROVED_COMMITS.items():
   self.assertIn(name+'@'+sha,workflow)
   self.assertEqual(len(sha),40)

 def test_no_wrong_mode_components(self):
  files=[str(p.relative_to(ROOT)).lower() for p in ROOT.rglob('*') if p.is_file()]
  self.assertFalse(any('native-portable' in s for s in files))
 def test_shellguard_scope(self):
  code=(ROOT/'launcher/FileOptimizerPortable.cpp').read_text(encoding='utf-8')
  for expected in ('FEATURE_BROWSER_EMULATION','FileOptimizer.ini','FileOptimizer.log','RegDeleteValueW','JobObjectBasicAccountingInformation','WEBVIEW2_USER_DATA_FOLDER'):
   self.assertIn(expected,code)
  self.assertNotIn('HKEY_LOCAL_MACHINE',code)

if __name__=='__main__':unittest.main()
