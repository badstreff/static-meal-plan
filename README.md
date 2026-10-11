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

The catalog includes six plans. The original four-day plan remains the default:

| Plan ID | Days | Calorie target | Estimated rest-day calories | Protein target |
| --- | --- | --- | --- | --- |
| `four-day-cut` | 4 | 2,400 | 2,412–2,576 | 200 g |
| `three-day-1800` | 3 | 1,800 | 1,776–1,793 | 160 g |
| `four-day-2000` | 4 | 2,000 | 1,960–2,010 | 170 g |
| `four-day-2200` | 4 | 2,200 | 2,185–2,231 | 185 g |
| `four-day-1800` | 4 | 1,800 | 1,775–1,835 | 160 g |
| `three-day-2400` | 3 | 2,400 | 2,412–2,424 | 200 g |

The new four-day 1,800 and three-day 2,400 plans each have two cooking days. Both include slow-cooker chicken taco chili adapted from [Skinnytaste](https://www.skinnytaste.com/crock-pot-chicken-taco-chili-4-pts/): a smaller yogurt-topped bowl or a larger cheese-topped bowl. Both recipes use whole cans to simplify prep; the smaller batch has a shorter ingredient list. The 2,400 plan uses one chili batch for all three dinners. Start the slow cooker early; recipes show cook times, safe chicken temperature, portions, and topping storage.

Snacks rotate among KIND bars with yogurt, individually wrapped cheese with yogurt and fruit, and pineapple cottage-cheese bowls. Groceries identify product flavors, package sizes and counts. Recipe notes give specific workout swaps for the 30 g / 150 calorie Fairlife shake, which is conditional in the grocery list. All plans avoid fish and seafood; vegetarian mushroom sauce also replaces oyster sauce in the older honey-garlic chicken.

Cottage-cheese bowls now use one whole **Dole 4 oz pineapple-in-juice cup**, including its juice, at 60 calories. The full bowl is about 320 calories / 32 g protein; the smaller bowl is about 240 / 23. Cottage-cheese estimates use [Good Culture 2%](https://goodculture.com/product/simply-cottage-cheese-24-oz-lowfat-classic/) at 90 calories / 14 g protein per 110 g. Cold toppings and almonds can stay separate until serving. [Pineapple label](https://www.dolesunshine.com/us/en/products/pineapple-paradise-in-100-pineapple-juice-16oz/).

**Breakfast side shakes use PBfit Classic + Fairlife fat-free (0%) milk.** The full oat breakfast has 16 g PBfit + 8 fl oz skim milk (~140 calories / 21 g protein); the smaller oat breakfast has 8 g PBfit + 4 fl oz skim milk (~70 / 10.5). Oats, apples, brown sugar, breakfast fat and the two 2% milk lattes retain their previous portions. Milk for the shake is additional to latte milk and appears separately in groceries. [PBfit label](https://www.pbfit.com/products/pbfit-classic) · [Fairlife skim label](https://fairlife.com/ultra-filtered-milk/fat-free-skim-milk/). PBfit is estimated at 60 calories per 16 g; if your jar shows 70, add 10 per full shake or 5 per smaller shake.

Packaged snack calculations use current manufacturer pages: [KIND Dark Chocolate Nuts & Sea Salt, 40 g](https://www.kindsnacks.com/products/nut-bar/dark-chocolate-nuts-sea-salt) = 190 calories / 6 g protein; [Oikos Triple Zero vanilla, 150 g](https://www.oikos.com/all-products/triple-zero/product/vanilla-multipack/) = 80 / 15; [Mini Babybel Original, 20 g](https://babybel.com/product/babybel-original-cheese/) = 70 / 4. Check the package you buy: sizes, flavors and formulations vary.

## Breakfast variety

The 2,400-calorie default keeps its original oats and ham-frittata breakfast rotation and food portions; only the oat breakfast side shake has changed to PBfit and skim milk. New fresh breakfasts appear in the lower-calorie plans:

| Breakfast | Used in | Calories including two lattes | Protein including two lattes |
| --- | --- | --- | --- |
| Cottage cheese pancakes, yogurt and berries — smaller portion | 1,800 and 2,000, day 3 | ~520 | ~45 g |
| Ham and egg English muffin — smaller portion | 2,000, day 4 | ~475 | ~43 g |
| Cottage cheese pancakes, yogurt and berries | 2,200, day 3 | ~715 | ~59 g |
| Ham and potato breakfast taquitos | 2,200, day 4 | ~630 | ~49 g |

Pancakes are adapted from The Kitchn; the English muffin is adapted from Skinnytaste; the ham taquitos are inspired by The Meal Prep Manual's potato and sausage taquitos. Each recipe links to its source. Ham replaces sausage or turkey bacon. None of the new recipes uses protein powder. Pancakes use rolled oats, which are listed separately from steel-cut oats.

All breakfast estimates include 12 fl oz total plain Fairlife 2% milk, split into two 6 fl oz lattes: about 180 calories and 19.5 g protein from milk alone. Check your MooTopia label if using that milk. New recipe notes distinguish the food estimate from the latte contribution; adapted totals are calculated from typical ingredient labels rather than copying unchanged source nutrition cards. The grocery lists include 36 fl oz latte milk for three days or 48 fl oz for four days.

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

Palettes come from [Digital Synopsis](https://digitalsynopsis.com/design/minimal-web-color-palettes-combination-hex-code/) and [Color Hunt](https://colorhunt.co/). Palette 7 is the default; swatches show the original colors. The optional **Midnight · dark** palette adds charcoal surfaces, soft white text and mint accents. It saves through the same switcher, carries across plans and uses dark native controls; printing stays light. Recipe source links remain beside the guides.
