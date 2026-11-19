/* Mapa Leonidy (gta6rp.sk/mapa/): filtre, vyhľadávanie, „nájdené“, odkazy na miesta. Leaflet 1.9.4. */
(function () {
  "use strict";
  var root = document.querySelector("[data-mg]");
  var dataEl = document.getElementById("mg-data");
  if (!root || !dataEl || !window.L) return;
  var D = JSON.parse(dataEl.textContent), T = D.ui, L = window.L;
  var KEY = "gta6rp_map_";
  function load(k) { try { return JSON.parse(localStorage.getItem(KEY + k)) || []; } catch (e) { return []; } }
  function save(k, v) { try { localStorage.setItem(KEY + k, JSON.stringify(v)); } catch (e) {} }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function norm(s) { return String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }

  var hidden = new Set(load("hidden")), found = new Set(load("found"));
  var hideFound = load("hidefound") === true;
  var cats = {}; D.cats.forEach(function (c) { cats[c.id] = c; });
  var byId = {}, regions = {};
  D.markers.forEach(function (m) { byId[m.id] = m; if (m.cat === "oblasti") regions[m.id] = m.t; });

  /* --- výška mapy podľa hlavičky --- */
  function fitHeight() { root.style.setProperty("--top", Math.round(root.getBoundingClientRect().top + window.scrollY) + "px"); }
  fitHeight();

  /* --- mapa --- */
  var W = D.w, H = D.h, bounds = [[0, 0], [H, W]];
  function ll(m) { return [H - m.y, m.x]; }
  var map = L.map(root.querySelector(".mg-leaflet"), {
    crs: L.CRS.Simple, minZoom: -2, maxZoom: 3, zoomSnap: 0.25, zoomDelta: 0.5, wheelPxPerZoomLevel: 90,
    attributionControl: false, zoomControl: false, maxBounds: [[-H * 0.25, -W * 0.25], [H * 1.25, W * 1.25]], maxBoundsViscosity: 0.8
  });
  L.imageOverlay(D.base, bounds, { alt: "" }).addTo(map);
  L.control.zoom({ position: "topright", zoomInTitle: T.zoomin, zoomOutTitle: T.zoomout }).addTo(map);
  var Fit = L.Control.extend({
    options: { position: "topright" },
    onAdd: function () {
      var b = L.DomUtil.create("button", "mg-fit");
      b.type = "button"; b.title = T.fit; b.setAttribute("aria-label", T.fit);
      b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3H5a2 2 0 0 0-2 2v3M21 8V5a2 2 0 0 0-2-2h-3M3 16v3a2 2 0 0 0 2 2h3M16 21h3a2 2 0 0 0 2-2v-3"/></svg>';
      L.DomEvent.disableClickPropagation(b);
      L.DomEvent.on(b, "click", function () { map.closePopup(); map.flyToBounds(bounds, { duration: 0.6 }); });
      return b;
    }
  });
  new Fit().addTo(map);
  function zoomClass() {
    var z = map.getZoom(), el = map.getContainer();
    el.classList.toggle("mg-far", z < 0.75);
  }
  map.on("zoomend", zoomClass);
  function fitAll() { map.invalidateSize(); map.fitBounds(bounds, { padding: [10, 10], animate: false }); }
  fitAll();
  zoomClass();

  /* --- značky --- */
  var layers = {};
  function iconFor(m) {
    var c = cats[m.cat];
    if (m.cat === "oblasti") {
      return L.divIcon({ className: "mg-region", iconSize: [0, 0],
        html: '<div class="mg-region-pin"><span class="mg-region-dot"></span><span class="mg-region-name">' + esc(m.t) + "</span></div>" });
    }
    return L.divIcon({ className: "mg-mk", iconSize: [34, 34], iconAnchor: [17, 40], popupAnchor: [0, -38],
      html: '<div class="mg-pin" style="--c:' + c.color + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + c.icon + "</svg></div>" });
  }
  function popupHtml(m) {
    var c = cats[m.cat], isF = found.has(m.id);
    var meta = "";
    if (m.region && m.cat !== "oblasti" && regions[m.region]) meta += "<span>" + esc(T.region) + ": " + esc(regions[m.region]) + "</span>";
    if (m.cat !== "oblasti") meta += "<span>" + esc(T.approx) + "</span>";
    return '<div class="mg-pop"><span class="mg-pop-cat" style="--c:' + c.color + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + c.icon + "</svg>" + esc(c.name) + "</span>" +
      "<h3>" + esc(m.t) + "</h3><p>" + esc(m.d) + "</p>" + (meta ? '<div class="mg-pop-meta">' + meta + "</div>" : "") +
      '<div class="mg-pop-actions"><button type="button" data-act="found" class="' + (isF ? "is-found" : "") + '">' + (isF ? T.unmark : T.mark) + "</button>" +
      '<button type="button" data-act="copy">' + esc(T.copy) + "</button></div></div>";
  }
  D.markers.forEach(function (m) {
    var mk = L.marker(ll(m), { icon: iconFor(m), title: m.t, alt: m.t, riseOnHover: true, keyboard: true });
    if (m.cat === "oblasti") mk.setZIndexOffset(1000);
    mk.bindPopup(function () { return popupHtml(m); }, { maxWidth: 320, minWidth: 250, autoPanPadding: [40, 40] });
    mk.on("popupopen", function (e) {
      setActive(m.id);
      history.replaceState(null, "", "#" + m.id);
      bindPopup(mk, m);
    });
    mk.on("popupclose", function () { setActive(null); if (location.hash === "#" + m.id) history.replaceState(null, "", location.pathname + location.search); });
    mk._mgId = m.id;
    layers[m.id] = mk;
  });
  function bindPopup(mk, m) {
    var el = mk.getPopup().getElement(); if (!el) return;
    el.querySelector('[data-act="found"]').onclick = function () { toggleFound(m.id); mk.setPopupContent(popupHtml(m)); bindPopup(mk, m); };
    el.querySelector('[data-act="copy"]').onclick = function (ev) {
      var url = location.origin + location.pathname + "#" + m.id, b = ev.currentTarget;
      var done = function () { b.textContent = T.copied; setTimeout(function () { b.textContent = T.copy; }, 1500); };
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, done); else done();
    };
  }
  var activeId = null;
  function setActive(id) {
    if (activeId && layers[activeId] && layers[activeId]._icon) layers[activeId]._icon.classList.remove("is-active");
    activeId = id;
    if (id && layers[id]._icon) layers[id]._icon.classList.add("is-active");
  }

  /* --- filtre --- */
  var catBtns = root.querySelectorAll(".mg-cat");
  function visible(m) { return !hidden.has(m.cat) && !(hideFound && found.has(m.id)); }
  function render() {
    D.markers.forEach(function (m) {
      var mk = layers[m.id], on = visible(m);
      if (on && !map.hasLayer(mk)) mk.addTo(map);
      if (!on && map.hasLayer(mk)) mk.remove();
      if (mk._icon) mk._icon.classList.toggle("is-found", found.has(m.id));
    });
    catBtns.forEach(function (b) { b.setAttribute("aria-pressed", String(!hidden.has(b.dataset.cat))); });
    var n = found.size;
    root.querySelector("[data-found]").textContent = n;
    root.querySelector("[data-bar]").style.width = (n / D.markers.length * 100) + "%";
    root.querySelector("[data-hidefound]").checked = hideFound;
  }
  map.on("layeradd", function (e) {
    var l = e.layer, id = l._mgId;
    if (id && l._icon) { l._icon.classList.toggle("is-found", found.has(id)); l._icon.classList.toggle("is-active", id === activeId); }
  });
  catBtns.forEach(function (b) {
    b.addEventListener("click", function () {
      var c = b.dataset.cat; hidden.has(c) ? hidden.delete(c) : hidden.add(c);
      save("hidden", Array.from(hidden)); render();
    });
  });
  root.querySelector("[data-all]").onclick = function () { hidden.clear(); save("hidden", []); render(); };
  root.querySelector("[data-none]").onclick = function () { D.cats.forEach(function (c) { hidden.add(c.id); }); save("hidden", Array.from(hidden)); map.closePopup(); render(); };
  root.querySelector("[data-hidefound]").onchange = function (e) { hideFound = e.target.checked; save("hidefound", hideFound); render(); };
  root.querySelector("[data-reset]").onclick = function () { found.clear(); save("found", []); render(); };
  function toggleFound(id) { found.has(id) ? found.delete(id) : found.add(id); save("found", Array.from(found)); render(); }

  /* --- otvorenie značky (vyhľadávanie, odkaz #id) --- */
  function openMarker(id, fly) {
    var m = byId[id]; if (!m) return;
    if (hidden.has(m.cat)) { hidden.delete(m.cat); save("hidden", Array.from(hidden)); }
    if (hideFound && found.has(id)) { hideFound = false; save("hidefound", false); }
    render();
    var mk = layers[id], z = Math.max(map.getZoom(), 1);
    closePanel();
    if (fly) map.flyTo(ll(m), z, { duration: 0.7 }); else map.setView(ll(m), z, { animate: false });
    setTimeout(function () { mk.openPopup(); }, fly ? 720 : 0);
  }

  /* --- vyhľadávanie --- */
  var input = root.querySelector(".mg-search input"), list = root.querySelector(".mg-results"), sel = -1, hits = [];
  function search() {
    var q = norm(input.value.trim());
    if (!q) { list.hidden = true; list.innerHTML = ""; return; }
    hits = D.markers.filter(function (m) { return norm(m.t + " " + (regions[m.region] || "")).indexOf(q) > -1 || norm(m.d).indexOf(q) > -1; })
      .sort(function (a, b) { return (norm(a.t).indexOf(q) === -1) - (norm(b.t).indexOf(q) === -1); }).slice(0, 12);
    sel = -1;
    list.innerHTML = hits.length ? hits.map(function (m, i) {
      var c = cats[m.cat];
      return '<li role="option" id="mg-r' + i + '"><button type="button" tabindex="-1" data-id="' + m.id + '"><span class="mg-ico" style="--c:' + c.color + '"><svg viewBox="0 0 24 24">' + c.icon + "</svg></span><span>" + esc(m.t) + "<small>" + esc(c.name) + (m.region && m.cat !== "oblasti" ? " · " + esc(regions[m.region]) : "") + "</small></span></button></li>";
    }).join("") : '<li class="mg-empty">' + esc(T.noresults) + "</li>";
    list.hidden = false;
  }
  function pick(id) { list.hidden = true; input.blur(); openMarker(id, true); }
  input.addEventListener("input", search);
  input.addEventListener("focus", search);
  input.addEventListener("keydown", function (e) {
    var items = list.querySelectorAll("li[role=option]");
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault(); if (!items.length) return;
      sel = (sel + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
      items.forEach(function (li, i) { li.setAttribute("aria-selected", String(i === sel)); });
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

  /* --- súradnice (HUD), režim ?edit na zisťovanie polohy --- */
  var hud = root.querySelector("[data-coords]");
  function setHud(p) { hud.textContent = "X " + Math.round(p.lng) + " · Y " + Math.round(H - p.lat); }
  map.on("mousemove", function (e) { setHud(e.latlng); });
  setHud({ lng: W / 2, lat: H / 2 });
  if (/[?&]edit\b/.test(location.search)) {
    map.on("click", function (e) {
      var x = Math.round(e.latlng.lng * 10) / 10, y = Math.round((H - e.latlng.lat) * 10) / 10;
      L.popup().setLatLng(e.latlng).setContent('<div class="mg-pop-edit">' + esc(T.edit) + ": x " + x + ", y " + y + "</div>").openOn(map);
      if (navigator.clipboard) navigator.clipboard.writeText(x + ", " + y).catch(function () {});
    });
  }

  render();
  window.addEventListener("resize", function () { fitHeight(); map.invalidateSize(); });
  var id = decodeURIComponent(location.hash.slice(1));
  if (byId[id]) openMarker(id, false);
  window.addEventListener("hashchange", function () { var h = decodeURIComponent(location.hash.slice(1)); if (byId[h]) openMarker(h, true); });
})();
