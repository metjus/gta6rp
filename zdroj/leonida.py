"""Stránka Mapa Leonidy (SK /mapa/, EN /en/map/): interaktívna mapa GTA VI s filtrami.

    python3 -I zdroj/leonida.py .

Podklad mapy a miesta sú z projektu GTADB.org (https://map.gtadb.org), licencia CC BY 4.0,
autori: GTADB.org a prispievatelia. Zdroj je v zdroj/gtadb/ (landmarks-6.json, LICENSE-DATA,
SOURCE = commit). Dlaždice mapy (sada „day“, zoom 0 až 5) sú v assets/mapa/day/{z}/{z},{y},{x}.jpg.
Aktualizácia: skopíruj nový map/data/6/landmarks.json z github.com/rolux/gtadb.org do
zdroj/gtadb/landmarks-6.json, zapíš commit do SOURCE a spusti tento skript.

Čo urobí:
- z údajov GTADB vygeneruje assets/mapa/miesta.json (názov, adresa, kategória, súradnice, fotka),
- vygeneruje mapa.html a en/map.html zo šablóny rp.html / en/rp.html,
- pridá položku „Mapa“ do menu a päty na všetkých stránkach.
Súradnice sú herné (x, y) ako na GTADB. Spúšťa sa po zdroj/launch.py a pred zdroj/build.py.
"""
import glob
import hashlib
import html
import json
import os
import re
import sys

WEB = sys.argv[1] if len(sys.argv) > 1 else "."
SRC = os.path.join(WEB, "zdroj/gtadb/landmarks-6.json")
OUT = "assets/mapa/miesta.json"
TILES = "/assets/mapa/day/{z}/{z},{y},{x}.jpg"
# Rozsah dlaždíc sady „day“ pri zoome 5 (x0, y0, x1, y1), podľa maps/maps.js na GTADB.
TILE_RANGE_Z5 = (17, 17, 83, 103)
GTADB = "https://map.gtadb.org/"
PHOTOS = "https://map.gtadb.org/photos/6/"
LICENSE = "https://creativecommons.org/licenses/by/4.0/deed."

ICONS = {
    "region": '<path d="M14.1 4.6 9.9 2.5a2 2 0 0 0-1.8 0L3.6 4.8A1 1 0 0 0 3 5.7v14.6a.7.7 0 0 0 1 .6l4.1-2.1a2 2 0 0 1 1.8 0l4.2 2.1a2 2 0 0 0 1.8 0l4.5-2.3a1 1 0 0 0 .6-.9V3.7a.7.7 0 0 0-1-.6l-4.1 2.1a2 2 0 0 1-1.8 0M15 5.8v15M9 3.2v15"/>',
    "star": '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8-6.2-3.2-6.2 3.2 1.2-6.8-5-4.9 6.9-1z"/>',
    "bed": '<path d="M2 4v16M2 8h18a2 2 0 0 1 2 2v10M2 17h20M6 8v9"/>',
    "food": '<path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2M7 2v20M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/>',
    "bag": '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4ZM3 6h18M16 10a4 4 0 0 1-8 0"/>',
    "bus": '<path d="M8 6v6M15 6v6M2 12h19.6M18 18h3s.5-1.7.8-2.8c.1-.4.2-.8.2-1.2 0-.4-.1-.8-.2-1.2l-1.4-5C20.1 6.8 19.1 6 18 6H4a2 2 0 0 0-2 2v10h3"/><circle cx="7" cy="18" r="2"/><path d="M9 18h5"/><circle cx="16" cy="18" r="2"/>',
    "fun": '<path d="M5.8 11.3 2 22l10.7-3.8M4 3h.01M22 8h.01M15 2h.01M22 20h.01M22 2l-2.2.7a2.9 2.9 0 0 0-1.9 3.4c.2.9-.5 1.9-1.5 1.9h-.4M8.6 2.7a2.9 2.9 0 0 1-1 3.3 2.9 2.9 0 0 0-1.3 3.7"/><path d="m11 13 2-2"/>',
    "gov": '<path d="M3 22h18M6 18v-7M10 18v-7M14 18v-7M18 18v-7M12 2l8 5H4z"/>',
    "office": '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01"/>',
    "factory": '<path d="M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/>',
    "home": '<path d="M3 10a2 2 0 0 1 .7-1.5l7-6a2 2 0 0 1 2.6 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/>',
    "tree": '<path d="m17 14 3 3.3a1 1 0 0 1-.7 1.7H4.7a1 1 0 0 1-.7-1.7L7 14h-.3a1 1 0 0 1-.7-1.7L9 9h-.2A1 1 0 0 1 8 7.3L12 3l4 4.3a1 1 0 0 1-.8 1.7H15l3 3.3a1 1 0 0 1-.7 1.7zM12 22v-3"/>',
    "dot": '<circle cx="12" cy="12" r="4"/>',
}

