const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');

(async () => {
  assert.ok(fs.existsSync(path.join(__dirname, 'index.html')), 'Meal-plan page has not been built');
  const browser = await chromium.launch({headless: true});
  const server = http.createServer((req, res) => {
    const file = path.join(__dirname, req.url.split('?')[0] === '/' ? 'index.html' : req.url.split('?')[0]);
    if (!file.startsWith(__dirname) || !fs.existsSync(file)) { res.writeHead(404); return res.end(); }
    res.setHeader('Content-Type', file.endsWith('.css') ? 'text/css' : file.endsWith('.js') ? 'application/javascript' : 'text/html');
    res.end(fs.readFileSync(file));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try {
    const page = await browser.newPage({viewport: {width: 390, height: 844}});
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/`);
    assert.equal(await page.locator('.day-card').count(), 4, 'All four days are visible');
    assert.equal(await page.locator('details.recipe').count(), 8, 'All eight meal recipes are present');
    const anchors = await page.locator('a[href^="#"]').evaluateAll(items => items.map(a => a.getAttribute('href').slice(1)));
    for (const id of anchors) assert.equal(await page.locator(`[id="${id}"]`).count(), 1, `Anchor target exists: ${id}`);
    await page.locator('#oats summary').click();
    assert.equal(await page.locator('#oats').getAttribute('open'), '', 'Recipe opens without navigating away');
    const checkbox = page.locator('#groceries input[type="checkbox"]').first();
    await checkbox.check();
    await page.reload();
    assert.equal(await checkbox.isChecked(), true, 'Grocery selection persists after reload');
    await page.getByRole('button', {name: 'Reset list'}).click();
    assert.equal(await checkbox.isChecked(), false, 'Reset clears grocery selection');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, 'No mobile horizontal overflow');
    await page.screenshot({path: path.join(__dirname, 'mobile-preview.png'), fullPage: true});
    await page.setViewportSize({width: 1440, height: 1000});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, 'No desktop horizontal overflow');
    await page.screenshot({path: path.join(__dirname, 'desktop-preview.png'), fullPage: true});
    await page.emulateMedia({media: 'print'});
    await page.locator('button[data-print]').click();
    assert.equal(await page.locator('details.recipe[open]').count(), 8, 'Print includes every recipe');
    assert.deepEqual(errors, [], 'No browser errors');
    const noJs = await browser.newPage({javaScriptEnabled: false, viewport: {width: 390, height: 844}});
    await noJs.goto(`http://127.0.0.1:${server.address().port}/`);
    assert.equal(await noJs.locator('.day-card').count(), 4, 'Plan works without JavaScript');
    await noJs.locator('#ham summary').click();
    assert.equal(await noJs.locator('#ham').getAttribute('open'), '', 'Recipe works without JavaScript');
    console.log('PASS: four-day content, recipe anchors, grocery persistence/reset, mobile/desktop layout, print, and no-JS access.');
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(e => { console.error(e.message); process.exitCode = 1; });
