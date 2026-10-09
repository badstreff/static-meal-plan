#!/usr/bin/env python3
"""Validate meal-plan.json and build a dependency-free static Pages site."""
import argparse
import hashlib
import json
import math
import re
import shutil
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MEALS = ('breakfast', 'lunch', 'dinner', 'snack')
ID_PATTERN = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
FRACTIONS = {Fraction(1, 2): '½', Fraction(1, 3): '⅓', Fraction(2, 3): '⅔', Fraction(1, 4): '¼', Fraction(3, 4): '¾', Fraction(1, 5): '⅕', Fraction(2, 5): '⅖', Fraction(3, 5): '⅗', Fraction(4, 5): '⅘', Fraction(1, 6): '⅙', Fraction(5, 6): '⅚', Fraction(1, 8): '⅛', Fraction(3, 8): '⅜', Fraction(5, 8): '⅝', Fraction(7, 8): '⅞'}
WORDS = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten')
UNIT_LABELS = {'count': '', 'portion': '', 'g-protein': 'g protein', 'cup-cooked': 'cup cooked', 'cup-dry': 'cup dry', 'tsp-dry': 'tsp dry'}
PLAN_COPY_FIELDS = {'heroDescription', 'planAside', 'recipeIntro', 'targetNote', 'workoutNote', 'nutritionNote', 'shoppingNote', 'storageNote', 'footer'}
RESERVED_RECIPE_IDS = {'main', 'plan', 'guides', 'groceries', 'palette-select', 'palette-note', 'list-progress'}


def fail(path, message):
    raise ValueError(f'{path}: {message}')


def mapping(value, path):
    if not isinstance(value, dict):
        fail(path, 'must be an object')
    return value


def text(value, path, allow_empty=False):
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        fail(path, 'must be nonempty text')
    return value


def integer(value, path):
    if type(value) is not int or value < 1:
        fail(path, 'must be a positive integer')
    return value


def array(value, path, nonempty=True):
    if not isinstance(value, list) or (nonempty and not value):
        fail(path, 'must be a nonempty array' if nonempty else 'must be an array')
    return value


def quantity(value, path='quantity'):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        fail(path, 'quantity must be a positive number or fraction string')
    try:
        result = Fraction(str(value))
    except (ValueError, ZeroDivisionError, OverflowError):
        fail(path, 'quantity must be a finite positive number or fraction string')
    if result <= 0:
        fail(path, 'quantity must be positive')
    return result


def safe_url(value, path):
    text(value, path)
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        fail(path, 'url must be an absolute HTTPS URL without credentials')


def format_fields(value, allowed, path):
    text(value, path)
    tokens = re.findall(r'\{([^{}]*)\}', value)
    if any(token not in allowed for token in tokens) or re.search(r'[{}]', re.sub(r'\{[^{}]*\}', '', value)):
        fail(path, f'only these placeholders are supported: {", ".join(sorted(allowed))}')


