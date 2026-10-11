const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const themes = fs.existsSync(`${__dirname}/themes.js`) ? require('./themes.js') : {};

// Changing a theme must never make the site's small text unreadable.
function luminance(hex) {
  const rgb = hex.match(/[a-f\d]{2}/gi).map(value => {
    const channel = parseInt(value, 16) / 255;
    return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  });
  return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
}
function contrast(a, b) {
  const values = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

test('includes the existing palettes plus one optional dark choice', () => {
  assert.equal(themes.palettes?.length, 13, 'Palette catalog is missing a choice');
  assert.equal(themes.palettes.filter(p => p.source === 'Digital Synopsis').length, 8);
  assert.equal(themes.palettes.filter(p => p.source === 'Color Hunt').length, 4);
  assert.equal(new Set(themes.palettes.map(p => p.id)).size, 13);
});

test('the saved dark palette uses dark surfaces and bright readable text', () => {
  const palette = themes.readPalette({getItem: () => 'dp-midnight'});
  assert.equal(palette.id, 'dp-midnight', 'The dark preference must survive a reload');
  assert.equal(palette.mode, 'dark');
  assert.equal(themes.getPalette().id, 'ds-7', 'Dark mode must remain optional');
  const tokens = themes.themeTokens(palette);
  for (const background of ['--paper', '--white', '--pale']) {
    assert.ok(luminance(tokens[background]) < 0.08, `${background} must stay dark`);
  }
  assert.ok(luminance(tokens['--ink']) > 0.65, 'Body text must be bright on dark surfaces');
  for (const background of ['--paper', '--white']) {
    assert.ok(contrast(tokens['--line'], tokens[background]) >= 3, `Control borders on ${background}`);
  }
});

test('unknown or unavailable saved preferences fall back to palette 7', () => {
  assert.equal(typeof themes.readPalette, 'function', 'Saved theme loading has not been added');
  for (const value of [null, '', 'removed-theme', 'toString']) {
    assert.equal(themes.readPalette({getItem: () => value}).id, 'ds-7');
  }
  assert.equal(themes.readPalette({getItem() { throw new Error('Storage denied'); }}).id, 'ds-7');
  assert.equal(themes.readPalette({getItem: () => 'ch-lavender'}).id, 'ch-lavender');
});

test('palette 7 preserves the current design and exact original swatches', () => {
  assert.equal(typeof themes.getPalette, 'function', 'Palette lookup has not been added');
  const palette = themes.getPalette('ds-7');
  assert.deepEqual(palette.colors, ['#E5FCC2', '#9DE0AD', '#45ADA8', '#547980', '#594F4F']);
  const tokens = themes.themeTokens(palette);
  assert.equal(tokens['--paper'], '#f6f8ee');
  assert.equal(tokens['--olive'], '#4e7278');
});

test('every theme keeps body, secondary, accent and target-card text readable', () => {
  assert.equal(typeof themes.themeTokens, 'function', 'Theme tokens have not been added');
  for (const palette of themes.palettes) {
    const tokens = themes.themeTokens(palette);
    for (const hex of [...palette.colors, ...Object.values(tokens)]) assert.match(hex, /^#[\da-f]{6}$/i);
    for (const foreground of ['--ink', '--muted', '--olive', '--rust']) {
      for (const background of ['--paper', '--white', '--pale']) {
        const ratio = contrast(tokens[foreground], tokens[background]);
        assert.ok(ratio >= 4.5, `${palette.id} ${foreground} on ${background}: ${ratio.toFixed(2)}`);
      }
    }
    for (const foreground of ['--accent-ink', '--accent-soft']) {
      assert.ok(contrast(tokens[foreground], tokens['--olive']) >= 4.5, `${palette.id} target-card text`);
    }
  }
});
