import json
import re
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent
DIST = ROOT.parent
PAGES = json.loads((ROOT / 'pages.json').read_text(encoding='utf-8'))
QUESTIONS = next(section for page in PAGES if page['slug'] == 'general' for section in page['sections'] if section['id'] == 'questions')
GROUP_URL = next(block['url'] for block in QUESTIONS['blocks'] if block['type'] == 'link')

def icon(name):
    paths = {
        'search': '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/>',
        'arrow': '<path d="M5 12h14m-5-5 5 5-5 5"/>',
        'external': '<path d="M14 4h6v6M20 4 10 14"/><path d="M10 4H4v16h16v-6"/>',
        'menu': '<path d="M4 6h16M4 12h16M4 18h16"/>',
        'close': '<path d="m6 6 12 12M18 6 6 18"/>',
        'link': '<path d="m10 13 4-4M8 16l-1 1a4.2 4.2 0 0 1-6-6l5-5a4.2 4.2 0 0 1 6 0m0 2 1-1a4.2 4.2 0 0 1 6 6l-5 5a4.2 4.2 0 0 1-6 0" transform="translate(2 0)"/>',
        'print': '<path d="M7 8V3h10v5M7 17H4V9h16v8h-3M7 14h10v7H7zM16 11h1"/>',
        'document': '<path d="M5 3h9l5 5v13H5zM14 3v6h5M8 13h8M8 17h6"/>',
        'home': '<path d="m3 10 9-7 9 7v11h-7v-7h-4v7H3z"/>',
        'copy': '<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
        'moon': '<path d="M20.7 13.2A8.8 8.8 0 0 1 10.8 3.3 8.8 8.8 0 1 0 20.7 13.2Z"/>',
        'sun': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.4 1.4m11.2 11.2L19 19M5 19l1.4-1.4M17.6 6.4 19 5"/>',
        'chat': '<path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5Z"/>',
    }
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths[name]}</svg>'

def text(value):
    return escape(str(value), quote=True)

def href(slug, base=''):
    return base + (f'{slug}/index.html' if slug != 'home' else 'index.html')

def block_html(block, base=''):
    kind = block['type']
    if kind == 'p':
        return f'<p>{text(block["text"])}</p>'
    if kind == 'callout':
        heading = f'<strong>{text(block["title"])}</strong>' if block.get('title') else ''
        link = f'<p><a href="{href(block["page"],base)}">{text(block["linkText"])}</a></p>' if block.get('page') else ''
        return f'<div class="callout"><span class="callout-icon" aria-hidden="true">{text(block.get("icon","💡"))}</span><div class="callout-body">{heading}<p>{text(block["text"])}</p>{link}</div></div>'
    if kind == 'link':
        return f'<a class="resource-link" href="{text(block["url"])}" target="_blank" rel="noopener noreferrer">{icon(block.get("icon", "document"))}<span>{text(block["text"])}</span>{icon("external")}</a>'
    if kind == 'table':
        head=''.join(f'<th scope="col">{text(v)}</th>' for v in block['headers'])
        rows=''.join('<tr>'+''.join(f'<td>{text(v).replace(chr(10),"<br>")}</td>' for v in row)+'</tr>' for row in block['rows'])
        return f'<div class="table-wrap" tabindex="0" aria-label="Таблица"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
    if kind == 'files':
        return '<ul class="file-list">'+''.join(f'<li><span class="file-icon">{icon("document")}</span><div><span class="file-name">{text(v["name"])}</span>'+ (f'<span class="file-description">{text(v["description"])}</span>' if v.get('description') else '')+f'</div><button class="icon-button copy-file" type="button" data-copy="{text(v["name"])}" aria-label="Копировать имя {text(v["name"])}">{icon("copy")}</button></li>' for v in block['files'])+'</ul>'
    if kind == 'accounts':
        return '<div class="account-list">'+''.join(f'<div class="account"><a href="{text(v["url"])}" target="_blank" rel="noopener noreferrer">{text(v["name"])} {icon("external")}</a><a class="account-email" href="mailto:{text(v["email"])}">{text(v["email"])}</a></div>' for v in block['accounts'])+'</div>'
    if kind == 'folder-example':
        prefix = f'{block["project"]}_{block["teamId"]}_'
        rows = [f'<tbody><tr class="example-root"><td colspan="2"><span aria-hidden="true">📂</span> <strong>{text(block["root"])}</strong></td></tr></tbody>']
        for folder in block['folders']:
            rows.append(f'<tbody><tr class="example-folder"><th scope="rowgroup" colspan="2"><span aria-hidden="true">📁</span> {text(folder["name"])}</th></tr>')
            for filename in folder['files']:
                extension = filename.rsplit('.', 1)[-1].upper()
                rows.append(f'<tr class="example-file"><td><span class="example-file-label"><span class="example-file-type" aria-hidden="true">{text(extension)}</span><span>{text(prefix + filename)}</span></span></td><td class="example-deadline">{text(folder["deadline"])}</td></tr>')
            if folder.get('note'):
                rows.append(f'<tr class="example-note"><td colspan="2">{text(folder["note"])}</td></tr>')
            rows.append('</tbody>')
        return f'<div class="folder-example"><div class="example-heading"><h3 id="folder-example">{text(block["title"])}</h3><p>Проект «{text(block["project"])}» · ТалантID команды {text(block["teamId"])}</p></div><div class="example-table-wrap"><table aria-label="{text(block["title"])}"><thead><tr><th scope="col">Название</th><th scope="col">Сдать до</th></tr></thead>{"".join(rows)}</table></div><p class="example-caption">{text(block["caption"])}</p></div>'
    raise ValueError(kind)

