"""Switch gta6rp.sk to the GTA VI launch design (release day 19 Nov 2026).

Usage: python3 -I zdroj/launch.py <web-dir>

What it does (safe to re-run, every edit is applied only once):
- adds the launch bar ("GTA VI je vonku") above the header on every page,
- appends the launch styles to each page's inline <style> and to assets/app.css
  (and bumps the ?v= hash of app.css everywhere),
- updates the footer tagline on every page,
- rewrites the homepage (SK + EN): hero, release panel instead of the countdown,
  roadmap, game facts, FAQ and meta texts.

Blog pages take their header/footer/styles from rp/navody/sceny.html and
en/rp/guides/scenes.html, so run this before zdroj/build.py.
"""
import glob, hashlib, os, re, sys

WEB = sys.argv[1]
MARK = "/*launch*/"
ARROW = ('<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
         'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-arrow-up-right" aria-hidden="true">'
         '<path d="M7 7h10v10"/><path d="M7 17 17 7"/></svg>')

CSS = MARK + (
    # launch bar
    '.launch-bar{z-index:4;color:#f6e9ff;text-align:center;letter-spacing:1.4px;text-transform:uppercase;'
    'background:linear-gradient(90deg,#1a0d3a,#2d0e40 50%,#1a0d3a);justify-content:center;align-items:center;gap:14px;'
    'min-height:40px;padding:9px 5%;font:700 11px/1.4 Manrope,Arial,sans-serif;display:flex;position:relative}'
    '.launch-bar:after{content:"";background:linear-gradient(90deg,#217aff,#a73cff,#ff49a7,#ffa74d);height:1px;position:absolute;bottom:0;left:0;right:0}'
    '.launch-bar strong{color:#fff;font-weight:800}.launch-meta{color:#cdb6e0;font-weight:600}'
    '.launch-cta{color:#ffbd80;align-items:center;gap:6px;display:inline-flex}.launch-cta svg{width:14px;height:14px;transition:translate .2s}'
    '.launch-bar:hover .launch-cta{color:#ffd6b5}.launch-bar:hover .launch-cta svg{translate:2px -2px}'
    '.live-dot{background:#ff3aaa;border-radius:50%;flex-shrink:0;width:8px;height:8px;animation:live-pulse 2s infinite;display:inline-block}'
    '@keyframes live-pulse{0%{box-shadow:0 0 0 0 #ff3aaa99}70%{box-shadow:0 0 0 9px #ff3aaa00}to{box-shadow:0 0 0 0 #ff3aaa00}}'
    '@media (width<=700px){.launch-bar{letter-spacing:1px;gap:10px;font-size:10px}.launch-meta{display:none}}'
    # hero
    '.world-eyebrow .live-dot{width:7px;height:7px}'
    '.out-stamp{vertical-align:.3em;color:#ffbd80;letter-spacing:.14em;white-space:nowrap;border:2px solid #ffbd80;border-radius:6px;'
    'margin-left:.5em;padding:.32em .6em;font:800 .4em/1 Manrope,Arial,sans-serif;display:inline-block;rotate:-5deg;'
    'box-shadow:0 0 22px #ffad6140,inset 0 0 12px #ffad6126}'
    # release panel
    '.launch-panel{background:linear-gradient(#191226,#191226) padding-box,linear-gradient(110deg,#217aff,#a73cff 35%,#ff49a7 70%,#ffa74d) border-box;'
    'border:1px solid #0000;box-shadow:0 26px 70px -24px #a73cff70}'
    '.launch-day{align-items:center;gap:30px;min-width:0;display:flex}'
    '.launch-day-num{flex-direction:column;flex-shrink:0;line-height:1;display:flex}'
    '.launch-day-num small{letter-spacing:3px;color:#ff9acb;margin-bottom:4px;font:800 11px/1 Manrope,Arial,sans-serif}'
    '.launch-day-num strong{-webkit-text-fill-color:transparent;letter-spacing:-2px;font-variant-numeric:tabular-nums;'
    'background:linear-gradient(105deg,#ffac75,#ff659c 45%,#f244c5);-webkit-background-clip:text;background-clip:text;'
    'padding-right:4px;font:600 clamp(68px,7vw,108px)/.95 Oswald,Arial,sans-serif}'
    '.launch-day-copy{min-width:0}.launch-day-copy .eyebrow{color:#ff9acb}'
    '.launch-day-copy p{color:#c9b3d8;max-width:360px;margin:8px 0 14px;font-size:13px;line-height:1.7}'
    '.launch-platforms{flex-wrap:wrap;gap:8px;margin:0;padding:0;list-style:none;display:flex}'
    '.launch-platforms li{color:#f3e6fb;background:#ffffff08;border:1px solid #ffffff2b;border-radius:99px;padding:6px 12px;font-size:11px;font-weight:700}'
    '@media (width<=600px){.launch-day{flex-direction:column;align-items:flex-start;gap:12px}.launch-day-copy p{font-size:12px}}'
    # roadmap: the current phase is the release
    '.roadmap li.is-now{border-color:#ff49a7}.phase.now{color:#ff8fcf;align-items:center;gap:8px;display:inline-flex}'
    '.phase.now .live-dot{width:7px;height:7px}'
    # small polish everywhere
    '.post-card,.knowledge-card{transition:translate .25s,border-color .25s,box-shadow .25s}'
    '.post-card:hover,.knowledge-card:hover{translate:0 -3px;box-shadow:0 18px 40px -20px #a73cffa0}'
    '::selection{color:#fff;background:#d6339a}html{scrollbar-color:#5b3d78 #100c1c}'
    '@media (prefers-reduced-motion:reduce){.live-dot{animation:none}.post-card,.knowledge-card{transition:none}'
    '.post-card:hover,.knowledge-card:hover{translate:none}}'
)

