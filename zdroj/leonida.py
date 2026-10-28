"""Interaktívna mapa Leonidy na úvodnej stránke (SK aj EN).

Vygeneruje sekciu medzi <!--leonida--> ... <!--/leonida--> v index.html a en/home.html
(prvýkrát ju vloží za .ticker) a nastaví ?v= pre assets/leonida.js.

    python3 -I zdroj/leonida.py .

Mapa je štylizovaná: obrys podľa Floridy, ktorou sa Leonida inšpiruje. Rockstar zatiaľ
nezverejnil oficiálnu mapu, preto sú polohy oblastí len orientačné.
"""
import hashlib
import html
import os
import re
import sys

WEB = sys.argv[1] if len(sys.argv) > 1 else "."

W, H = 820, 780


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


REGIONS = [
    {"id": "vice-city", "at": (-80.2, 25.78), "label": "t",
     "sk": {"tag": "METROPOLA", "name": "Vice City",
            "desc": "Moderná metropola plná pláží, nočných klubov, áut a sociálnych sietí. Mesto, ktoré preslávilo GTA: Vice City z roku 2002, sa vracia po viac ako dvadsiatich rokoch.",
            "rp": ["Influencerka", "Kaucionár", "Promotér klubu"]},
     "en": {"tag": "METROPOLIS", "name": "Vice City",
            "desc": "A modern metropolis of beaches, nightclubs, cars and social media. The city made famous by 2002's GTA: Vice City returns after more than twenty years.",
            "rp": ["Influencer", "Bail bondsman", "Club promoter"]}},
    {"id": "leonida-keys", "at": (-81.1, 24.7), "label": "b",
     "sk": {"tag": "OSTROVY", "name": "Leonida Keys",
            "desc": "Reťaz ostrovov na juhu štátu. Mosty nad tyrkysovou vodou, rybárske lode a pomalý život. Práve tu žije a pracuje Jason Duval.",
            "rp": ["Kapitánka lode", "Barman z prístavu", "Potápač"]},
     "en": {"tag": "ISLANDS", "name": "Leonida Keys",
            "desc": "A chain of islands in the south of the state. Bridges over turquoise water, fishing boats and a slow pace of life. This is where Jason Duval lives and works.",
            "rp": ["Boat captain", "Harbour bartender", "Diver"]}},
    {"id": "grassrivers", "at": (-81.2, 25.98), "label": "l",
     "sk": {"tag": "MOČIARE", "name": "Grassrivers",
            "desc": "Rozsiahle močiare a mokrade, obdoba Everglades. Airboaty, aligátory a ľudia, ktorí žijú ďaleko od mesta a jeho pravidiel.",
            "rp": ["Sprievodca na airboate", "Samotár z močiara", "Rybár"]},
     "en": {"tag": "WETLANDS", "name": "Grassrivers",
            "desc": "Vast swamps and wetlands, Leonida's version of the Everglades. Airboats, alligators and people living far from the city and its rules.",
            "rp": ["Airboat guide", "Swamp loner", "Fisherman"]}},
    {"id": "ambrosia", "at": (-81.25, 26.85), "label": "l",
     "sk": {"tag": "PRIEMYSEL", "name": "Ambrosia",
            "desc": "Priemyselné mesto, ktorého život sa točí okolo rafinérie cukru. Podľa Rockstaru tu majú domov aj motorkárske kluby.",
            "rp": ["Robotník z rafinérie", "Motorkár", "Mechanik"]},
     "en": {"tag": "INDUSTRY", "name": "Ambrosia",
            "desc": "An industrial town whose life revolves around a sugar refinery. According to Rockstar, it's also home to biker clubs.",
            "rp": ["Refinery worker", "Biker", "Mechanic"]}},
    {"id": "port-gellhorn", "at": (-85.6, 30.12), "label": "b",
     "sk": {"tag": "PRÍSTAV", "name": "Port Gellhorn",
            "desc": "Kedysi rušné prístavné letovisko, dnes skôr zabudnuté mesto s lacnými motelmi a ľuďmi, ktorí hľadajú, ako sa uživiť.",
            "rp": ["Majiteľ motela", "Prístavný robotník", "Drobný podvodník"]},
     "en": {"tag": "PORT TOWN", "name": "Port Gellhorn",
            "desc": "Once a busy port resort, now more of a forgotten town with cheap motels and people trying to get by.",
            "rp": ["Motel owner", "Dock worker", "Small-time hustler"]}},
    {"id": "mount-kalaga", "at": (-82.7, 30.25), "label": "b",
     "sk": {"tag": "DIVOČINA", "name": "Mount Kalaga",
            "desc": "Národný park s horami, lesmi a jazerami. Miesto na lov, rybolov a jazdu v teréne.",
            "rp": ["Strážkyňa parku", "Lovec", "Off-road sprievodca"]},
     "en": {"tag": "WILDERNESS", "name": "Mount Kalaga",
            "desc": "A national park with mountains, forests and lakes. A place for hunting, fishing and off-roading.",
            "rp": ["Park ranger", "Hunter", "Off-road guide"]}},
]

