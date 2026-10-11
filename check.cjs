const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { execFileSync } = require('node:child_process');
const { palettes } = require('./themes.js');

(async () => {
  execFileSync('python3', [path.join(__dirname, 'scripts/build.py')], {stdio: 'inherit'});
  const siteRoot = path.join(__dirname, '_site');
  const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'meal-plan.json'), 'utf8'));
  const plan = data.plans[data.activePlanId];
  const recipeIds = [...new Set(plan.days.flatMap(id => Object.values(data.days[id].meals)))];
  assert.ok(fs.existsSync(path.join(siteRoot, 'index.html')), 'Meal-plan page has not been built');
  const browser = await chromium.launch({headless: true});
  const server = http.createServer((req, res) => {
    let file = path.join(siteRoot, req.url.split('?')[0]);
    if (!file.startsWith(siteRoot + path.sep) || !fs.existsSync(file)) { res.writeHead(404); return res.end(); }
    if (fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
    if (!fs.existsSync(file)) { res.writeHead(404); return res.end(); }
    res.setHeader('Content-Type', file.endsWith('.css') ? 'text/css' : file.endsWith('.js') ? 'application/javascript' : 'text/html');
    res.end(fs.readFileSync(file));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try {
    const page = await browser.newPage({viewport: {width: 390, height: 844}});
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/`);
    assert.equal(await page.locator('.day-card').count(), plan.days.length, 'All selected days are visible');
    assert.equal(await page.locator('details.recipe').count(), recipeIds.length, 'All selected recipes are present');
    const palette = page.getByLabel('Palette', {exact: true});
    assert.equal(await palette.locator('option').count(), palettes.length, 'Every palette is available');
    assert.equal(await palette.inputValue(), 'ds-7', 'Palette 7 is the default');
    const defaultBackground = await page.locator('body').evaluate(body => getComputedStyle(body).backgroundColor);
    await palette.selectOption('ch-lavender');
    assert.notEqual(await page.locator('body').evaluate(body => getComputedStyle(body).backgroundColor), defaultBackground, 'Switching changes the page colors');
    await page.reload();
    assert.equal(await palette.inputValue(), 'ch-lavender', 'Palette choice persists after reload');
    await palette.selectOption('dp-midnight');
    assert.equal(await page.locator('html').evaluate(root => getComputedStyle(root).colorScheme), 'dark', 'Dark palette styles native controls');
    await page.reload();
    assert.equal(await palette.inputValue(), 'dp-midnight', 'Dark palette persists after reload');
    for (const id of await palette.locator('option').evaluateAll(options => options.map(option => option.value))) {
      await palette.selectOption(id);
      assert.equal(await page.locator('html').getAttribute('data-palette'), id, `Palette applies: ${id}`);
    }
    await palette.selectOption('ds-7');
    assert.equal(await page.locator('html').evaluate(root => getComputedStyle(root).colorScheme), 'light', 'A light palette restores native controls');
    const anchors = await page.locator('a[href^="#"]').evaluateAll(items => items.map(a => a.getAttribute('href').slice(1)).filter(Boolean));
    for (const id of anchors) assert.equal(await page.locator(`[id="${id}"]`).count(), 1, `Anchor target exists: ${id}`);
    await page.locator(`#${recipeIds[0]} summary`).click();
    assert.equal(await page.locator(`#${recipeIds[0]}`).getAttribute('open'), '', 'Recipe opens without navigating away');
    const checkbox = page.locator('#groceries input[type="checkbox"]').first();
    await checkbox.check();
    await page.reload();
    assert.equal(await checkbox.isChecked(), true, 'Grocery selection persists after reload');
    await page.getByRole('button', {name: 'Reset list'}).click();
    assert.equal(await checkbox.isChecked(), false, 'Reset clears grocery selection');
    const defaultCheckboxId = await checkbox.getAttribute('id');
    await checkbox.check();
    await palette.selectOption('dp-midnight');
    const planSelect = page.getByLabel('Meal plan', {exact: true});
    assert.equal(await planSelect.locator('option').count(), Object.keys(data.plans).length, 'Every plan is selectable');
    for (const id of Object.keys(data.plans).filter(id => id !== data.activePlanId)) {
      const destination = await planSelect.locator(`option[data-plan-id="${id}"]`).getAttribute('value');
      await Promise.all([page.waitForURL(`**/plans/${id}/`), planSelect.selectOption(destination)]);
      assert.equal(await page.locator('body').getAttribute('data-plan-id'), id, 'Selected plan is shown');
      assert.equal(await page.locator('.day-card').count(), data.plans[id].days.length, 'Selected day count is correct');
      assert.equal(await palette.inputValue(), 'dp-midnight', 'Dark palette carries across plans');
      assert.equal(await page.locator('#groceries input:checked').count(), 0, 'Other plan starts with its own checklist');
      const otherCheckbox = page.locator('#groceries input[type="checkbox"]').first();
      const otherCheckboxId = await otherCheckbox.getAttribute('id');
      await otherCheckbox.check();
      const defaultUrl = await planSelect.locator(`option[data-plan-id="${data.activePlanId}"]`).getAttribute('value');
      await Promise.all([page.waitForURL(`**/plans/${data.activePlanId}/`), planSelect.selectOption(defaultUrl)]);
      assert.equal(await page.locator(`#${defaultCheckboxId}`).isChecked(), true, 'Default checklist is retained');
      const revisitUrl = await planSelect.locator(`option[data-plan-id="${id}"]`).getAttribute('value');
      await Promise.all([page.waitForURL(`**/plans/${id}/`), planSelect.selectOption(revisitUrl)]);
      assert.equal(await page.locator(`#${otherCheckboxId}`).isChecked(), true, 'Other checklist is retained');
      await page.getByRole('button', {name:'Reset list'}).click();
      const returnUrl = await planSelect.locator(`option[data-plan-id="${data.activePlanId}"]`).getAttribute('value');
      await Promise.all([page.waitForURL(`**/plans/${data.activePlanId}/`), planSelect.selectOption(returnUrl)]);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, 'Selector has no mobile horizontal overflow');
    }
    await page.getByRole('button', {name:'Reset list'}).click();
    await palette.selectOption('ds-7');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, 'No mobile horizontal overflow');
    await page.screenshot({path: path.join(__dirname, 'mobile-preview.png'), fullPage: true});
    await page.setViewportSize({width: 1440, height: 1000});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, 'No desktop horizontal overflow');
    await page.screenshot({path: path.join(__dirname, 'desktop-preview.png'), fullPage: true});
    await palette.selectOption('dp-midnight');
    await page.locator('button[data-print]').click();
    await page.emulateMedia({media: 'print'});
    assert.equal(await page.locator('html').evaluate(root => getComputedStyle(root).colorScheme), 'light', 'Printing a dark palette uses light controls');
    assert.equal(await page.locator('.storage p').last().evaluate(p => getComputedStyle(p).color), 'rgb(17, 17, 17)', 'Dark-palette print text remains legible');
    assert.equal(await page.locator('details.recipe[open]').count(), recipeIds.length, 'Print includes every recipe');
    assert.deepEqual(errors, [], 'No browser errors');
    const noJs = await browser.newPage({javaScriptEnabled: false, viewport: {width: 390, height: 844}});
    await noJs.goto(`http://127.0.0.1:${server.address().port}/`);
    assert.equal(await noJs.locator('.day-card').count(), plan.days.length, 'Plan works without JavaScript');
    await noJs.locator(`#${recipeIds[0]} summary`).click();
    assert.equal(await noJs.locator(`#${recipeIds[0]}`).getAttribute('open'), '', 'Recipe works without JavaScript');
    for (const id of Object.keys(data.plans).filter(id => id !== data.activePlanId)) {
      await noJs.locator(`[data-plan-links] a[href$="/plans/${id}/"]`).click();
      assert.equal(await noJs.locator('.day-card').count(), data.plans[id].days.length, 'Plan links work without JavaScript');
      assert.equal(await noJs.locator('[data-plan-picker]').isVisible(), false, 'No inactive dropdown without JavaScript');
    }
    console.log('PASS: plan switching and independent checklists, palette persistence, recipe anchors, mobile/desktop layout, print, and no-JS navigation.');
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(e => { console.error(e.message); process.exitCode = 1; });
