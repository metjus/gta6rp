"""Stránka Mapa Leonidy (SK /mapa/, EN /en/map/): interaktívna mapa s kategóriami a filtrami.

    python3 -I zdroj/leonida.py .

Čo urobí:
- vygeneruje podklad mapy assets/leonida-base.svg (štylizovaná Leonida podľa Floridy),
- vygeneruje mapa.html a en/map.html zo šablóny rp.html / en/rp.html (hlavička, päta, štýly),
- dá do stránky údaje o značkách (CATS, MARKERS nižšie) ako JSON,
- pridá položku „Mapa“ do menu a päty na všetkých stránkach,
- nastaví ?v= pre assets/mapa.js, assets/leaflet.js a assets/leaflet.css.
Spúšťa sa po zdroj/launch.py a pred zdroj/build.py (blog si menu berie zo šablóny).

Mapový engine je Leaflet 1.9.4 (BSD-2, assets/leaflet.js). Súradnice značiek sú v pixeloch
podkladu (BASE_W x BASE_H, 0,0 vľavo hore). Pozícia sa dá zistiť na /mapa/?edit: klik do mapy
ukáže súradnice. Údaje sú len z oficiálnych informácií Rockstar Games, polohy sú približné.
Nové značky: pridaj riadok do MARKERS (id, kategória, x, y, texty SK aj EN).
"""
import glob
import hashlib
import html
import json
import math
import os
import re
import sys

WEB = sys.argv[1] if len(sys.argv) > 1 else "."
W, H = 820, 780
BASE = "assets/leonida-base.svg"
BASE_W, BASE_H = W, H


def pt(lon, lat):
    return (lon + 88) * 90 + 40, (31.3 - lat) * 104 + 30


COAST = [
    (-87.52, 30.28), (-87.6, 30.99), (-86.2, 31.0), (-85.0, 31.0), (-84.86, 30.71), (-83.5, 30.64),
    (-82.2, 30.57), (-82.0, 30.62), (-81.45, 30.72), (-81.4, 30.4), (-81.25, 29.8), (-81.0, 29.25),
    (-80.75, 28.75), (-80.55, 28.45), (-80.6, 28.1), (-80.38, 27.6), (-80.15, 27.1), (-80.03, 26.6),
    (-80.08, 26.0), (-80.12, 25.75), (-80.3, 25.45), (-80.4, 25.25), (-80.6, 25.18), (-81.05, 25.13),
    (-81.15, 25.35), (-81.35, 25.8), (-81.72, 25.95), (-81.85, 26.35), (-82.05, 26.55), (-82.25, 26.85),
    (-82.45, 27.2), (-82.68, 27.45), (-82.6, 27.85), (-82.82, 27.95), (-82.75, 28.3), (-82.65, 28.75),
    (-82.75, 29.05), (-83.05, 29.15), (-83.4, 29.5), (-83.7, 29.95), (-84.1, 30.08), (-84.35, 30.0),
    (-84.65, 29.85), (-85.05, 29.65), (-85.35, 29.68), (-85.4, 29.95), (-85.7, 30.15), (-86.1, 30.38),
    (-86.6, 30.4), (-87.2, 30.32),
]
KEYS = [(-80.38, 25.16), (-80.5, 25.0), (-80.66, 24.88), (-80.86, 24.78), (-81.06, 24.72),
        (-81.3, 24.67), (-81.52, 24.63), (-81.78, 24.56)]
ROADS = [
    [(-80.15, 25.78), (-80.1, 26.6), (-80.35, 27.6), (-80.75, 28.6), (-81.3, 29.9), (-81.6, 30.5)],
    [(-80.25, 25.9), (-80.9, 26.1), (-81.75, 26.15)],
    [(-80.45, 25.45), (-80.5, 25.05), (-81.0, 24.76), (-81.75, 24.58)],
    [(-81.3, 29.9), (-82.4, 30.3), (-84.3, 30.45), (-85.7, 30.45), (-87.2, 30.5)],
    [(-80.2, 26.3), (-81.0, 27.4), (-81.4, 28.5), (-82.4, 29.6), (-82.4, 30.3)],
]


