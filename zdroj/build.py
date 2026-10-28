"""Add a blog (SK /blog/, EN /en/blog/) to the static gta6rp.sk site.

Usage: python3 -I build.py <web-dir>
Reads posts from posts.py next to this script. Safe to re-run: page-level
edits (nav link, footer link) are applied only once.
"""
import html, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from posts import POSTS

WEB = sys.argv[1]
SITE = "https://gta6rp.sk"
ARROW = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-arrow-up-right" aria-hidden="true"><path d="M7 7h10v10"/><path d="M7 17 17 7"/></svg>'

L = {
    "sk": dict(tpl="rp/navody/sceny.html", base="/blog/", home="/", locale="sk_SK",
               blog="Blog", blog_title="Blog: zaujímavosti o GTA 6 a roleplayi",
               blog_h1="Zaujímavosti o GTA 6 a roleplayi",
               blog_desc="Novinky, zaujímavosti a tipy o GTA 6, štáte Leonida a GTA roleplayi. Po slovensky, bez zbytočnej omáčky.",
               blog_lead="Čo vieme o hre, odkiaľ sa vzal GTA roleplay a nápady, ako sa naň pripraviť.",
               eyebrow="BLOG GTA6RP.SK", read="min čítania", more="Čítať článok",
               next="ĎALŠIE ČLÁNKY", all="Všetky články", crumbs="Drobčeková navigácia",
               nav_after='<a href="/rp/pojmy/">RP slovník</a>', nav_link='<a href="/blog/">Blog</a>',
               foot_after='<a href="/rp/">Svet RP</a>', foot_link='<a href="/blog/">Blog</a>',
               cta_eye="TVOJ PRÍBEH ZAČÍNA TERAZ", cta_h="Daj svojmu nápadu meno.",
               cta_p="V dielni postáv si vytvoríš vlastné lore, uložíš koncept a môžeš sa k nemu vrátiť.",
               cta_btn="Vytvoriť svoju postavu", cta_href="/rp/tvorba-postavy/",
               months=["januára", "februára", "marca", "apríla", "mája", "júna", "júla", "augusta", "septembra", "októbra", "novembra", "decembra"]),
    "en": dict(tpl="en/rp/guides/scenes.html", base="/en/blog/", home="/en/", locale="en_US",
               blog="Blog", blog_title="Blog: GTA 6 and roleplay facts",
               blog_h1="GTA 6 and roleplay, explained",
               blog_desc="News, facts and tips about GTA 6, the state of Leonida and GTA roleplay. Short reads, no filler.",
               blog_lead="What we know about the game, where GTA roleplay came from and ideas to get ready for it.",
               eyebrow="GTA6RP.SK BLOG", read="min read", more="Read article",
               next="MORE ARTICLES", all="All articles", crumbs="Breadcrumb",
               nav_after='<a href="/en/rp/glossary/">RP glossary</a>', nav_link='<a href="/en/blog/">Blog</a>',
               foot_after='<a href="/en/rp/">Explore RP</a>', foot_link='<a href="/en/blog/">Blog</a>',
               cta_eye="YOUR STORY STARTS NOW", cta_h="Give your idea a name.",
               cta_p="Build your character's backstory in the workshop, save a draft and return to it whenever you like.",
               cta_btn="Create your character", cta_href="/en/rp/character-builder/",
               months=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]),
}

