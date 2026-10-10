# The Daily Plate

A static meal plan with daily recipe guides, a calculated grocery checklist, print styles, and 12 saved color palettes.

**Live page:** https://badstreff.github.io/static-meal-plan/

## Choose the default or browse another plan

All meal content lives in [`meal-plan.json`](meal-plan.json). Set its top-level `activePlanId` to a key in `plans`, then push to `main`.

```json
"activePlanId": "four-day-cut"
```

`activePlanId` chooses the plan shown on the homepage. The meal-plan selector lets visitors browse every plan in the JSON. With JavaScript disabled, ordinary plan links appear instead. Each plan has a stable URL at `plans/<plan-id>/` and its own saved grocery checklist; palette preferences carry across plans. The default plan's checklist is shared between its homepage and its dedicated URL.

GitHub Actions validates the document, runs tests, generates the homepage and every plan page, and publishes `_site`. Invalid content stops deployment. Displaying meals and recipes does not require JavaScript or a JSON request.

The catalog includes four plans. The original four-day plan remains the default:

| Plan ID | Days | Calorie target | Estimated rest-day calories | Protein target |
| --- | --- | --- | --- | --- |
| `four-day-cut` | 4 | 2,400 | Original plan | 200 g |
| `three-day-1800` | 3 | 1,800 | 1,773–1,796 | 160 g |
| `four-day-2000` | 4 | 2,000 | 1,970–2,020 | 170 g |
| `four-day-2200` | 4 | 2,200 | 2,191–2,195 | 185 g |

The new variations add Taco Mac, teriyaki beef bowls, cilantro lime chicken bowls and sriracha lime chicken bowls from The Meal Prep Manual, plus cherry-balsamic pork adapted from Skinnytaste. Each has two batch days and its own calculated groceries. Frozen mixed vegetables replace broccoli in the chicken bowls; portions and side dishes are adjusted for the plan. Every breakfast includes two lattes, and workout snack notes account for the 30 g / 150 calorie Fairlife shake. Nutrition estimates are per serving and depend on actual brands and ingredients.

## Add or reorder plans and days

Add this entry alongside the existing plans. It appears in the selector after the next build. Set `activePlanId` to `two-day-cut` if it should become the homepage default:

```json
"two-day-cut": {
  "title": "Two-day cut",
  "people": 1,
  "targets": { "calories": 2400, "proteinGrams": 200 },
  "days": ["day-01", "day-02"],
  "extraItems": ["fairlife"]
}
```

The `days` array controls order and may repeat IDs. Replace an ID to swap a day. Each day references one recipe for each meal:

```json
"day-01": {
  "meals": {
    "breakfast": "oats",
    "lunch": "buffalo",
    "dinner": "honey",
    "snack": "yogurt"
  }
}
```

Duplicate a day under another ID to make a variation, then change its recipe references. A recipe's `kind` must match its meal slot. Each page displays only that plan's recipes. Guides follow its day order; groceries cover its meals and `people` count. Smaller portions use separate recipe IDs so the original plan stays unchanged.

Batch recipes are prepared on their first selected day. For plans beyond the 3–4 day refrigeration window, plan separate batches or freezing; the generator is not a food-storage scheduler.

Global wording lives in `site`. A plan may include a `copy` object overriding `heroDescription`, `planAside`, `recipeIntro`, `targetNote`, `workoutNote`, `nutritionNote`, `shoppingNote`, `storageNote`, or `footer`. For example:

```json
"copy": {
  "heroDescription": "A short plan for a busy week.",
  "workoutNote": "Include your Fairlife shake in today's snack."
}
```

## Recipe and ingredient schema

Recipes have `title`, `shortTitle`, `kind`, `preparation`, `servings`, `prepTime`, `nutrition`, `description`, `ingredients`, `steps`, `note`, and an optional `source` containing `label` and an HTTPS `url`.

`servings` describes the base quantities. `preparation: "fresh"` scales the recipe guide to one preparation for the plan's people. `preparation: "batch"` scales its guide to all selected portions. Groceries always cover the entire plan. Nutrition is an approximate estimate **per serving** and is not recalculated when ingredients change.

```json
{
  "itemId": "oats",
  "quantity": 60,
  "unit": "g",
  "label": "dry steel-cut oats + water per package"
}
```

Use positive numbers or fraction strings such as `"2/3"`; calculations use exact fractions. Unmeasured ingredients use `"quantity": null` and `"asNeeded": true`. Ingredient `format` supports `{amount}`, `{label}`, and `{alternatives}`. Recipe steps support `{portions}` and `{portionsWord}`. Refer to listed ingredient amounts in steps so instructions remain correct when portions change.

`items` defines grocery labels, an ordered `groceryGroups` category, a canonical `unit`, and a `units` conversion map. Each conversion multiplies the ingredient amount into that canonical unit. Shopping settings support `roundTo`, `packSize` with `packLabel`, `showRequired`, `asNeeded`, `mode: "pantry"`, a quantity `format`, and a `suffix`. `variants` combine onion types; `alternatives` preserve butter/half-and-half choices.

Rounding happens after summing requirements. Approximate rice, berry, lemon and garlic conversions are documented in the JSON's `measurementNotes`; use package yields where they differ. The generated list corrects the former olive-oil estimate to 5 tablespoons, plus cooking spray.

`extraItems` adds conditional items with an `asNeeded` description, such as Fairlife shakes; it does not change recipe nutrition. Grocery ticks are saved in the current browser, scoped to the selected plan and quantities. Changed requirements start a fresh checklist. Palette preferences are independent.

## Build, preview and test

The builder uses only Python's standard library. No installation is needed:

```sh
python3 scripts/build.py
python3 -m http.server 8000 --directory _site
```

Open http://localhost:8000. For another document: `python3 scripts/build.py --data another-plan.json --output-dir _site`.

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
node --test themes.test.cjs
```

With Playwright and Chromium installed, `node check.cjs` additionally checks mobile/desktop layout, recipe navigation, grocery persistence/reset, palettes, printing, and no-JavaScript access. Deployment runs the dependency-free Python and Node tests.

Regression tests use a fixed catalog in `scripts/fixtures/meal-plan.json`; leave that fixture alone when editing your meal plan. A separate test validates and renders the live `meal-plan.json`, so valid content changes and plan switches do not require changing tests.

## File layout

| File | Role |
| --- | --- |
| `meal-plan.json` | Content, selector, measurements and shopping assumptions |
| `scripts/build.py` | Validation, quantity calculations and static generation |
| `templates/index.html` | Page layout |
| `styles.css` | Responsive and print styles |
| `app.js` | Grocery persistence, recipe navigation and printing |
| `themes.js` | Palette catalog and saved selection |
| `_site/index.html` | Generated default homepage, ignored by git |
| `_site/plans/<plan-id>/index.html` | Generated pages for every plan, ignored by git |

Schema version is `1`. Validation rejects unsupported versions, duplicate JSON keys, missing slots/references, invalid units/quantities, mismatched recipe kinds, unsafe source URLs, and conflicting recipe IDs. Inactive plans are also validated.

Palettes come from [Digital Synopsis](https://digitalsynopsis.com/design/minimal-web-color-palettes-combination-hex-code/) and [Color Hunt](https://colorhunt.co/). Palette 7 is the default; swatches show the original colors. Recipe source links remain beside the guides.
