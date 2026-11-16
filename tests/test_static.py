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
  self.assertIn('vhick/Portable-Package-Builder@v1.0.0',uses)
  self.assertEqual(uses.count('vhick/portable-release-publisher@v1.1.1'),2)
  self.assertEqual(flow['concurrency']['cancel-in-progress'],'false')
 def test_no_wrong_mode_components(self):
  files=[str(p.relative_to(ROOT)).lower() for p in ROOT.rglob('*') if p.is_file()]
  self.assertFalse(any('native-portable' in s for s in files))
 def test_shellguard_scope(self):
  code=(ROOT/'launcher/FileOptimizerPortable.cpp').read_text(encoding='utf-8')
  for expected in ('FEATURE_BROWSER_EMULATION','FileOptimizer.ini','FileOptimizer.log','RegDeleteValueW','JobObjectBasicAccountingInformation','WEBVIEW2_USER_DATA_FOLDER'):
   self.assertIn(expected,code)
  self.assertNotIn('HKEY_LOCAL_MACHINE',code)

if __name__=='__main__':unittest.main()