BLOG_CSS = (".post-grid{grid-template-columns:repeat(auto-fill,minmax(min(100%,330px),1fr));gap:22px;display:grid}"
            ".post-card{background:var(--panel);border:1px solid var(--line);border-radius:10px;flex-direction:column;gap:14px;padding:28px;display:flex}"
            ".post-card:hover{border-color:#9655b8}.post-card h2{margin:0;font-size:26px}.post-card h2 a:hover{color:var(--peach)}"
            ".post-card p{color:#bdaccb;flex:1;margin:0;font-size:13px;line-height:1.85}"
            ".post-card .more{color:var(--peach);align-items:center;gap:8px;font-size:12px;font-weight:800;display:inline-flex}"
            ".post-meta{color:#a993b8;letter-spacing:.4px;font-size:11px}.post-meta .cat{color:var(--pink);font-weight:800}"
            ".article-layout article a:not(.button){color:var(--pink);text-underline-offset:3px;text-decoration:underline}"
            ".article-layout article strong{color:var(--white)}"
            ".fact-box{background:#ffffff08;border-left:3px solid var(--pink);border-radius:0 8px 8px 0;margin:0 0 35px;padding:18px 22px}"
            ".fact-box p{margin:0}"
            "@media (width<=600px){.post-card{padding:22px}.post-card h2{font-size:23px}}")


def esc(s):
    return html.escape(s, quote=True)


def words(h):
    return len(re.sub(r"<[^>]+>", " ", h).split())


def nice_date(lang, iso):
    y, m, d = map(int, iso.split("-"))
    if lang == "sk":
        return f"{d}. {L[lang]['months'][m - 1]} {y}"
    return f"{L[lang]['months'][m - 1]} {d}, {y}"


def read(rel):
    with open(os.path.join(WEB, rel), encoding="utf-8") as f:
        return f.read()