BAR = {
    "sk": ('<a class="launch-bar" href="/#vydanie"><span class="live-dot" aria-hidden="true"></span><strong>GTA VI je vonku</strong>'
           '<span class="launch-meta">Vydané 19. 11. 2026 · PS5 · Xbox Series X/S</span><span class="launch-cta">Čo teraz' + ARROW.format(14) + '</span></a>'),
    "en": ('<a class="launch-bar" href="/en/#release"><span class="live-dot" aria-hidden="true"></span><strong>GTA VI is out now</strong>'
           '<span class="launch-meta">Released 19 Nov 2026 · PS5 · Xbox Series X/S</span><span class="launch-cta">What now' + ARROW.format(14) + '</span></a>'),
}

FOOTER = [
    ("<p>Hra ešte len príde.<br>Tvoj príbeh začína teraz.</p>", "<p>GTA VI je vonku.<br>Tvoj príbeh začína teraz.</p>"),
    ("príbehy, ktoré ešte len vzniknú.", "príbehy, ktoré práve vznikajú."),
    ("<p>The game is still ahead.<br>Your story starts now.</p>", "<p>GTA VI is out.<br>Your story starts now.</p>"),
    ("roleplay and stories yet to be told.", "roleplay and stories being written right now."),
]


def sub1(s, old, new, f, regex=False):
    """Replace exactly one occurrence; already-applied edits are skipped."""
    if regex:
        n = len(re.findall(old, s, flags=re.S))
        if n == 1:
            return re.sub(old, lambda m: new, s, count=1, flags=re.S)
    else:
        if new in s and old not in s:
            return s
        n = s.count(old)
        if n == 1:
            return s.replace(old, new, 1)
    if new in s:
        return s
    raise SystemExit(f"{f}: expected one match for {old[:70]!r}, found {n}")


def panel(lang):
    if lang == "sk":
        return ('<section class="departure launch-panel" id="vydanie" aria-labelledby="launch-title"><div class="departure-title">'
                '<span class="eyebrow">VYDANÉ 19. 11. 2026</span><h2 id="launch-title">VICE CITY</h2><span>GTA VI / HRA JE VONKU</span></div>'
                '<div class="launch-day"><div class="launch-day-num"><small>DEŇ</small><strong data-launch-day>01</strong></div>'
                '<div class="launch-day-copy"><span class="eyebrow">TVOJE DNI V LEONIDE</span><p>Toľko dní je GTA VI vonku. Ideálny čas dať postave meno a príbeh.</p>'
                '<ul class="launch-platforms" aria-label="Platformy"><li>PlayStation 5</li><li>Xbox Series X</li><li>Xbox Series S</li></ul></div></div>'
                '<a href="https://www.rockstargames.com/VI" target="_blank" rel="noopener noreferrer" class="departure-link">Oficiálne info<br>&amp; trailery '
                + ARROW.format(22) + '</a>' + DAY_JS + '</section>')
    return ('<section class="departure launch-panel" id="release" aria-labelledby="launch-title"><div class="departure-title">'
            '<span class="eyebrow">RELEASED 19 NOV 2026</span><h2 id="launch-title">VICE CITY</h2><span>GTA VI / OUT NOW</span></div>'
            '<div class="launch-day"><div class="launch-day-num"><small>DAY</small><strong data-launch-day>01</strong></div>'
            '<div class="launch-day-copy"><span class="eyebrow">YOUR DAYS IN LEONIDA</span><p>That\'s how long GTA VI has been out. A good time to give your character a name and a story.</p>'
            '<ul class="launch-platforms" aria-label="Platforms"><li>PlayStation 5</li><li>Xbox Series X</li><li>Xbox Series S</li></ul></div></div>'
            '<a href="https://www.rockstargames.com/VI" target="_blank" rel="noopener noreferrer" class="departure-link">Official news<br>&amp; trailers '
            + ARROW.format(22) + '</a>' + DAY_JS + '</section>')


