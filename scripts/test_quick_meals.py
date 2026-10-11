"""Dining-out and assembly guides must describe the actual low-effort workflow."""
import json
import re
import unittest
from pathlib import Path
import build

class QuickMealGuideTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((Path(__file__).parent / 'fixtures/meal-plan.json').read_text())
        self.plan = self.data['plans']['four-day-cut']
        self.plan['days'] = ['day-01']
        self.data['recipes']['buffalo']['preparation'] = 'dining-out'
        self.data['recipes']['honey']['preparation'] = 'assemble'

    def test_dining_out_guide_says_order_instead_of_cook(self):
        html = build.render_page(self.data)
        self.assertIn('Order this meal from the restaurant.', html)
        order = re.search(r'<details class="recipe" id="buffalo">(.*?)</details>', html)[1]
        self.assertIn('Order on day 1.', order)
        self.assertNotIn('Make fresh on', order)

    def test_assembly_meals_do_not_create_batch_cooking_sessions(self):
        html = build.render_page(self.data)
        self.assertEqual(build.schedule(self.data, self.plan)[1], [])
        self.assertIn('Breakfast fresh. No batch cooking.', html)
        self.assertIn('Assemble this meal; follow the quick heating steps if listed.', html)
        guide = re.search(r'<details class="daily-guide".*?</details>', html)[0]
        self.assertNotIn('Cook fresh for this meal.', guide)
        self.assertIn('Order Buffalo chicken.', guide)
        self.assertIn('Assemble Honey garlic thighs.', guide)

if __name__ == '__main__': unittest.main()