def validate_data(data):
    mapping(data, 'document')
    if type(data.get('schemaVersion')) is not int or data['schemaVersion'] != 1:
        fail('schemaVersion', 'only version 1 is supported')
    collections = {}
    for name in ('plans', 'days', 'recipes', 'items'):
        collection = mapping(data.get(name), name)
        if not collection:
            fail(name, 'must not be empty')
        for key, value in collection.items():
            if not isinstance(key, str) or not ID_PATTERN.fullmatch(key):
                fail(name, f'invalid ID {key!r}; use lowercase letters, numbers and hyphens')
            mapping(value, f'{name}.{key}')
        collections[name] = collection
    active = data.get('activePlanId')
    if not isinstance(active, str) or active not in collections['plans']:
        fail('activePlanId', f'unknown plan {active!r}')
    site = mapping(data.get('site'), 'site')
    for field in ('brand', 'heroHeading', 'heroDescription', 'planAside', 'guideHeading', 'recipeHeading', 'recipeIntro', 'targetNote', 'workoutNote', 'nutritionNote', 'shoppingNote', 'storageNote', 'storageSafety', 'footer'):
        text(site.get(field), f'site.{field}')
    for field in ('storageUrl', 'repoUrl'):
        safe_url(site.get(field), f'site.{field}')
    groups = array(data.get('groceryGroups'), 'groceryGroups')
    for group in groups:
        text(group, 'groceryGroups')
    if len(groups) != len(set(groups)):
        fail('groceryGroups', 'must contain unique names')
    for item_id, item in collections['items'].items():
        path = f'items.{item_id}'
        text(item.get('label'), f'{path}.label')
        if item.get('group') not in groups:
            fail(path, 'group must be in groceryGroups')
        unit = text(item.get('unit'), f'{path}.unit')
        units = mapping(item.get('units'), f'{path}.units')
        if unit not in units or quantity(units[unit], f'{path}.units.{unit}') != 1:
            fail(path, 'canonical unit must have a conversion factor of 1')
        for name, factor in units.items():
            text(name, f'{path}.units')
            quantity(factor, f'{path}.units.{name}')
        shopping = mapping(item.get('shopping', {}), f'{path}.shopping')
        for field in ('roundTo', 'packSize', 'approximateGramsPerUnit'):
            if field in shopping:
                quantity(shopping[field], f'{path}.shopping.{field}')
        if 'packSize' in shopping:
            text(shopping.get('packLabel'), f'{path}.shopping.packLabel')
        if shopping.get('mode') not in (None, 'pantry'):
            fail(path, 'shopping.mode must be pantry when supplied')
        for field in ('format', 'suffix'):
            if field in shopping:
                format_fields(shopping[field], {'quantity'}, f'{path}.shopping.{field}')
        if 'asNeeded' in shopping:
            text(shopping['asNeeded'], f'{path}.shopping.asNeeded')
        if 'showRequired' in shopping and type(shopping['showRequired']) is not bool:
            fail(path, 'shopping.showRequired must be a boolean')
        if 'variants' in item:
            for key, label in mapping(item['variants'], f'{path}.variants').items():
                text(key, f'{path}.variants')
                text(label, f'{path}.variants.{key}')
        if 'alternatives' in item:
            for choice in array(item['alternatives'], f'{path}.alternatives'):
                mapping(choice, f'{path}.alternatives')
                quantity(choice.get('quantity'), f'{path}.alternatives.quantity')
                text(choice.get('unit'), f'{path}.alternatives.unit')
                text(choice.get('label'), f'{path}.alternatives.label')
    for recipe_id, recipe in collections['recipes'].items():
        path = f'recipes.{recipe_id}'
        if recipe_id in RESERVED_RECIPE_IDS or recipe_id.startswith(('guide-', 'item-')):
            fail(path, 'recipe ID conflicts with a generated page ID')
        for field in ('title', 'shortTitle', 'prepTime', 'description', 'note'):
            text(recipe.get(field), f'{path}.{field}')
        if recipe.get('kind') not in MEALS:
            fail(path, f'kind must be one of {MEALS}')
        if recipe.get('preparation') not in ('fresh', 'batch'):
            fail(path, 'preparation must be fresh or batch')
        integer(recipe.get('servings'), f'{path}.servings')
        nutrition = mapping(recipe.get('nutrition'), f'{path}.nutrition')
        for field in ('calories', 'proteinGrams'):
            quantity(nutrition.get(field), f'{path}.nutrition.{field}')
        for index, row in enumerate(array(recipe.get('ingredients'), f'{path}.ingredients')):
            rp = f'{path}.ingredients[{index}]'
            mapping(row, rp)
            item_id = row.get('itemId')
            if not isinstance(item_id, str) or item_id not in collections['items']:
                fail(rp, f'unknown itemId {item_id!r}')
            item = collections['items'][item_id]
            if row.get('unit') not in item['units']:
                fail(rp, f'unknown unit {row.get("unit")!r} for {item_id}')
            if row.get('asNeeded') is True:
                if row.get('quantity') is not None:
                    fail(rp, 'asNeeded ingredients must have null quantity')
            else:
                quantity(row.get('quantity'), f'{rp}.quantity')
            if 'asNeeded' in row and type(row['asNeeded']) is not bool:
                fail(rp, 'asNeeded must be a boolean')
            if 'label' in row:
                text(row['label'], f'{rp}.label')
            if 'variant' in row and row['variant'] not in item.get('variants', {}):
                fail(rp, f'unknown variant {row["variant"]!r}')
            if 'variants' in item and row.get('variant') not in item['variants']:
                fail(rp, 'ingredient must select a variant')
            if 'format' in row:
                format_fields(row['format'], {'amount', 'label', 'alternatives'}, f'{rp}.format')
                if '{alternatives}' in row['format'] and not item.get('alternatives'):
                    fail(rp, 'alternatives format requires item alternatives')
        for step in array(recipe.get('steps'), f'{path}.steps'):
            format_fields(step, {'portions', 'portionsWord'}, f'{path}.steps')
        if recipe.get('source') is not None:
            source = mapping(recipe['source'], f'{path}.source')
            text(source.get('label'), f'{path}.source.label')
            safe_url(source.get('url'), f'{path}.source.url')
    for day_id, day in collections['days'].items():
        path = f'days.{day_id}.meals'
        meals = mapping(day.get('meals'), path)
        if set(meals) != set(MEALS):
            fail(path, f'must contain breakfast, lunch, dinner and snack; got {list(meals)}')
        for slot, recipe_id in meals.items():
            if not isinstance(recipe_id, str) or recipe_id not in collections['recipes']:
                fail(path, f'unknown recipe {recipe_id!r}')
            if collections['recipes'][recipe_id]['kind'] != slot:
                fail(path, f'{recipe_id} is not a {slot} recipe')
    for plan_id, plan in collections['plans'].items():
        path = f'plans.{plan_id}'
        text(plan.get('title'), f'{path}.title')
        integer(plan.get('people'), f'{path}.people')
        if 'copy' in plan:
            for field, value in mapping(plan['copy'], f'{path}.copy').items():
                if field not in PLAN_COPY_FIELDS:
                    fail(f'{path}.copy', f'unknown copy field {field!r}')
                text(value, f'{path}.copy.{field}')
        targets = mapping(plan.get('targets'), f'{path}.targets')
        for field in ('calories', 'proteinGrams'):
            quantity(targets.get(field), f'{path}.targets.{field}')
        for day_id in array(plan.get('days'), f'{path}.days'):
            if not isinstance(day_id, str) or day_id not in collections['days']:
                fail(f'{path}.days', f'unknown day {day_id!r}')
        for item_id in array(plan.get('extraItems', []), f'{path}.extraItems', nonempty=False):
            if not isinstance(item_id, str) or item_id not in collections['items']:
                fail(f'{path}.extraItems', f'unknown item {item_id!r}')
            if not collections['items'][item_id].get('shopping', {}).get('asNeeded'):
                fail(f'{path}.extraItems', 'extraItems must have an asNeeded shopping description')
    for note in array(data.get('measurementNotes'), 'measurementNotes'):
        text(note, 'measurementNotes')
    return data