def smooth(points, closed):
    p = [pt(*q) for q in points]
    n = len(p)
    d = f"M{p[0][0]:.1f} {p[0][1]:.1f}"
    last = n if closed else n - 1
    for i in range(last):
        p0 = p[(i - 1) % n] if closed or i > 0 else p[i]
        p1, p2 = p[i], p[(i + 1) % n]
        p3 = p[(i + 2) % n] if closed or i + 2 < n else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d + ("Z" if closed else "")




def base_svg():
    land = smooth(COAST, True)
    ok = pt(-80.83, 26.95)
    keys = "".join(
        f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{9 - i * .5:.1f}" ry="3.2" transform="rotate({-28 + i * 2} {x:.1f} {y:.1f})"/>'
        for i, (x, y) in enumerate(pt(*k) for k in KEYS))
    roads = "".join(f'<path d="{smooth(r, False)}"/>' for r in ROADS)
    grid = "".join(f'<path d="M{x} 0V{H}"/>' for x in range(0, W + 1, 41)) + "".join(f'<path d="M0 {y}H{W}"/>' for y in range(0, H + 1, 39))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 2}" height="{H * 2}">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ff965d"/><stop offset=".55" stop-color="#fa399c"/><stop offset="1" stop-color="#b22bdd"/></linearGradient>'
        '<radialGradient id="land" cx=".75" cy=".75" r=".9"><stop stop-color="#2f1d45"/><stop offset="1" stop-color="#1c1530"/></radialGradient>'
        '<filter id="blur" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="6"/></filter></defs>'
        f'<rect width="{W}" height="{H}" fill="#0d0a17"/>'
        f'<g stroke="#ffffff08" stroke-width=".6">{grid}</g>'
        f'<path d="{land}" fill="none" stroke="url(#g)" stroke-width="12" opacity=".22" filter="url(#blur)"/>'
        f'<path d="{land}" fill="url(#land)"/>'
        f'<g fill="#2f1d45" stroke="#fa399c" stroke-width=".8">{keys}</g>'
        f'<ellipse cx="{ok[0]:.1f}" cy="{ok[1]:.1f}" rx="22" ry="27" fill="#120d20" stroke="#fa399c55"/>'
        f'<g fill="none" stroke="#ffffff22" stroke-width="1.2" stroke-dasharray="3 6">{roads}</g>'
        f'<path d="{land}" fill="none" stroke="url(#g)" stroke-width="2" stroke-linejoin="round"/>'
        '</svg>')


# Kategórie: id, skupina, farba, ikona (cesta SVG 24x24, lucide), názvy SK/EN.
ICONS = {
    "region": '<path d="M14.1 4.6 9.9 2.5a2 2 0 0 0-1.8 0L3.6 4.8A1 1 0 0 0 3 5.7v14.6a.7.7 0 0 0 1 .6l4.1-2.1a2 2 0 0 1 1.8 0l4.2 2.1a2 2 0 0 0 1.8 0l4.5-2.3a1 1 0 0 0 .6-.9V3.7a.7.7 0 0 0-1-.6l-4.1 2.1a2 2 0 0 1-1.8 0M15 5.8v15M9 3.2v15"/>',
    "place": '<path d="M20 10c0 5-5.5 10.2-7.4 11.8a1 1 0 0 1-1.2 0C9.5 20.2 4 15 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    "person": '<circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 0 0-16 0"/>',
    "activity": '<circle cx="12" cy="12" r="10"/><path d="m16.2 7.8-2.1 6.4-6.3 2.1 2.1-6.4z"/>',
    "rp": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/><path d="M8 12h.01M12 12h.01M16 12h.01"/>',
}

GROUPS = [("game", "Svet GTA VI", "World of GTA VI"), ("rp", "Roleplay", "Roleplay")]
CATS = [
    {"id": "oblasti", "group": "game", "icon": "region", "color": "#ff7aa8", "sk": "Oblasti", "en": "Areas"},
    {"id": "miesta", "group": "game", "icon": "place", "color": "#ffb36b", "sk": "Miesta", "en": "Places"},
    {"id": "postavy", "group": "game", "icon": "person", "color": "#c58bff", "sk": "Postavy", "en": "Characters"},
    {"id": "aktivity", "group": "game", "icon": "activity", "color": "#5fd4c4", "sk": "Aktivity", "en": "Activities"},
    {"id": "rp", "group": "rp", "icon": "rp", "color": "#7fa8ff", "sk": "Nápady na RP postavu", "en": "RP character ideas"},
]

