(() => {
  const storageKey = 'daily-plate-palette-v1';
  const synopsis = 'https://digitalsynopsis.com/design/minimal-web-color-palettes-combination-hex-code/';
  // Names describe these choices; the swatches are the exact source colors.
  const palettes = [
    {id: 'ds-1', name: '1 · Peach & dusk', source: 'Digital Synopsis', url: synopsis, colors: ['#F8B195', '#F67280', '#C06C84', '#6C5B7B', '#355C7D'], paper: 0, accent: 4, shadow: 1},
    {id: 'ds-2', name: '2 · Coral & charcoal', source: 'Digital Synopsis', url: synopsis, colors: ['#99B898', '#FECEAB', '#FF847C', '#E84A5F', '#2A363B'], paper: 1, accent: 3, shadow: 0},
    {id: 'ds-3', name: '3 · Pastel garden', source: 'Digital Synopsis', url: synopsis, colors: ['#A8E6CE', '#DCEDC2', '#FFD3B5', '#FFAAA6', '#FF8C94'], paper: 1, accent: 4, shadow: 0},
    {id: 'ds-4', name: '4 · Raspberry & slate', source: 'Digital Synopsis', url: synopsis, colors: ['#A8A7A7', '#CC527A', '#E8175D', '#474747', '#363636'], paper: 0, accent: 2, shadow: 1},
    {id: 'ds-5', name: '5 · Golden hour', source: 'Digital Synopsis', url: synopsis, colors: ['#A7226E', '#EC2049', '#F26B38', '#F7DB4F', '#2F9599'], paper: 3, accent: 0, shadow: 4},
    {id: 'ds-6', name: '6 · Citrus & poppy', source: 'Digital Synopsis', url: synopsis, colors: ['#E1F5C4', '#EDE574', '#F9D423', '#FC913A', '#FF4E50'], paper: 0, accent: 4, shadow: 2},
    {id: 'ds-7', name: '7 · Mint & teal (default)', source: 'Digital Synopsis', url: synopsis, colors: ['#E5FCC2', '#9DE0AD', '#45ADA8', '#547980', '#594F4F'], paper: 0, accent: 3, shadow: 1},
    {id: 'ds-8', name: '8 · Rose & sea glass', source: 'Digital Synopsis', url: synopsis, colors: ['#FE4365', '#FC9D9A', '#F9CDAD', '#C8C8A9', '#83AF9B'], paper: 2, accent: 0, shadow: 4},
    {id: 'ch-sage', name: 'Sage & cream', source: 'Color Hunt', url: 'https://colorhunt.co/palette/f8f3d9ebe5c2b9b28a504b38', colors: ['#F8F3D9', '#EBE5C2', '#B9B28A', '#504B38'], paper: 0, accent: 3, shadow: 2},
    {id: 'ch-coastal', name: 'Coastal blue', source: 'Color Hunt', url: 'https://colorhunt.co/palette/89a8b2b3c8cfe5e1daf1f0e8', colors: ['#89A8B2', '#B3C8CF', '#E5E1DA', '#F1F0E8'], paper: 3, accent: 0, shadow: 1},
    {id: 'ch-lavender', name: 'Lavender & cream', source: 'Color Hunt', url: 'https://colorhunt.co/palette/fff2e0c0c9eea2aadb898ac4', colors: ['#FFF2E0', '#C0C9EE', '#A2AADB', '#898AC4'], paper: 0, accent: 3, shadow: 1},
    {id: 'ch-terracotta', name: 'Terracotta & linen', source: 'Color Hunt', url: 'https://colorhunt.co/palette/f8ede3dfd3c3d0b8a88d493a', colors: ['#F8EDE3', '#DFD3C3', '#D0B8A8', '#8D493A'], paper: 0, accent: 3, shadow: 2}
  ];
  function getPalette(id) {
    return palettes.find(palette => palette.id === id) || palettes[6];
  }
  function readPalette(storage) {
    try { return getPalette(storage.getItem(storageKey)); }
    catch { return getPalette(); }
  }
  function rgb(hex) {
    return hex.slice(1).match(/../g).map(channel => parseInt(channel, 16));
  }
  function mix(a, b, amount) {
    const other = rgb(b);
    return '#' + rgb(a).map((channel, i) => Math.round(channel * (1 - amount) + other[i] * amount).toString(16).padStart(2, '0')).join('');
  }
  function luminance(hex) {
    const channels = rgb(hex).map(value => {
      const v = value / 255;
      return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
    });
    return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
  }
  function readable(color, backgrounds) {
    for (let step = 0; step < 100; step++) {
      const foreground = luminance(color);
      if (backgrounds.every(background => {
        const backdrop = luminance(background);
        return (Math.max(foreground, backdrop) + 0.05) / (Math.min(foreground, backdrop) + 0.05) >= 4.6;
      })) return color;
      color = mix(color, '#000000', 0.05);
    }
    return '#000000';
  }
  function themeTokens(palette) {
    const base = palette.colors[palette.paper];
    const accent = palette.colors[palette.accent];
    const paper = mix(base, '#ffffff', 0.58);
    const surface = mix(base, '#ffffff', 0.91);
    const pale = mix(base, '#ffffff', 0.18);
    const backgrounds = [paper, surface, pale, '#ffffff'];
    const ink = readable(mix(accent, '#000000', 0.55), backgrounds);
    const olive = readable(accent, backgrounds);
    const tokens = {
      '--paper': paper, '--white': surface, '--pale': pale,
      '--ink': ink, '--olive': olive, '--rust': olive,
      '--muted': readable(mix(ink, paper, 0.3), backgrounds),
      '--line': mix(ink, paper, 0.84),
      '--accent-ink': '#ffffff', '--accent-soft': '#ffffff',
      '--shadow': palette.colors[palette.shadow],
      '--target-line': mix(olive, '#ffffff', 0.35)
    };
    palette.colors.slice(0, 4).forEach((color, i) => { tokens[`--stripe-${i + 1}`] = color; });
    if (palette.id === 'ds-7') Object.assign(tokens, {
      '--paper': '#f6f8ee', '--white': '#fcfdf8', '--ink': '#3f3939',
      '--olive': '#4e7278', '--muted': '#666b69', '--line': '#d7e1d8',
      '--pale': '#e5fcc2', '--rust': '#406765', '--accent-ink': '#f6f8ee',
      '--accent-soft': '#e5fcc2', '--shadow': '#9de0ad', '--target-line': '#83afaa',
      '--stripe-1': '#45ada8', '--stripe-2': '#547980', '--stripe-3': '#9de0ad', '--stripe-4': '#594f4f'
    });
    return tokens;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {palettes, getPalette, readPalette, themeTokens};
  }
  if (typeof document === 'undefined') return;

  let storage;
  try { storage = window.localStorage; } catch { /* Browsing without storage is supported. */ }
  let current = readPalette(storage);
  function paint(palette) {
    Object.entries(themeTokens(palette)).forEach(([name, color]) => document.documentElement.style.setProperty(name, color));
    document.documentElement.dataset.palette = palette.id;
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', themeTokens(palette)['--paper']);
  }
  // Runs in the head so a saved choice is applied before the page is painted.
  paint(current);
  function mount() {
    const toolbar = document.querySelector('[data-palette-toolbar]');
    if (!toolbar) return;
    const select = document.querySelector('#palette-select');
    const swatches = document.querySelector('[data-palette-swatches]');
    const source = document.querySelector('[data-palette-source]');
    ['Digital Synopsis', 'Color Hunt'].forEach(name => {
      const group = document.createElement('optgroup');
      group.label = name;
      palettes.filter(palette => palette.source === name).forEach(palette => {
        const option = document.createElement('option');
        option.value = palette.id;
        option.textContent = palette.name;
        group.append(option);
      });
      select.append(group);
    });
    function updatePreview() {
      select.value = current.id;
      swatches.replaceChildren(...current.colors.map(color => {
        const swatch = document.createElement('span');
        swatch.style.backgroundColor = color;
        swatch.title = color;
        return swatch;
      }));
      swatches.setAttribute('aria-label', `Original palette colors: ${current.colors.join(', ')}`);
      source.href = current.url;
      source.textContent = `${current.source} ↗`;
    }
    select.addEventListener('change', () => {
      current = getPalette(select.value);
      paint(current);
      updatePreview();
      try { storage?.setItem(storageKey, current.id); } catch { /* Optional persistence. */ }
    });
    updatePreview();
    toolbar.hidden = false;
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, {once: true});
  else mount();
})();
