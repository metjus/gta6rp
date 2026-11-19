/* Mapa Leonidy (gta6rp.sk/mapa/). Podklad a miesta 1:1 z GTADB.org (a prispievatelia), CC BY 4.0. Leaflet 1.9.4. */
(function () {
  "use strict";
  var root = document.querySelector("[data-mg]");
  var dataEl = document.getElementById("mg-data");
  if (!root || !dataEl || !window.L) return;
  var D = JSON.parse(dataEl.textContent), T = D.ui, L = window.L;
  var KEY = "gta6rp_map_";
  function load(k, d) { try { var v = JSON.parse(localStorage.getItem(KEY + k)); return v == null ? d : v; } catch (e) { return d; } }
  function save(k, v) { try { localStorage.setItem(KEY + k, JSON.stringify(v)); } catch (e) {} }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function norm(s) { return String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
  function num(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " "); }

  var hidden = new Set(load("hidden2", ["oblasti"])), found = new Set(load("found", []));
  var hideFound = load("hidefound", false) === true;
  var filter = load("filter", "all"), layerId = load("layer", D.layers[0].id);
  var typeIds = new Set(D.typeIds), types = {}; D.types.forEach(function (t) { types[t.id] = t; });
  var items = [], places = [], byId = {}, query = "";

  /* --- výška mapy podľa hlavičky --- */
  function fitHeight() { root.style.setProperty("--top", Math.round(root.getBoundingClientRect().top + window.scrollY) + "px"); }
  fitHeight();

  /* --- mapa: herné súradnice x, y (ako GTADB), zoom 0 = 1024 px na celý svet --- */
  var CRS = L.extend({}, L.CRS.Simple, { transformation: new L.Transformation(1 / 32, 512, -1 / 32, 512) });
  var WORLD = L.latLngBounds([[-16384, -16384], [16384, 16384]]);
  var map = L.map(root.querySelector(".mg-leaflet"), {
    crs: CRS, minZoom: 0, maxZoom: 7, zoomSnap: 0.25, zoomDelta: 0.5, wheelPxPerZoomLevel: 90,
    zoomControl: false, preferCanvas: true, maxBounds: WORLD, maxBoundsViscosity: 0.8
  });
  map.attributionControl.setPrefix(false);
  var ATTR = '<a href="' + D.gtadb + '" target="_blank" rel="noopener">' + esc(T.credit) + "</a> (CC BY 4.0)";
  var tiles = {};
  D.layers.forEach(function (l) {
    tiles[l.id] = L.tileLayer(l.url, { bounds: L.latLngBounds(l.bounds), minNativeZoom: 0, maxNativeZoom: l.maxNative, noWrap: true, keepBuffer: 3, attribution: ATTR });
  });
  if (!tiles[layerId]) layerId = D.layers[0].id;
  function setBg() { D.layers.forEach(function (l) { if (l.id === layerId) map.getContainer().style.background = l.bg; }); }
  tiles[layerId].addTo(map); setBg();
  var layerSel = root.querySelector("[data-layer]");
  layerSel.value = layerId;
  layerSel.onchange = function () {
    map.removeLayer(tiles[layerId]); layerId = layerSel.value; tiles[layerId].addTo(map); tiles[layerId].bringToBack(); setBg(); save("layer", layerId);
  };

  L.control.zoom({ position: "topright", zoomInTitle: T.zoomin, zoomOutTitle: T.zoomout }).addTo(map);
  var LAND = L.latLngBounds([[-8300, -10000], [9200, 3400]]);
  var Fit = L.Control.extend({
    options: { position: "topright" },
    onAdd: function () {
      var b = L.DomUtil.create("button", "mg-fit");
      b.type = "button"; b.title = T.fit; b.setAttribute("aria-label", T.fit);
      b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3H5a2 2 0 0 0-2 2v3M21 8V5a2 2 0 0 0-2-2h-3M3 16v3a2 2 0 0 0 2 2h3M16 21h3a2 2 0 0 0 2-2v-3"/></svg>';
      L.DomEvent.disableClickPropagation(b);
      L.DomEvent.on(b, "click", function () { map.closePopup(); map.flyToBounds(LAND, { duration: 0.6 }); });
      return b;
    }
  });
  new Fit().addTo(map);
  map.fitBounds(LAND, { animate: false });

  /* --- značka ako na GTADB: kvapka s bielym okrajom vo farbe miesta, špička na presnej polohe --- */
  var R = 7;
  L.Canvas.include({
    _updatePin: function (layer) {
      if (!this._drawing || layer._empty()) return;
      var p = layer._point, ctx = this._ctx, r = layer._radius, cy = p.y - r * Math.SQRT2;
      ctx.beginPath();
      ctx.arc(p.x, cy, r, Math.PI * 0.75, Math.PI * 2.25);
      ctx.lineTo(p.x, p.y);
      ctx.closePath();
      this._fillStroke(ctx, layer);
    }
  });
  var Pin = L.CircleMarker.extend({
    _updatePath: function () { this._renderer._updatePin(this); },
    _updateBounds: function () {
      var r = this._radius + 3, p = this._point;
      this._pxBounds = new L.Bounds(p.subtract([r, r * 2.6]), p.add([r, 3]));
    },
    _containsPoint: function (q) {
      var r = this._radius, c = this._point.subtract([0, r * Math.SQRT2]);
      return q.distanceTo(c) <= r + 3 || (Math.abs(q.x - c.x) <= r * 0.7 && q.y >= c.y && q.y <= this._point.y + 1);
    }
  });

  /* --- údaje GTADB, rovnaké pravidlá ako map/index.js --- */
  function igName(p) { return p.ig.split(", ")[0] || "?"; }
  function rlAddr(p) { return p.rl.replace(/(?!^)\?$/, ""); }
  function rlName(p) { return rlAddr(p).split(", ")[0] || "?"; }
  function visTags(p) { return p.tags.filter(function (t) { return !/^\/\//.test(t) && !/^L\d+$/i.test(t); }); }
  function typesOf(p) { var t = p.tags.filter(function (x) { return typeIds.has(x); }); return t.length ? t : ["unclassified"]; }
  function rlStatus(p) { return p.rl === "" || p.rl === "?" ? "unknown" : p.tags.indexOf("unconfirmed") > -1 ? "unconfirmed" : "confirmed"; }
  var STREET = /\s(?:Ave|Blvd|Ct|Dr|Hwy|Ln|Pkwy|Pl|Rd|St|Way),/;
  var FILTERS = {
    all: function () { return true; },
    igNameConfirmed: function (p) { return !!p.ig && p.ig[0] !== "?" && p.ig.indexOf("?,") < 0 && p.ig[0] !== '"'; },
    igNameUnconfirmed: function (p) { return p.ig[0] !== "?" && p.ig.indexOf("?,") > -1; },
    igNameUnknown: function (p) { return p.ig[0] === "?" || p.ig[0] === '"'; },
    igAddressConfirmed: function (p) { return STREET.test(p.ig); },
    igAddressUnknown: function (p) { return !STREET.test(p.ig); },
    igLatLngConfirmed: function (p) { return p.ig.slice(-1) !== "?" && p.ll !== null; },
    igLatLngUnconfirmed: function (p) { return p.ig.slice(-1) === "?"; },
    igLatLngUnknown: function (p) { return p.ll === null; },
    igWithPhoto: function (p) { return p.igV !== null; },
    igWithoutPhoto: function (p) { return p.igV === null; },
    igClassified: function (p) { return p.types[0] !== "unclassified"; },
    igUnclassified: function (p) { return p.types[0] === "unclassified"; },
    rlLandmarkConfirmed: function (p) { return rlStatus(p) === "confirmed"; },
    rlLandmarkUnconfirmed: function (p) { return rlStatus(p) === "unconfirmed"; },
    rlLandmarkUnknown: function (p) { return rlStatus(p) === "unknown"; },
    rlLatLngMissing: function (p) { return rlAddr(p)[0] !== "?" && !p.rlLL; },
    rlWithPhoto: function (p) { return p.rlV !== null; },
    rlWithoutPhoto: function (p) { return p.rlV === null; }
  };
  if (!FILTERS[filter]) filter = "all";
  function matchFind(it) {
    if (!query) return true;
    var neg = query[0] === "!", q = neg ? query.slice(1) : query;
    if (!q) return true;
    var hit = it.find.indexOf(q) > -1;
    return neg ? !hit : hit;
  }

  /* --- popup --- */
  function photo(p, kind, v, alt) {
    return '<figure class="mg-pop-photo"><img loading="lazy" alt="' + esc(alt) + '" src="' + D.photos + encodeURIComponent(p.id + "," + kind) + ".jpg?v=" + v + '" onerror="this.parentNode.remove()"><figcaption>' + esc(kind === "ig" ? T.photo : T.rlphoto) + " · GTADB.org</figcaption></figure>";
  }
  function regionHtml(r) {
    return '<div class="mg-pop"><span class="mg-pop-cat" style="--c:' + D.regionColor + '">' + esc(T.region) + " · GTA6RP.sk</span>" +
      "<h3>" + esc(r.t) + "</h3><p>" + esc(r.d) + "</p>" +
      '<div class="mg-pop-ideas"><small>' + esc(T.ideas) + "</small><div>" + r.rp.map(function (x) { return "<span>" + esc(x) + "</span>"; }).join("") + "</div></div>" +
      actions(r.id) + "</div>";
  }
  function placeHtml(p) {
    var tg = visTags(p), ra = rlAddr(p);
    var ty = p.types.map(function (t) { return '<span class="mg-pop-type" style="--c:' + types[t].color + '">' + esc(types[t].name) + "</span>"; }).join("");
    var gl = D.gtadb + "#VI," + (p.ll ? p.x.toFixed(3) + "," + p.y.toFixed(3) : "0.000,0.000") + ",4.000," + p.id;
    return '<div class="mg-pop">' +
      (p.igV !== null ? photo(p, "ig", p.igV, T.photo + ": " + igName(p)) : "") +
      '<div class="mg-pop-types">' + ty + '<span class="mg-pop-id">' + esc(p.id) + "</span></div>" +
      "<h3>" + esc(igName(p)) + "</h3>" +
      '<p class="mg-pop-addr">' + esc(p.ig || "?") + "</p>" +
      (p.ll ? "" : '<p class="mg-pop-nopos">' + esc(T.nopos) + "</p>") +
      '<div class="mg-pop-rl"><small>' + esc(T.real) + "</small><b>" + esc(rlName(p)) + "</b>" + (ra && ra !== rlName(p) ? "<span>" + esc(ra) + "</span>" : "") + "</div>" +
      (p.rlV !== null ? photo(p, "rl", p.rlV, T.rlphoto + ": " + rlName(p)) : "") +
      (tg.length ? '<div class="mg-pop-tags"><small>' + esc(T.tags) + "</small>" + tg.map(function (t) { return "<span>" + esc(t) + "</span>"; }).join("") + "</div>" : "") +
      actions(p.id) +
      '<a class="mg-pop-src" href="' + gl + '" target="_blank" rel="noopener">GTADB.org ↗</a></div>';
  }
  function actions(id) {
    var f = found.has(id);
    return '<div class="mg-pop-actions"><button type="button" data-act="found" class="' + (f ? "is-found" : "") + '">' + esc(f ? T.unmark : T.mark) + "</button>" +
      '<button type="button" data-act="copy">' + esc(T.copy) + "</button></div>";
  }
  var popup = L.popup({ maxWidth: 320, minWidth: 260, autoPanPaddingTopLeft: [20, 60], autoPanPaddingBottomRight: [20, 20], className: "mg-popup" });
  var current = null;
  function openItem(it, view) {
    current = it;
    var ll = it.ll || map.getCenter();
    if (view && it.ll) map.setView(it.ll, Math.max(map.getZoom(), it.region ? 2 : 4), { animate: view === "fly" });
    popup.options.offset = it.region || !it.ll ? [0, 7] : [0, -R * 2.4];
    popup.setLatLng(ll).setContent(it.region ? regionHtml(it) : placeHtml(it)).openOn(map);
    history.replaceState(null, "", "#" + it.id);
    highlight();
  }
  map.on("popupopen", function (e) {
    var el = e.popup.getElement(); if (!el || !current) return;
    var it = current;
    var fb = el.querySelector('[data-act="found"]'), cb = el.querySelector('[data-act="copy"]');
    if (fb) fb.onclick = function () { toggleFound(it.id); fb.classList.toggle("is-found", found.has(it.id)); fb.textContent = found.has(it.id) ? T.unmark : T.mark; };
    if (cb) cb.onclick = function () {
      var url = location.origin + location.pathname + "#" + it.id;
      var done = function () { cb.textContent = T.copied; setTimeout(function () { cb.textContent = T.copy; }, 1500); };
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, done); else done();
    };
  });
  map.on("popupclose", function () { current = null; highlight(); if (location.hash) history.replaceState(null, "", location.pathname + location.search); });

  /* --- vrstvy --- */
  var pins = L.layerGroup().addTo(map), regions = L.layerGroup();
  function styleFor(p) {
    var f = found.has(p.id), sel = current === p;
    return { radius: R, color: "#fff", weight: sel ? 2.5 : 1, fillColor: p.color, fillOpacity: f ? 0.35 : 1, opacity: f ? 0.55 : 1 };
  }
  var lastSel = null;
  function highlight() {
    var prev = lastSel;
    lastSel = current && !current.region ? current : null;
    if (prev && prev.marker) prev.marker.setStyle(styleFor(prev));
    if (lastSel && lastSel.marker && pins.hasLayer(lastSel.marker)) { lastSel.marker.setStyle(styleFor(lastSel)); lastSel.marker.bringToFront(); }
    D.regions.forEach(function (r) { var el = r.marker.getElement(); if (el) el.classList.toggle("is-active", current === r); });
  }
  var tip = L.tooltip({ direction: "top", offset: [0, -R * 2.8], className: "mg-tip", opacity: 1 });
  function addPlace(p) {
    if (!p.ll) return;
    var m = new Pin(p.ll, styleFor(p));
    m.on("click", function (e) { L.DomEvent.stop(e); closePanel(); openItem(p); });
    m.on("mouseover", function () { tip.setLatLng(p.ll).setContent(esc(igName(p)) + "<br><small>" + esc(rlName(p)) + "</small>"); map.openTooltip(tip); });
    m.on("mouseout", function () { map.closeTooltip(tip); });
    p.marker = m;
  }
  D.regions.forEach(function (r) {
    r.region = true; r.ll = [r.y, r.x]; byId[r.id] = r; items.push(r);
    r.find = norm(r.t);
    r.marker = L.marker(r.ll, {
      keyboard: true, title: r.t, riseOnHover: true, zIndexOffset: 1000,
      icon: L.divIcon({ className: "mg-region", iconSize: [0, 0], html: '<div class="mg-region-pin"><span class="mg-region-dot"></span><span class="mg-region-name">' + esc(r.t) + "</span></div>" })
    }).on("click", function () { closePanel(); openItem(r); });
  });

  /* --- filtre --- */
  var catBtns = root.querySelectorAll(".mg-cat"), shownEl = root.querySelector("[data-shown]");
  var filterSel = root.querySelector("[data-filter]");
  filterSel.value = filter;
  function visible(p) {
    if (hideFound && found.has(p.id)) return false;
    if (!p.types.some(function (t) { return !hidden.has(t); })) return false;
    return FILTERS[filter](p) && matchFind(p);
  }
  function render() {
    var n = 0, all = 0;
    places.forEach(function (p) {
      var v = visible(p);
      if (v) all++;
      if (!p.marker) return;
      var has = pins.hasLayer(p.marker);
      if (v) n++;
      if (v && !has) pins.addLayer(p.marker); else if (!v && has) pins.removeLayer(p.marker);
      if (v) p.marker.setStyle(styleFor(p));
    });
    var regOn = !hidden.has("oblasti");
    if (regOn && !map.hasLayer(regions)) regions.addTo(map);
    if (!regOn && map.hasLayer(regions)) regions.remove();
    D.regions.forEach(function (r) {
      var v = !(hideFound && found.has(r.id)) && matchFind(r), has = regions.hasLayer(r.marker);
      if (v && !has) regions.addLayer(r.marker); else if (!v && has) regions.removeLayer(r.marker);
      var el = r.marker.getElement(); if (el) el.classList.toggle("is-found", found.has(r.id));
    });
    catBtns.forEach(function (b) { b.setAttribute("aria-pressed", String(!hidden.has(b.dataset.cat))); });
    if (shownEl && places.length) shownEl.textContent = num(all) + " " + T.shown + (all !== n ? " · " + num(n) + " " + T.onmap : "");
    var f = 0; found.forEach(function (id) { if (byId[id]) f++; });
    root.querySelector("[data-found]").textContent = num(f);
    root.querySelector("[data-bar]").style.width = (f / Math.max(places.length, 1) * 100) + "%";
    root.querySelector("[data-hidefound]").checked = hideFound;
    highlight();
  }
  catBtns.forEach(function (b) {
    b.addEventListener("click", function () {
      var c = b.dataset.cat; hidden.has(c) ? hidden.delete(c) : hidden.add(c);
      save("hidden2", Array.from(hidden)); render();
    });
  });
  root.querySelector("[data-all]").onclick = function () { D.types.forEach(function (t) { hidden.delete(t.id); }); filter = "all"; filterSel.value = "all"; save("filter", filter); save("hidden2", Array.from(hidden)); render(); };
  root.querySelector("[data-none]").onclick = function () { D.types.forEach(function (t) { hidden.add(t.id); }); hidden.add("oblasti"); save("hidden2", Array.from(hidden)); map.closePopup(); render(); };
  filterSel.onchange = function () { filter = filterSel.value; save("filter", filter); render(); };
  root.querySelector("[data-hidefound]").onchange = function (e) { hideFound = e.target.checked; save("hidefound", hideFound); render(); };
  root.querySelector("[data-reset]").onclick = function () { found.clear(); save("found", []); render(); };
  function toggleFound(id) { found.has(id) ? found.delete(id) : found.add(id); save("found", Array.from(found)); render(); }

  function reveal(id) {
    var it = byId[id]; if (!it) return;
    if (it.region) hidden.delete("oblasti");
    else {
      if (!it.types.some(function (t) { return !hidden.has(t); })) hidden.delete(it.types[0]);
      if (!FILTERS[filter](it)) { filter = "all"; filterSel.value = "all"; save("filter", filter); }
    }
    save("hidden2", Array.from(hidden));
    if (hideFound && found.has(id)) { hideFound = false; save("hidefound", false); }
    render(); closePanel(); openItem(it, "fly");
  }

  /* --- vyhľadávanie ako „Find“ na GTADB: id, adresy aj tagy, „!“ na začiatku = neobsahuje; filtruje aj body na mape --- */
  var input = root.querySelector(".mg-search input"), list = root.querySelector(".mg-results"), sel = -1, hits = [], tmr = 0;
  function search() {
    var raw = input.value.trim();
    query = norm(raw);
    clearTimeout(tmr); tmr = setTimeout(render, 120);
    if (raw.length < 2 || query[0] === "!") { list.hidden = true; list.innerHTML = ""; return; }
    hits = [];
    for (var i = 0; i < items.length; i++) if (items[i].find.indexOf(query) > -1) hits.push(items[i]);
    function rank(it) { var n = norm(it.region ? it.t : igName(it)); return it.region ? -1 : n.indexOf(query) === 0 ? 0 : n.indexOf(query) > -1 ? 1 : 2; }
    hits.sort(function (a, b) { return rank(a) - rank(b); });
    var total = hits.length;
    hits = hits.slice(0, 15); sel = -1;
    list.innerHTML = hits.length ? hits.map(function (it, i) {
      var title = it.region ? it.t : igName(it) + " · " + rlName(it);
      var sub = it.region ? T.region + " · GTA6RP.sk" : (it.ig || "?") + (it.ll ? "" : " · " + T.nopos);
      var col = it.region ? D.regionColor : it.color;
      return '<li role="option" id="mg-r' + i + '"><button type="button" tabindex="-1" data-id="' + esc(it.id) + '"><span class="mg-ico" style="--c:' + col + '"></span><span>' + esc(title) + "<small>" + esc(sub) + "</small></span></button></li>";
    }).join("") + (total > 15 ? '<li class="mg-empty">+ ' + num(total - 15) + " " + esc(T.more) + "</li>" : "") : '<li class="mg-empty">' + esc(T.noresults) + "</li>";
    list.hidden = false;
  }
  function pick(id) { list.hidden = true; input.blur(); reveal(id); }
  input.addEventListener("input", search);
  input.addEventListener("focus", function () { if (input.value.trim().length > 1) search(); });
  input.addEventListener("keydown", function (e) {
    var lis = list.querySelectorAll("li[role=option]");
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault(); if (!lis.length) return;
      sel = (sel + (e.key === "ArrowDown" ? 1 : -1) + lis.length) % lis.length;
      lis.forEach(function (li, i) { li.setAttribute("aria-selected", String(i === sel)); });
      input.setAttribute("aria-activedescendant", "mg-r" + sel);
    } else if (e.key === "Enter") {
      e.preventDefault(); var h = hits[sel > -1 ? sel : 0]; if (h && !list.hidden) pick(h.id);
    } else if (e.key === "Escape") { list.hidden = true; }
  });
  list.addEventListener("mousedown", function (e) { var b = e.target.closest("button[data-id]"); if (b) { e.preventDefault(); pick(b.dataset.id); } });
  document.addEventListener("click", function (e) { if (!e.target.closest(".mg-search")) list.hidden = true; });

  /* --- mobilný panel --- */
  var openBtn = root.querySelector(".mg-open");
  function closePanel() { root.classList.remove("is-panel"); openBtn.setAttribute("aria-expanded", "false"); }
  openBtn.onclick = function () { root.classList.add("is-panel"); openBtn.setAttribute("aria-expanded", "true"); };
  root.querySelector(".mg-close").onclick = closePanel;
  map.on("click", closePanel);

  /* --- súradnice --- */
  var hud = root.querySelector("[data-coords]");
  function setHud(p) { hud.textContent = "X " + p.lng.toFixed(1) + " · Y " + p.lat.toFixed(1); }
  map.on("mousemove", function (e) { setHud(e.latlng); });
  setHud(map.getCenter());

  window.addEventListener("resize", function () { fitHeight(); map.invalidateSize(); });
  window.addEventListener("hashchange", function () { var h = decodeURIComponent(location.hash.slice(1)); if (byId[h]) reveal(h); });
  render();

  /* --- miesta z GTADB (načítajú sa po mape) --- */
  var loading = root.querySelector("[data-loading]");
  fetch(D.places).then(function (r) { return r.json(); }).then(function (rows) {
    rows.forEach(function (r) {
      var p = { id: r[0], ig: r[1], x: r[2], y: r[3], rl: r[4], tags: r[5], igV: r[6], rlV: r[7], rlLL: r[8] === 1, color: "#" + r[9] };
      p.ll = p.x === null ? null : [p.y, p.x];
      p.types = typesOf(p);
      p.find = norm(p.id + "\n" + p.ig + "\n" + p.rl + "\n" + p.tags.join("\n"));
      addPlace(p); items.push(p); places.push(p); byId[p.id] = p;
    });
    render();
    loading.hidden = true;
    root.dataset.ready = "1";
    var h = decodeURIComponent(location.hash.slice(1));
    if (byId[h]) { var it = byId[h]; if (it.ll) map.setView(it.ll, it.region ? 2 : 4, { animate: false }); openItem(it); }
  }).catch(function () { loading.hidden = true; });
})();