# Kategórie: id, ikona, farba, SK, EN, tagy z GTADB (prvá zhoda vyhráva).
CATS = [
    ("oblasti", "region", "#ff5fa2", "Oblasti", "Areas", None),
    ("pamiatky", "star", "#ffd166", "Pamätihodnosti", "Landmarks", ["landmark"]),
    ("hotely", "bed", "#c792ff", "Hotely", "Hotels", ["hotel"]),
    ("jedlo", "food", "#ff8a5c", "Reštaurácie a bary", "Restaurants and bars", ["restaurant"]),
    ("obchody", "bag", "#ff6ad5", "Obchody", "Shops", ["retail", "#supermarket", "#clothes", "#hair"]),
    ("doprava", "bus", "#4cc9f0", "Doprava", "Transport", ["transportation", "#bus", "#train", "#airport", "#marina", "#metromover", "#gas"]),
    ("zabava", "fun", "#f9f871", "Voľný čas a zábava", "Leisure and events", ["leisure", "events"]),
    ("verejne", "gov", "#90e0ef", "Verejné budovy", "Public buildings", ["government", "public"]),
    ("kancelarie", "office", "#b8c0ff", "Kancelárie", "Offices", ["office"]),
    ("priemysel", "factory", "#adb5bd", "Priemysel", "Industry", ["industrial", "utilities", "construction"]),
    ("byvanie", "home", "#80ed99", "Bývanie", "Housing", ["residential"]),
    ("priroda", "tree", "#52b788", "Príroda", "Nature", ["natural"]),
    ("ostatne", "dot", "#e9ecef", "Ostatné", "Other", []),
]
GROUPS = [("game", ["oblasti"], "Leonida", "Leonida"),
          ("places", [c[0] for c in CATS[1:]], "Miesta (GTADB.org)", "Places (GTADB.org)")]

