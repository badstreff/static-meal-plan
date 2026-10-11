"""Daily macro accounting, optional workout snacks, and plan guardrails."""
import copy
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'scripts/fixtures/meal-plan.json'
spec = importlib.util.spec_from_file_location('macro_builder', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class MacroTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.plan = self.data['plans']['four-day-cut']
        self.plan['targets'] = {
            'calories': 2000, 'proteinGrams': 175,
            'macroPercent': {'carbs': 35, 'protein': 35, 'fat': 30},
        }
        self.data['nutritionPolicy'] = {
            'macroTolerancePercentagePoints': 3,
            'calorieTolerancePercent': 5,
            'maxConsecutiveSameMeal': 2,
        }
        for recipe_id, recipe in self.data['recipes'].items():
            recipe['family'] = recipe_id
            recipe['nutrition'] = {
                'calories': 500, 'carbsGrams': 43.75,
                'proteinGrams': 43.75, 'fatGrams': 50 / 3,
            }

    def workout(self):
        recipe = copy.deepcopy(self.data['recipes']['yogurt'])
        recipe.update(title='Workout snack', shortTitle='Workout snack', preparation='fresh')
        self.data['recipes']['workout-snack'] = recipe
        self.data['recipes']['yogurt']['workoutRecipe'] = 'workout-snack'
        return recipe

    def test_balanced_daily_macros_and_calories_pass(self):
        self.assertIs(builder.validate_data(self.data), self.data)
        self.plan['people'] = 2
        totals = builder.day_totals(self.data, 'day-01')
        self.assertEqual(totals['calories'], 2000)
        self.assertEqual(totals['carbsGrams'], 175)
        self.assertEqual(totals['proteinGrams'], 175)
        self.assertAlmostEqual(totals['fatGrams'], 200 / 3)

    def test_macro_percent_uses_macro_energy_instead_of_label_calories(self):
        split = builder.macro_split({'calories': 2400, 'carbsGrams': 175,
                                     'proteinGrams': 175, 'fatGrams': 200 / 3})
        self.assertAlmostEqual(split['carbs'], 35)
        self.assertAlmostEqual(split['protein'], 35)
        self.assertAlmostEqual(split['fat'], 30)

    def test_each_day_must_meet_macro_tolerance(self):
        self.data['recipes']['oats']['nutrition']['fatGrams'] = 100
        with self.assertRaisesRegex(ValueError, r'day-01.*rest.*fat'):
            builder.validate_data(self.data)

    def test_calorie_tolerance_is_enforced_at_both_limits(self):
        for calories in (400, 600):
            with self.subTest(calories=calories):
                for recipe in self.data['recipes'].values():
                    recipe['nutrition']['calories'] = calories
                with self.assertRaisesRegex(ValueError, r'day-01.*calories'):
                    builder.validate_data(self.data)

    def test_policy_defaults_and_exact_macro_boundary_pass(self):
        self.data['nutritionPolicy'] = {}
        for recipe in self.data['recipes'].values():
            recipe['nutrition'].update(carbsGrams=47.5, proteinGrams=40, fatGrams=50 / 3)
        self.assertIs(builder.validate_data(self.data), self.data)

    def test_macro_targets_without_policy_display_without_enforcement(self):
        del self.data['nutritionPolicy']
        self.data['recipes']['oats']['nutrition']['fatGrams'] = 100
        self.assertIn('Estimated energy split', builder.render_page(self.data))

    def test_optional_macro_values_are_numeric_finite_and_nonnegative(self):
        del self.data['nutritionPolicy']
        del self.plan['targets']['macroPercent']
        for field in ('carbsGrams', 'fatGrams'):
            for value in (True, -1, float('inf'), float('nan'), '5', None):
                with self.subTest(field=field, value=value):
                    data = copy.deepcopy(self.data)
                    data['recipes']['oats']['nutrition'][field] = value
                    with self.assertRaisesRegex(ValueError, field):
                        builder.validate_data(data)
        self.data['recipes']['oats']['nutrition'].update(carbsGrams=0, fatGrams=0)
        self.assertIs(builder.validate_data(self.data), self.data)

    def test_carbs_and_fat_must_be_provided_together(self):
        del self.data['recipes']['oats']['nutrition']['fatGrams']
        with self.assertRaisesRegex(ValueError, 'carbsGrams.*fatGrams'):
            builder.validate_data(self.data)

    def test_macro_target_plan_requires_macros_on_every_selected_recipe(self):
        del self.data['recipes']['oats']['nutrition']['carbsGrams']
        del self.data['recipes']['oats']['nutrition']['fatGrams']
        with self.assertRaisesRegex(ValueError, 'oats.*macro'):
            builder.validate_data(self.data)

    def test_invalid_macro_targets_are_rejected(self):
        for target in ({'carbs': 35, 'protein': 35},
                       {'carbs': 35, 'protein': 35, 'fat': 35},
                       {'carbs': '35', 'protein': 35, 'fat': 30},
                       {'carbs': -1, 'protein': 71, 'fat': 30},
                       {'carbs': float('nan'), 'protein': 35, 'fat': 30}):
            with self.subTest(target=target):
                self.plan['targets']['macroPercent'] = target
                with self.assertRaisesRegex(ValueError, 'macroPercent'):
                    builder.validate_data(self.data)

    def test_invalid_policy_values_are_rejected(self):
        for field, values in {
            'macroTolerancePercentagePoints': (-1, 101, True, '3', float('inf')),
            'calorieTolerancePercent': (-1, 101, True, '5', float('nan')),
            'maxConsecutiveSameMeal': (0, True, 2.5, '2'),
        }.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    data = copy.deepcopy(self.data)
                    data['nutritionPolicy'][field] = value
                    with self.assertRaisesRegex(ValueError, field):
                        builder.validate_data(data)

    def test_different_portion_ids_with_same_family_count_as_repeats(self):
        for index in range(3):
            recipe_id = f'oats-portion-{index}'
            self.data['recipes'][recipe_id] = copy.deepcopy(self.data['recipes']['oats'])
            day = copy.deepcopy(self.data['days']['day-01'])
            day['meals']['breakfast'] = recipe_id
            self.data['days'][f'variant-{index}'] = day
        self.plan['days'] = ['variant-0', 'variant-1', 'variant-2']
        with self.assertRaisesRegex(ValueError, r'breakfast.*oats.*consecutive'):
            builder.validate_data(self.data)

    def test_two_consecutive_uses_are_allowed(self):
        self.plan['days'] = ['day-01', 'day-01', 'day-02']
        self.assertIs(builder.validate_data(self.data), self.data)

    def test_repetition_is_checked_in_inactive_plans(self):
        self.data['plans']['inactive'] = dict(self.plan, days=['day-01'] * 3)
        with self.assertRaisesRegex(ValueError, 'inactive.*consecutive'):
            builder.validate_data(self.data)

    def test_invalid_family_identifier_is_rejected(self):
        self.data['recipes']['oats']['family'] = 'Oats portion'
        with self.assertRaisesRegex(ValueError, 'family'):
            builder.validate_data(self.data)

    def test_workout_totals_replace_the_rest_snack(self):
        recipe = self.workout()
        recipe['nutrition'] = {'calories': 600, 'carbsGrams': 50,
                               'proteinGrams': 60, 'fatGrams': 20}
        totals = builder.day_totals(self.data, 'day-01', workout=True)
        self.assertEqual(totals['calories'], 2100)
        self.assertEqual(totals['proteinGrams'], 191.25)
        self.assertEqual(totals['carbsGrams'], 181.25)

    def test_unknown_workout_recipe_is_rejected(self):
        self.data['recipes']['yogurt']['workoutRecipe'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'workoutRecipe.*missing'):
            builder.validate_data(self.data)

    def test_workout_recipe_must_be_a_different_snack(self):
        for origin, target in (('yogurt', 'oats'), ('oats', 'yogurt'), ('yogurt', 'yogurt')):
            with self.subTest(origin=origin, target=target):
                data = copy.deepcopy(self.data)
                data['recipes'][origin]['workoutRecipe'] = target
                with self.assertRaisesRegex(ValueError, 'workoutRecipe'):
                    builder.validate_data(data)

    def test_workout_daily_macros_are_enforced(self):
        self.workout()['nutrition']['fatGrams'] = 100
        with self.assertRaisesRegex(ValueError, r'day-01.*workout.*fat'):
            builder.validate_data(self.data)

    def omitted_fruit_workout(self):
        recipe = self.workout()
        recipe['nutrition'].update(calories=440, carbsGrams=13.75)
        recipe['workoutMacroTolerance'] = {
            'percentagePoints': 6,
            'reason': 'Fruit omitted by preference; other meals are unchanged.',
        }
        return recipe

    def test_workout_preference_allows_bounded_deviation_and_shows_reason(self):
        self.omitted_fruit_workout()
        self.assertIs(builder.validate_data(self.data), self.data)
        html = builder.render_page(self.data)
        card = re.search(r'<article class="day-card">(.*?)</article>', html)[1]
        self.assertIn('Fruit omitted by preference; other meals are unchanged.', card)
        self.assertIn('1,940 kcal', card)
        self.assertIn('Carbs 145 g', card)

    def test_workout_preference_does_not_relax_rest_day_or_calorie_checks(self):
        recipe = self.omitted_fruit_workout()
        self.data['recipes']['yogurt']['nutrition']['carbsGrams'] = 0
        with self.assertRaisesRegex(ValueError, r'day-01.*rest.*carbs'):
            builder.validate_data(self.data)
        self.data['recipes']['yogurt']['nutrition']['carbsGrams'] = 43.75
        recipe['nutrition']['calories'] = 200
        with self.assertRaisesRegex(ValueError, r'day-01.*workout.*calories'):
            builder.validate_data(self.data)

    def test_workout_preference_still_enforces_its_macro_bound(self):
        recipe = self.omitted_fruit_workout()
        recipe['nutrition']['carbsGrams'] = 0
        with self.assertRaisesRegex(ValueError, r'day-01.*workout.*carbs'):
            builder.validate_data(self.data)

    def test_workout_preference_requires_valid_tolerance_and_reason(self):
        self.omitted_fruit_workout()
        for value in ({'percentagePoints': -1, 'reason': 'Preference'},
                      {'percentagePoints': True, 'reason': 'Preference'},
                      {'percentagePoints': 101, 'reason': 'Preference'},
                      {'percentagePoints': float('nan'), 'reason': 'Preference'},
                      {'percentagePoints': 6, 'reason': ''},
                      {'percentagePoints': 6}):
            with self.subTest(value=value):
                self.data['recipes']['workout-snack']['workoutMacroTolerance'] = value
                with self.assertRaisesRegex(ValueError, 'workoutMacroTolerance'):
                    builder.validate_data(self.data)

    def test_macro_target_requires_workout_nutrition(self):
        recipe = self.workout()
        del recipe['nutrition']['carbsGrams']
        del recipe['nutrition']['fatGrams']
        with self.assertRaisesRegex(ValueError, 'workout-snack.*macro'):
            builder.validate_data(self.data)

    def test_cards_and_target_show_macro_values(self):
        html = builder.render_page(self.data)
        cards = re.findall(r'<article class="day-card">(.*?)</article>', html)
        for card in cards:
            self.assertIn('Daily totals', card)
            self.assertIn('2,000 kcal', card)
            self.assertIn('Carbs 175 g', card)
            self.assertIn('Protein 175 g', card)
            self.assertIn('Fat 66.7 g', card)
            self.assertIn('35% carbs', card)
            self.assertIn('35% protein', card)
            self.assertIn('30% fat', card)
        self.assertIn('Macro target', html)
        self.assertIn('35% carbs / 35% protein / 30% fat', html)
        recipe = re.search(r'<details class="recipe" id="oats">(.*?)</details>', html)[1]
        self.assertIn('g carbs', recipe)
        self.assertIn('g fat', recipe)

    def test_workout_guides_are_linked_with_per_person_amounts(self):
        self.plan['people'] = 2
        recipe = self.workout()
        recipe['servings'] = 2
        recipe['ingredients'] = [dict(itemId='fairlife', quantity=2, unit='count')]
        baseline_groceries = builder.build_groceries(self.data, self.plan)
        html = builder.render_page(self.data)
        self.assertEqual(builder.build_groceries(self.data, self.plan), baseline_groceries)
        self.assertNotIn('workout-snack', builder.selected_counts(self.data, self.plan))
        self.assertIn('href="#workout-snack"', html)
        card = re.search(r'<article class="day-card">(.*?)</article>', html)[1]
        self.assertIn('Workout day', card)
        self.assertIn('2,000 kcal', card)
        workout = re.search(r'<details class="recipe" id="workout-snack">(.*?)</details>', html)[1]
        self.assertIn('Per person', workout)
        self.assertIn('2 snacks', workout)
        self.assertIn('1 fairlife', workout.lower())
        self.assertIn('training', workout.lower())

    def test_legacy_fixture_still_renders_without_invented_macros(self):
        legacy = json.loads(FIXTURE.read_text())
        before = copy.deepcopy(legacy)
        html = builder.render_page(legacy)
        self.assertEqual(legacy, before)
        self.assertEqual(html.count('class="recipe"'), 8)
        self.assertNotIn('g carbs', html)
        self.assertNotIn('g fat', html)
        self.assertNotIn('Estimated energy split', html)


if __name__ == '__main__':
    unittest.main()