REGIONS = [
    ("vice-city", (-80.2, 25.78), "Vice City",
     "Moderná metropola plná pláží, nočných klubov, áut a sociálnych sietí. Mesto, ktoré preslávilo GTA: Vice City z roku 2002, sa vracia po viac ako dvadsiatich rokoch.",
     "A modern metropolis of beaches, nightclubs, cars and social media. The city made famous by 2002's GTA: Vice City returns after more than twenty years.",
     [("Influencerka", "Influencer"), ("Kaucionár", "Bail bondsman"), ("Promotér klubu", "Club promoter")]),
    ("leonida-keys", (-81.1, 24.7), "Leonida Keys",
     "Reťaz ostrovov na juhu štátu. Mosty nad tyrkysovou vodou, rybárske lode a pomalý život, za ktorým sa niekedy skrýva pašovanie.",
     "A chain of islands in the south of the state. Bridges over turquoise water, fishing boats and a slow pace of life that sometimes hides smuggling.",
     [("Kapitánka lode", "Boat captain"), ("Barman z prístavu", "Harbour bartender"), ("Potápač", "Diver")]),
    ("grassrivers", (-81.2, 25.98), "Grassrivers",
     "Rozsiahle močiare a mokrade, obdoba Everglades. Člny s obrovskou vrtuľou, aligátory a ľudia, ktorí žijú ďaleko od mesta a jeho pravidiel.",
     "Vast swamps and wetlands, Leonida's version of the Everglades. Airboats, alligators and people living far from the city and its rules.",
     [("Sprievodca na airboate", "Airboat guide"), ("Samotár z močiara", "Swamp loner"), ("Rybár", "Fisherman")]),
    ("ambrosia", (-81.25, 26.85), "Ambrosia",
     "Priemyselné mesto, ktorého život sa točí okolo rafinérie cukru. Podľa Rockstaru tu majú domov aj motorkárske kluby.",
     "An industrial town whose life revolves around a sugar refinery. According to Rockstar, it's also home to biker clubs.",
     [("Robotník z rafinérie", "Refinery worker"), ("Motorkár", "Biker"), ("Mechanik", "Mechanic")]),
    ("port-gellhorn", (-85.6, 30.12), "Port Gellhorn",
     "Kedysi rušné prístavné letovisko, dnes skôr zabudnuté mesto s lacnými motelmi a ľuďmi, ktorí hľadajú, ako sa uživiť.",
     "Once a busy port resort, now more of a forgotten town with cheap motels and people trying to get by.",
     [("Majiteľ motela", "Motel owner"), ("Prístavný robotník", "Dock worker"), ("Drobný podvodník", "Small-time hustler")]),
    ("mount-kalaga", (-82.7, 30.25), "Mount Kalaga",
     "Národný park s horami, lesmi a jazerami. Miesto na lov, rybolov a jazdu v teréne.",
     "A national park with mountains, forests and lakes. A place for hunting, fishing and off-roading.",
     [("Strážkyňa parku", "Park ranger"), ("Lovec", "Hunter"), ("Off-road sprievodca", "Off-road guide")]),
]

