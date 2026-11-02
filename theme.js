(() => {
  'use strict';
  const key = 'rki-theme';
  const valid = value => value === 'light' || value === 'dark';
  const root = document.documentElement;
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  let preference = null;
  try {
    const saved = localStorage.getItem(key);
    if (valid(saved)) preference = saved;
  } catch { /* Browsers may disable storage for local HTML files. */ }
  if (location.protocol === 'file:') {
    const requested = new URL(location.href).searchParams.get('theme');
    if (valid(requested)) preference = requested;
  }
  let current;

  function withTheme(href) {
    if (location.protocol !== 'file:' || !preference || href.startsWith('#')) return href;
    const target = new URL(href, location.href);
    if (target.protocol !== 'file:' || !target.pathname.endsWith('.html')) return href;
    target.searchParams.set('theme', current);
    return target.href;
  }
  function syncControls() {
    const dark = current === 'dark';
    const label = dark ? 'Включить светлую тему' : 'Включить тёмную тему';
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.setAttribute('aria-pressed', String(dark));
      button.setAttribute('aria-label', label);
      button.title = label;
    });
    document.querySelectorAll('a[href]').forEach(link => {
      const href = link.getAttribute('href');
      const themed = withTheme(href);
      if (themed !== href) link.setAttribute('href', themed);
    });
  }
  function apply(value) {
    current = value;
    root.dataset.theme = value;
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', value === 'dark' ? '#232420' : '#f5f4ef');
    syncControls();
  }
  function set(value) {
    if (!valid(value)) return;
    preference = value;
    try { localStorage.setItem(key, value); } catch { /* Navigation still carries the selection for local files. */ }
    apply(value);
  }
  apply(preference || (system.matches ? 'dark' : 'light'));
  window.RKITheme = Object.freeze({ set, withTheme, getCurrent: () => current });
  document.addEventListener('DOMContentLoaded', () => {
    syncControls();
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.addEventListener('click', () => set(current === 'dark' ? 'light' : 'dark'));
    });
  }, { once: true });
  system.addEventListener('change', () => {
    if (!preference) apply(system.matches ? 'dark' : 'light');
  });
  window.addEventListener('storage', event => {
    if (event.key !== key) return;
    preference = valid(event.newValue) ? event.newValue : null;
    apply(preference || (system.matches ? 'dark' : 'light'));
  });
})();
