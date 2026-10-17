"""Exercise final-pair provenance guards with genuine isolated Git inputs."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

from verify_completion_pair import source_inputs


class PairSources(unittest.TestCase):
    def test_optional_pair_contracts_require_portable_proof_before_any_source_read(self):
        script=Path(__file__).with_name('verify_completion_pair.py')
        for flag in ('--retry-contract', '--direct-contract', '--selection-delivery-contract'):
            with self.subTest(flag=flag):
                command=[sys.executable,'-B',str(script),flag,'--master','/missing-master',
                         '--tracker','/missing-tracker','--old-master','/missing-old-master',
                         '--old-tracker','/missing-old-tracker','--python39',sys.executable,'--output','/missing-output']
                result=subprocess.run(command,capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0)
                self.assertIn(flag+' requires --portable-contract',result.stderr)
                self.assertNotIn('not a git repository',result.stderr)

    def test_selection_delivery_pair_cannot_silently_skip_runtime_replay(self):
        script=Path(__file__).with_name('verify_completion_pair.py')
        result=subprocess.run([sys.executable,'-B',str(script),'--portable-contract',
            '--selection-delivery-contract','--upgrades-only','--master','/missing-master',
            '--tracker','/missing-tracker','--old-master','/missing-old-master',
            '--old-tracker','/missing-old-tracker','--python39',sys.executable,
            '--output','/missing-output'],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('requires actual portable replay; omit --upgrades-only',result.stderr)
        self.assertNotIn('not a git repository',result.stderr)

    def test_every_source_must_be_clean_official_and_old_pair_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            args=SimpleNamespace(require_pinned=True)
            def git(root, *words):
                return subprocess.check_output(['git', '-C', str(root), *words], stderr=subprocess.STDOUT).decode().strip()
            for name, repo in (('tracker','task-tracker'),('old_tracker','task-tracker'),
                               ('master','master-repo'),('old_master','master-repo')):
                root=Path(directory)/name; root.mkdir(); setattr(args,name,root)
                git(root,'init','--quiet'); git(root,'remote','add','origin','https://github.com/MojoTheApe/'+repo+'.git')
                if name=='old_master':
                    (root/'compatibility.json').write_text(json.dumps({'tracker_repository':'MojoTheApe/task-tracker',
                        'tracker_revision':git(args.old_tracker,'rev-parse','HEAD')}))
                else: (root/'fixture.txt').write_text('Isolated source identity fixture.\n')
                git(root,'add','.');git(root,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                    'commit','--quiet','-m','Fixture source')
            result=source_inputs(args)
            self.assertTrue(result['old_compatibility_pin_matches'])
            for name in ('master','tracker','old_master','old_tracker'):
                root=getattr(args,name); dirty=root/'uncommitted.txt';dirty.write_text('Changed source')
                with self.assertRaisesRegex(ValueError, 'clean official '+name): source_inputs(args)
                dirty.unlink()
                git(root,'remote','set-url','origin','https://github.com/foreign/source.git')
                with self.assertRaisesRegex(ValueError, 'clean official '+name): source_inputs(args)
                repo='task-tracker' if name.endswith('tracker') else 'master-repo'
                git(root,'remote','set-url','origin','https://github.com/MojoTheApe/'+repo+'.git')
            (args.old_master/'compatibility.json').write_text(json.dumps({'tracker_repository':'MojoTheApe/task-tracker',
                'tracker_revision':'f'*40}))
            git(args.old_master,'add','.');git(args.old_master,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                'commit','--quiet','-m','Fixture wrong old pin')
            with self.assertRaisesRegex(ValueError, 'Old Master compatibility pin differs'): source_inputs(args)


if __name__ == '__main__': unittest.main()
