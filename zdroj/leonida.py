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
# Vrstvy podkladu ako na GTADB (maps/maps.js): id, názov, URL, rozsah dlaždíc pri zoome 5 (x0, y0, x1, y1).
# Predvolená je yanis,18 rovnako ako na map.gtadb.org. Farba mora je z GTADB maps/maps.css.
LAYERS = [
    ("yanis18", "Yanis V18 (GTADB)", "/assets/mapa/yanis18/{z}/{z},{y},{x}.jpg", (21, 21, 103, 99), "#2c67a4"),
    ("day", "Day (GTADB)", "/assets/mapa/day/{z}/{z},{y},{x}.jpg", (17, 17, 83, 103), "#2f90b0"),
]
GTADB = "https://map.gtadb.org/"
PHOTOS = "https://map.gtadb.org/photos/6/"
LICENSE = "https://creativecommons.org/licenses/by/4.0/deed."

ICONS = {
    "region": '<path d="M14.1 4.6 9.9 2.5a2 2 0 0 0-1.8 0L3.6 4.8A1 1 0 0 0 3 5.7v14.6a.7.7 0 0 0 1 .6l4.1-2.1a2 2 0 0 1 1.8 0l4.2 2.1a2 2 0 0 0 1.8 0l4.5-2.3a1 1 0 0 0 .6-.9V3.7a.7.7 0 0 0-1-.6l-4.1 2.1a2 2 0 0 1-1.8 0M15 5.8v15M9 3.2v15"/>',
}

# Typy miest presne ako na GTADB (map/index.js landmarkTypes) a ich farby (map/index.css .marker.<typ>).
# Miesto môže mať viac typov; miesto bez typu je „nezaradené“ (GTADB filter „IG unclassified“).
TYPES = [
    ("agriculture", "#808000", "Poľnohospodárstvo", "Agriculture"),
    ("construction", "#c08040", "Stavby", "Construction"),
    ("government", "#e00000", "Štátne inštitúcie", "Government"),
    ("hotel", "#60e0a0", "Hotely", "Hotel"),
    ("industrial", "#c0c000", "Priemysel", "Industrial"),
    ("landmark", "#800080", "Pamätihodnosti", "Landmark"),
    ("leisure", "#e000e0", "Voľný čas", "Leisure"),
    ("mixed", "#800000", "Zmiešané", "Mixed"),
    ("natural", "#007000", "Príroda", "Natural"),
    ("office", "#00e0e0", "Kancelárie", "Office"),
    ("other", "#e0e0e0", "Iné", "Other"),
    ("public", "#e07000", "Verejné", "Public"),
    ("residential", "#00c000", "Bývanie", "Residential"),
    ("restaurant", "#a0e060", "Reštaurácie", "Restaurant"),
    ("retail", "#0000c0", "Obchody", "Retail"),
    ("transportation", "#808080", "Doprava", "Transportation"),
    ("utilities", "#202020", "Infraštruktúra", "Utilities"),
    ("unclassified", "#ff4fa3", "Nezaradené", "Unclassified"),
]
TYPE_IDS = [t[0] for t in TYPES[:-1]]
# GTADB filtre (map/index.js filterOptions), preložené.
FILTERS = [
    ("all", "všetky", "all"),
    ("igNameConfirmed", "názov v hre potvrdený", "IG name confirmed"),
    ("igNameUnconfirmed", "názov v hre nepotvrdený", "IG name unconfirmed"),
    ("igNameUnknown", "názov v hre neznámy", "IG name unknown"),
    ("igAddressConfirmed", "adresa v hre potvrdená", "IG address confirmed"),
    ("igAddressUnknown", "adresa v hre neznáma", "IG address unknown"),
    ("igLatLngConfirmed", "poloha v hre potvrdená", "IG latlng confirmed"),
    ("igLatLngUnconfirmed", "poloha v hre nepotvrdená", "IG latlng unconfirmed"),
    ("igLatLngUnknown", "poloha v hre neznáma", "IG latlng unknown"),
    ("igWithPhoto", "so záberom z hry", "with IG photo"),
    ("igWithoutPhoto", "bez záberu z hry", "without IG photo"),
    ("igClassified", "so zaradením", "IG classified"),
    ("igUnclassified", "bez zaradenia", "IG unclassified"),
    ("rlLandmarkConfirmed", "skutočné miesto potvrdené", "RL landmark confirmed"),
    ("rlLandmarkUnconfirmed", "skutočné miesto nepotvrdené", "RL landmark unconfirmed"),
    ("rlLandmarkUnknown", "skutočné miesto neznáme", "RL landmark unknown"),
    ("rlLatLngMissing", "chýba skutočná poloha", "RL latlng missing"),
    ("rlWithPhoto", "so skutočnou fotkou", "with RL photo"),
    ("rlWithoutPhoto", "bez skutočnej fotky", "without RL photo"),
]
REGION_COLOR = "#ff5fa2"

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


