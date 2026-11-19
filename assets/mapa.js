/* Mapa Leonidy (gta6rp.sk/mapa/). Podklad a miesta: GTADB.org a prispievatelia, CC BY 4.0. Leaflet 1.9.4. */
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

  var hidden = new Set(load("hidden", ["ostatne"])), found = new Set(load("found", []));
  var hideFound = load("hidefound", false) === true, onlyEnter = load("enter", false) === true;
  var cats = {}; D.cats.forEach(function (c) { cats[c.id] = c; });
  var items = [], byId = {};

  /* --- výška mapy podľa hlavičky --- */
  function fitHeight() { root.style.setProperty("--top", Math.round(root.getBoundingClientRect().top + window.scrollY) + "px"); }
  fitHeight();

  /* --- mapa: herné súradnice x, y (ako GTADB), zoom 0 = 1024 px na celý svet --- */
  var CRS = L.extend({}, L.CRS.Simple, { transformation: new L.Transformation(1 / 32, 512, -1 / 32, 512) });
  var B = L.latLngBounds(D.bounds);
  var map = L.map(root.querySelector(".mg-leaflet"), {
    crs: CRS, minZoom: 0, maxZoom: 7, zoomSnap: 0.25, zoomDelta: 0.5, wheelPxPerZoomLevel: 90,
    zoomControl: false, preferCanvas: true, maxBounds: B.pad(0.15), maxBoundsViscosity: 0.8
  });
  map.attributionControl.setPrefix(false);
  L.tileLayer(D.tiles, {
    bounds: B, minNativeZoom: 0, maxNativeZoom: 5, noWrap: true, keepBuffer: 3,
    attribution: '<a href="' + D.gtadb + '" target="_blank" rel="noopener">GTADB.org</a> (CC BY 4.0)'
  }).addTo(map);
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

  /* --- popup --- */
  function regionHtml(r) {
    return '<div class="mg-pop"><span class="mg-pop-cat" style="--c:' + cats.oblasti.color + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + cats.oblasti.icon + "</svg>" + esc(cats.oblasti.name) + "</span>" +
      "<h3>" + esc(r.t) + "</h3><p>" + esc(r.d) + "</p>" +
      '<div class="mg-pop-ideas"><small>' + esc(T.ideas) + "</small><div>" + r.rp.map(function (x) { return "<span>" + esc(x) + "</span>"; }).join("") + "</div></div>" +
      actions(r.id) + '<a class="mg-pop-cta" href="' + T.builder + '">' + esc(T.cta) + " ↗</a></div>";
  }
  function placeHtml(p) {
    var c = cats[p.cat], title = p.name || p.rl || p.addr || "?";
    var meta = "";
    if (p.enter) meta += '<span class="is-enter">' + esc(T.enterable) + "</span>";
    if (!p.name) meta += "<span>" + esc(T.nameless) + "</span>";
    return '<div class="mg-pop">' +
      (p.photo ? '<figure class="mg-pop-photo"><img loading="lazy" alt="' + esc(T.photo + ": " + title) + '" src="' + D.photos + encodeURIComponent(p.id + ",ig") + ".jpg?v=" + p.photo + '" onerror="this.parentNode.remove()"><figcaption>' + esc(T.photo) + " · GTADB.org</figcaption></figure>" : "") +
      '<span class="mg-pop-cat" style="--c:' + c.color + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + c.icon + "</svg>" + esc(c.name) + "</span>" +
      "<h3>" + esc(title) + "</h3>" + (p.addr ? '<p class="mg-pop-addr">' + esc(p.addr) + "</p>" : "") +
      (p.rl ? '<p class="mg-pop-rl"><small>' + esc(T.real) + "</small>" + esc(p.rl) + "</p>" : "") +
      (meta ? '<div class="mg-pop-meta">' + meta + "</div>" : "") + actions(p.id) +
      '<a class="mg-pop-src" href="' + D.gtadb + "#VI," + Math.round(p.x) + "," + Math.round(p.y) + ',5" target="_blank" rel="noopener">GTADB.org ↗</a></div>';
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
    if (view) map.setView(it.ll, Math.max(map.getZoom(), it.region ? 2 : 4), { animate: view === "fly" });
    popup.setLatLng(it.ll).setContent(it.region ? regionHtml(it) : placeHtml(it)).openOn(map);
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
  var groups = {}; D.cats.forEach(function (c) { groups[c.id] = L.layerGroup(); });
  var ring = L.circleMarker([0, 0], { radius: 12, color: "#fff", weight: 3, fill: false, interactive: false });
  function radius() { var z = map.getZoom(); return z < 1.5 ? 2.6 : z < 2.5 ? 3.6 : z < 3.5 ? 5 : z < 5 ? 6.5 : 8; }
  function styleFor(it) {
    var f = found.has(it.id);
    return { radius: radius(), color: "#0b0a14", weight: 1.2, fillColor: cats[it.cat].color, fillOpacity: f ? 0.35 : 0.95, opacity: f ? 0.5 : 1 };
  }
  function highlight() {
    if (current && !current.region) { ring.setLatLng(current.ll).setRadius(radius() + 5); if (!map.hasLayer(ring)) ring.addTo(map); }
    else if (map.hasLayer(ring)) ring.remove();
    D.regions.forEach(function (r) { var el = r.marker.getElement(); if (el) el.classList.toggle("is-active", current === r); });
  }
  var tip = L.tooltip({ direction: "top", offset: [0, -6], className: "mg-tip", opacity: 1 });
  function addPlace(p) {
    var m = L.circleMarker(p.ll, styleFor(p));
    m.on("click", function (e) { L.DomEvent.stop(e); closePanel(); openItem(p); });
    m.on("mouseover", function () { tip.setLatLng(p.ll).setContent(esc(p.name || p.rl || p.addr || "?")); map.openTooltip(tip); });
    m.on("mouseout", function () { map.closeTooltip(tip); });
    p.marker = m;
  }
  D.regions.forEach(function (r) {
    r.region = true; r.cat = "oblasti"; r.ll = [r.y, r.x]; byId[r.id] = r; items.push(r);
    r.marker = L.marker(r.ll, {
      keyboard: true, title: r.t, riseOnHover: true, zIndexOffset: 1000,
      icon: L.divIcon({ className: "mg-region", iconSize: [0, 0], html: '<div class="mg-region-pin"><span class="mg-region-dot"></span><span class="mg-region-name">' + esc(r.t) + "</span></div>" })
    }).on("click", function () { closePanel(); openItem(r); });
    groups.oblasti.addLayer(r.marker);
  });

  /* --- filtre --- */
  var catBtns = root.querySelectorAll(".mg-cat");
  function visible(it) { return !(hideFound && found.has(it.id)) && !(onlyEnter && !it.region && !it.enter); }
  function render() {
    D.cats.forEach(function (c) {
      var g = groups[c.id], on = !hidden.has(c.id);
      if (on && !map.hasLayer(g)) g.addTo(map);
      if (!on && map.hasLayer(g)) g.remove();
    });
    items.forEach(function (it) {
      var g = groups[it.cat], v = visible(it), has = g.hasLayer(it.marker);
      if (v && !has) g.addLayer(it.marker); else if (!v && has) g.removeLayer(it.marker);
      if (!it.region) it.marker.setStyle(styleFor(it));
      else { var el = it.marker.getElement(); if (el) el.classList.toggle("is-found", found.has(it.id)); }
    });
    catBtns.forEach(function (b) { b.setAttribute("aria-pressed", String(!hidden.has(b.dataset.cat))); });
    var n = 0; found.forEach(function (id) { if (byId[id]) n++; });
    root.querySelector("[data-found]").textContent = num(n);
    root.querySelector("[data-bar]").style.width = (n / Math.max(items.length, 1) * 100) + "%";
    root.querySelector("[data-hidefound]").checked = hideFound;
    root.querySelector("[data-enter]").checked = onlyEnter;
    highlight();
  }
  map.on("zoomend", function () { var r = radius(); items.forEach(function (it) { if (!it.region) it.marker.setRadius(r); }); highlight(); map.getContainer().classList.toggle("mg-far", map.getZoom() < 1.5); });
  catBtns.forEach(function (b) {
    b.addEventListener("click", function () {
      var c = b.dataset.cat; hidden.has(c) ? hidden.delete(c) : hidden.add(c);
      save("hidden", Array.from(hidden)); render();
    });
  });
  root.querySelector("[data-all]").onclick = function () { hidden.clear(); save("hidden", []); render(); };
  root.querySelector("[data-none]").onclick = function () { D.cats.forEach(function (c) { hidden.add(c.id); }); save("hidden", Array.from(hidden)); map.closePopup(); render(); };
  root.querySelector("[data-hidefound]").onchange = function (e) { hideFound = e.target.checked; save("hidefound", hideFound); render(); };
  root.querySelector("[data-enter]").onchange = function (e) { onlyEnter = e.target.checked; save("enter", onlyEnter); render(); };
  root.querySelector("[data-reset]").onclick = function () { found.clear(); save("found", []); render(); };
  function toggleFound(id) { found.has(id) ? found.delete(id) : found.add(id); save("found", Array.from(found)); render(); }

  function reveal(id) {
    var it = byId[id]; if (!it) return;
    if (hidden.has(it.cat)) { hidden.delete(it.cat); save("hidden", Array.from(hidden)); }
    if (hideFound && found.has(id)) { hideFound = false; save("hidefound", false); }
    if (onlyEnter && !it.region && !it.enter) { onlyEnter = false; save("enter", false); }
    render(); closePanel(); openItem(it, "fly");
  }

  /* --- vyhľadávanie --- */
  var input = root.querySelector(".mg-search input"), list = root.querySelector(".mg-results"), sel = -1, hits = [];
  function search() {
    var q = norm(input.value.trim());
    if (q.length < 2) { list.hidden = true; list.innerHTML = ""; return; }
    hits = [];
    for (var i = 0; i < items.length && hits.length < 60; i++) {
      var it = items[i], s = it.find || (it.find = norm([it.t || it.name, it.rl, it.addr].join(" ")));
      if (s.indexOf(q) > -1) hits.push(it);
    }
    hits.sort(function (a, b) {
      var an = norm(a.t || a.name || ""), bn = norm(b.t || b.name || "");
      return (b.region ? 2 : 0) - (a.region ? 2 : 0) || (an.indexOf(q) === 0 ? -1 : an.indexOf(q) > -1 ? 0 : 1) - (bn.indexOf(q) === 0 ? -1 : bn.indexOf(q) > -1 ? 0 : 1);
    });
    hits = hits.slice(0, 15); sel = -1;
    list.innerHTML = hits.length ? hits.map(function (it, i) {
      var c = cats[it.cat], title = it.t || it.name || it.rl || it.addr;
      var sub = it.region ? c.name : c.name + (it.addr ? " · " + it.addr : "");
      return '<li role="option" id="mg-r' + i + '"><button type="button" tabindex="-1" data-id="' + it.id + '"><span class="mg-ico" style="--c:' + c.color + '"><svg viewBox="0 0 24 24">' + c.icon + "</svg></span><span>" + esc(title) + "<small>" + esc(sub) + "</small></span></button></li>";
    }).join("") : '<li class="mg-empty">' + esc(T.noresults) + "</li>";
    list.hidden = false;
  }
  function pick(id) { list.hidden = true; input.blur(); reveal(id); }
  input.addEventListener("input", search);
  input.addEventListener("focus", search);
  input.addEventListener("keydown", function (e) {
    var lis = list.querySelectorAll("li[role=option]");
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault(); if (!lis.length) return;
      sel = (sel + (e.key === "ArrowDown" ? 1 : -1) + lis.length) % lis.length;
      lis.forEach(function (li, i) { li.setAttribute("aria-selected", String(i === sel)); });
      input.setAttribute("aria-activedescendant", "mg-r" + sel);
    } else if (e.key === "Enter") {
      e.preventDefault(); var h = hits[sel > -1 ? sel : 0]; if (h) pick(h.id);
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
  function setHud(p) { hud.textContent = "X " + Math.round(p.lng) + " · Y " + Math.round(p.lat); }
  map.on("mousemove", function (e) { setHud(e.latlng); });
  setHud(map.getCenter());
  map.on("moveend", function () { if (!matchMedia("(hover:hover)").matches) setHud(map.getCenter()); });

  window.addEventListener("resize", function () { fitHeight(); map.invalidateSize(); });
  window.addEventListener("hashchange", function () { var h = decodeURIComponent(location.hash.slice(1)); if (byId[h]) reveal(h); });
  render();

  /* --- miesta z GTADB (načítajú sa po mape) --- */
  var loading = root.querySelector("[data-loading]");
  fetch(D.places).then(function (r) { return r.json(); }).then(function (rows) {
    rows.forEach(function (r) {
      var p = { id: r[0], name: r[1], addr: r[2], cat: cats[r[3]] ? r[3] : "ostatne", x: r[4], y: r[5], rl: r[6], photo: r[7], enter: r[8] === 1 };
      p.ll = [p.y, p.x]; addPlace(p); items.push(p); byId[p.id] = p;
    });
    render();
    loading.hidden = true;
    var h = decodeURIComponent(location.hash.slice(1));
    if (byId[h]) { var it = byId[h]; map.setView(it.ll, it.region ? 2 : 4, { animate: false }); openItem(it); }
  }).catch(function () { loading.hidden = true; });
})();
