(() => {
  'use strict';
  const base = document.body.dataset.base || '';
  const overlay = document.querySelector('.search-overlay');
  const input = document.querySelector('.search-input');
  const results = document.querySelector('.search-results');
  const sidebar = document.querySelector('.sidebar');
  const main = document.querySelector('.main');
  const menuButton = document.querySelector('.menu-toggle');
  const scrim = document.querySelector('.sidebar-scrim');
  const mobile = matchMedia('(max-width: 760px)');
  let priorFocus, chosen = -1, toastTimer;
  const normalize = str => str.toLocaleLowerCase('ru').replaceAll('ё', 'е');
  const escape = str => str.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function menu(open) {
    const wasOpen = document.body.classList.contains('menu-open');
    document.body.classList.toggle('menu-open', open);
    menuButton.setAttribute('aria-expanded', String(open));
    menuButton.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
    scrim.hidden = !open;
    sidebar.inert = mobile.matches && !open;
    main.inert = mobile.matches && open;
    if (open) sidebar.querySelector('.nav-link[aria-current="page"]').focus();
    else if (wasOpen) menuButton.focus();
  }
  menuButton.addEventListener('click', () => menu(!document.body.classList.contains('menu-open')));
  scrim.addEventListener('click', () => menu(false));
  mobile.addEventListener('change', () => menu(false));
  menu(false);

  function mark(str, terms) {
    const pattern = terms.filter(Boolean).map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
    if (!pattern) return escape(str);
    const regex = new RegExp(pattern, 'ig');
    let html = '', last = 0;
    for (const m of str.matchAll(regex)) {
      html += escape(str.slice(last, m.index)) + '<mark>' + escape(m[0]) + '</mark>';
      last = m.index + m[0].length;
    }
    return html + escape(str.slice(last));
  }
  function search() {
    const query = input.value.trim();
    chosen = -1;
    if (!query) {
      results.innerHTML = '<div class="search-empty"><strong>■■■■■■■ ■■■■■■ ■ ■■■■■■■</strong><p>■■■■■■■■■ ■■■■■■■■■■■■ ■■■■■■■ ■■■■■ ■■■ ■■■■■■■■■■■</p></div>';
      return;
    }
    const terms = normalize(query).split(/\s+/);
    const found = (window.RKI_SEARCH_INDEX || []).filter(r => terms.every(term => normalize(r.title+' '+r.pageTitle+' '+r.body).includes(term))).sort((a,b) => {
      const rank = r => terms.reduce((s,t) => s + (normalize(r.title).includes(t) ? 4 : 0) + (normalize(r.pageTitle).includes(t) ? 1 : 0),0);
      return rank(b) - rank(a);
    }).slice(0,30);
    results.innerHTML = found.length ? found.map(r => {
      const first = normalize(r.body).indexOf(terms[0]);
      const start = first > 70 ? first - 55 : 0;
      const snippet = (start ? '…' : '') + r.body.slice(start,start+190) + (r.body.length > start+190 ? '…' : '');
      return '<a class="search-result" href="'+escape(window.RKITheme.withTheme(base+r.url))+'"><span class="search-result-path">'+escape(r.pageTitle)+'</span><strong>'+mark(r.title,query.split(/\s+/))+'</strong><p>'+mark(snippet,query.split(/\s+/))+'</p></a>';
    }).join('') : '<div class="search-empty"><strong>■■■■■■ ■■ ■■■■■■■</strong><p>■■■■■■■■■■ ■■■■■■ ■■■■■ ■■■ ■■■■■ ■■■■■■■■ ■■■■■■■</p></div>';
  }
  function openSearch() {
    priorFocus = document.activeElement;
    menu(false);
    overlay.hidden = false;
    document.body.classList.add('search-open');
    document.querySelector('.app').inert = true;
    search();
    input.focus();
  }
  function closeSearch() {
    overlay.hidden = true;
    document.body.classList.remove('search-open');
    document.querySelector('.app').inert = false;
    sidebar.inert = mobile.matches && !document.body.classList.contains('menu-open');
    if (priorFocus?.isConnected && !priorFocus.closest('[inert]')) priorFocus.focus();
    else menuButton.focus();
  }
  document.querySelectorAll('[data-search-open]').forEach(el => el.addEventListener('click',openSearch));
  document.querySelector('.search-close').addEventListener('click',closeSearch);
  overlay.addEventListener('click',event => { if(event.target === overlay) closeSearch(); });
  input.addEventListener('input',search);
  results.addEventListener('click',event => { if(event.target.closest('a')) closeSearch(); });
  document.addEventListener('keydown',event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      overlay.hidden ? openSearch() : closeSearch();
    }
    if (event.key === 'Escape') {
      if (!overlay.hidden) closeSearch();
      else if(document.body.classList.contains('menu-open')) { menu(false); menuButton.focus(); }
    }
    if (!overlay.hidden) {
      const links = [...results.querySelectorAll('a')];
      if (['ArrowDown','ArrowUp'].includes(event.key) && links.length) {
        event.preventDefault();
        chosen = chosen < 0 ? (event.key === 'ArrowDown' ? 0 : links.length-1) : (event.key === 'ArrowDown' ? (chosen+1)%links.length : (chosen-1+links.length)%links.length);
        links.forEach((link,i) => link.classList.toggle('is-selected',i===chosen));
        links[chosen].scrollIntoView({block:'nearest'});
      }
      if(event.key === 'Enter' && links.length && document.activeElement === input) {
        event.preventDefault(); links[Math.max(0,chosen)].click();
      }
      if(event.key === 'Tab') {
        const focusable = [...overlay.querySelectorAll('input,button,a[href]')];
        const at = focusable.indexOf(document.activeElement);
        if(event.shiftKey && at === 0) {event.preventDefault();focusable.at(-1).focus();}
        if(!event.shiftKey && at === focusable.length-1) {event.preventDefault();focusable[0].focus();}
      }
    }
    if (event.key === 'Tab' && overlay.hidden && document.body.classList.contains('menu-open')) {
      const links = [...sidebar.querySelectorAll('a[href],button')];
      const at = links.indexOf(document.activeElement);
      if (event.shiftKey && at === 0) { event.preventDefault(); links.at(-1).focus(); }
      if (!event.shiftKey && at === links.length-1) { event.preventDefault(); links[0].focus(); }
    }
  });

  function toast(message) {
    const target = document.querySelector('.toast');
    target.textContent = message;
    target.classList.add('visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => target.classList.remove('visible'),2400);
  }
  async function copy(value) {
    try {
      if (navigator.clipboard && isSecureContext) await navigator.clipboard.writeText(value);
      else {
        const area = document.createElement('textarea');
        area.value = value; area.style.position='fixed'; area.style.opacity='0'; document.body.append(area); area.select();
        const copied = document.execCommand('copy'); area.remove(); if(!copied) throw new Error('copy');
      }
      toast('■■■■■■■■■■■');
    } catch { toast('■■ ■■■■■■■ ■■■■■■■■■■■■ ■■■■■■■■ ■■■■■ ■■■■■■■■'); }
  }
  document.querySelector('[data-copy-page]').addEventListener('click',()=>copy(location.href));
  document.querySelectorAll('[data-copy]').forEach(el => el.addEventListener('click',()=>copy(el.dataset.copy)));
  document.querySelector('[data-print]').addEventListener('click',()=>window.print());

  const tocLinks = [...document.querySelectorAll('.toc a')];
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) if(entry.isIntersecting) {
      tocLinks.forEach(link => {
        const active = link.hash === '#'+entry.target.id;
        link.classList.toggle('is-active',active);
        active ? link.setAttribute('aria-current','location') : link.removeAttribute('aria-current');
      });
    }
  },{rootMargin:'-70px 0px -65% 0px'});
  document.querySelectorAll('.content h2[id]').forEach(h => observer.observe(h));
})();