# Oblasti, ktoré pomenoval Rockstar. Poloha (herné x, y) je stred oblasti na mape GTADB.
REGIONS = [
    ("vice-city", (-900, 300), "Vice City",
     "Moderná metropola plná pláží, nočných klubov, áut a sociálnych sietí. Mesto, ktoré preslávilo GTA: Vice City z roku 2002, sa vracia po viac ako dvadsiatich rokoch.",
     "A modern metropolis of beaches, nightclubs, cars and social media. The city made famous by 2002's GTA: Vice City returns after more than twenty years.",
     [("Influencerka", "Influencer"), ("Kaucionár", "Bail bondsman"), ("Promotér klubu", "Club promoter")]),
    ("leonida-keys", (-3700, -6500), "Leonida Keys",
     "Reťaz ostrovov na juhu štátu. Mosty nad tyrkysovou vodou, rybárske lode a pomalý život, za ktorým sa niekedy skrýva pašovanie. Tu žije Jason Duval.",
     "A chain of islands in the south of the state. Bridges over turquoise water, fishing boats and a slow pace of life that sometimes hides smuggling. Home of Jason Duval.",
     [("Kapitánka lode", "Boat captain"), ("Barman z prístavu", "Harbour bartender"), ("Potápač", "Diver")]),
    ("grassrivers", (-3300, -4300), "Grassrivers",
     "Rozsiahle močiare a mokrade, obdoba Everglades. Člny s obrovskou vrtuľou, aligátory a ľudia, ktorí žijú ďaleko od mesta a jeho pravidiel.",
     "Vast swamps and wetlands, Leonida's version of the Everglades. Airboats, alligators and people living far from the city and its rules.",
     [("Sprievodca na airboate", "Airboat guide"), ("Samotár z močiara", "Swamp loner"), ("Rybár", "Fisherman")]),
    ("ambrosia", (-2769, 3882), "Ambrosia",
     "Priemyselné mesto, ktorého život sa točí okolo rafinérie cukru. Podľa Rockstaru tu majú domov aj motorkárske kluby.",
     "An industrial town whose life revolves around a sugar refinery. According to Rockstar, it's also home to biker clubs.",
     [("Robotník z rafinérie", "Refinery worker"), ("Motorkár", "Biker"), ("Mechanik", "Mechanic")]),
    ("port-gellhorn", (-6492, 3775), "Port Gellhorn",
     "Kedysi rušné prístavné letovisko, dnes skôr zabudnuté mesto s lacnými motelmi a ľuďmi, ktorí hľadajú, ako sa uživiť.",
     "Once a busy port resort, now more of a forgotten town with cheap motels and people trying to get by.",
     [("Majiteľ motela", "Motel owner"), ("Prístavný robotník", "Dock worker"), ("Drobný podvodník", "Small-time hustler")]),
    ("mount-kalaga", (-3900, 6150), "Mount Kalaga",
     "Národný park s horami, lesmi a jazerami. Miesto na lov, rybolov a jazdu v teréne.",
     "A national park with mountains, forests and lakes. A place for hunting, fishing and off-roading.",
     [("Strážkyňa parku", "Park ranger"), ("Lovec", "Hunter"), ("Off-road sprievodca", "Off-road guide")]),
]


def category(tags):
    for cid, _, _, _, _, match in CATS[1:-1]:
        if any(t in tags for t in match):
            return cid
    return "ostatne"


def places():
    """GTADB landmarks -> kompaktný zoznam: [id, názov, adresa, kategória, x, y, skutočné miesto, fotka v, vstup]."""
    src = json.load(open(SRC, encoding="utf-8"))
    out = []
    for lid, v in src.items():
        ig, xy, igphoto, rl, _, _, tags, _, edited = v[:9]
        if not xy or len(xy) < 2:
            continue
        parts = [p.strip() for p in ig.split(",")]
        name = parts[0] if parts and parts[0] not in ("", "?") else ""
        addr = ", ".join(p for p in parts[1:] if p)
        rl = re.sub(r"(?<=.)\?$", "", rl or "").strip()
        rl_name = rl.split(",")[0].strip() if rl and rl != "?" else ""
        photo = edited[1] if igphoto and len(edited) > 1 and edited[1] else 0
        out.append([lid, name, addr, category(tags), round(xy[0], 1), round(xy[1], 1), rl_name, photo,
                    1 if "enterable" in tags else 0])
    out.sort(key=lambda r: int(r[0][1:]) if r[0][1:].isdigit() else 0)
    return out


def icon(name):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


