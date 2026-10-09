# The Daily Plate

A four-day meal plan for quick reference from a phone: fresh breakfasts, two cooking sessions, daily recipe guides, and a consolidated grocery checklist.

**Live page:** https://badstreff.github.io/static-meal-plan/

## Contents

- Steel-cut oats with apple, brown sugar, butter or half-and-half, and a separate protein shake.
- Fresh ham and spinach frittata with toast.
- Buffalo and Greek chicken lunches; honey garlic and chile lemon chicken dinners.
- Rest-day snacks and workout-day Fairlife swaps.
- Ingredients already scaled for one person over four days.
- A palette switcher with eight Digital Synopsis palettes and four Color Hunt choices, saved in your browser.

## Run locally

No package installation or build is needed:

```sh
python3 -m http.server 8000
```

Open http://localhost:8000. GitHub Pages serves the repository root using the existing workflow.

`index.html` contains all content, `styles.css` the responsive/print styles, and `app.js` optional grocery persistence, recipe navigation, and printing. The meal plan and native recipe accordions also work without JavaScript. Grocery ticks are stored only in the current browser; reset them for a new shopping trip.

## Verification

With Playwright available, run `node check.cjs`. It checks mobile and desktop overflow, complete recipe navigation, saved checklist state, reset behavior, print expansion, and no-JavaScript access. It writes local preview screenshots.

The palette selector defaults to palette 7 from [Digital Synopsis’s minimalist palette collection](https://digitalsynopsis.com/design/minimal-web-color-palettes-combination-hex-code/) and also includes sage, coastal blue, lavender, and terracotta options from [Color Hunt](https://colorhunt.co/). `themes.js` stores the original swatches and derives readable page colors. Run `node --test themes.test.cjs` to verify the catalog, saved-preference fallbacks, default appearance, and text contrast in all 12 themes.

Nutrition is approximate. Use actual food and shake labels when tracking. Original recipe links are included beside the adapted guides.