# (id, kategória, (lon, lat), oblasť, SK názov, SK popis, EN názov, EN popis)
POINTS = [
    ("only-raw-records", "miesta", (-80.28, 25.86), "vice-city", "Only Raw Records",
     "Nahrávacie štúdio, ktoré vedú Boobie Ike a Dre'Quan Priest. Dre'Quan verí, že tu má ďalšiu veľkú hviezdu.",
     "Only Raw Records", "The record label run by Boobie Ike and Dre'Quan Priest. Dre'Quan believes he has the next big star."),
    ("boobie-klub", "miesta", (-80.3, 25.72), "vice-city", "Boobieho striptízový klub",
     "Jeden z podnikov Boobieho Ikea, popri nehnuteľnostiach a nahrávacom štúdiu.",
     "Boobie's strip club", "One of Boobie Ike's businesses, alongside his real estate and his record label."),
    ("rafineria", "miesta", (-81.05, 26.72), "ambrosia", "Rafinéria cukru",
     "Okolo nej sa točí život v Ambrosii. Práca, peniaze aj problémy celého mesta.",
     "Sugar refinery", "Life in Ambrosia revolves around it: the town's work, money and problems."),
    ("jason", "postavy", (-80.82, 24.8), "leonida-keys", "Jason Duval",
     "Vyrastal medzi podvodníkmi, prešiel armádou a teraz žije v Leonida Keys, kde robí pre miestnych drogových dílerov.",
     "Jason Duval", "Grew up around grifters, spent time in the army and now lives in the Leonida Keys, working for local drug runners."),
    ("brian", "postavy", (-81.42, 24.64), "leonida-keys", "Brian Heder",
     "Pašerák starej školy, ktorý žije v Keys so svojou treťou manželkou Lori. Jasonovi dáva strechu nad hlavou výmenou za prácu.",
     "Brian Heder", "An old-school smuggler living in the Keys with his third wife, Lori. He gives Jason a roof in exchange for work."),
    ("boobie", "postavy", (-80.36, 25.8), "vice-city", "Boobie Ike",
     "Legenda Vice City, ktorá premenila pouličnú minulosť na podnikanie: nehnuteľnosti, striptízový klub a Only Raw Records.",
     "Boobie Ike", "A Vice City legend who turned his street past into business: real estate, a strip club and Only Raw Records."),
    ("drequan", "postavy", (-80.22, 25.93), "vice-city", "Dre'Quan Priest",
     "Bývalý díler, ktorý chce uspieť v hudobnom biznise. Spolu s Boobiem stojí za Only Raw Records.",
     "Dre'Quan Priest", "A former dealer trying to make it in the music business. He runs Only Raw Records with Boobie."),
    ("real-dimez", "postavy", (-80.12, 25.66), "vice-city", "Real Dimez",
     "Bae-Luxe a Roxy, kamarátky zo strednej, ktoré preslávila virálna pieseň. Chcú z pozornosti na sieťach urobiť kariéru.",
     "Real Dimez", "Bae-Luxe and Roxy, high school friends made famous by a viral song, trying to turn social media buzz into a career."),
    ("plaze", "aktivity", (-80.08, 25.84), "vice-city", "Pláže Vice City",
     "Piesok, slnko a ľudia, ktorí chcú byť videní. Ideálne miesto na RP stretnutia a natáčanie pre sociálne siete.",
     "Vice City beaches", "Sand, sun and people who want to be seen. A natural place for RP meetups and social media content."),
    ("kluby", "aktivity", (-80.2, 25.62), "vice-city", "Nočné kluby",
     "Nočný život Vice City, ktorý Rockstar ukazuje od prvého traileru.",
     "Nightclubs", "Vice City's nightlife, shown by Rockstar since the very first trailer."),
    ("airboaty", "aktivity", (-80.98, 25.9), "grassrivers", "Airboaty a aligátory",
     "Člny s obrovskou vrtuľou cez močiare Grassrivers. A aligátory, ktoré si z trailerov pamätá každý.",
     "Airboats and alligators", "Giant-fan boats across the Grassrivers swamps, and the alligators everyone remembers from the trailers."),
    ("motorkari", "aktivity", (-81.38, 27.02), "ambrosia", "Motorkárske kluby",
     "Podľa Rockstaru majú v Ambrosii domov motorkárske kluby. Drsnejšia, vidiecka strana Leonidy.",
     "Biker clubs", "According to Rockstar, biker clubs call Ambrosia home. The rougher, rural side of Leonida."),
    ("rybarske-lode", "aktivity", (-80.6, 24.92), "leonida-keys", "Rybárske lode",
     "Prístavy a lode v Keys. Pokojná práca na vode, alebo zásterka pre niečo iné.",
     "Fishing boats", "Harbours and boats in the Keys. Quiet work on the water, or cover for something else."),
    ("motely", "aktivity", (-85.85, 30.28), "port-gellhorn", "Lacné motely",
     "Port Gellhorn je plný motelov, ktoré pamätajú lepšie časy. Miesto, kde sa ľudia schovávajú alebo začínajú odznova.",
     "Cheap motels", "Port Gellhorn is full of motels that have seen better days. A place where people hide or start over."),
    ("lov", "aktivity", (-82.45, 30.42), "mount-kalaga", "Lov",
     "Mount Kalaga je podľa Rockstaru miesto na lov.",
     "Hunting", "According to Rockstar, Mount Kalaga is a place for hunting."),
    ("rybolov", "aktivity", (-82.95, 30.4), "mount-kalaga", "Rybolov",
     "Jazerá v národnom parku Mount Kalaga.",
     "Fishing", "The lakes of Mount Kalaga National Park."),
    ("offroad", "aktivity", (-82.55, 30.05), "mount-kalaga", "Jazda v teréne",
     "Lesné cesty a kopce Mount Kalaga na off-road.",
     "Off-roading", "The forest trails and hills of Mount Kalaga."),
]