UI = {
    "sk": {
        "h1": "Mapa Leonidy", "sub": "Interaktívna mapa GTA VI",
        "intro": "Celá Leonida s viac ako 3 600 miestami: hotely, obchody, reštaurácie, doprava a ďalšie. Filtruj, hľadaj a označuj, čo už poznáš.",
        "search": "Hľadať miesto, postavu…", "noresults": "Nič sme nenašli.",
        "all": "Zobraziť všetko", "none": "Skryť všetko",
        "found": "Nájdené", "hidefound": "Skryť nájdené", "reset": "Vynulovať",
        "mark": "Označiť ako nájdené", "unmark": "Nájdené ✓", "copy": "Kopírovať odkaz", "copied": "Skopírované",
        "region": "Oblasť", "filters": "Filtre", "close": "Zavrieť panel",
        "zoomin": "Priblížiť", "zoomout": "Oddialiť", "fit": "Celá mapa",
        "note": "Mapa a miesta: GTADB.org a prispievatelia, licencia CC BY 4.0, upravené (preklad kategórií, výber vrstvy). Popisy oblastí a nápady na RP postavy sú naše.",
        "nameless": "Názov v hre zatiaľ neznámy", "real": "V skutočnosti", "enterable": "Dá sa vstúpiť", "onlyenter": "Len budovy, do ktorých sa dá vstúpiť",
        "photo": "Záber z hry", "ideas": "Nápady na RP postavu", "places": "miest", "loading": "Načítavam miesta…",
        "official": "Otvoriť GTADB.org",
        "builder": "/rp/tvorba-postavy/", "cta": "Vytvoriť postavu",
        "aria": "Interaktívna mapa Leonidy", "edit": "Súradnice",
    },
    "en": {
        "h1": "Leonida map", "sub": "Interactive GTA VI map",
        "intro": "All of Leonida with more than 3,600 places: hotels, shops, restaurants, transport and more. Filter, search and mark what you already know.",
        "search": "Search a place or character…", "noresults": "Nothing found.",
        "all": "Show all", "none": "Hide all",
        "found": "Found", "hidefound": "Hide found", "reset": "Reset",
        "mark": "Mark as found", "unmark": "Found ✓", "copy": "Copy link", "copied": "Copied",
        "region": "Area", "filters": "Filters", "close": "Close panel",
        "zoomin": "Zoom in", "zoomout": "Zoom out", "fit": "Full map",
        "note": "Map and places: GTADB.org and contributors, licensed CC BY 4.0, adapted (category translation, layer choice). Area descriptions and RP character ideas are our own.",
        "nameless": "In-game name not known yet", "real": "Real-life counterpart", "enterable": "Enterable", "onlyenter": "Only buildings you can enter",
        "photo": "In-game shot", "ideas": "RP character ideas", "places": "places", "loading": "Loading places…",
        "official": "Open GTADB.org",
        "builder": "/en/rp/character-builder/", "cta": "Create a character",
        "aria": "Interactive map of Leonida", "edit": "Coordinates",
    },
}
SEARCH_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>'