TEXT = {
    "sk": {
        "eyebrow": "MAPA LEONIDY / NASTAV SI GPS",
        "h2": "ODKIAĽ JE<br>TVOJA <em>POSTAVA?</em>",
        "intro": "Rockstar pomenoval šesť oblastí štátu Leonida. Klikni na bod na mape, nastav trasu a zisti, aké príbehy sa tam dajú hrať.",
        "aria": "Interaktívna mapa Leonidy",
        "hud": "LEONIDA · GPS",
        "flight": "BRATISLAVA → VICE CITY",
        "route": "TRASA",
        "all": "Celá mapa",
        "ideas": "NÁPADY NA RP POSTAVU",
        "cta": "Vytvoriť postavu",
        "builder": "/rp/tvorba-postavy/",
        "prev": "Predchádzajúca oblasť", "next": "Ďalšia oblasť",
        "note": "Štylizovaná mapa, nie oficiálna mapa hry. Polohy oblastí sú orientačné. Popisy podľa Rockstar Games, nápady na postavy sú len pre RP.",
    },
    "en": {
        "eyebrow": "LEONIDA MAP / SET YOUR GPS",
        "h2": "WHERE IS YOUR<br>CHARACTER <em>FROM?</em>",
        "intro": "Rockstar has named six areas of the state of Leonida. Tap a point on the map, set a route and see what stories you could play there.",
        "aria": "Interactive map of Leonida",
        "hud": "LEONIDA · GPS",
        "flight": "BRATISLAVA → VICE CITY",
        "route": "ROUTE",
        "all": "Full map",
        "ideas": "RP CHARACTER IDEAS",
        "cta": "Create a character",
        "builder": "/en/rp/character-builder/",
        "prev": "Previous area", "next": "Next area",
        "note": "Stylised map, not the official game map. Area positions are approximate. Descriptions based on Rockstar Games, character ideas are for RP only.",
    },
}

ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9"/></svg>'


def svg():
    land = smooth(COAST, True)
    ok = pt(-80.83, 26.95)
    keys = "".join(
        f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{9 - i * .5:.1f}" ry="3.2" transform="rotate({-28 + i * 2} {x:.1f} {y:.1f})"/>'
        for i, (x, y) in enumerate(pt(*k) for k in KEYS))
    roads = "".join(f'<path d="{smooth(r, False)}"/>' for r in ROADS)
    return (
        f'<svg class="lm-svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">'
        '<defs><linearGradient id="lm-g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ff965d"/><stop offset=".55" stop-color="#fa399c"/><stop offset="1" stop-color="#b22bdd"/></linearGradient>'
        '<radialGradient id="lm-land" cx=".75" cy=".75" r=".9"><stop stop-color="#2c1b40"/><stop offset="1" stop-color="#1a1428"/></radialGradient>'
        f'<path id="lm-shore" d="{land}" pathLength="1"/>'
        '<pattern id="lm-dots" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#3a2d52"/></pattern></defs>'
        f'<rect x="-400" y="-400" width="{W + 800}" height="{H + 800}" fill="url(#lm-dots)"/>'
        f'<g class="lm-land"><use href="#lm-shore" class="lm-fill"/><g class="lm-keys">{keys}</g>'
        f'<ellipse class="lm-lake" cx="{ok[0]:.1f}" cy="{ok[1]:.1f}" rx="22" ry="27"/></g>'
        f'<g class="lm-roads">{roads}</g>'
        '<use href="#lm-shore" class="lm-glow"/><use href="#lm-shore" class="lm-coast"/>'
        '<path class="lm-route-bg"/><path class="lm-route"/>'
        '<g class="lm-car"><circle r="11" class="lm-car-halo"/><circle r="5"/></g>'
        '<g class="lm-plane"><path transform="translate(-12 -12)" d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5z"/></g>'
        '</svg>')