RP_DESC = {
    "sk": "Nápad na RP postavu z oblasti {r}. Toto nie je miesto z hry, ale inšpirácia pre tvoj príbeh.",
    "en": "An RP character idea from {r}. Not an in-game location, just inspiration for your story.",
}


def slug(s):
    s = s.lower()
    for a, b in zip("áäčďéíľĺňóôŕšťúýž", "aacdeillnoorstuyz"):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def markers():
    out = []
    for rid, at, name, sk, en, ideas in REGIONS:
        x, y = pt(*at)
        out.append({"id": rid, "cat": "oblasti", "x": round(x, 1), "y": round(y, 1), "region": rid,
                    "sk": {"t": name, "d": sk}, "en": {"t": name, "d": en}})
        for i, (isk, ien) in enumerate(ideas):
            ang = (i * 120 + 210) * 3.14159 / 180
            out.append({"id": f"rp-{slug(ien)}", "cat": "rp", "region": rid,
                        "x": round(x + 30 * math.cos(ang), 1), "y": round(y + 30 * math.sin(ang), 1),
                        "sk": {"t": isk, "d": RP_DESC["sk"].format(r=name)},
                        "en": {"t": ien, "d": RP_DESC["en"].format(r=name)}})
    for pid, cat, at, rid, tsk, dsk, ten, den in POINTS:
        x, y = pt(*at)
        out.append({"id": pid, "cat": cat, "x": round(x, 1), "y": round(y, 1), "region": rid,
                    "sk": {"t": tsk, "d": dsk}, "en": {"t": ten, "d": den}})
    ids = [m["id"] for m in out]
    assert len(ids) == len(set(ids)), "duplicitné id značky"
    return out


UI = {
    "sk": {
        "h1": "Mapa Leonidy", "sub": "Interaktívna mapa GTA VI",
        "intro": "Oblasti, miesta, postavy a aktivity, ktoré Rockstar oficiálne predstavil, plus nápady na RP postavy. Filtruj, hľadaj a označuj, čo už poznáš.",
        "search": "Hľadať miesto, postavu…", "noresults": "Nič sme nenašli.",
        "all": "Zobraziť všetko", "none": "Skryť všetko",
        "found": "Nájdené", "hidefound": "Skryť nájdené", "reset": "Vynulovať",
        "mark": "Označiť ako nájdené", "unmark": "Nájdené ✓", "copy": "Kopírovať odkaz", "copied": "Skopírované",
        "approx": "Približná poloha", "region": "Oblasť", "filters": "Filtre", "close": "Zavrieť panel",
        "zoomin": "Priblížiť", "zoomout": "Oddialiť", "fit": "Celá mapa",
        "note": "Štylizovaná mapa, nie mapa z hry. Údaje podľa Rockstar Games, polohy sú orientačné. Nápady na RP postavy sú naše.",
        "official": "Oficiálna mapa Leonidy na stiahnutie (Rockstar Games)",
        "builder": "/rp/tvorba-postavy/", "cta": "Vytvoriť postavu",
        "aria": "Interaktívna mapa Leonidy", "edit": "Súradnice",
    },
    "en": {
        "h1": "Leonida map", "sub": "Interactive GTA VI map",
        "intro": "Areas, places, characters and activities officially revealed by Rockstar, plus RP character ideas. Filter, search and mark what you already know.",
        "search": "Search a place or character…", "noresults": "Nothing found.",
        "all": "Show all", "none": "Hide all",
        "found": "Found", "hidefound": "Hide found", "reset": "Reset",
        "mark": "Mark as found", "unmark": "Found ✓", "copy": "Copy link", "copied": "Copied",
        "approx": "Approximate position", "region": "Area", "filters": "Filters", "close": "Close panel",
        "zoomin": "Zoom in", "zoomout": "Zoom out", "fit": "Full map",
        "note": "Stylised map, not the in-game map. Data based on Rockstar Games, positions are approximate. RP character ideas are our own.",
        "official": "Download the official Leonida map (Rockstar Games)",
        "builder": "/en/rp/character-builder/", "cta": "Create a character",
        "aria": "Interactive map of Leonida", "edit": "Coordinates",
    },
}
OFFICIAL_URL = "https://www.rockstargames.com/VI"
SEARCH_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>'


