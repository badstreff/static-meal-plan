# The Daily Plate

A static meal plan with daily recipe guides, a calculated grocery checklist, print styles, and 13 saved color palettes.

Vibe coded with chatgpt, if it turns out to be useful I will put some more work into it.

**Live page:** https://badstreff.github.io/static-meal-plan/

## Choose the default or browse another plan

All meal content lives in [`meal-plan.json`](meal-plan.json). Set its top-level `activePlanId` to a key in `plans`, then push to `main`.

```json
"activePlanId": "four-day-cut"
```

`activePlanId` chooses the plan shown on the homepage. The meal-plan selector lets visitors browse every plan in the JSON. With JavaScript disabled, ordinary plan links appear instead. Each plan has a stable URL at `plans/<plan-id>/` and its own saved grocery checklist; palette preferences carry across plans. The default plan's checklist is shared between its homepage and its dedicated URL.

GitHub Actions validates the document, runs tests, generates the homepage and every plan page, and publishes `_site`. Invalid content stops deployment. Displaying meals and recipes does not require JavaScript or a JSON request.

The catalog includes ten plans. The original four-day plan remains the default:

| Plan ID | Days | Calorie target | Estimated regular-day calories | Protein target |
| --- | --- | --- | --- | --- |
| `four-day-cut` | 4 | 2,400 | 2,458–2,463 | 210 g |
| `three-day-1800` | 3 | 1,800 | 1,771–1,859 | 158 g |
| `four-day-2000` | 4 | 2,000 | 2,020–2,054 | 175 g |
| `four-day-2200` | 4 | 2,200 | 2,243–2,251 | 192 g |
| `four-day-1800` | 4 | 1,800 | 1,798–1,842 | 158 g |
| `three-day-2400` | 3 | 2,400 | 2,393–2,457 | 210 g |
| `fatigue-day-1800` | 1 | 1,800 | 1,831 | 158 g |
| `fatigue-day-2000` | 1 | 2,000 | 2,018 | 175 g |
| `fatigue-day-2200` | 1 | 2,200 | 2,179 | 192 g |
| `fatigue-day-2400` | 1 | 2,400 | 2,387 | 210 g |

Every day targets **35% carbohydrate / 35% protein / 30% fat by calories**. Both regular and workout snack versions stay within three percentage points per macro and 5% of the calorie target. Cards show daily grams and the estimated energy split. Percentages normalize 4/4/9 macro energy; label calories are summed separately and can differ due to fiber and rounding.