# Day counter: release day = day 1. Before release it keeps the static "01".
DAY_JS = ('<script>(()=>{const d=Math.floor((Date.now()-Date.parse("2026-11-19T00:00:00+01:00"))/864e5)+1;'
          'if(d>1)document.querySelectorAll("[data-launch-day]").forEach(e=>e.textContent=String(d).padStart(2,"0"))})()</script>')

DOT = '<span class="live-dot" aria-hidden="true"></span>'

HOME = {
    "index.html": [
        ("<title>GTA 6: dátum vydania, odpočet a roleplay | GTA6RP.sk</title>", "<title>GTA 6 je vonku: hra, Leonida a roleplay | GTA6RP.sk</title>"),
        ('content="GTA 6: dátum vydania, odpočet a roleplay | GTA6RP.sk"', 'content="GTA 6 je vonku: hra, Leonida a roleplay | GTA6RP.sk"'),
        ('content="GTA 6: odpočet do oznámeného vydania a informácie o hre. Spoznaj roleplay, RP pravidlá, príkazy a tvorbu vlastnej postavy."',
         'content="GTA 6 vyšlo 19. 11. 2026. Informácie o hre po slovensky, RP pravidlá, príkazy, návody a tvorba vlastnej postavy pre GTA VI roleplay."'),
        ('<span></span> VITAJ NA GTA6RP.SK</p>', '<span></span>' + DOT + ' VITAJ NA GTA6RP.SK</p>'),
        ('<span class="world-pretitle">GTA 6 JE LEN ZAČIATOK.</span>', '<span class="world-pretitle">GTA 6 JE VONKU.<span class="out-stamp">19. 11. 2026</span></span>'),
        ('Spoznaj RP, vytvor svoju postavu a priprav jej miesto v novom svete GTA VI.</p>',
         'Leonida je otvorená: spoznaj RP, vytvor si postavu a vstúp do Vice City s vlastným príbehom.</p>'),
        ('<a class="world-status" href="#co-pride"><span class="world-status-dot"></span><span>RP návody už teraz <span class="world-status-divider">/</span> Katalóg serverov pripravujeme</span></a>',
         '<a class="world-status" href="#vydanie"><span class="world-status-dot"></span><span>Vonku od 19. 11. 2026 <span class="world-status-divider">/</span> PS5 · Xbox Series X/S</span></a>'),
        ('<p>Hra ešte len príde. Príbeh môžeš začať písať už dnes.', '<p>Hra je vonku. Príbeh môžeš začať písať hneď.'),
        ('<li><span class="phase live">UŽ TERAZ</span>', '<li><span class="phase live">PRIPRAVENÉ</span>'),
        ('<li><span class="phase">PO VYDANÍ HRY</span><h3>Spoznaj nový svet.</h3><p>Viac obsahu o GTA VI, konkrétne tipy a sprievodcovia podľa skutočných možností hry.</p></li>',
         '<li class="is-now"><span class="phase now">' + DOT + 'PRÁVE TERAZ</span><h3>Spoznaj nový svet.</h3><p>GTA VI je vonku. Pridávame tipy a sprievodcov podľa toho, čo hra skutočne ponúka.</p>'
         '<a href="/blog/">Čítať blog ' + ARROW.format(18) + '</a></li>'),
        ('<h2>Späť do Vice City.<br><span>O krok bližšie k Leonide.</span></h2>', '<h2>Vitaj späť vo Vice City.<br><span>Leonida je otvorená.</span></h2>'),
        ('<p>Grand Theft Auto VI je ďalšia kapitola série od Rockstar Games.', '<p>Grand Theft Auto VI je najnovšia kapitola série od Rockstar Games, vydaná 19. novembra 2026.'),
        ('Informácie overené 20. 10. 2026.', 'Informácie overené 11. 11. 2026.'),
        ('<dt>OZNÁMENÉ VYDANIE</dt>', '<dt>VYDANÉ</dt>'),
        ('<dt>OZNÁMENÉ PLATFORMY</dt>', '<dt>PLATFORMY</dt>'),
        ('<h2>Čakáme na hru.<br>Nie na dobré otázky.</h2>', '<h2>Hra je vonku.<br>Tu sú odpovede.</h2>'),
        ('Kedy vyjde GTA 6?', 'Kedy vyšlo GTA 6 a na čom si ho zahrám?'),
        ('<p>Rockstar Games uvádza 19. november 2026 pre PlayStation 5 a Xbox Series X a Xbox Series S. Odpočet na tomto webe je orientačný k začiatku tohto dňa v Bratislave, nie k potvrdenej hodine spustenia. Aktuálny termín nájdeš na',
         '<p>GTA VI vyšlo 19. novembra 2026 na PlayStation 5, Xbox Series X a Xbox Series S. Novinky a aktuálne informácie o hre nájdeš na'),
        ('Čo nájdem na GTA6RP.sk už teraz?', 'Čo nájdem na GTA6RP.sk?'),
        ('Môžem sa tu už pripojiť na GTA 6 RP server?', 'Hra je vonku. Môžem už hrať GTA 6 RP?'),
        ('<p>Nie. GTA6RP.sk je momentálne informačný web a miesto na prípravu vlastných RP príbehov. Neposkytujeme pripojenie na GTA VI RP server. Vydanie hry samo osebe neznamená dostupnosť komunitných RP serverov.</p>',
         '<p>GTA6RP.sk je informačný web a miesto na prípravu vlastných RP príbehov, pripojenie na GTA VI RP server neposkytujeme. Vydanie hry samo osebe neznamená dostupnosť komunitných RP serverov. Keď bude o RP v GTA VI niečo oficiálne, nájdeš to tu aj na <a href="/blog/">blogu</a>.</p>'),
        ('Čo pribudne po vydaní hry?', 'Čo pribudne teraz, keď je hra vonku?'),
        ('<p>Viac obsahu pripravíme po vydaní hry: konkrétne tipy, sprievodcovia a informácie založené na tom, čo hra skutočne ponúkne.',
         '<p>Postupne pridáme konkrétne tipy, sprievodcov a informácie založené na tom, čo hra skutočne ponúka.'),
        ('<h2>Zapamätaj si adresu.<br>Zvyšok príbehu napíšeš ty.</h2>', '<h2>Leonida je otvorená.<br>Zvyšok príbehu napíšeš ty.</h2>'),
    ],
    "en/home.html": [
        ("GTA 6 Release Date, Countdown &amp; Roleplay | GTA6RP.sk", "GTA 6 Is Out: Game Info, Leonida &amp; Roleplay | GTA6RP.sk"),
        ('content="Follow the countdown to the announced GTA 6 release date. Explore roleplay guides, RP rules, commands and character backstory examples."',
         'content="GTA 6 launched on 19 November 2026. Game info, roleplay guides, RP rules, commands and a character builder for GTA VI roleplay."'),
        ('<span></span> WELCOME TO GTA6RP.SK</p>', '<span></span>' + DOT + ' WELCOME TO GTA6RP.SK</p>'),
        ('<span class="world-pretitle">GTA 6 IS JUST THE START.</span>', '<span class="world-pretitle">GTA 6 IS OUT NOW.<span class="out-stamp">19 NOV 2026</span></span>'),
        ('Discover RP, create your character and find their place in the world of GTA VI.</p>',
         'Leonida is open: discover RP, create your character and step into Vice City with a story of your own.</p>'),
        ('<a class="world-status" href="#co-pride"><span class="world-status-dot"></span><span>RP guides available now <span class="world-status-divider">/</span> Server directory in development</span></a>',
         '<a class="world-status" href="#release"><span class="world-status-dot"></span><span>Out since 19 Nov 2026 <span class="world-status-divider">/</span> PS5 · Xbox Series X/S</span></a>'),
        ('<p>The game is still ahead. Your story can start today.', '<p>The game is out. Your story can start right now.'),
        ('<li><span class="phase live">AVAILABLE NOW</span>', '<li><span class="phase live">READY</span>'),
        ('<li><span class="phase">AFTER THE GAME RELEASES</span><h3>Explore a new world.</h3><p>More GTA VI content, practical tips and guides based on what the game actually offers.</p></li>',
         '<li class="is-now"><span class="phase now">' + DOT + 'RIGHT NOW</span><h3>Explore a new world.</h3><p>GTA VI is out. We\'re adding tips and guides based on what the game actually offers.</p>'
         '<a href="/en/blog/">Read the blog ' + ARROW.format(18) + '</a></li>'),
        ('<h2>Back to Vice City.<br><span>One step closer to Leonida.</span></h2>', '<h2>Welcome back to Vice City.<br><span>Leonida is open.</span></h2>'),
        ("<p>Grand Theft Auto VI is the next chapter in Rockstar Games' series.", "<p>Grand Theft Auto VI is the latest chapter in Rockstar Games' series, released on 19 November 2026."),
        ('Information checked on 20 October 2026.', 'Information checked on 11 November 2026.'),
        ('<dt>ANNOUNCED RELEASE</dt>', '<dt>RELEASED</dt>'),
        ('<dt>ANNOUNCED PLATFORMS</dt>', '<dt>PLATFORMS</dt>'),
        ('<h2>Waiting for the game.<br>Ready for your questions.</h2>', '<h2>The game is out.<br>Here are the answers.</h2>'),
        ('When does GTA 6 come out?', 'When did GTA 6 come out and where can I play it?'),
        ('<p>Rockstar Games lists 19 November 2026 for PlayStation 5, Xbox Series X and Xbox Series S. Our countdown runs to the start of that day in Bratislava, not a confirmed launch time. Check the latest date on the',
         '<p>GTA VI was released on 19 November 2026 for PlayStation 5, Xbox Series X and Xbox Series S. For news and the latest information, see the'),
        ('What can I find on GTA6RP.sk right now?', 'What can I find on GTA6RP.sk?'),
        ('Can I join a GTA 6 RP server here already?', 'The game is out. Can I play GTA 6 RP yet?'),
        ("<p>No. GTA6RP.sk currently provides information and a space to prepare your RP stories. We don't offer a connection to a GTA VI RP server. The game's release alone does not mean community RP servers will be available.</p>",
         "<p>GTA6RP.sk provides information and a space to prepare your RP stories; we don't offer a connection to a GTA VI RP server. The game's release alone does not mean community RP servers are available. When there is official news about RP in GTA VI, you'll find it here and on the <a href=\"/en/blog/\">blog</a>.</p>"),
        ('What will be added after the game releases?', 'What gets added now that the game is out?'),
        ("<p>We'll add practical tips, guides and information based on what the released game actually offers.",
         "<p>We're adding practical tips, guides and information based on what the game actually offers."),
        ('<h2>Remember the address.<br>The rest of the story is yours.</h2>', '<h2>Leonida is open.<br>The rest of the story is yours.</h2>'),
    ],
}