def icon(name):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


def section(lang, base_url):
    t = UI[lang]
    data = {"lang": lang, "base": base_url, "w": BASE_W, "h": BASE_H, "ui": t,
            "cats": [{"id": c["id"], "color": c["color"], "icon": ICONS[c["icon"]], "name": c[lang]} for c in CATS],
            "markers": [{"id": m["id"], "cat": m["cat"], "x": m["x"], "y": m["y"], "region": m["region"],
                         "t": m[lang]["t"], "d": m[lang]["d"]} for m in markers()]}
    counts = {}
    for m in data["markers"]:
        counts[m["cat"]] = counts.get(m["cat"], 0) + 1
    groups = ""
    for gid, gsk, gen in GROUPS:
        chips = "".join(
            f'<button type="button" class="mg-cat" data-cat="{c["id"]}" aria-pressed="true" style="--c:{c["color"]}">'
            f'<span class="mg-ico">{icon(c["icon"])}</span><span class="mg-cat-name">{html.escape(c[lang])}</span>'
            f'<span class="mg-cat-n">{counts.get(c["id"], 0)}</span></button>'
            for c in CATS if c["group"] == gid)
        groups += f'<div class="mg-group"><h2>{gsk if lang == "sk" else gen}</h2><div class="mg-cats">{chips}</div></div>'
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return (
        '<section class="mg" data-mg aria-labelledby="mg-title">'
        f'<aside class="mg-panel" id="mg-panel" aria-label="{t["filters"]}">'
        f'<div class="mg-panel-head"><span class="eyebrow">{t["sub"]}</span><h1 id="mg-title">{t["h1"]}</h1>'
        f'<button type="button" class="mg-close" aria-label="{t["close"]}">×</button></div>'
        f'<p class="mg-intro">{t["intro"]}</p>'
        f'<div class="mg-search"><label class="mg-search-box">{SEARCH_ICON}<input type="search" placeholder="{t["search"]}" aria-label="{t["search"]}" autocomplete="off"></label>'
        '<ul class="mg-results" role="listbox" hidden></ul></div>'
        f'<div class="mg-bulk"><button type="button" data-all>{t["all"]}</button><button type="button" data-none>{t["none"]}</button></div>'
        + groups +
        f'<div class="mg-progress"><div class="mg-progress-top"><span>{t["found"]}</span><b><span data-found>0</span> / {len(data["markers"])}</b></div>'
        '<div class="mg-bar"><i data-bar></i></div>'
        f'<div class="mg-progress-actions"><label><input type="checkbox" data-hidefound> {t["hidefound"]}</label>'
        f'<button type="button" data-reset>{t["reset"]}</button></div></div>'
        f'<p class="mg-note">{t["note"]} <a href="{OFFICIAL_URL}" target="_blank" rel="noopener">{t["official"]} ↗</a></p>'
        f'<a class="button mg-cta" href="{t["builder"]}">{t["cta"]} ↗</a>'
        '</aside>'
        f'<div class="mg-map" role="region" aria-label="{t["aria"]}"><div class="mg-leaflet"></div>'
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
            + section(lang, f"/{BASE}?v={v['base']}") + "</main>")
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
    open(os.path.join(WEB, BASE), "w", encoding="utf-8").write(base_svg())
    css = minify_css(open(os.path.join(WEB, "zdroj/leonida.css"), encoding="utf-8").read())
    v = {"leaflet.css": ver("assets/leaflet.css"), "leaflet.js": ver("assets/leaflet.js"),
         "mapa.js": ver("assets/mapa.js"), "base": ver(BASE)}
    menu()
    for lang in ("sk", "en"):
        page(lang, css, v)


if __name__ == "__main__":
    main()
