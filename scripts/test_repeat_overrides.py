import copy
import unittest
from test_build import builder, FIXTURE
import json

class RepeatOverridesTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.plan = copy.deepcopy(self.data['plans']['four-day-cut'])
        self.plan['days'] = ['day-01'] * 4
        self.plan['repeatLimitOverrides'] = {'breakfast': 4, 'snack': 4}
        self.policy = {'maxConsecutiveSameMeal': 2, 'calorieTolerancePercent': 5}
        self.plan['targets'].pop('macroPercent', None)

    def test_breakfast_and_snack_exception_preserves_lunch_guard(self):
        with self.assertRaisesRegex(ValueError, 'lunch meal family'):
            builder.validate_plan_nutrition(self.data, 'custom', self.plan, self.policy)

    def test_explicit_slot_overrides_allow_requested_repetition(self):
        self.plan['repeatLimitOverrides'].update(lunch=4, dinner=4)
        builder.validate_plan_nutrition(self.data, 'custom', self.plan, self.policy)

    def test_invalid_overrides_are_rejected(self):
        for overrides in [{'breakfast': 0}, {'breakfast': True}, {'breakfast': 2.5}, {'brunch': 4}, []]:
            with self.subTest(overrides=overrides):
                self.plan['repeatLimitOverrides'] = overrides
                with self.assertRaisesRegex(ValueError, 'repeatLimitOverrides'):
                    builder.validate_plan_nutrition(self.data, 'custom', self.plan, self.policy)
