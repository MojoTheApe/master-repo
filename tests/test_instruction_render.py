"""Prevent selected primary guidance and Tracker-owned PR fields from drifting."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_project import INPUTS, NEW, REAL_RENDER, files
import project
import instruction_render


class SelectedInstructions(unittest.TestCase):
    def test_selection_package_order_precedes_selection_on_its_supported_route(self):
        template = (project.SOURCE/'templates/workflow/DELIVERY.md').read_text()
        for profile in project.PROFILES:
            for stage in (False, True):
                for version in (None, 1, 2, 3):
                    choices = {None: {}, 1: {'implementation_limit': 3},
                               2: {'implementation_limit': 5, 'batch_limit': 5},
                               3: {'implementation_limit': 5, 'batch_limit': 5, 'review_limit': 4}}[version]
                    inputs = dict(INPUTS, profile=profile, staging=stage, **choices)
                    for selection in ({}, {'task_context': {'schema_version': 1}},
                                      {'completion_policy': {'schema_version': 1}},
                                      {'ci_retry': {'schema_version': 1, 'max_executions': 2}}):
                        with self.subTest(profile=profile, stage=stage, version=version, selection=selection):
                            if 'task_context' in selection and version not in (2, 3):
                                with self.assertRaises(ValueError):
                                    project.descriptor(dict(inputs, **selection), NEW)
                                continue
                            data = project.descriptor(dict(inputs, **selection), NEW)
                            text = instruction_render.render(template, data)
                            supported = profile == 'package' and not stage and version in (2, 3)
                            self.assertEqual('before reserving maintenance' in text, supported)
                            if supported:
                                self.assertIn('fully verified package', text)
                                self.assertIn('other pending delivery and unresolved owners', text)

    def test_first_context_or_retry_selection_does_not_add_a_delivery_document_change(self):
        template = (project.SOURCE/'templates/workflow/DELIVERY.md').read_text()
        inputs = dict(INPUTS, profile='package', staging=False, implementation_limit=5, batch_limit=5)
        before = instruction_render.render(template, project.descriptor(inputs, NEW))
        for choice in ({'task_context': {'schema_version': 1}},
                       {'ci_retry': {'schema_version': 1, 'max_executions': 2}}):
            with self.subTest(choice=choice):
                after = instruction_render.render(template, project.descriptor(dict(inputs, **choice), NEW))
                self.assertEqual(before, after)

    def test_primary_route_target_and_optional_features_follow_actual_selection(self):
        modes = {None: {}, 1: {'implementation_limit': 3},
                 2: {'implementation_limit': 5, 'batch_limit': 5},
                 3: {'implementation_limit': 5, 'batch_limit': 5, 'review_limit': 4}}
        for profile in project.PROFILES:
            for stage in (False, True):
                for version, choices in modes.items():
                    inputs = dict(INPUTS, profile=profile, staging=stage, **choices)
                    with self.subTest(profile=profile, stage=stage, version=version):
                        exported = files(inputs, NEW)
                        workflow = exported['docs/repository/WORKFLOW.md']
                        delivery = exported['docs/repository/DELIVERY.md']
                        self.assertNotIn('__SELECTED_', workflow + delivery)
                        self.assertNotIn('__TASK_CONTEXT_GUIDANCE__', workflow)
                        self.assertNotIn('## Adopted task context', workflow)
                        self.assertNotIn('## Adopted instruction-only', workflow)
                        for other in (1, 2, 3):
                            self.assertEqual(f'execution schema {other}' in workflow, version == other)
                        self.assertEqual('legacy single implementation slot' in workflow, version is None)
                        if version in (2, 3):
                            self.assertIn('complete frozen member set', workflow)
                            self.assertNotIn('one review/integration lane', workflow)
                            self.assertIn('ordinary source PR contains exactly one task', workflow)
                        if version == 2:
                            self.assertIn('one shared source/combined-review lane', workflow)
                        elif version == 3:
                            self.assertIn('4 separately owned source-review slots', workflow)
                            self.assertIn('one separate integration Reviewer', workflow)
                        self.assertIn('Stage is enabled' if stage else 'Stage is disabled', workflow)
                        target = project.PROFILES[profile]
                        self.assertEqual('stable release' in delivery, target == 'verified-stable-package')
                        self.assertEqual('verifies production delivery' in delivery, target == 'verified-production')

    def test_adopted_context_retains_readiness_semantic_review_and_author_return(self):
        data = project.descriptor(dict(INPUTS, implementation_limit=5, batch_limit=5,
                                       task_context={'schema_version': 1},
                                       process_instructions={'schema_version': 1, 'required_checks': ['descriptor', 'tracker-link']}), NEW)
        text = instruction_render.render((project.SOURCE/'templates/workflow/WORKFLOW.md').read_text(), data)
        self.assertIn('## Adopted task context', text)
        self.assertIn('before start/resume', text)
        self.assertIn('owned independent compatibility review', text)
        self.assertIn('disjoint paths alone prove no semantic compatibility', text)
        self.assertIn('## Adopted instruction-only exception', text)
        self.assertIn('complete immutable-diff classifier', text)
        self.assertIn('Mixed, unsafe, unknown or incomplete proof', text)

    def test_master_keeps_tracker_pr_template_verbatim_before_common_notes(self):
        with tempfile.TemporaryDirectory() as temporary:
            engine = Path(temporary)/'engine'
            (engine/'tracker').mkdir(parents=True)
            template = ('Tracker issues: EX-12\n\nExact selected Tracker source and frozen '
                        'integration membership rules.\n')
            def exporter(command, **kwargs):
                target = Path(command[command.index('--output') + 1])
                exported = {'tracker/config.json': '{}', 'docs/TRACKER_AGENT_WORKFLOW.md': 'Exact guide.\n',
                            '.github/pull_request_template.md': template}
                from test_project import portable_files
                exported.update(portable_files())
                for name, content in exported.items():
                    path = target/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content)
                return mock.Mock(returncode=0, stdout='', stderr='')
            with mock.patch.object(project, 'tracker_checkout', return_value=engine), mock.patch.object(project.subprocess, 'run', side_effect=exporter):
                output = REAL_RENDER(INPUTS, NEW, engine)
            final = output['.github/pull_request_template.md']
            self.assertTrue(final.startswith(template))
            self.assertEqual(final.count('Tracker issues:'), 1)
            self.assertIn('System knowledge and related processes', final)
            self.assertNotIn('same single task', final)

    def test_separated_local_route_reference_keeps_exact_body_and_navigation(self):
        original = '# Full supported route reference\n\nPinned reference content.\n'
        exported = {'docs/TRACKER_AGENT_WORKFLOW.md': 'Read docs/WORKFLOW_REFERENCE.md and [reference](WORKFLOW_REFERENCE.md).\n'
                '[Config](../tracker/config.json), [task](../tracker/task-template.md).\n',
                    'docs/WORKFLOW_REFERENCE.md': original}
        from test_project import portable_files
        exported.update(portable_files())
        project.separate_export(exported)
        self.assertEqual(exported['docs/repository/WORKFLOW_REFERENCE.md'], original)
        self.assertIn('docs/repository/WORKFLOW_REFERENCE.md', exported['docs/repository/TRACKER.md'])
        self.assertIn('[reference](WORKFLOW_REFERENCE.md)', exported['docs/repository/TRACKER.md'])
        self.assertIn('repository/WORKFLOW_REFERENCE.md', exported['docs/WORKFLOW_REFERENCE.md'])
        self.assertIn('[Config](../../tracker/config.json)', exported['docs/repository/TRACKER.md'])
        self.assertIn('[task](../../tracker/task-template.md)', exported['docs/repository/TRACKER.md'])

    def test_modern_navigation_uses_explicit_route_stage_and_delivery_without_fake_batch(self):
        # Master-owned pure descriptor/navigation tests. No simulated engine
        # export, lifecycle, durable activation or source approval is involved.
        from test_project_choices import choices
        template = (project.SOURCE/'templates/workflow/WORKFLOW.md').read_text()
        delivery = (project.SOURCE/'templates/workflow/DELIVERY.md').read_text()
        for route in ('direct', 'batch'):
            for stage in (False, True):
                for profile, completion in project.PROFILES.items():
                    value = dict(profile=profile, completion=completion, route=route, staging=stage)
                    if route == 'batch': value['batch_limit'] = 2
                    data = project.descriptor(choices(**value), NEW)
                    with self.subTest(route=route, stage=stage, profile=profile):
                        text = instruction_render.render(template, data)
                        target = instruction_render.render(delivery, data)
                        self.assertNotIn('__', text)
                        self.assertIn('Stage is enabled' if stage else 'Stage is disabled', text)
                        self.assertIn('outer7', target)
                        self.assertNotIn('before reserving maintenance', target)
                        if route == 'direct':
                            self.assertIn('does not enter Approved or a synthetic batch', text)
                            self.assertIn('task-status reconciliation and archive/release', text)
                            self.assertNotIn('ordinary sources remain approval-only', text)
                        else:
                            self.assertIn('one separate integration Reviewer', text)
                            self.assertIn('complete frozen member set', text)
                        self.assertNotIn('unchanged Approved source', text)
                        self.assertEqual('stable release' in target, completion == 'verified-stable-package')
                        self.assertEqual('verifies production delivery' in target, completion == 'verified-production')

    def test_capture_guidance_is_only_selected_and_never_role_inferred(self):
        from test_project_choices import choices
        template = (project.SOURCE/'templates/workflow/WORKFLOW.md').read_text()
        value = choices(role='knowledge')
        text = instruction_render.render(template, project.descriptor(value, NEW))
        self.assertNotIn('genuine capture operation', text)
        value['knowledge_capture'] = {'schema_version': 1, 'roots': ['notes/'], 'scope': 'Approved ordinary notes'}
        text = instruction_render.render(template, project.descriptor(value, NEW))
        for bound in ('already adopted explicit knowledge policy', 'real approved mandate',
                      'complete immutable-diff', 'independent semantic attestation',
                      '.md/.txt', 'without an Issue alias', 'full checks remain'):
            self.assertIn(bound, text)
        self.assertIn('outside-mandate changes use a real engineering task', text)