No meal family is scheduled more than two consecutive days, including differently sized versions of the same dish. The new four-day 1,800 plan has two cook days; the three-day 2,400 plan has three. Both include whole-can slow-cooker chicken taco chili adapted from [Skinnytaste](https://www.skinnytaste.com/crock-pot-chicken-taco-chili-4-pts/). The 2,400 plan has chili for its first two dinners, then cherry-balsamic pork.

Snacks rotate among KIND bars with yogurt, individually wrapped cheese with yogurt and fruit, and pineapple cottage-cheese bowls. Groceries identify product flavors, package sizes and counts. Daily cards link an explicit workout snack guide containing one 30 g / 150 calorie Fairlife shake. It replaces the regular snack; groceries cover regular snacks, with shakes listed conditionally. Check the workout guide for topping changes before shopping. All plans avoid fish and seafood; vegetarian mushroom sauce also replaces oyster sauce in the older honey-garlic chicken.

Cottage-cheese bowls use one whole **Dole 4 oz pineapple-in-juice cup**, including its juice, at 60 calories. Cottage cheese assumes [Good Culture 2%](https://goodculture.com/product/simply-cottage-cheese-24-oz-lowfat-classic/) at 90 calories / 14 g protein per 110 g. Portions vary by plan; the guide shows the exact cottage cheese and almond amounts. [Pineapple label](https://www.dolesunshine.com/us/en/products/pineapple-paradise-in-100-pineapple-juice-16oz/).

**Breakfast side shakes use PBfit Classic + Fairlife fat-free (0%) milk.** The default oat breakfast retains 16 g PBfit + 8 fl oz skim milk, along with its original oats, apple, brown sugar and breakfast fat portions. Smaller plans adjust food portions to balance the day. All breakfasts retain two lattes, each with 6 fl oz 2% milk. Shake milk is additional and appears separately in groceries. PBfit assumes 60 calories / 8 g protein / 4 g carbs / 2 g fat per 16 g; jars can differ, so use your label. [PBfit](https://www.pbfit.com/products/pbfit-classic) · [Fairlife skim](https://fairlife.com/ultra-filtered-milk/fat-free-skim-milk/).

Packaged snack calculations use current manufacturer pages: [KIND Dark Chocolate Nuts & Sea Salt, 40 g](https://www.kindsnacks.com/products/nut-bar/dark-chocolate-nuts-sea-salt) = 190 calories / 6 g protein; [Oikos Triple Zero vanilla, 150 g](https://www.oikos.com/all-products/triple-zero/product/vanilla-multipack/) = 80 / 15; [Mini Babybel Original, 20 g](https://babybel.com/product/babybel-original-cheese/) = 70 / 4. Check the package you buy: sizes, flavors and formulations vary.


## Fatigue days

Four one-day plans reduce cooking to breakfast and a five-minute home meal. Each includes both lattes, exactly one restaurant meal and a ready-to-eat snack; lunch and dinner can trade places. They use the same macro and workout-snack checks as the longer plans.

| Target | Breakfast | Dining-out lunch | Simple home dinner | Estimated calories |
| --- | --- | --- | --- | --- |
| 1,800 | Apple steel-cut oats + PBfit side shake + two lattes | Chipotle chicken, brown rice and black-bean bowl | No-cook chicken, bean and almond salad | 1,831 |
| 2,000 | Ham and egg English muffin + two lattes | Panda Plate: double Grilled Teriyaki Chicken, all Super Greens | Microwave chicken, rice, beans and vegetables | 2,018 |
| 2,200 | Cottage cheese pancakes + two lattes | Chipotle double-chicken bowl with brown rice, beans and corn salsa | Canned-chicken sandwich and microwave vegetables | 2,179 |
| 2,400 | Original ham frittata and toast + two lattes | Panda Plate: double Grilled Teriyaki Chicken, half white rice / half Super Greens | Microwave chicken, rice and vegetables | 2,387 |

Restaurant guides specify the full order, toppings and drink assumptions. Their estimates sum standard portions from [Chipotle’s official U.S. chart](https://www.chipotle.com/content/dam/chipotle/menu/nutrition/US-Nutrition-Facts-Paper-Menu-3-2025.pdf) and [Panda Express’s current official nutrition table](https://www.pandaexpress.com/nutritioninformation), checked October 11, 2026. Actual scoops and half-side splits vary; extra sauce, chips and caloric drinks change the totals.

Restaurant order items appear in a separate **Dining out · order separately** shopping group. Their ingredients are already included in the restaurant order and do not inflate home groceries. Pantry dinners use fully cooked canned chicken (weighed drained), ready-to-heat jasmine rice (weighed cooked), canned beans and frozen vegetables. Rice pouches are separate from the dry-rice items used in batch plans. Package labels and edible can yields vary; the grocery list rounds required drained chicken upward. Refrigerate unused opened food promptly.

## Breakfast variety

The 2,400-calorie default keeps its original oats and ham-frittata breakfast food portions and rotation, including the separate PBfit shake. Other plans also offer cottage cheese pancakes with yogurt and berries, ham and egg English muffins, and ham and potato taquitos. Portions are adjusted per plan; each guide includes both lattes in its nutrition.

Pancakes are adapted from The Kitchn; the English muffin is adapted from Skinnytaste; the ham taquitos are inspired by The Meal Prep Manual's potato and sausage taquitos. Each recipe links to its source. Ham replaces sausage or turkey bacon. None of the new recipes uses protein powder. Pancakes use rolled oats, which are listed separately from steel-cut oats.

All breakfast estimates include 12 fl oz total plain Fairlife 2% milk, split into two 6 fl oz lattes: about 180 calories and 19.5 g protein from milk alone. Check your MooTopia label if using that milk. Recipe notes identify the latte contribution; adapted totals are calculated from ingredient references. The grocery lists include 36 fl oz latte milk for three days or 48 fl oz for four days.

## Add or reorder plans and days

Add this entry alongside the existing plans. It appears in the selector after the next build. Set `activePlanId` to `two-day-cut` if it should become the homepage default:

```json
"two-day-cut": {
  "title": "Two-day cut",
  "people": 1,
  "targets": { "calories": 2400, "proteinGrams": 210, "macroPercent": { "carbs": 35, "protein": 35, "fat": 30 } },
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

Batch recipes are prepared on their first selected day. Assembled meals and restaurant orders stay outside that cooking schedule. For plans beyond the 3–4 day refrigeration window, plan separate batches or freezing; the generator is not a food-storage scheduler.

Global wording lives in `site`. A plan may include a `copy` object overriding `heroDescription`, `planAside`, `recipeIntro`, `targetNote`, `workoutNote`, `nutritionNote`, `shoppingNote`, `storageNote`, or `footer`. For example:

```json
"copy": {
  "heroDescription": "A short plan for a busy week.",
  "workoutNote": "Include your Fairlife shake in today's snack."
}
```

## Recipe and ingredient schema

Recipes have `title`, `shortTitle`, `kind`, `preparation`, `servings`, `prepTime`, `nutrition`, `description`, `ingredients`, `steps`, `note`, and an optional `source` containing `label` and an HTTPS `url`.

`servings` describes the base quantities. `preparation: "fresh"` scales the recipe guide to one preparation for the plan's people. `preparation: "batch"` scales its guide to all selected portions. `"assemble"` describes a no-cook or quick microwave meal; `"dining-out"` describes a restaurant order. Both scale to one meal per person and never create a batch-cooking session. Groceries always cover the entire plan. Nutrition is an approximate estimate **per serving**. After changing ingredients or item reference values, run `python3 scripts/nutrition.py --write` to recalculate it. `python3 scripts/nutrition.py` checks that stored recipe estimates match their ingredients. Deployment tests also check for drift.

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

Rounding happens after summing requirements. Approximate rice, berry, lemon and garlic conversions are documented in the JSON's `measurementNotes`; use package yields where they differ. Measured cooking and finishing oil is included in both groceries and macros.

`extraItems` adds conditional items with an `asNeeded` description, such as Fairlife shakes; it does not change recipe nutrition. Grocery ticks are saved in the current browser, scoped to the selected plan and quantities. Changed requirements start a fresh checklist. Palette preferences are independent.


Recipes can also specify a stable `family` ID and a snack-only `workoutRecipe` reference. `family` identifies the same dish across portion variations for the repeat guard. A workout recipe replaces the snack when calculating workout totals and gets its own guide; it is excluded from regular groceries and cooking batches.

Each item’s optional `nutrition` reference contains `quantity`, `unit`, `calories`, `carbsGrams`, `proteinGrams`, `fatGrams`, a `basis` note and optionally `source: {label, url}`. The calculator converts ingredient quantities through `items.units`, sums measured ingredients and divides by recipe servings. Unmeasured optional extras are excluded. Generic food references are explicit approximate assumptions; linked brands use the stated label/serving assumptions.

Recipe nutrition includes `calories`, `proteinGrams`, `carbsGrams` and `fatGrams`. Older documents with only calories and protein still render. `plan.targets.macroPercent` declares the desired percentages. The catalog enables this policy:

```json
"nutritionPolicy": {
  "macroTolerancePercentagePoints": 3,
  "calorieTolerancePercent": 5,
  "maxConsecutiveSameMeal": 2
}
```

Validation checks all plans and both snack versions, not just the default. Macro targets without a policy display without enforcing bounds. Omitting a policy preserves older catalogs. When adding content to this catalog, keep ingredient references and declared nutrition consistent and adjust portions until validation passes.

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
| `scripts/nutrition.py` | Ingredient-based recipe nutrition recalculation and drift checks |
| `templates/index.html` | Page layout |
| `styles.css` | Responsive and print styles |
| `app.js` | Grocery persistence, recipe navigation and printing |
| `themes.js` | Palette catalog and saved selection |
| `_site/index.html` | Generated default homepage, ignored by git |
| `_site/plans/<plan-id>/index.html` | Generated pages for every plan, ignored by git |

Schema version is `1`. Validation rejects unsupported versions, duplicate JSON keys, missing slots/references, invalid units/quantities, mismatched recipe kinds, unsafe source URLs, and conflicting recipe IDs. Inactive plans are also validated.

Palettes come from [Digital Synopsis](https://digitalsynopsis.com/design/minimal-web-color-palettes-combination-hex-code/) and [Color Hunt](https://colorhunt.co/). Palette 7 is the default; swatches show the original colors. The optional **Midnight · dark** palette adds charcoal surfaces, soft white text and mint accents. It saves through the same switcher, carries across plans and uses dark native controls; printing stays light. Recipe source links remain beside the guides.
