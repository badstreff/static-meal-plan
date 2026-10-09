import copy
import importlib.util
import json
import re
import subprocess
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'scripts/fixtures/meal-plan.json'
spec = importlib.util.spec_from_file_location('meal_builder', ROOT / 'scripts/build.py')
builder = None
if spec and Path(spec.origin).exists():
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)


class MealPlanTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(builder, 'JSON meal-plan builder has not been implemented')
        self.assertTrue((ROOT / 'meal-plan.json').exists(), 'Meal content has not been moved into JSON')
        self.data = json.loads(FIXTURE.read_text())

    def test_live_content_validates_and_renders_selected_plan(self):
        data = builder.load_data(ROOT / 'meal-plan.json')
        html = builder.render_page(data)
        plan = data['plans'][data['activePlanId']]
        self.assertEqual(html.count('class="day-card"'), len(plan['days']))
        self.assertEqual(html.count('class="recipe"'), len(builder.selected_counts(data, plan)))
        self.assertIn(f'data-plan-id="{data["activePlanId"]}"', html)

    def alternate(self, days, people=1):
        plan = copy.deepcopy(self.data['plans']['four-day-cut'])
        plan.update(title='Alternate plan', days=days, people=people)
        self.data['plans']['alternate'] = plan
        self.data['activePlanId'] = 'alternate'
        return plan

    def test_current_plan_preserves_food_preferences(self):
        html = builder.render_page(self.data)
        self.assertEqual(html.count('class="day-card"'), 4)
        self.assertEqual(html.count('class="recipe"'), 8)
        for text in ['steel-cut oats', 'brown sugar', 'diced cooked ham', 'Fairlife', '150 calories']:
            self.assertIn(text, html)
        self.assertIn('40 g protein', html)
        self.assertIn('./themes.js', html)

    def test_active_plan_selects_only_its_days_and_recipes(self):
        self.alternate(['day-01'])
        html = builder.render_page(self.data)
        self.assertIn('Alternate plan', html)
        self.assertEqual(html.count('class="day-card"'), 1)
        self.assertEqual(html.count('class="recipe"'), 4)
        self.assertNotIn('id="ham"', html)
        self.assertNotIn('id="greek"', html)
        self.assertNotIn('Four days.', html)

    def test_repeated_days_have_unique_guides_and_scaled_groceries(self):
        plan = self.alternate(['day-01', 'day-01'])
        html = builder.render_page(self.data)
        ids = re.findall(r'\bid="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn('id="guide-01"', html)
        self.assertIn('id="guide-02"', html)
        groceries = {row['id']: row for row in builder.build_groceries(self.data, plan)}
        self.assertEqual(groceries['oats']['quantity'], Fraction(120))
        self.assertEqual(groceries['chicken-breast']['quantity'], Fraction(1))

    def test_quantities_aggregate_before_shopping_rounding(self):
        groceries = {row['id']: row for row in builder.build_groceries(self.data, self.data['plans']['four-day-cut'])}
        self.assertEqual(groceries['chicken-breast']['quantity'], Fraction(9, 4))
        self.assertEqual(groceries['chicken-thighs']['quantity'], Fraction(3))
        self.assertEqual(groceries['honey']['quantity'], Fraction(11, 3))
        self.assertEqual(groceries['yogurt']['quantity'], Fraction(640))
        self.assertIn('650 g', groceries['yogurt']['detail'])
        self.assertEqual(groceries['protein-powder']['quantity'], Fraction(80))

    def test_people_scale_the_whole_plan(self):
        plan = self.alternate(['day-01'], people=2)
        groceries = {row['id']: row for row in builder.build_groceries(self.data, plan)}
        self.assertEqual(groceries['oats']['quantity'], Fraction(120))
        self.assertEqual(groceries['chicken-breast']['quantity'], Fraction(1))

    def test_unused_ingredients_do_not_appear_in_groceries(self):
        plan = self.alternate(['day-01'])
        ids = {row['id'] for row in builder.build_groceries(self.data, plan)}
        self.assertNotIn('ham', ids)
        self.assertNotIn('olives', ids)
        self.assertIn('fairlife', ids)

    def test_unknown_plan_is_rejected(self):
        self.data['activePlanId'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'activePlanId'):
            builder.validate_data(self.data)

    def test_unknown_day_is_rejected_even_in_inactive_plans(self):
        self.data['plans']['inactive'] = dict(self.data['plans']['four-day-cut'], days=['missing'])
        with self.assertRaisesRegex(ValueError, 'missing'):
            builder.validate_data(self.data)

    def test_unknown_recipe_is_rejected(self):
        self.data['days']['day-01']['meals']['lunch'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'missing'):
            builder.validate_data(self.data)

    def test_missing_meal_is_rejected(self):
        del self.data['days']['day-01']['meals']['snack']
        with self.assertRaisesRegex(ValueError, 'snack'):
            builder.validate_data(self.data)

    def test_invalid_quantities_are_rejected(self):
        ingredient = self.data['recipes']['oats']['ingredients'][0]
        for value in [0, -1, True, None, '0', '-2', '2/0', 'NaN', float('inf')]:
            with self.subTest(value=value):
                ingredient['quantity'] = value
                with self.assertRaisesRegex(ValueError, 'quantity'):
                    builder.validate_data(self.data)

    def test_invalid_recipe_servings_are_rejected(self):
        for servings in [0, -1, True, 1.5]:
            self.data['recipes']['buffalo']['servings'] = servings
            with self.assertRaisesRegex(ValueError, 'servings'):
                builder.validate_data(self.data)

    def test_unknown_ingredient_or_unit_is_rejected(self):
        ingredient = self.data['recipes']['oats']['ingredients'][0]
        ingredient['itemId'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'missing'):
            builder.validate_data(self.data)
        ingredient['itemId'] = 'oats'
        ingredient['unit'] = 'bucket'
        with self.assertRaisesRegex(ValueError, 'bucket'):
            builder.validate_data(self.data)

    def test_empty_or_unsupported_plan_is_rejected(self):
        self.data['plans']['four-day-cut']['days'] = []
        with self.assertRaisesRegex(ValueError, 'days'):
            builder.validate_data(self.data)
        self.data['schemaVersion'] = 99
        with self.assertRaisesRegex(ValueError, 'schemaVersion'):
            builder.validate_data(self.data)

    def test_content_is_escaped(self):
        self.data['recipes']['oats']['title'] = '<script>alert("x")</script>'
        html = builder.render_page(self.data)
        self.assertNotIn('<script>alert(', html)
        self.assertIn('&lt;script&gt;', html)

    def test_unsafe_source_links_are_rejected(self):
        self.data['recipes']['ham']['source']['url'] = 'javascript:alert(1)'
        with self.assertRaisesRegex(ValueError, 'url'):
            builder.validate_data(self.data)

    def test_grocery_state_is_scoped_to_plan_and_quantity(self):
        first = builder.render_page(self.data)
        key = re.search(r'data-grocery-key="([^"]+)"', first)[1]
        self.alternate(['day-01'])
        second = builder.render_page(self.data)
        self.assertNotEqual(key, re.search(r'data-grocery-key="([^"]+)"', second)[1])
        old_key = re.search(r'data-grocery-key="([^"]+)"', second)[1]
        self.data['recipes']['oats']['ingredients'][0]['quantity'] = 90
        self.assertNotEqual(old_key, re.search(r'data-grocery-key="([^"]+)"', builder.render_page(self.data))[1])

    def test_output_is_deterministic(self):
        self.assertEqual(builder.render_page(self.data), builder.render_page(copy.deepcopy(self.data)))

    def test_meal_order_is_independent_of_json_object_order(self):
        self.data['days']['day-01']['meals'] = dict(reversed(list(self.data['days']['day-01']['meals'].items())))
        html = builder.render_page(self.data)
        card = re.search(r'<article class="day-card">(.*?)</article>', html)[1]
        self.assertEqual(re.findall(r'<div class="meal-row"><span>(.*?)</span>', card), ['Breakfast','Lunch','Dinner','Snack'])

    def test_fresh_recipe_with_multiple_base_servings_scales_to_one_meal(self):
        self.data['recipes']['oats']['servings'] = 2
        for row in self.data['recipes']['oats']['ingredients']:
            if row['quantity'] is not None:
                row['quantity'] = str(Fraction(str(row['quantity'])) * 2)
        html = builder.render_page(self.data)
        oats = re.search(r'<details class="recipe" id="oats">(.*?)</details>', html)[1]
        self.assertIn('60 g dry steel-cut oats', oats)
        self.assertIn('1 breakfast', oats)

    def test_scaled_batch_steps_use_equal_portions(self):
        self.alternate(['day-02','day-02','day-02'])
        html = builder.render_page(self.data)
        cottage = re.search(r'<details class="recipe" id="cottage">(.*?)</details>', html)[1]
        self.assertIn('three bowls', cottage)
        self.assertNotIn('half the berries', cottage)

    def test_plan_copy_can_override_global_intro_and_notes(self):
        self.alternate(['day-01'])['copy'] = {'heroDescription':'An alternate introduction.','workoutNote':'A plan-specific snack note.'}
        html = builder.render_page(self.data)
        self.assertIn('An alternate introduction.', html)
        self.assertIn('A plan-specific snack note.', html)

    def test_recipe_ids_cannot_collide_with_generated_page_ids(self):
        self.data['recipes']['guide-01'] = copy.deepcopy(self.data['recipes']['oats'])
        with self.assertRaisesRegex(ValueError, 'ID'):
            builder.validate_data(self.data)

    def test_scaled_instructions_use_the_listed_ingredient_amounts(self):
        self.alternate(['day-01'], people=2)
        html = builder.render_page(self.data)
        oats = re.search(r'<details class="recipe" id="oats">(.*?)</details>', html)[1]
        self.assertIn('80 g protein', oats)
        steps = re.search(r'<ol>(.*?)</ol>', oats)[1]
        self.assertNotIn('40 g', steps)
        self.assertIn('listed protein amount', steps)
        self.alternate(['day-01'])
        buffalo = re.search(r'<details class="recipe" id="buffalo">(.*?)</details>', builder.render_page(self.data))[1]
        self.assertIn('⅓ tsp olive oil for cooking', buffalo)
        steps = re.search(r'<ol>(.*?)</ol>', buffalo)[1]
        self.assertNotIn('⅔ tsp', steps)
        self.assertIn('listed cooking oil', steps)

    def test_fresh_lunch_and_dinner_guides_never_call_for_reheating(self):
        self.alternate(['day-01','day-01'])
        for rid in ['buffalo','honey']:
            self.data['recipes'][rid]['preparation'] = 'fresh'
        html = builder.render_page(self.data)
        for guide in re.findall(r'<details class="daily-guide".*?</details>', html):
            self.assertNotIn('reheat', guide.lower())
            self.assertNotIn('prepared portion', guide)
            self.assertIn('Make Buffalo chicken fresh.', guide)
            self.assertEqual(guide.count('Cook fresh for this meal.'), 2)

    def test_batch_breakfast_guides_prepare_on_first_day_and_serve_later(self):
        self.alternate(['day-01','day-01'])
        self.data['recipes']['oats']['preparation'] = 'batch'
        html = builder.render_page(self.data)
        first = re.search(r'<details class="daily-guide" id="guide-01">(.*?)</details>', html)[1]
        later = re.search(r'<details class="daily-guide" id="guide-02">(.*?)</details>', html)[1]
        self.assertIn('Make 2 portions of Oats &amp; apple.', first)
        self.assertNotIn('Cook fresh this morning.', first)
        self.assertNotIn('Oats &amp; apple fresh', later)
        self.assertIn('from the prepared batch', later)
        self.assertNotIn('<dd>Made fresh</dd>', html)

    def test_build_publishes_only_generated_page_and_runtime_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / '_site'
            builder.build_site(FIXTURE, output)
            self.assertEqual({p.name for p in output.iterdir()}, {'index.html', 'styles.css', 'app.js', 'themes.js'})
            self.assertIn('data-plan-id="four-day-cut"', (output / 'index.html').read_text())

    def test_invalid_build_does_not_overwrite_previous_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            output = path / '_site'
            output.mkdir()
            (output / 'index.html').write_text('previous page')
            self.data['activePlanId'] = 'missing'
            source = path / 'bad.json'
            source.write_text(json.dumps(self.data))
            with self.assertRaises(ValueError):
                builder.build_site(source, output)
            self.assertEqual((output / 'index.html').read_text(), 'previous page')

    def test_cli_rejects_duplicate_keys_and_non_json_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            for content in ['{"schemaVersion":1,"schemaVersion":2}', '{"number":NaN}']:
                source = Path(directory) / 'bad.json'
                source.write_text(content)
                result = subprocess.run(['python3', str(ROOT / 'scripts/build.py'), '--data', str(source), '--output-dir', str(Path(directory) / 'output')], text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Build failed:', result.stderr)
                self.assertFalse((Path(directory) / 'output').exists())


if __name__ == '__main__':
    unittest.main()
