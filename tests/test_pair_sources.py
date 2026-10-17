"""Exercise final-pair provenance guards with genuine isolated Git inputs."""
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

from verify_completion_pair import source_inputs


class PairSources(unittest.TestCase):
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
