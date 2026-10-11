#!/usr/bin/env python3
"""Recalculate estimated recipe nutrition from declared ingredient references.

All weights describe ingredients as listed (raw meat and dry rice). Optional,
unmeasured garnishes are excluded. Branded labels and generic assumptions live
with each item in meal-plan.json; they are estimates, not a nutrition database.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path

FIELDS = ('calories', 'carbsGrams', 'proteinGrams', 'fatGrams')


def ingredient_nutrition(data, ingredient):
    if ingredient.get('asNeeded'):
        return dict.fromkeys(FIELDS, 0.0)
    item_id = ingredient['itemId']
    item = data['items'][item_id]
    reference = item.get('nutrition')
    if not reference:
        raise ValueError(f'Missing ingredient nutrition reference: {item_id}')
    factor = (Fraction(str(ingredient['quantity'])) * Fraction(str(item['units'][ingredient['unit']]))
              / (Fraction(str(reference['quantity'])) * Fraction(str(item['units'][reference['unit']]))))
    return {key: float(factor) * reference[key] for key in FIELDS}


def recipe_nutrition(data, recipe, rounded=True):
    totals = dict.fromkeys(FIELDS, 0.0)
    for ingredient in recipe['ingredients']:
        values = ingredient_nutrition(data, ingredient)
        for key in FIELDS:
            totals[key] += values[key] / recipe['servings']
    if rounded:
        return {key: round(value) if key == 'calories' else round(value, 1) for key, value in totals.items()}
    return totals


def check_nutrition(data):
    issues = []
    for recipe_id, recipe in data['recipes'].items():
        expected = recipe_nutrition(data, recipe)
        for key, value in expected.items():
            if recipe['nutrition'].get(key) != value:
                issues.append(f'{recipe_id}.{key}: stored {recipe["nutrition"].get(key)}, ingredients {value}')
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', default=str(Path(__file__).resolve().parents[1] / 'meal-plan.json'))
    parser.add_argument('--write', action='store_true', help='Update recipe estimates from ingredient references')
    args = parser.parse_args()
    path = Path(args.path)
    data = json.loads(path.read_text())
    if args.write:
        for recipe in data['recipes'].values():
            recipe['nutrition'] = recipe_nutrition(data, recipe)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    issues = check_nutrition(data)
    if issues:
        print('\n'.join(issues))
        return 1
    print(f'Ingredient nutrition matches all {len(data["recipes"])} recipes.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