def section(lang, v):
    t = UI[lang]
    pl = places()
    counts = {}
    for p in pl:
        counts[p[3]] = counts.get(p[3], 0) + 1
    counts["oblasti"] = len(REGIONS)
    total = len(pl) + len(REGIONS)
    x0, y0, x1, y1 = TILE_RANGE_Z5
    data = {"lang": lang, "ui": t, "tiles": TILES, "places": f"/{OUT}?v={v['places']}", "photos": PHOTOS,
            "gtadb": GTADB, "total": total,
            "bounds": [[16384 - (y1 + 1) * 256, x0 * 256 - 16384], [16384 - y0 * 256, (x1 + 1) * 256 - 16384]],
            "cats": [{"id": c[0], "color": c[2], "icon": ICONS[c[1]], "name": c[3] if lang == "sk" else c[4]} for c in CATS],
            "regions": [{"id": r[0], "x": r[1][0], "y": r[1][1], "t": r[2], "d": r[3] if lang == "sk" else r[4],
                         "rp": [i[0] if lang == "sk" else i[1] for i in r[5]]} for r in REGIONS]}
    groups = ""
    cat = {c[0]: c for c in CATS}
    for gid, ids, gsk, gen in GROUPS:
        chips = "".join(
            f'<button type="button" class="mg-cat" data-cat="{cid}" aria-pressed="true" style="--c:{cat[cid][2]}">'
            f'<span class="mg-ico">{icon(cat[cid][1])}</span><span class="mg-cat-name">{html.escape(cat[cid][3] if lang == "sk" else cat[cid][4])}</span>'
            f'<span class="mg-cat-n">{counts.get(cid, 0):,}</span></button>'.replace(",", "\u00a0")
            for cid in ids if counts.get(cid))
        groups += f'<div class="mg-group"><h2>{gsk if lang == "sk" else gen}</h2><div class="mg-cats">{chips}</div></div>'
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    lic = LICENSE + ("sk" if lang == "sk" else "en")
    return (
        '<section class="mg" data-mg aria-labelledby="mg-title">'
        f'<aside class="mg-panel" id="mg-panel" aria-label="{t["filters"]}">'
        f'<div class="mg-panel-head"><span class="eyebrow">{t["sub"]}</span><h1 id="mg-title">{t["h1"]}</h1>'
        f'<button type="button" class="mg-close" aria-label="{t["close"]}">×</button></div>'
        f'<p class="mg-intro">{t["intro"]}</p>'
        f'<div class="mg-search"><label class="mg-search-box">{SEARCH_ICON}<input type="search" placeholder="{t["search"]}" aria-label="{t["search"]}" autocomplete="off"></label>'
        '<ul class="mg-results" role="listbox" hidden></ul></div>'
        f'<div class="mg-bulk"><button type="button" data-all>{t["all"]}</button><button type="button" data-none>{t["none"]}</button></div>'
        f'<label class="mg-switch"><input type="checkbox" data-enter> <span>{t["onlyenter"]}</span></label>'
        + groups +
        f'<div class="mg-progress"><div class="mg-progress-top"><span>{t["found"]}</span><b><span data-found>0</span> / {total:,}</b></div>'.replace(",", "\u00a0") +
        '<div class="mg-bar"><i data-bar></i></div>'
        f'<div class="mg-progress-actions"><label><input type="checkbox" data-hidefound> {t["hidefound"]}</label>'
        f'<button type="button" data-reset>{t["reset"]}</button></div></div>'
        f'<p class="mg-note">{t["note"]} <a href="{GTADB}" target="_blank" rel="noopener">{t["official"]} ↗</a> · '
        f'<a href="{lic}" target="_blank" rel="noopener license">CC BY 4.0</a></p>'
        f'<a class="button mg-cta" href="{t["builder"]}">{t["cta"]} ↗</a>'
        '</aside>'
        f'<div class="mg-map" role="region" aria-label="{t["aria"]}"><div class="mg-leaflet"></div>'
        f'<div class="mg-loading" data-loading>{t["loading"]}</div>'
        f'<button type="button" class="mg-open" aria-controls="mg-panel" aria-expanded="false">{icon("region")}<span>{t["filters"]}</span></button>'
        '<div class="mg-hud" aria-hidden="true"><b>LEONIDA · GPS</b><span data-coords></span></div>'
        '</div>'
        f'<script type="application/json" id="mg-data">{payload}</script>'
        '</section>')


PAGE = {
    "sk": dict(tpl="rp.html", out="mapa.html", url="/mapa/", other="/en/map/", tpl_url="/rp/", tpl_other="/en/rp/",
               title="Mapa Leonidy: oblasti GTA 6 a nápady na RP postavu",
               desc="Interaktívna mapa Leonidy z GTA 6: Vice City, Leonida Keys, Grassrivers, Ambrosia, Port Gellhorn a Mount Kalaga. Nastav si trasu a nájdi nápad na RP postavu.",
               crumbs="Drobčeková navigácia", home="/", crumb="Mapa Leonidy",
               nav_after='<a href="/#o-hre">O GTA 6</a>', nav_link='<a href="/mapa/">Mapa</a>',
               foot_after='<a href="/rp/">Svet RP</a>', foot_link='<a href="/mapa/">Mapa Leonidy</a>'),
    "en": dict(tpl="en/rp.html", out="en/map.html", url="/en/map/", other="/mapa/", tpl_url="/en/rp/", tpl_other="/rp/",
               title="Leonida map: GTA 6 areas and RP character ideas",
               desc="Interactive map of Leonida from GTA 6: Vice City, Leonida Keys, Grassrivers, Ambrosia, Port Gellhorn and Mount Kalaga. Set a route and find an RP character idea.",
               crumbs="Breadcrumb", home="/en/", crumb="Leonida map",
               nav_after='<a href="/en/#o-hre">About GTA 6</a>', nav_link='<a href="/en/map/">Map</a>',
               foot_after='<a href="/en/rp/">Explore RP</a>', foot_link='<a href="/en/map/">Leonida map</a>'),
}
SITE = "https://gta6rp.sk"