def main():
    # 1) app.css: append launch styles, then version every page with the new hash
    css_path = os.path.join(WEB, "assets/app.css")
    app = open(css_path, encoding="utf-8").read()
    if MARK not in app:
        app += CSS
        open(css_path, "w", encoding="utf-8").write(app)
    ver = hashlib.sha1(app.encode()).hexdigest()[:10]

    pages = sorted(p for p in glob.glob(os.path.join(WEB, "**/*.html"), recursive=True) if "/.git/" not in p)
    for path in pages:
        rel = os.path.relpath(path, WEB)
        s = open(path, encoding="utf-8").read()
        lang = "en" if re.search(r'<html lang="en"', s) else "sk"
        s = re.sub(r"/assets/app\.css\?v=[0-9a-f]+", "/assets/app.css?v=" + ver, s)
        if MARK not in s:
            s = s.replace("</style>", CSS + "</style>", 1)
        if 'class="launch-bar"' not in s:
            s = sub1(s, '<header class="site-header">', BAR[lang] + '<header class="site-header">', rel)
        for old, new in FOOTER:
            s = s.replace(old, new)
        if rel in HOME:
            for old, new in HOME[rel]:
                if old.startswith("content=") or "| GTA6RP.sk" in old:
                    s = s.replace(old, new)  # title/description repeat in og: and twitter: tags
                else:
                    s = sub1(s, old, new, rel)
            s = sub1(s, r'<section class="departure">.*?</section>', panel(lang), rel, regex=True)
            # ticker: first item announces the release, "know the rules" makes room for it
            first, second = ("TVOR POSTAVU", "POZNAJ PRAVIDLÁ") if lang == "sk" else ("BUILD YOUR CHARACTER", "KNOW THE RULES")
            out = "GTA VI JE VONKU" if lang == "sk" else "GTA VI IS OUT"
            s = re.sub(r'<span>' + first + r'</span>(<svg.*?</svg>)<span>' + second + '</span>',
                       lambda m: f'<span>{out}</span>{m.group(1)}<span>{first}</span>', s, count=1, flags=re.S)
        open(path, "w", encoding="utf-8").write(s)
    print(f"launch design applied to {len(pages)} pages, app.css?v={ver}")


main()