def pretty(value):
    value = Fraction(value)
    whole, remainder = divmod(value.numerator, value.denominator)
    part = Fraction(remainder, value.denominator)
    if not part:
        return str(whole)
    symbol = FRACTIONS.get(part, f'{part.numerator}/{part.denominator}')
    return (str(whole) + ('' if part in FRACTIONS else ' ') if whole else '') + symbol


def word(value):
    return WORDS[value] if 0 <= value < len(WORDS) else str(value)


def amount_label(value, unit):
    label = UNIT_LABELS.get(unit, unit)
    if value > 1:
        first, *rest = label.split(' ')
        if first in ('cup', 'pint', 'slice', 'clove', 'lemon'):
            label = ' '.join([first + 's', *rest])
    return f'{pretty(value)} {label}'.strip()


def alternatives(item, factor):
    return ' OR '.join(f'{amount_label(quantity(choice["quantity"]) * factor, choice["unit"])} {choice["label"]}' for choice in item['alternatives'])


def selected_counts(data, plan):
    return Counter(recipe_id for day_id in plan['days'] for recipe_id in data['days'][day_id]['meals'].values())


def round_up(value, step):
    return math.ceil(value / step) * step


def build_groceries(data, plan):
    totals = defaultdict(Fraction)
    variants = defaultdict(lambda: defaultdict(Fraction))
    needed = set(plan.get('extraItems', []))
    for recipe_id, uses in selected_counts(data, plan).items():
        recipe = data['recipes'][recipe_id]
        factor = Fraction(uses * plan['people'], recipe['servings'])
        for row in recipe['ingredients']:
            item_id = row['itemId']
            needed.add(item_id)
            if row.get('asNeeded'):
                continue
            item = data['items'][item_id]
            value = quantity(row['quantity']) * quantity(item['units'][row['unit']]) * factor
            totals[item_id] += value
            if 'variant' in row:
                variants[item_id][row['variant']] += value
    groceries = []
    for item_id, item in data['items'].items():
        if item_id not in needed:
            continue
        total = totals[item_id]
        shopping = item.get('shopping', {})
        rounded = round_up(total, quantity(shopping['roundTo'])) if total and 'roundTo' in shopping else total
        if item.get('alternatives'):
            detail = alternatives(item, total)
        elif shopping.get('mode') == 'pantry' or not total:
            detail = shopping.get('asNeeded', 'To taste')
        elif item.get('variants'):
            step = quantity(shopping.get('roundTo', 1))
            detail = ' + '.join(f'{pretty(round_up(variants[item_id][key], step))} {label}' for key, label in item['variants'].items() if variants[item_id][key])
        elif 'packSize' in shopping:
            count = math.ceil(total / quantity(shopping['packSize']))
            detail = (f'{count} × ' if count > 1 else '1 ' if shopping['packLabel'] in ('can', 'large head') else '') + shopping['packLabel']
            if shopping.get('showRequired'):
                detail += '; use ' + amount_label(total, item['unit'])
        elif 'approximateGramsPerUnit' in shopping:
            grams = total * quantity(shopping['approximateGramsPerUnit'])
            detail = f'About {pretty(grams)} g'
        elif 'format' in shopping:
            detail = shopping['format'].format(quantity=pretty(rounded))
        else:
            detail = amount_label(rounded, item['unit'])
        if total and shopping.get('mode') != 'pantry' and 'suffix' in shopping:
            detail += ' · ' + shopping['suffix'].format(quantity=pretty(total))
        groceries.append({'id':item_id, 'name':item['label'], 'group':item['group'], 'quantity':total, 'detail':detail})
    return groceries


