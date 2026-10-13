import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('skill_impact', Path(__file__).resolve().parents[1] / 'scripts/check_skill_impact.py')
impact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(impact)


class SkillImpactTests(unittest.TestCase):
    def test_standard_change_cannot_skip_assessment(self):
        with self.assertRaises(ValueError):
            impact.assess('Description only', ['standard.md'])

    def test_updated_requires_source_skill_change(self):
        body = 'Project Workflow impact: updated\nProject Workflow reason: Update the navigation rule for the new standard.\n'
        with self.assertRaises(ValueError):
            impact.assess(body, ['templates/project/AGENTS.md'])
        self.assertIn('updated', impact.assess(body, ['standard.md', impact.SKILL + 'SKILL.md']))

    def test_concrete_no_impact_is_allowed(self):
        body = 'Project Workflow impact: no-impact\nProject Workflow reason: Correct an example typo without changing any workflow behavior.\n'
        self.assertIn('no-impact', impact.assess(body, ['docs/adoption.md']))
        with self.assertRaises(ValueError):
            impact.assess(body, [impact.SKILL + 'references/parallel-execution.md'])

    def test_duplicate_or_empty_assessments_fail(self):
        for body in ('Project Workflow impact: no-impact\nProject Workflow reason: none',
                     'Project Workflow impact: updated\nProject Workflow impact: no-impact\nProject Workflow reason: A meaningful explanation of the impact.'):
            with self.assertRaises(ValueError):
                impact.assess(body, ['scripts/standard.py'])

    def test_history_only_changes_do_not_require_assessment(self):
        impact.assess(None, ['docs/repository/CHANGELOG.md'])


if __name__ == '__main__':
    unittest.main()