def places():
    """GTADB landmarks 1:1 -> [id, ig adresa, x, y, rl adresa, tagy, ig foto v, rl foto v, rl má polohu, farba].

    Nič sa nevynecháva ani nepremenúva: adresy a tagy sú presne ako v landmarks.json, farba bodu je
    farba miesta z GTADB (item[7]). Verzia fotky je None, ak fotka chýba.
    """
    src = json.load(open(SRC, encoding="utf-8"))
    out = []
    for lid, v in src.items():
        ig, xy, igphoto, rl, rlxy, rlphoto, tags, color, edited = v[:9]
        has = bool(xy) and len(xy) >= 2
        out.append([lid, ig, xy[0] if has else None, xy[1] if has else None, rl, tags,
                    (edited[1] if len(edited) > 1 else 0) if igphoto else None,
                    (edited[2] if len(edited) > 2 else 0) if rlphoto else None,
                    1 if rlxy else 0, color])
    return out


def types_of(row):
    t = [x for x in row[5] if x in TYPE_IDS]
    return t or ["unclassified"]


def icon(name):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


UI = {
    "sk": {
        "h1": "Mapa Leonidy", "sub": "Interaktívna mapa GTA VI",
        "intro": "Mapa a všetkých {n} miest z GTADB.org, 1:1 ako na ich stránke: názvy, adresy, polohy, typy aj filtre. Hľadaj, filtruj a označuj, čo už poznáš.",
        "layer": "Podklad", "filter": "Filter GTADB", "types": "Typy miest", "regions": "Oblasti a nápady na RP", "nopos": "Poloha v hre zatiaľ neznáma", "tags": "Tagy", "rlphoto": "Skutočná fotka", "shown": "zobrazených",
        "search": "Hľadať miesto, postavu…", "noresults": "Nič sme nenašli.",
        "all": "Zobraziť všetko", "none": "Skryť všetko",
        "found": "Nájdené", "hidefound": "Skryť nájdené", "reset": "Vynulovať",
        "mark": "Označiť ako nájdené", "unmark": "Nájdené ✓", "copy": "Kopírovať odkaz", "copied": "Skopírované",
        "region": "Oblasť", "filters": "Filtre", "close": "Zavrieť panel",
        "zoomin": "Priblížiť", "zoomout": "Oddialiť", "fit": "Celá mapa",
        "note": "Mapa a miesta: GTADB.org a prispievatelia, licencia CC BY 4.0. Názvy, adresy, polohy, tagy a farby bodov sú bez zmeny (preložené sú len názvy typov a filtrov). Na mape je {p} z {n} miest, ostatné ešte nemajú polohu a nájdeš ich vo vyhľadávaní. Oblasti a nápady na RP sú naše.",
        "nameless": "Názov v hre zatiaľ neznámy", "real": "V skutočnosti", "enterable": "Dá sa vstúpiť", "onlyenter": "Len budovy, do ktorých sa dá vstúpiť",
        "photo": "Záber z hry", "ideas": "Nápady na RP postavu", "places": "miest", "loading": "Načítavam miesta…",
        "official": "Otvoriť GTADB.org",
        "builder": "/rp/tvorba-postavy/", "cta": "Vytvoriť postavu",
        "aria": "Interaktívna mapa Leonidy", "edit": "Súradnice", "credit": "GTADB.org a prispievatelia", "onmap": "na mape", "more": "ďalších (spresni hľadanie)",
    },
    "en": {
        "h1": "Leonida map", "sub": "Interactive GTA VI map",
        "intro": "The map and all {n} places from GTADB.org, 1:1 as on their site: names, addresses, positions, types and filters. Search, filter and mark what you already know.",
        "layer": "Base map", "filter": "GTADB filter", "types": "Place types", "regions": "Areas and RP ideas", "nopos": "In-game position not known yet", "tags": "Tags", "rlphoto": "Real-life photo", "shown": "shown",
        "search": "Search a place or character…", "noresults": "Nothing found.",
        "all": "Show all", "none": "Hide all",
        "found": "Found", "hidefound": "Hide found", "reset": "Reset",
        "mark": "Mark as found", "unmark": "Found ✓", "copy": "Copy link", "copied": "Copied",
        "region": "Area", "filters": "Filters", "close": "Close panel",
        "zoomin": "Zoom in", "zoomout": "Zoom out", "fit": "Full map",
        "note": "Map and places: GTADB.org and contributors, licensed CC BY 4.0, data unchanged. {p} of {n} places are on the map, the rest have no position yet and are in search. Areas and RP ideas are our own.",
        "nameless": "In-game name not known yet", "real": "Real-life counterpart", "enterable": "Enterable", "onlyenter": "Only buildings you can enter",
        "photo": "In-game shot", "ideas": "RP character ideas", "places": "places", "loading": "Loading places…",
        "official": "Open GTADB.org",
        "builder": "/en/rp/character-builder/", "cta": "Create a character",
        "aria": "Interactive map of Leonida", "edit": "Coordinates", "credit": "GTADB.org and contributors", "onmap": "on the map", "more": "more (refine your search)",
    },
}
SEARCH_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>'