HOME = {
    'slug':'home','title':'Разработка компьютерных игр','icon':'🗂️',
    'eyebrow':'Национальная технологическая олимпиада',
    'lead':'Задание второго этапа сезона 2026–2027. Всё о проекте, четырех блоках работы и сдаче материалов — в одном месте.',
    'description':'Техническое задание второго этапа НТО по профилю «Разработка компьютерных игр». Сезон 2026–2027.',
    'badges':['II этап','Сезон 2026–2027'], 'sections':[]
}
ALL = [HOME]+PAGES

def navigation(page,base):
    groups=[('Задание',['home','general','age-rating']),('Блоки работы',['game-design','art','programming','product']),('Материалы',['submission'])]
    result=[]
    for group,slugs in groups:
        links=[]
        for slug in slugs:
            item=next(v for v in ALL if v['slug']==slug)
            label='Обзор задания' if slug=='home' else item['title']
            active=' aria-current="page" class="nav-link is-active"' if slug==page['slug'] else ' class="nav-link"'
            links.append(f'<a{active} href="{href(slug,base)}"><span class="nav-icon" aria-hidden="true">{text(item["icon"])}</span><span>{text(label)}</span></a>')
        result.append(f'<div class="nav-group"><p class="nav-label">{group}</p>'+''.join(links)+'</div>')
    return ''.join(result)

def homepage(base):
    cards=[]
    card_descriptions={
      'general':'Идея игры, ограничения, команда, сроки и инструменты.',
      'age-rating':'Границы допустимого содержания игры и материалов.',
      'game-design':'Опыт игрока, игровые циклы и концепт-документ.',
      'art':'Визуальный образ игры в артбуке из семи страниц.',
      'programming':'Центральный цикл, архитектура и три уровня реализации.',
      'product':'Демоверсия, плейтест, тизер, ролики и презентация.',
      'submission':'Состав файлов, структура папок, доступ и отправка.'
    }
    for page in PAGES:
        score=next((x for x in page['badges'] if 'балл' in x),'')
        cards.append(f'<a class="page-card" href="{href(page["slug"],base)}"><span class="card-icon" aria-hidden="true">{text(page["icon"])}</span><div><span class="card-title">{text(page["title"])}</span><p class="card-description">{card_descriptions[page["slug"]]}</p>{f"<span class=badge>{text(score)}</span>" if score else ""}</div><span class="card-arrow">{icon("arrow")}</span></a>')
    return f'''<div class="callout"><span class="callout-icon" aria-hidden="true">🚪</span><div class="callout-body"><strong>Одна комната или одна сцена</strong><p>Создайте камерную игру о реальной или вымышленной деятельности. Свяжите операции, дайте игроку выбор и покажите последствия решений.</p></div></div>
    <div class="stats-grid" aria-label="Кратко о демоверсии"><div class="stat"><span class="stat-value">10+ минут</span><span class="stat-label">Первое прохождение</span></div><div class="stat"><span class="stat-value">Windows</span><span class="stat-label">Готовая сборка</span></div><div class="stat"><span class="stat-value">Мышь</span><span class="stat-label">Основное управление</span></div></div>
    <h2 id="pages">Страницы задания</h2><p>Начните с общей информации, затем откройте блок, над которым работаете.</p><div class="page-grid">{''.join(cards)}</div>
    <h2 id="dates">Ключевые даты</h2><div class="table-wrap"><table><thead><tr><th scope="col">Что сдаём</th><th scope="col">Срок</th></tr></thead><tbody><tr><td>Геймдизайн</td><td>21 ноября 2026</td></tr><tr><td>Арт и программирование</td><td>28 ноября 2026</td></tr><tr><td>Продукт</td><td>1 декабря 2026</td></tr></tbody></table></div><p class="secondary-text">Все блоки открываются 10 ноября. Полный календарь — в <a href="{href('general',base)}#dates">общей информации</a>.</p>
    <h2 id="questions">Вопросы организаторам</h2>{''.join(block_html(block,base) for block in QUESTIONS['blocks'])}'''

