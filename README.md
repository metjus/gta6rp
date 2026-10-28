# gta6rp.sk

Statický web GTA6RP.sk (SK na `/`, EN na `/en/`), Apache + Cloudflare.

- `web/` – presne to, čo ide na server (obsah koreňa webu vrátane `.htaccess`).
- `zdroj/` – blog: texty článkov v `posts.py` a `build.py`, ktorý z nich vygeneruje stránky blogu, menu, `sitemap.xml` a `llms.txt`.
- `.cpanel.yml` – nasadenie cez cPanel Git Version Control: skopíruje `web/` do koreňa domény.

## Nový článok
1. Pridaj článok na začiatok zoznamu `POSTS` v `zdroj/posts.py` (SK aj EN).
2. `python3 -I zdroj/build.py web`
3. Commit a push do `main`.

Súbory v `web/assets/` sa cachujú rok. Pri zmene súboru zmeň jeho meno alebo `?v=` v HTML.
