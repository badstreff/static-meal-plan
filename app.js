(() => {
  const groceries = [...document.querySelectorAll('#groceries input[type="checkbox"]')];
  const key = 'daily-plate-groceries-v1';
  const progress = document.querySelector('#list-progress');
  let saved = [];
  try {
    const parsed = JSON.parse(localStorage.getItem(key) || '[]');
    if (Array.isArray(parsed)) saved = parsed;
  } catch { /* Checklist remains usable when storage is unavailable. */ }
  groceries.forEach(input => { input.checked = saved.includes(input.id); });
  function updateList() {
    const checked = groceries.filter(input => input.checked).map(input => input.id);
    progress.textContent = `${checked.length} / ${groceries.length} checked`;
    try { localStorage.setItem(key, JSON.stringify(checked)); } catch { /* Optional persistence. */ }
  }
  groceries.forEach(input => input.addEventListener('change', updateList));
  document.querySelector('[data-reset]').addEventListener('click', () => {
    groceries.forEach(input => { input.checked = false; });
    updateList();
  });
  updateList();
  function openTarget() {
    let target;
    try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch { return; }
    if (!target) return;
    if (target.matches('details')) target.open = true;
    const parent = target.closest('details');
    if (parent) parent.open = true;
  }
  window.addEventListener('hashchange', openTarget);
  openTarget();
  const recipes = [...document.querySelectorAll('details.recipe')];
  const expand = document.querySelector('[data-expand]');
  function updateExpand() {
    expand.textContent = recipes.every(recipe => recipe.open) ? 'Collapse all recipes' : 'Expand all recipes';
  }
  expand.addEventListener('click', () => {
    const shouldOpen = !recipes.every(recipe => recipe.open);
    recipes.forEach(recipe => { recipe.open = shouldOpen; });
    updateExpand();
  });
  recipes.forEach(recipe => recipe.addEventListener('toggle', updateExpand));
  let prePrint;
  function preparePrint() {
    if (prePrint) return;
    const all = [...document.querySelectorAll('details')];
    prePrint = all.map(detail => [detail, detail.open]);
    all.forEach(detail => { detail.open = true; });
  }
  window.addEventListener('beforeprint', preparePrint);
  window.addEventListener('afterprint', () => {
    (prePrint || []).forEach(([detail, open]) => { detail.open = open; });
    prePrint = undefined;
  });
  document.querySelector('[data-print]').addEventListener('click', () => { preparePrint(); window.print(); });
})();