def section(lang):
    t = TEXT[lang]
    pins, data = [], []
    for i, r in enumerate(REGIONS):
        x, y = pt(*r["at"])
        c = r[lang]
        pins.append(
            f'<button type="button" class="lm-pin lm-l-{r["label"]}" data-i="{i}" data-x="{x:.1f}" data-y="{y:.1f}" '
            f'style="left:{x / W * 100:.2f}%;top:{y / H * 100:.2f}%;--d:{i * .12:.2f}s" aria-pressed="{str(i == 0).lower()}">'
            f'<span class="lm-dot"></span><span class="lm-name">{html.escape(c["name"])}</span></button>')
        data.append(
            f'<article class="lm-card" data-i="{i}"{"" if i == 0 else " hidden"}>'
            f'<div class="lm-count"><span>0{i + 1}</span> / 06 · {c["tag"]}</div>'
            f'<h3>{html.escape(c["name"])}</h3><p>{html.escape(c["desc"])}</p>'
            f'<div class="lm-ideas"><small>{t["ideas"]}</small><ul>'
            + "".join(f"<li>{html.escape(x)}</li>" for x in c["rp"]) + "</ul></div></article>")
    return (
        f'<!--leonida--><section class="lm" id="{"mapa" if lang == "sk" else "map"}" aria-labelledby="lm-title" data-leonida data-route="{t["route"]}">'
        f'<div class="lm-stage"><div class="lm-map" role="group" aria-label="{t["aria"]}">'
        + svg() + '<div class="lm-sweep" aria-hidden="true"></div>'
        + "".join(pins)
        + f'<div class="lm-hud lm-hud-tl" aria-hidden="true"><b>{t["hud"]}</b><span class="lm-coords">25.78°N 80.20°W</span></div>'
        f'<div class="lm-hud lm-hud-br" aria-hidden="true"><span class="lm-route-label">{t["flight"]}</span></div>'
        f'<button type="button" class="lm-reset" hidden>{t["all"]}</button>'
        '</div>'
        '<div class="lm-side"><div class="lm-head"><span class="eyebrow">' + t["eyebrow"] + '</span>'
        f'<h2 id="lm-title">{t["h2"]}</h2><p>{t["intro"]}</p></div>'
        '<div class="lm-panel" aria-live="polite">' + "".join(data)
        + f'<div class="lm-nav"><button type="button" class="lm-prev" aria-label="{t["prev"]}">←</button>'
        f'<button type="button" class="lm-next" aria-label="{t["next"]}">→</button>'
        f'<a class="button" href="{t["builder"]}">{t["cta"]} {ARROW}</a></div></div></div></div>'
        f'<p class="lm-note">{t["note"]}</p>'
        '</section><!--/leonida-->')


def main():
    js = open(os.path.join(WEB, "assets/leonida.js"), "rb").read()
    css = open(os.path.join(WEB, "zdroj/leonida.css"), encoding="utf-8").read()
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s*([{};:,>])\s*", r"\1", re.sub(r"\s+", " ", css)).replace(";}", "}").strip()
    v = hashlib.sha1(js).hexdigest()[:10]
    for lang, rel in (("sk", "index.html"), ("en", "en/home.html")):
        path = os.path.join(WEB, rel)
        s = open(path, encoding="utf-8").read()
        block = section(lang)
        if "<!--leonida-->" in s:
            a, b = s.index("<!--leonida-->"), s.index("<!--/leonida-->") + len("<!--/leonida-->")
            s = s[:a] + block + s[b:]
        else:
            i = s.index('<div class="ticker">')
            i = s.index("</div>", i) + len("</div>")
            s = s[:i] + block + s[i:]
        tag_css = f'<style id="lm-css">{css}</style>'
        if 'id="lm-css"' in s:
            a = s.index('<style id="lm-css">')
            b = s.index("</style>", a) + len("</style>")
            s = s[:a] + tag_css + s[b:]
        else:
            s = s.replace("</head>", tag_css + "</head>", 1)
        tag_js = f'<script defer src="/assets/leonida.js?v={v}"></script>'
        if "/assets/leonida.js" in s:
            a = s.index('<script defer src="/assets/leonida.js')
            b = s.index("</script>", a) + len("</script>")
            s = s[:a] + tag_js + s[b:]
        else:
            s = s.replace("</head>", tag_js + "</head>", 1)
        open(path, "w", encoding="utf-8").write(s)
        print("ok", rel)


if __name__ == "__main__":
    main()