def rich_text(value):
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escape(value))


def icon(name):
    paths = {'arrow':'<path d="M5 12h14m-5-5 5 5-5 5"/>', 'leaf':'<path d="M19 4C9 3 4 8 5 14s11 7 14-10Z"/><path d="m5 20 9-10"/>'}
    return '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' + paths[name] + '</svg>'


def joined(values):
    if len(values) < 2:
        return ''.join(values)
    return ', '.join(values[:-1]) + ' and ' + values[-1]


def day_phrase(positions):
    return ('day ' if len(positions) == 1 else 'days ') + joined([str(value) for value in positions])


def schedule(data, plan):
    positions = defaultdict(list)
    for number, day_id in enumerate(plan['days'], 1):
        for recipe_id in data['days'][day_id]['meals'].values():
            positions[recipe_id].append(number)
    cooking = sorted({days[0] for recipe_id, days in positions.items() if data['recipes'][recipe_id]['preparation'] == 'batch'})
    return positions, cooking


def ingredient_text(data, row, factor):
    item = data['items'][row['itemId']]
    label = row.get('label', item['label'].lower())
    measured = quantity(row['quantity']) * factor if not row.get('asNeeded') else None
    amount = amount_label(measured, row['unit']) if measured is not None else ''
    choices = alternatives(item, measured * quantity(item['units'][row['unit']])) if item.get('alternatives') and measured is not None else ''
    pattern = row.get('format', '{amount} {label}' if measured is not None else '{label}, to taste')
    return pattern.format(amount=amount, label=label, alternatives=choices)