def page(lang, css, v):
    c = PAGE[lang]
    s = open(os.path.join(WEB, c["tpl"]), encoding="utf-8").read()
    head, body = s.split("</head>", 1)
    old_title = re.search(r"<title>(.*?)</title>", head).group(1)
    old_desc = re.search(r'<meta name="description" content="(.*?)">', head).group(1)
    head = head.replace(old_title, html.escape(c["title"], quote=False)).replace(old_desc, html.escape(c["desc"]))
    sk_url, en_url = (c["url"], c["other"]) if lang == "sk" else (c["other"], c["url"])
    sk_tpl, en_tpl = (c["tpl_url"], c["tpl_other"]) if lang == "sk" else (c["tpl_other"], c["tpl_url"])
    head = head.replace(SITE + en_tpl + '"', SITE + en_url + '"').replace(SITE + sk_tpl + '"', SITE + sk_url + '"')
    head += (f'<link rel="stylesheet" href="/assets/leaflet.css?v={v["leaflet.css"]}"><style id="mg-css">{css}</style>'
             f'<script defer src="/assets/leaflet.js?v={v["leaflet.js"]}"></script><script defer src="/assets/mapa.js?v={v["mapa.js"]}"></script>')
    sw = re.search(r'<div class="language-switch".*?</div>', body).group(0)
    body = body.replace(sw, sw.replace(f'href="{en_tpl}"', f'href="{en_url}"').replace(f'href="{sk_tpl}"', f'href="{sk_url}"'))
    body = body.replace(c["nav_link"], c["nav_link"].replace("<a ", '<a aria-current="page" '), 1)
    crumbs = (f'<div class="mg-crumbs"><nav class="breadcrumbs" aria-label="{c["crumbs"]}"><a href="{c["home"]}">GTA6RP.sk</a>'
              f'<span>/</span><span aria-current="page">{c["crumb"]}</span></nav></div>')
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "GTA6RP.sk", "item": SITE + c["home"]},
        {"@type": "ListItem", "position": 2, "name": c["crumb"], "item": SITE + c["url"]}]}
    main = (f'<main id="main">{crumbs}<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
            + section(lang, v) + "</main>")
    body = re.sub(r'<main id="main">.*</main>', lambda _: main, body, count=1, flags=re.S)
    open(os.path.join(WEB, c["out"]), "w", encoding="utf-8").write(head + "</head>" + body)
    print("ok", c["out"])


def menu():
    for path in glob.glob(os.path.join(WEB, "**/*.html"), recursive=True):
        if os.sep + "zdroj" + os.sep in path:
            continue
        s = open(path, encoding="utf-8").read()
        lang = "en" if 'lang="en"' in s[:200] else "sk"
        c, t = PAGE[lang], s
        if c["nav_link"] not in t and 'aria-current="page" href="' + c["url"] not in t and c["nav_after"] in t:
            t = t.replace(c["nav_after"], c["nav_after"] + c["nav_link"], 1)
        if c["foot_link"] not in t and c["foot_after"] + "<a" in t:
            t = t.replace(c["foot_after"] + "<a", c["foot_after"] + c["foot_link"] + "<a", 1)
        if t != s:
            open(path, "w", encoding="utf-8").write(t)




def minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return re.sub(r"\s*([{};:,>])\s*", r"\1", re.sub(r"\s+", " ", css)).replace(";}", "}").strip()


def ver(rel):
    return hashlib.sha1(open(os.path.join(WEB, rel), "rb").read()).hexdigest()[:10]


def main():
    pl = places()
    open(os.path.join(WEB, OUT), "w", encoding="utf-8").write(json.dumps(pl, ensure_ascii=False, separators=(",", ":")))
    css = minify_css(open(os.path.join(WEB, "zdroj/leonida.css"), encoding="utf-8").read())
    v = {"leaflet.css": ver("assets/leaflet.css"), "leaflet.js": ver("assets/leaflet.js"),
         "mapa.js": ver("assets/mapa.js"), "places": ver(OUT)}
    menu()
    for lang in ("sk", "en"):
        page(lang, css, v)
    print(len(pl), "miest")


if __name__ == "__main__":
    main()
