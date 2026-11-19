# gta6rp.sk

Statický web GTA6RP.sk (SK na `/`, EN na `/en/`), Apache + Cloudflare.

Koreň repozitára = koreň webu. Hostcreators pri každom pushnutí do `main` nasadí repozitár do `/gta6rp.sk/web/current/` a web sa zobrazuje priamo odtiaľ.

- `zdroj/` – blog: texty článkov v `posts.py` a `build.py`, ktorý z nich vygeneruje stránky blogu, menu, `sitemap.xml` a `llms.txt`. Na webe je skrytý (404).

## Nový článok
1. Pridaj článok na začiatok zoznamu `POSTS` v `zdroj/posts.py` (SK aj EN).
2. `python3 -I zdroj/build.py .`
3. Commit a push do `main`.

Súbory v `assets/` sa cachujú rok. Pri zmene súboru zmeň jeho meno alebo `?v=` v HTML.

## Launch dizajn (vydanie GTA VI)
`python3 -I zdroj/launch.py .` prepne web na launch verziu (lišta „GTA VI je vonku“, panel s počítadlom dní namiesto odpočtu, texty na úvodnej stránke, päta). Spúšťa sa pred `zdroj/build.py`, blog si hlavičku a pätu berie zo šablóny.

## Mapa Leonidy
`python3 -I zdroj/leonida.py .` vygeneruje stránku `/mapa/` a `/en/map/` (mapa.html, en/map.html) zo šablóny rp.html, súbor miest `assets/mapa/miesta.json` a pridá položku „Mapa“ do menu a päty všetkých stránok. Spúšťa sa po `zdroj/launch.py` a pred `zdroj/build.py`.
Podklad mapy (dlaždice v `assets/mapa/day/`) a miesta (`zdroj/gtadb/landmarks-6.json`) sú z GTADB.org (github.com/rolux/gtadb.org), licencia CC BY 4.0, uvedenie autorov je na stránke. Kategórie, oblasti a texty sú v `zdroj/leonida.py`, štýly v `zdroj/leonida.css`, správanie v `assets/mapa.js` (Leaflet 1.9.4).