def recipe_html(data, plan, recipe_id, uses, positions):
    recipe = data['recipes'][recipe_id]
    servings = uses * plan['people'] if recipe['preparation'] == 'batch' else plan['people']
    factor = Fraction(servings, recipe['servings'])
    singular = recipe['kind'] if recipe['kind'] != 'lunch' else 'lunch'
    serving_label = singular + ('es' if singular == 'lunch' else 's') if servings != 1 else singular
    metadata = f'{recipe["prepTime"]} · {servings} {serving_label}'
    when = positions[recipe_id]
    calendar = (f'Cook on day {when[0]}; eat on {day_phrase(when)}.' if recipe['preparation'] == 'batch' else f'Make fresh on {day_phrase(when)}.')
    ingredients = ''.join('<li>' + escape(ingredient_text(data, row, factor)) + '</li>' for row in recipe['ingredients'])
    steps = ''.join('<li>' + escape(step.format(portions=servings, portionsWord=word(servings))) + '</li>' for step in recipe['steps'])
    source = recipe.get('source')
    source_html = f'<a class="source" href="{escape(source["url"], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(source["label"])} ↗</a>' if source else '<span class="source">Your breakfast preference</span>'
    nutrition = recipe['nutrition']
    return f'<details class="recipe" id="{recipe_id}"><summary><span class="recipe-kind">{escape(recipe["kind"].title())}</span><span class="recipe-title">{escape(recipe["title"])}</span><span class="recipe-meta">{escape(metadata)}</span><span class="plus" aria-hidden="true">+</span></summary><div class="recipe-body"><p>{escape(recipe["description"])}</p><div class="nutrition"><span>~{pretty(quantity(nutrition["calories"]))} kcal <small>per meal</small></span><span>~{pretty(quantity(nutrition["proteinGrams"]))} g protein</span></div><div class="recipe-columns"><div><h4>What you need</h4><ul>{ingredients}</ul></div><div><h4>How to make it</h4><ol>{steps}</ol></div></div><p class="recipe-note">{escape(calendar)} {rich_text(recipe["note"])}</p>{source_html}</div></details>'