search_records=[]
for page in ALL:
    base='' if page['slug']=='home' else '../'
    sections = page['sections']
    if page['slug']=='home':
        content=homepage(base)
        headings=[('pages','Страницы задания'),('dates','Ключевые даты'),('questions','Вопросы организаторам')]
    else:
        content=''.join(f'<section aria-labelledby="{text(s["id"])}"><h2 id="{text(s["id"])}">{text(s["title"])}</h2>'+''.join(block_html(b,base) for b in s['blocks'])+'</section>' for s in sections)
        headings=[(s['id'],s['title']) for s in sections]
    toc=''.join(f'<a href="#{text(id)}">{text(title)}</a>' for id,title in headings)
    index=ALL.index(page)
    footerlinks=[]
    for offset,cls,label in [(-1,'prev','Предыдущая страница'),(1,'next','Следующая страница')]:
        if 0<=index+offset<len(ALL):
            adjacent=ALL[index+offset]
            footerlinks.append(f'<a class="{cls}" href="{href(adjacent["slug"],base)}"><small>{label}</small><strong>{text("Обзор задания" if adjacent["slug"]=="home" else adjacent["title"])}</strong><span class="nav-arrow">{icon("arrow")}</span></a>')
        else:
            footerlinks.append('<span></span>')
    title='Обзор задания' if page['slug']=='home' else page['title']
    markup=f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="{text(page['description'])}"><meta name="theme-color" content="#f5f4ef"><title>{text(title)} · РКИ 2026–2027</title><script src="{base}theme.js"></script><link rel="icon" href="{base}favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{base}styles.css"><link rel="stylesheet" href="{base}extras.css"><link rel="stylesheet" href="{base}theme.css"><script src="{base}search-index.js" defer></script><script src="{base}app.js" defer></script></head>