def write(rel, s):
    path = os.path.join(WEB, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


NAV_CSS = '@media (width<=700px){.site-header>nav a[href$="#co-pride"]{display:none}}'


def add_links(s, lang):
    c = L[lang]
    if NAV_CSS not in s and "</style>" in s:
        s = s.replace("</style>", NAV_CSS + "</style>", 1)
    if c["nav_link"] not in s:
        s = s.replace(c["nav_after"] + '<a href="/', c["nav_after"] + c["nav_link"] + '<a href="/', 1)
    foot = s[s.find("<footer"):]
    if c["foot_link"] not in foot:
        s = s[:s.find("<footer")] + foot.replace(c["foot_after"], c["foot_after"] + c["foot_link"], 1)
    return s


def parts(lang):
    t = read(L[lang]["tpl"])
    head = t[:t.index("<title>")].replace("</style>", BLOG_CSS + "</style>", 1)
    script = re.search(r'<script defer src="/assets/core\.js[^"]*"></script>', t).group(0)
    header = add_links(t[t.index('<header'):t.index('</header>') + 9], lang)
    footer = add_links(t[t.index('<footer'):], lang)
    return head, script, header, footer


def lang_switch(header, lang, sk_url, en_url):
    return re.sub(r'(<a href=")[^"]*(" data-language="en")', r'\g<1>' + en_url + r'\2',
                  re.sub(r'(<a href=")[^"]*(" data-language="sk")', r'\g<1>' + sk_url + r'\2', header))


def meta(lang, title, desc, url, sk_url, en_url, og_type):
    full = f"{title} | GTA6RP.sk"
    alt = "GTA6RP.sk — GTA 6 a roleplay po slovensky" if lang == "sk" else "GTA6RP.sk — GTA 6 and roleplay"
    return (f'<title>{esc(full)}</title><meta name="description" content="{esc(desc)}">'
            f'<meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="{SITE}{url}">'
            f'<meta property="og:type" content="{og_type}"><meta property="og:locale" content="{L[lang]["locale"]}"><meta property="og:site_name" content="GTA6RP.sk">'
            f'<meta property="og:title" content="{esc(full)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{SITE}{url}">'
            f'<meta property="og:image" content="{SITE}/og-brand.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:type" content="image/jpeg"><meta property="og:image:alt" content="{esc(alt)}">'
            f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(full)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{SITE}/og-brand.jpg"><meta name="twitter:image:alt" content="{esc(alt)}">'
            f'<link rel="alternate" hreflang="sk" href="{SITE}{sk_url}"><link rel="alternate" hreflang="en" href="{SITE}{en_url}"><link rel="alternate" hreflang="x-default" href="{SITE}{sk_url}">')


def crumbs(lang, items):
    c = L[lang]
    html_items = []
    for i, (name, url) in enumerate(items):
        if i == len(items) - 1:
            html_items.append(f'<span aria-current="page">{esc(name)}</span>')
        else:
            html_items.append(f'<a href="{url}">{esc(name)}</a>')
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items)]}
    return (f'<nav class="breadcrumbs" aria-label="{c["crumbs"]}">' + "<span>/</span>".join(html_items) + "</nav>"
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')


def url_of(lang, post):
    return L[lang]["base"] + post[lang]["slug"] + "/"


def mins(post, lang):
    return max(2, round(words(post[lang]["body"]) / 200))


def meta_line(lang, post):
    p = post[lang]
    return (f'<span class="cat">{esc(p["cat"])}</span> · <time datetime="{post["date"]}">{nice_date(lang, post["date"])}</time>'
            f' · {mins(post, lang)} {L[lang]["read"]}')


def build_index(lang):
    c = L[lang]
    head, script, header, footer = parts(lang)
    header = lang_switch(header, lang, "/blog/", "/en/blog/")
    cards = "".join(
        f'<article class="post-card"><div class="post-meta">{meta_line(lang, p)}</div>'
        f'<h2><a href="{url_of(lang, p)}">{esc(p[lang]["title"])}</a></h2><p>{esc(p[lang]["desc"])}</p>'
        f'<a class="more" href="{url_of(lang, p)}" aria-label="{esc(c["more"] + ": " + p[lang]["title"])}">{c["more"]} {ARROW}</a></article>'
        for p in POSTS)
    ld = {"@context": "https://schema.org", "@type": "Blog", "name": c["blog_title"], "url": SITE + c["base"], "inLanguage": lang,
          "publisher": {"@type": "Organization", "name": "GTA6RP.sk", "url": SITE + "/"},
          "blogPost": [{"@type": "BlogPosting", "headline": p[lang]["title"], "url": SITE + url_of(lang, p), "datePublished": p["date"]} for p in POSTS]}
    main = (f'<main id="main"><section class="section article-page">'
            + crumbs(lang, [("GTA6RP.sk", c["home"]), (c["blog"], c["base"])])
            + f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
            f'<div class="page-intro"><div class="eyebrow muted">{c["eyebrow"]}</div><h1>{esc(c["blog_h1"])}</h1><p>{esc(c["blog_lead"])}</p></div>'
            f'<div class="post-grid">{cards}</div></section></main>')
    page = head + meta(lang, c["blog_title"], c["blog_desc"], c["base"], "/blog/", "/en/blog/", "website") + script + "</head><body>" \
        + ('<a class="skip-link" href="#main">' + ("Preskočiť na obsah" if lang == "sk" else "Skip to content") + "</a>") + header + main + footer
    write(("" if lang == "sk" else "en/") + "blog.html", page)


def build_post(lang, i):
    c = L[lang]
    post = POSTS[i]
    p = post[lang]
    head, script, header, footer = parts(lang)
    sk_url, en_url, url = url_of("sk", post), url_of("en", post), url_of(lang, post)
    header = lang_switch(header, lang, sk_url, en_url)
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"], "description": p["desc"],
          "inLanguage": lang, "datePublished": post["date"], "dateModified": post["date"], "image": SITE + "/og-brand.jpg",
          "author": {"@type": "Organization", "name": "GTA6RP.sk", "url": SITE + "/"},
          "publisher": {"@type": "Organization", "name": "GTA6RP.sk", "url": SITE + "/"},
          "mainEntityOfPage": SITE + url}
    others = [q for j, q in enumerate(POSTS) if j != i][:4]
    aside = (f'<aside><span class="eyebrow">{c["next"]}</span>'
             + "".join(f'<a href="{url_of(lang, q)}">{esc(q[lang]["title"])} {ARROW}</a>' for q in others)
             + f'<a href="{c["base"]}">{c["all"]} {ARROW}</a></aside>')
    cta = (f'<div class="article-next"><span class="eyebrow">{c["cta_eye"]}</span><h2>{c["cta_h"]}</h2><p>{c["cta_p"]}</p>'
           f'<a class="button" href="{c["cta_href"]}">{c["cta_btn"]} {ARROW.replace("18", "17")}</a></div>')
    main = (f'<main id="main"><section class="section article-page">'
            + crumbs(lang, [("GTA6RP.sk", c["home"]), (c["blog"], c["base"]), (p["title"], url)])
            + f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
            f'<div class="page-intro"><div class="eyebrow muted">{c["eyebrow"]}</div><h1>{esc(p["title"])}</h1>'
            f'<div class="post-meta">{meta_line(lang, post)}</div><p style="margin-top:18px">{esc(p["lead"])}</p></div>'
            f'<div class="article-layout"><article>{p["body"].strip()}{cta}</article>{aside}</div></section></main>')
    page = head + meta(lang, p["title"], p["desc"], url, sk_url, en_url, "article") \
        + f'<meta property="article:published_time" content="{post["date"]}">' + script + "</head><body>" \
        + ('<a class="skip-link" href="#main">' + ("Preskočiť na obsah" if lang == "sk" else "Skip to content") + "</a>") + header + main + footer
    write(("" if lang == "sk" else "en/") + "blog/" + p["slug"] + ".html", page)