def render_page(data):
    validate_data(data)
    plan = data['plans'][data['activePlanId']]
    site = dict(data['site'], **plan.get('copy', {}))
    count = len(plan['days'])
    day_title = f'{word(count).capitalize()} ' + ('day' if count == 1 else 'days')
    positions, cooking = schedule(data, plan)
    counts = selected_counts(data, plan)
    groceries = build_groceries(data, plan)
    fingerprint = hashlib.sha256(json.dumps([(row['id'], row['name'], str(row['quantity']), row['detail']) for row in groceries], ensure_ascii=False).encode()).hexdigest()[:12]
    cards, guides = [], []
    for number, day_id in enumerate(plan['days'], 1):
        no = f'{number:02d}'
        meals = data['days'][day_id]['meals']
        rows = ''.join(f'<div class="meal-row"><span>{slot.title()}</span><a href="#{meals[slot]}">{escape(data["recipes"][meals[slot]]["shortTitle"])}</a></div>' for slot in MEALS)
        cards.append(f'<article class="day-card"><div class="day-label">DAY <strong>{no}</strong></div>{rows}<a class="day-link" href="#guide-{no}">Your day {number} guide {icon("arrow")}</a></article>')
        batches = [rid for rid in meals.values() if data['recipes'][rid]['preparation'] == 'batch' and positions[rid][0] == number]
        if batches:
            ordinal = {1:'first',2:'second',3:'third'}.get(cooking.index(number)+1, str(cooking.index(number)+1))
            title = f'Cook the {ordinal} batch'
            statements = []
            for rid in batches:
                recipe = data['recipes'][rid]
                statements.append(f'Make {counts[rid] * plan["people"]} portions of {recipe["shortTitle"]}.')
                later = positions[rid][1:]
                if later:
                    statements.append(f'Save the remaining portions for {day_phrase(later)}.')
            note = ' '.join(statements)
        else:
            fresh = [data['recipes'][meals[slot]] for slot in MEALS if data['recipes'][meals[slot]]['preparation'] == 'fresh']
            prepared = len(fresh) < len(MEALS)
            title = 'Fresh meals and prepared portions' if fresh and prepared else 'Serve prepared portions' if prepared else 'Make today’s meals fresh'
            note = ' '.join(f'Make {recipe["shortTitle"]} fresh.' for recipe in fresh)
            if prepared:
                note += ' Serve prepared portions. Reheat cooked meals until hot throughout (165°F / 74°C); add cold toppings afterward.'
        guide_rows = []
        for slot in MEALS:
            rid = meals[slot]
            recipe = data['recipes'][rid]
            if recipe['preparation'] == 'fresh':
                instruction = 'Cook fresh this morning.' if slot == 'breakfast' else 'Make fresh for this snack.' if slot == 'snack' else 'Cook fresh for this meal.'
            elif positions[rid][0] == number:
                instruction = 'Prepare the batch today; serve one portion per person.'
            else:
                instruction = 'Serve one portion per person from the prepared batch.'
            if slot == 'snack' and 'fairlife' in plan.get('extraItems', []):
                instruction += ' Use the Fairlife version if you train today.'
            guide_rows.append(f'<li><span>{slot.title()}</span><a href="#{rid}">{escape(recipe["shortTitle"])} {icon("arrow")}</a><small>{instruction}</small></li>')
        guides.append(f'<details class="daily-guide" id="guide-{no}"><summary><span class="guide-day">DAY {no}</span><span>{escape(title)}</span><span class="plus" aria-hidden="true">+</span></summary><div class="guide-content"><p class="cook-note">{escape(note)}</p><ul>{"".join(guide_rows)}</ul></div></details>')
    notebook = ''.join(recipe_html(data, plan, rid, counts[rid], positions) for rid in data['recipes'] if rid in counts)
    groups = []
    for group in data['groceryGroups']:
        entries = [row for row in groceries if row['group'] == group]
        if not entries:
            continue
        rows = ''.join(f'<li><label for="item-{row["id"]}"><input id="item-{row["id"]}" type="checkbox"><span><strong>{escape(row["name"])}</strong><small>{escape(row["detail"])}</small></span></label></li>' for row in entries)
        groups.append(f'<section class="shop-group"><h3>{escape(group)}</h3><ul>{rows}</ul></section>')
    cooked, dry = Fraction(0), Fraction(0)
    for rid, uses in counts.items():
        factor = Fraction(uses * plan['people'], data['recipes'][rid]['servings'])
        for row in data['recipes'][rid]['ingredients']:
            if row['itemId'] == 'brown-rice' and not row.get('asNeeded'):
                if row['unit'] == 'cup-cooked':
                    cooked += quantity(row['quantity']) * factor
                elif row['unit'] in ('cup-dry','tsp-dry'):
                    dry += quantity(row['quantity']) * factor * (Fraction(1,48) if row['unit']=='tsp-dry' else 1)
    rice_parts = []
    if cooked:
        rice_parts.append(f'Cook <strong>{escape(amount_label(cooked,"cup"))} total</strong> for the prepared rice bowls.')
    if dry:
        cups, rest = divmod(dry, 1)
        dry_amount = joined([amount_label(value, unit) for value, unit in ((cups,'cup'),(rest*48,'tsp')) if value])
        rice_parts.append(f'The quick-cooking rice recipes separately use <strong>{escape(dry_amount)} dry rice</strong>.')
    rice_note = '<aside class="rice-note"><strong>A note on rice</strong><p>' + ' '.join(rice_parts) + ' Follow package yields; shopping quantities include the configured bag size.</p></aside>' if rice_parts else ''
    cooking_text = ('Cook batches on ' + day_phrase(cooking) + '. ') if cooking else ''
    values = {
        'PAGE_TITLE': escape(site['brand'].title() + ' — ' + plan['title']),
        'DESCRIPTION': escape(f'{plan["title"]} with daily recipe guides and a grocery checklist.',quote=True),
        'BREAKFAST_MODE': 'Made fresh' if all(data['recipes'][data['days'][day_id]['meals']['breakfast']]['preparation'] == 'fresh' for day_id in plan['days']) else 'Follow daily guide',
        'PLAN_ID':data['activePlanId'], 'GROCERY_KEY':f'daily-plate-groceries-v2:{data["activePlanId"]}:{fingerprint}',
        'BRAND':escape(site['brand']), 'DAY_TITLE':escape(day_title), 'HERO_HEADING':escape(site['heroHeading']),
        'HERO_DESCRIPTION':escape(site['heroDescription']),
        'EYEBROW':escape(f'{day_title.upper()} · {word(plan["people"]).upper()} {"PERSON" if plan["people"]==1 else "PEOPLE"} · {word(len(cooking)).upper()} COOKING {"SESSION" if len(cooking)==1 else "SESSIONS"}'),
        'CALORIES':f'{float(quantity(plan["targets"]["calories"])):,.0f}', 'PROTEIN':pretty(quantity(plan['targets']['proteinGrams'])),
        'TARGET_NOTE':escape(site['targetNote']), 'PLAN_HEADING':escape(f'Your next {day_title.lower()}'),
        'PLAN_ASIDE':escape(site['planAside']), 'CARDS':''.join(cards), 'WORKOUT_NOTE':rich_text(site['workoutNote']),
        'GUIDE_HEADING':escape(site['guideHeading']), 'GUIDE_ASIDE':escape(f'Cook {len(cooking)} batch {"day" if len(cooking)==1 else "days"}. Breakfast each morning.'),
        'GUIDES':''.join(guides), 'RECIPE_HEADING':escape(site['recipeHeading']), 'RECIPE_INTRO':escape(site['recipeIntro']),
        'RECIPES':notebook, 'NUTRITION_NOTE':rich_text(site['nutritionNote']), 'SHOPPING_HEADING':escape(f'One trip. {day_title}.'),
        'SHOPPING_NOTE':escape(site['shoppingNote']), 'SHOPPING_GROUPS':''.join(groups), 'RICE_NOTE':rice_note,
        'STORAGE_NOTE':escape(cooking_text + site['storageNote']), 'STORAGE_SAFETY':escape(site['storageSafety']),
        'STORAGE_URL':escape(site['storageUrl'],quote=True), 'FOOTER':escape(site['footer']), 'REPO_URL':escape(site['repoUrl'],quote=True)
    }
    template = (ROOT/'templates/index.html').read_text()
    return re.sub(r'\{\{([A-Z_]+)\}\}', lambda match: values[match[1]], template)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail('JSON', f'duplicate key {key!r}')
        result[key] = value
    return result


def load_data(path):
    def reject_constant(value):
        fail('JSON', f'{value} is not a JSON number')
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object, parse_constant=reject_constant)


def build_site(data_path, output_dir):
    data = load_data(data_path)
    rendered = render_page(data)
    assets = [ROOT/name for name in ('styles.css','app.js','themes.js')]
    for asset in assets:
        if not asset.is_file():
            fail('assets', f'missing {asset.name}')
    output = Path(output_dir)
    if output.resolve() == ROOT:
        fail('output-dir', 'choose a build directory rather than the repository root')
    output.mkdir(parents=True, exist_ok=True)
    for asset in assets:
        shutil.copyfile(asset, output/asset.name)
    (output/'index.html').write_text(rendered)
    return rendered


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT/'meal-plan.json')
    parser.add_argument('--output-dir', type=Path, default=ROOT/'_site')
    args = parser.parse_args()
    try:
        build_site(args.data, args.output_dir)
    except (ValueError, OSError, KeyError) as error:
        print(f'Build failed: {error}', file=sys.stderr)
        return 1
    print(f'Built {args.output_dir}/index.html from {args.data.name}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