<body data-base="{base}" data-page="{page['slug']}"><a class="skip-link" href="#main-content">Перейти к содержанию</a><div class="app">
<aside class="sidebar" id="sidebar" aria-label="Навигация по заданию"><div class="sidebar-head"><a class="brand" href="{href('home',base)}"><span class="brand-mark">Р</span><span class="brand-copy">Разработка игр<small>НТО · 2026–2027</small></span></a></div><button class="search-trigger" type="button" data-search-open>{icon('search')}<span>Поиск по заданию</span><kbd>Ctrl K</kbd></button><nav>{navigation(page,base)}</nav><div class="sidebar-foot"><strong>Задание второго этапа</strong><span>Одна комната или одна сцена</span><a class="support-link" href="{GROUP_URL}" target="_blank" rel="noopener noreferrer">{icon('chat')}<span>Вопросы организаторам</span>{icon('external')}</a></div></aside>
<button class="sidebar-scrim" type="button" aria-label="Закрыть меню" hidden></button>
<main class="main" id="main-content" tabindex="-1"><header class="topbar"><button class="menu-toggle" aria-label="Открыть меню" aria-controls="sidebar" aria-expanded="false">{icon('menu')}</button><nav class="breadcrumbs" aria-label="Хлебные крошки"><a href="{href('home',base)}">РКИ</a><span class="separator" aria-hidden="true">/</span><span>II этап</span><span class="separator" aria-hidden="true">/</span><span class="current" aria-current="page">{text(title)}</span></nav><div class="topbar-actions"><button class="icon-button theme-toggle" type="button" data-theme-toggle aria-label="Включить тёмную тему" aria-pressed="false" title="Включить тёмную тему"><span class="theme-moon">{icon('moon')}</span><span class="theme-sun">{icon('sun')}</span></button><button class="icon-button" type="button" data-copy-page aria-label="Скопировать ссылку на страницу" title="Скопировать ссылку">{icon('link')}</button><button class="icon-button" type="button" data-print aria-label="Распечатать страницу" title="Печать">{icon('print')}</button></div></header>
<div class="page-layout"><article class="page"><div class="page-icon" aria-hidden="true">{text(page['icon'])}</div><p class="eyebrow">{text(page['eyebrow'])}</p><h1 class="page-title">{text(page['title'])}</h1><p class="page-lead">{text(page['lead'])}</p><div class="page-meta">{''.join(f'<span class="badge {"badge-blue" if i==0 else "badge-outline"}">{text(b)}</span>' for i,b in enumerate(page['badges']))}</div><div class="content">{content}</div><nav class="page-navigation" aria-label="Соседние страницы">{''.join(footerlinks)}</nav><footer class="page-footer">НТО · Профиль «Разработка компьютерных игр» · Сезон 2026–2027</footer></article><aside class="toc" aria-label="На этой странице"><p class="toc-title">На этой странице</p>{toc}</aside></div></main></div>
<div class="search-overlay" hidden><div class="search-dialog" role="dialog" aria-modal="true" aria-label="Поиск по заданию"><div class="search-header">{icon('search')}<input class="search-input" type="search" placeholder="Поиск по страницам и разделам" aria-label="Поисковый запрос" autocomplete="off" aria-controls="search-results"><button class="search-close" type="button" aria-label="Закрыть поиск">{icon('close')}</button></div><div class="search-results" id="search-results" aria-live="polite"></div><div class="search-hint"><span>↑ ↓ выбрать · Enter открыть</span><span>Esc закрыть</span></div></div></div><div class="toast" role="status" aria-live="polite"></div>
</body></html>'''
    directory=DIST if page['slug']=='home' else DIST/page['slug']
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'index.html').write_text(markup,encoding='utf-8')
    search_records.append({'title':page['title'],'pageTitle':page['title'],'url':href(page['slug']),'body':page['lead']})
    for section in sections:
        body=[]
        for b in section['blocks']:
            if 'title' in b: body.append(b['title'])
            if 'text' in b: body.append(b['text'])
            if 'linkText' in b: body.append(b['linkText'])
            if b['type']=='table': body.extend(' '.join(str(x) for x in row) for row in b['rows'])
            if b['type']=='files': body.extend(v['name']+' '+v.get('description','') for v in b['files'])
            if b['type']=='accounts': body.extend(' '.join(v.values()) for v in b['accounts'])
            if b['type']=='folder-example':
                body.extend([b['root'],b['project'],b['teamId'],b['caption']])
                for folder in b['folders']:
                    body.extend([folder['name'],folder['deadline'],folder.get('note','')])
                    body.extend(f'{b["project"]}_{b["teamId"]}_{name}' for name in folder['files'])
        search_records.append({'title':section['title'],'pageTitle':page['title'],'url':href(page['slug'])+'#'+section['id'],'body':' '.join(body)})
(DIST/'search-index.js').write_text('window.RKI_SEARCH_INDEX = '+json.dumps(search_records,ensure_ascii=False)+';\n',encoding='utf-8')
(DIST/'favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="10" fill="#edf0e6"/><path d="M14 34V12h11c11 0 11 14 0 14H14m10 0 10 8" fill="none" stroke="#3c4937" stroke-width="4" stroke-linejoin="round"/></svg>',encoding='utf-8')
print(f'Built {len(ALL)} HTML pages and {len(search_records)} searchable sections.')