def patch_existing():
    for root, _, files in os.walk(WEB):
        for f in files:
            if not f.endswith(".html"):
                continue
            rel = os.path.relpath(os.path.join(root, f), WEB)
            if rel.startswith(("blog", "en/blog")):
                continue
            lang = "en" if rel.startswith("en/") else "sk"
            s = read(rel)
            n = add_links(s, lang)
            if n != s:
                write(rel, n)


def sitemap():
    s = read("sitemap.xml")
    s = re.sub(r"<url><loc>https://gta6rp\.sk/(?:en/)?blog/.*?</url>\n", "", s)
    rows = []
    pairs = [("/blog/", "/en/blog/", max(p["date"] for p in POSTS))] + [(url_of("sk", p), url_of("en", p), p["date"]) for p in POSTS]
    for sk, en, d in pairs:
        alt = (f'<xhtml:link rel="alternate" hreflang="sk" href="{SITE}{sk}"/><xhtml:link rel="alternate" hreflang="en" href="{SITE}{en}"/>'
               f'<xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{sk}"/>')
        for u in (sk, en):
            rows.append(f"<url><loc>{SITE}{u}</loc><lastmod>{d}</lastmod>{alt}</url>\n")
    s = s.replace("</urlset>", "".join(rows) + "</urlset>")
    write("sitemap.xml", s)


def llms():
    s = read("llms.txt")
    s = re.sub(r"\n## Blog\n.*?(?=\n## |\Z)", "", s, flags=re.S)
    s = re.sub(r"\n## English blog\n.*?(?=\n## |\Z)", "", s, flags=re.S)
    sk = "\n## Blog\n\n- [Blog](https://gta6rp.sk/blog/): Zaujímavosti o GTA VI a roleplayi.\n" + "".join(
        f"- [{p['sk']['title']}]({SITE}{url_of('sk', p)}): {p['sk']['desc']}\n" for p in POSTS)
    en = "\n## English blog\n\n- [Blog](https://gta6rp.sk/en/blog/): GTA VI and roleplay facts.\n" + "".join(
        f"- [{p['en']['title']}]({SITE}{url_of('en', p)}): {p['en']['desc']}\n" for p in POSTS)
    s = s.replace("\n## Optional", sk + "\n## Optional", 1).rstrip("\n") + "\n" + en
    write("llms.txt", s)


patch_existing()
for lang in ("sk", "en"):
    build_index(lang)
    for i in range(len(POSTS)):
        build_post(lang, i)
sitemap()
llms()
print("ok", len(POSTS), "posts")