def section(lang, v):
    t = UI[lang]
    pl = places()
    counts = {}
    for r in pl:
        for ty in types_of(r):
            counts[ty] = counts.get(ty, 0) + 1
    positioned = sum(1 for r in pl if r[2] is not None)
    data = {"lang": lang, "ui": t, "places": f"/{OUT}?v={v['places']}", "photos": PHOTOS, "gtadb": GTADB,
            "layers": [{"id": lid, "name": name, "url": url, "maxNative": 5, "bounds": tile_bounds(rng), "bg": bg} for lid, name, url, rng, bg in LAYERS],
            "types": [{"id": ty[0], "color": ty[1], "name": ty[2] if lang == "sk" else ty[3]} for ty in TYPES],
            "typeIds": TYPE_IDS, "regionColor": REGION_COLOR,
            "regions": [{"id": r[0], "x": r[1][0], "y": r[1][1], "t": r[2], "d": r[3] if lang == "sk" else r[4],
                         "rp": [i[0] if lang == "sk" else i[1] for i in r[5]]} for r in REGIONS]}
    chips = "".join(
        f'<button type="button" class="mg-cat" data-cat="{ty[0]}" aria-pressed="true" style="--c:{ty[1]}">'
        f'<span class="mg-dot"></span><span class="mg-cat-name">{html.escape(ty[2] if lang == "sk" else ty[3])}</span>'
        f'<span class="mg-cat-n">{counts.get(ty[0], 0)}</span></button>'
        for ty in TYPES if counts.get(ty[0]))
    reg = (f'<button type="button" class="mg-cat" data-cat="oblasti" aria-pressed="false" style="--c:{REGION_COLOR}">'
           f'<span class="mg-dot"></span><span class="mg-cat-name">{t["regions"]}</span><span class="mg-cat-n">{len(REGIONS)}</span></button>')
    opts = "".join(f'<option value="{f[0]}">{html.escape(f[1] if lang == "sk" else f[2])}</option>' for f in FILTERS)
    layers = "".join(f'<option value="{lid}">{html.escape(name)}</option>' for lid, name, *_ in LAYERS)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    lic = LICENSE + ("sk" if lang == "sk" else "en")
    nbsp = lambda n: f"{n:,}".replace(",", "\u00a0")
    return (
        '<section class="mg" data-mg aria-labelledby="mg-title">'
        f'<aside class="mg-panel" id="mg-panel" aria-label="{t["filters"]}">'
        f'<div class="mg-panel-head"><span class="eyebrow">{t["sub"]}</span><h1 id="mg-title">{t["h1"]}</h1>'
        f'<button type="button" class="mg-close" aria-label="{t["close"]}">×</button></div>'
        f'<p class="mg-intro">{t["intro"].format(n=nbsp(len(pl)))}</p>'
        f'<div class="mg-search"><label class="mg-search-box">{SEARCH_ICON}<input type="search" placeholder="{t["search"]}" aria-label="{t["search"]}" autocomplete="off"></label>'
        '<ul class="mg-results" role="listbox" hidden></ul></div>'
        f'<div class="mg-selects"><label><span>{t["layer"]}</span><select data-layer>{layers}</select></label>'
        f'<label><span>{t["filter"]}</span><select data-filter>{opts}</select></label></div>'
        f'<div class="mg-bulk"><button type="button" data-all>{t["all"]}</button><button type="button" data-none>{t["none"]}</button></div>'
        f'<div class="mg-group"><h2>{t["types"]} <small data-shown></small></h2><div class="mg-cats mg-cats-2">{chips}</div></div>'
        f'<div class="mg-group"><h2>GTA6RP.sk</h2><div class="mg-cats">{reg}</div></div>'
        f'<div class="mg-progress"><div class="mg-progress-top"><span>{t["found"]}</span><b><span data-found>0</span> / {nbsp(len(pl))}</b></div>'
        '<div class="mg-bar"><i data-bar></i></div>'
        f'<div class="mg-progress-actions"><label><input type="checkbox" data-hidefound> {t["hidefound"]}</label>'
        f'<button type="button" data-reset>{t["reset"]}</button></div></div>'
        f'<p class="mg-note">{t["note"].format(p=nbsp(positioned), n=nbsp(len(pl)))} <a href="{GTADB}" target="_blank" rel="noopener">{t["official"]} ↗</a> · '
        f'<a href="{lic}" target="_blank" rel="noopener license">CC BY 4.0</a></p>'
        '</aside>'
        f'<div class="mg-map" role="region" aria-label="{t["aria"]}"><div class="mg-leaflet"></div>'
        f'<div class="mg-loading" data-loading>{t["loading"]}</div>'
        f'<button type="button" class="mg-open" aria-controls="mg-panel" aria-expanded="false">{icon("region")}<span>{t["filters"]}</span></button>'
        '<div class="mg-hud" aria-hidden="true"><b>LEONIDA · GPS</b><span data-coords></span></div>'
        '</div>'
        f'<script type="application/json" id="mg-data">{payload}</script>'
        '</section>')


def tile_bounds(rng):
    x0, y0, x1, y1 = rng
    return [[16384 - (y1 + 1) * 256, x0 * 256 - 16384], [16384 - y0 * 256, (x1 + 1) * 256 - 16384]]


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
    # Na stránke mapy bez tlačidla „Tvorba postavy“ v hlavičke (želanie Matthewa, 19. 11. 2026).
    body = re.sub(r'<a class="button small" href="[^"]*">.*?</svg></a>', "", body, count=1, flags=re.S)
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
