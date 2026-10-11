import unittest
import json
from pathlib import Path
from nutrition import recipe_nutrition, check_nutrition

class IngredientNutritionTests(unittest.TestCase):
    def setUp(self):
        self.data = {'items': {'milk': {'units': {'cup': 1, 'fl oz': '1/8'}, 'nutrition': {'quantity': 1, 'unit': 'cup', 'calories': 120, 'carbsGrams': 6, 'proteinGrams': 13, 'fatGrams': 4.5}}}, 'recipes': {'latte': {'servings': 2, 'ingredients': [{'itemId': 'milk', 'quantity': 12, 'unit': 'fl oz'}, {'itemId': 'milk', 'quantity': None, 'unit': 'cup', 'asNeeded': True}], 'nutrition': {'calories': 90, 'carbsGrams': 4.5, 'proteinGrams': 9.8, 'fatGrams': 3.4}}}}
    def test_conversion_and_servings(self):
        self.assertEqual(recipe_nutrition(self.data, self.data['recipes']['latte']), self.data['recipes']['latte']['nutrition'])
    def test_detects_metadata_drift(self):
        self.assertEqual(check_nutrition(self.data), [])
        self.data['recipes']['latte']['nutrition']['proteinGrams'] = 100
        self.assertIn('latte', check_nutrition(self.data)[0])
    def test_missing_reference_fails(self):
        del self.data['items']['milk']['nutrition']
        with self.assertRaisesRegex(ValueError, 'milk'): recipe_nutrition(self.data, self.data['recipes']['latte'])

class LiveNutritionTests(unittest.TestCase):
    def test_catalog_nutrition_matches_measured_ingredients(self):
        data = json.loads((Path(__file__).resolve().parents[1] / 'meal-plan.json').read_text())
        self.assertEqual(check_nutrition(data), [])

if __name__ == '__main__': unittest.main()
