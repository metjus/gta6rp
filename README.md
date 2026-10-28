# gta6rp.sk

Statický web GTA6RP.sk (SK na `/`, EN na `/en/`), Apache + Cloudflare.

Koreň repozitára = koreň webu. Hostcreators pri každom pushnutí do `main` nasadí repozitár do `/gta6rp.sk/web/current/` a web sa zobrazuje priamo odtiaľ.

- `zdroj/` – blog: texty článkov v `posts.py` a `build.py`, ktorý z nich vygeneruje stránky blogu, menu, `sitemap.xml` a `llms.txt`. Na webe je skrytý (404).

## Nový článok
1. Pridaj článok na začiatok zoznamu `POSTS` v `zdroj/posts.py` (SK aj EN).
2. `python3 -I zdroj/build.py .`
3. Commit a push do `main`.

Súbory v `assets/` sa cachujú rok. Pri zmene súboru zmeň jeho meno alebo `?v=` v HTML.
