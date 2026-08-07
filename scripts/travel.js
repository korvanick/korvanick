// ============================================================================
//  TRAVEL MAP
//
//  Markers are plain DOM elements (L.divIcon), not canvas or SVG vectors.
//  Vector layers share one renderer surface that Leaflet repaints on its own
//  schedule, so changing their geometry after a zoom means racing that
//  schedule. DOM markers are painted individually and Leaflet repositions
//  them itself during the zoom animation.
//
//  Nothing about how the map LOOKS lives here. Dot size comes from a zoom
//  bucket class on the map container, dot colour from a type class on the dot.
//  Both are defined in travel.css.
//
//  travel.json entries:
//    name       required   "Helsinki, Finland"
//    coords     required   [lat, lon]
//    type       required   been | future
//    message    optional   popup text
//    highlight  optional   true -> the dot carries a card
//    rank       optional   1 = shown first when cards compete for space.
//                          A highlight WITHOUT a rank never shows on its own:
//                          its card appears only while the dot is hovered.
//                          That second tier is how the map carries more
//                          highlights than there is room to display at once.
//    photo      optional   "/images/gallery/foo.jpg" -> thumbnail on the card
// ============================================================================

// --- Opening view. Swap INITIAL_VIEW for WORLD_VIEW to open on the whole map
//     instead of home. A #slug in the URL overrides either one.
const WORLD_VIEW   = { center: [30, 0], zoom: 2 };
const INITIAL_VIEW = { center: [47.6062, -122.3321], zoom: 12 };

// Two types, deliberately. Only 'been' feeds the headline counts -- adding
// somewhere to the future list must never make the map claim more travel than
// has actually happened.
const TYPES = ['been', 'future'];

// A city whose message is longer than this gets a bigger dot: 76% of visited
// cities have SOME text, so mere presence marks nearly everything and says
// nothing. Length is the honest proxy for "there is a story here" -- at 90 it
// picks out about a third of them. Lower it to mark more.
const NOTE_MIN_CHARS = 90;
const TYPE_NAMES = { been: "Places I've been", future: 'Future Adventures' };

const WORLD = L.latLngBounds([-85, -180], [85, 180]);

const map = L.map('map', {
    maxBounds: WORLD,
    maxBoundsViscosity: 1.0     // the edge is a wall, not a rubber band
}).setView(INITIAL_VIEW.center, INITIAL_VIEW.zoom);

// CARTO's basemap, in whichever version sits with the current site theme:
// dark_all under the default dark theme, light_all (Positron) when the header
// switch is flipped. Same tile scheme and the same attribution either way, so
// only the URL changes.
//
// The dot palette in travel.css follows the same switch -- the "there is
// something written here" outline is near-white on the dark map and near-black
// on the light one, because on a light basemap a white ring is invisible.
//
// To pin the map to one version regardless of theme, replace basemapUrl()'s
// body with a single return.
function basemapUrl() {
    const light = document.documentElement.getAttribute('data-theme') === 'light';
    return `https://{s}.basemaps.cartocdn.com/${light ? 'light_all' : 'dark_all'}/{z}/{x}/{y}{r}.png`;
}

const basemap = L.tileLayer(basemapUrl(), {
    subdomains: 'abcd',
    maxZoom: 20,
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
}).addTo(map);

// Watch <html> rather than listening to the header button: the theme can also
// be set by the inline <head> script on load, and this way travel.js needs to
// know nothing about how the switch is wired. setUrl keeps the tiles already
// on screen until the replacements have loaded, so the swap doesn't flash.
new MutationObserver(() => basemap.setUrl(basemapUrl()))
    .observe(document.documentElement, { attributeFilter: ['data-theme'] });

// How far out you can zoom is measured from the container rather than
// hardcoded, and recalculated when the window changes.
//
// The whole world is 256 * 2^zoom pixels square, so this picks the largest
// zoom at which it still fits the container's HEIGHT -- you can always see
// pole to pole. On a wide monitor that leaves the world narrower than the
// window, which is why the tiles repeat sideways: filling the sides with more
// map reads better than dark bars. Measuring width instead would keep a single
// world but crop the poles on an ultrawide.
function fitMinZoom() {
    map.setMinZoom(Math.max(1, Math.floor(Math.log2(map.getSize().y / 256))));
}
map.on('resize', fitMinZoom);
fitMinZoom();

// --------------------------------------------------------------------------- gallery
//
//  How many photos exist for each city, so a card can offer the way through to
//  them. Read from gallery.json, which already records a location per photo --
//  nothing is written twice and nothing needs maintaining here.
//
//  Best effort: if the file is missing the map still works, the cards just
//  lose their link.

// Photos from a neighbouring city count as this city's: Bellevue and Lake
// Forest Park are Seattle for anyone browsing pictures. 20 km groups those and
// the Twin Cities suburbs without merging places that deserve to stay apart --
// at 30 km The Hague starts absorbing Rotterdam. gallery.js uses the same
// number; change both together.
const NEARBY_KM = 20;

const photoCount = new Map();       // exact city name -> photos taken there
const nearbyCount = new Map();      // city name -> photos there or within NEARBY_KM
const photoHost = new Map();        // city name -> the city whose slug the link should use

function kmApart(a, b) {
    const p1 = a[0] * Math.PI / 180, p2 = b[0] * Math.PI / 180;
    const dp = (b[0] - a[0]) * Math.PI / 180, dl = (b[1] - a[1]) * Math.PI / 180;
    const x = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
    return 6371 * 2 * Math.asin(Math.sqrt(x));
}

// A city can qualify for the camera on a NEIGHBOUR's photos -- Bloomington has
// none of its own and borrows the Twin Cities'. The count and the link then have
// to disagree, because /gallery#city=bloomington-minnesota filters to nothing.
// So the host is recorded alongside the count: whichever city inside the radius
// actually holds the most photos is the one the link points at. A city with its
// own photos is always its own host.
function countNearby(cities) {
    cities.forEach(({ name, coords }) => {
        let total = 0;
        let host = null, hostCount = 0;
        cities.forEach(other => {
            const n = photoCount.get(other.name);
            if (n && kmApart(coords, other.coords) <= NEARBY_KM) {
                total += n;
                if (n > hostCount) { host = other.name; hostCount = n; }
            }
        });
        if (total) {
            nearbyCount.set(name, total);
            photoHost.set(name, photoCount.get(name) ? name : host);
        }
    });
}

function loadPhotoCounts() {
    return fetch('/data/gallery.json')
        .then(r => (r.ok ? r.json() : []))
        .then(list => list.forEach(p => {
            if (p.location) photoCount.set(p.location, (photoCount.get(p.location) || 0) + 1);
        }))
        .catch(() => {});
}

// ----------------------------------------------------------------------------- helpers

const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[c]));

// "Reykjavík, Iceland" -> "reykjavik-iceland", for #deep-links
const slugify = (s) => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

// Dot size by zoom. Three buckets, matching .dot-z0 ... .dot-z2 in travel.css,
// which is where the actual pixel sizes live.
function zoomBucket(z) {
    if (z <= 5)  return 'dot-z0';   // world and continent
    if (z <= 11) return 'dot-z1';   // country and region
    return 'dot-z2';                // city and street
}

const BUCKETS = ['dot-z0', 'dot-z1', 'dot-z2'];
let currentBucket = null;

function applyZoomBucket() {
    const bucket = zoomBucket(map.getZoom());
    if (bucket === currentBucket) return;
    currentBucket = bucket;
    const el = map.getContainer();
    el.classList.remove(...BUCKETS);
    el.classList.add(bucket);
}

// The wrapper is a zero-size box sitting exactly on the coordinate; the inner
// span is centred on it with a CSS transform. Keeping the wrapper at 0x0 is
// what lets CSS change the dot's size without JavaScript having to recompute
// an icon anchor to keep it centred.
function dotIcon(type, highlight, hasNote) {
    const kind = TYPES.includes(type) ? type : 'been';
    const extra = (highlight ? ' is-highlight' : '') + (hasNote ? ' has-note' : '');
    return L.divIcon({
        className: 'travel-dot-wrapper',
        html: `<span class="travel-dot type-${kind}${extra}"></span>`,
        iconSize: [0, 0],
        iconAnchor: [0, 0],
        popupAnchor: [0, -10]
    });
}

// One card, two places. The always-on card on a highlight and the box you get
// from clicking any dot are the same component with the same content: photo,
// name, and the city's message. Nothing is written twice.
// A card shows the gallery's small thumbnail; the link opens the full-size
// photo in the gallery's lightbox. Both are derived from the one `photo` path
// in travel.json, matching how gallery.js builds its own grid.
function thumbUrl(src) {
    return src.replace(/\/([^/]+)$/, '/thumbs/$1');
}
function cardHtml(loc) {
    const body = (loc.message || '').trim();
    // A camera glyph rather than a count in words: it rides on the end of the
    // title without lengthening it, so the name still fits the line. The count
    // lives in the tooltip for anyone who wants it. Both cards carry it -- the
    // one you hover and the one you click are the same card.
    const count = nearbyCount.get(loc.name) || 0;
    const host = photoHost.get(loc.name) || loc.name;
    const label = host === loc.name
        ? `${count} photo${count === 1 ? '' : 's'} from ${loc.name}`
        : `${count} photo${count === 1 ? '' : 's'} from around ${loc.name}, in ${host}`;
    const link = count
        ? `&nbsp;<a class="card-photos" href="/gallery#city=${slugify(host)}" ` +
          `aria-label="${escapeHtml(label)}">` +
          `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3 7.5 5H4a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-3.5L15 3H9Zm3 5.5A4.5 4.5 0 1 1 7.5 13 4.5 4.5 0 0 1 12 8.5Zm0 2A2.5 2.5 0 1 0 14.5 13 2.5 2.5 0 0 0 12 10.5Z"/></svg>` +
          `</a>`
        : '';
    // The thumbnail opens the full-size photo over the map. Staying on the page
    // keeps you where you were: the gallery is a separate trip, and the camera
    // glyph beside the name is the way to take it.
    const photo = loc.photo
        ? `<a class="card-photo" href="${escapeHtml(loc.photo)}" ` +
          `data-full="${escapeHtml(loc.photo)}" data-caption="${escapeHtml(loc.name)}">` +
          `<img data-src="${escapeHtml(thumbUrl(loc.photo))}" alt=""></a>`
        : '';
    return `<div class="travel-card">${photo}` +
           `<b class="card-title">${escapeHtml(loc.name)}</b>${link}` +
           (body ? `<p class="card-text">${escapeHtml(body)}</p>` : '') +
           `</div>`;
}

// ----------------------------------------------------------------------------- state

const entries = [];                          // every city, in load order
const layers = {};                           // type -> L.layerGroup
const shown = { been: true, future: true };
// No hover on a phone, so cards that appear on their own would just be in the
// way: small screens start with auto-display off and reach cards by tapping a
// dot. The breakpoint matches the one the panel collapses at.
const SMALL_SCREEN = window.matchMedia('(max-width: 820px)').matches;
let labelsOn = !SMALL_SCREEN;
const labelled = [];                         // highlights, sorted by rank below

TYPES.forEach(t => { layers[t] = L.layerGroup(); });

// --------------------------------------------------------------------------- labels
//
//  Always-on cards are the one thing here that can genuinely clutter the map,
//  so they are laid out rather than just drawn: walk the highlights in rank
//  order, keep a card only if its box does not overlap one already kept, and
//  hide the rest. Zooming in makes room, so cards reappear on their own.
//  Nothing is hidden permanently and the dot is always still there.
//
//  Which cards survive at a given zoom is therefore decided by "rank" in
//  travel.json: rank 1 wins its space first, then rank 2, and so on. Set the
//  ranks so the top few are spread across the world -- they are the ones that
//  will be visible when the whole map is on screen.
//
//  Rankless highlights sit out of that contest entirely and wait to be hovered.

const LABEL_GAP = 6;   // px of breathing room required between two labels
const EDGE_PAD = 4;    // px a card must clear the map's edge by to be drawn

// The highlight being hovered. It sits OUT of the layout below rather than at
// the front of it: a peeked card floats over whatever is already on screen,
// claiming no space and pushing nobody out. It is the one card that is allowed
// to overlap, because it is gone again the moment the pointer moves.
let peeking = null;

// The highlight whose popup is open. Its always-on card stands down while the
// popup is showing the same thing -- otherwise a tap on a phone, which fires
// mouseover AND click, leaves the card and the popup stacked on top of each
// other saying the same words.
let popupOpen = null;

// Card images wait for their card to be shown. `loading="lazy"` is no help
// here: a hidden card is still inside the viewport as far as the browser is
// concerned, so all 30-odd thumbnails would download on page load whether or
// not anything displayed them.
function revealImages(root) {
    if (!root) return;
    root.querySelectorAll('img[data-src]').forEach(img => {
        img.src = img.dataset.src;
        delete img.dataset.src;
    });
}

function dotOf(entry) {
    const icon = entry.marker.getElement();
    return icon && icon.querySelector('.travel-dot');
}

// A card hanging over the map's edge gets pushed back inside rather than being
// sliced by it or hidden. Leaflet positions tooltips with a transform, so the
// nudge goes on the margins, which it doesn't touch. Returns where the card
// actually ends up, so collision testing works on the moved box.
function nudgeIntoView(el, box, view) {
    let dx = 0, dy = 0;
    if (box.left < view.left + EDGE_PAD)        dx = view.left + EDGE_PAD - box.left;
    else if (box.right > view.right - EDGE_PAD) dx = view.right - EDGE_PAD - box.right;
    if (box.top < view.top + EDGE_PAD)            dy = view.top + EDGE_PAD - box.top;
    else if (box.bottom > view.bottom - EDGE_PAD) dy = view.bottom - EDGE_PAD - box.bottom;

    el.style.marginLeft = dx ? `${dx}px` : '';
    el.style.marginTop = dy ? `${dy}px` : '';
    return { left: box.left + dx, right: box.right + dx,
             top: box.top + dy, bottom: box.bottom + dy };
}

function boxesOverlap(a, b) {
    return !(a.right + LABEL_GAP < b.left || a.left - LABEL_GAP > b.right ||
             a.bottom + LABEL_GAP < b.top || a.top - LABEL_GAP > b.bottom);
}

function layoutLabels() {
    const view = map.getContainer().getBoundingClientRect();
    const kept = [];
    let shown = 0;

    // Reading a rect after writing to the DOM forces the browser to redo layout
    // then and there, so a read/write/read/write loop over 30 cards costs 30
    // reflows. Everything is read first, then everything is written.
    const contenders = [];

    labelled.forEach(entry => {
        const el = entry.tooltip && entry.tooltip.getElement();
        const dot = dotOf(entry);
        if (!el) return;                                  // type is filtered off
        if (entry === peeking) return;                    // floats above; see below

        el.classList.remove('is-peek');

        // Its popup is open: the card would be a second copy of it.
        if (entry === popupOpen) {
            el.classList.add('is-hidden');
            if (dot) dot.classList.remove('card-hidden');
            return;
        }

        // Two reasons a card never shows on its own: it has no rank, or the
        // "Show highlights" box is off, which turns every card hover-only.
        // Either way there is something here to read, so the dot glows.
        if (!isRanked(entry) || !labelsOn) {
            el.classList.add('is-hidden');
            if (dot) dot.classList.add('card-hidden');
            return;
        }

        el.style.marginLeft = '';
        el.style.marginTop = '';
        contenders.push({ el, dot });
    });

    // --- read pass: where Leaflet would put each card, nudge not yet applied
    contenders.forEach(c => { c.raw = c.el.getBoundingClientRect(); });

    // --- write pass: nothing below reads layout again
    contenders.forEach(({ el, dot, raw }) => {
        // Entirely outside the map: nothing to draw and nothing to announce.
        const offscreen = raw.right < view.left || raw.left > view.right ||
                          raw.bottom < view.top || raw.top > view.bottom;
        if (offscreen) {
            el.classList.add('is-hidden');
            if (dot) dot.classList.remove('card-hidden');
            return;
        }

        const box = nudgeIntoView(el, raw, view);
        const collides = kept.some(k => boxesOverlap(box, k));

        el.classList.toggle('is-hidden', collides);
        if (dot) dot.classList.toggle('card-hidden', collides);
        if (!collides) { kept.push(box); shown++; revealImages(el); }
    });

    // The hovered card, laid over the top of everything already placed.
    if (peeking && peeking !== popupOpen) {
        const el = peeking.tooltip && peeking.tooltip.getElement();
        const dot = dotOf(peeking);
        if (el) {
            el.classList.remove('is-hidden');
            el.classList.add('is-peek');
            el.style.marginLeft = '';
            el.style.marginTop = '';
            nudgeIntoView(el, el.getBoundingClientRect(), view);   // edges too
            revealImages(el);
        }
        if (dot) dot.classList.remove('card-hidden');    // you are reading it now
    }

    // The counter describes the ranked tier only -- the hover-only cards are
    // never "missing", so counting them would make the number read as a fault.
    const ranked = labelled.filter(isRanked).length;
    const counter = map.getContainer().querySelector('.highlight-count');
    if (counter) {
        counter.textContent = labelsOn && shown < ranked ? `${shown} of ${ranked}` : String(ranked);
    }
}

// Lowest rank first. Rankless entries are hover-only and never reach the queue.
function byRank(a, b) {
    return (a.rank ?? Infinity) - (b.rank ?? Infinity);
}

const isRanked = (entry) => entry.rank != null;

// --------------------------------------------------------------------------- panel

function buildPanel(stats) {
    const panel = L.control({ position: 'topleft' });

    panel.onAdd = function () {
        const box = L.DomUtil.create('div', 'map-panel');
        box.innerHTML = `
          <button class="panel-toggle" type="button" aria-expanded="false" aria-controls="panel-body">
            Map key
          </button>
          <div class="panel-body" id="panel-body">
            <p class="map-counts">
              <strong>${stats.cities}</strong> cities across <strong>${stats.continents}</strong> continents
            </p>
            <ul class="legend">
              ${TYPES.map(t => `
                <li>
                  <label class="legend-item">
                    <input type="checkbox" class="type-check" data-type="${t}" checked>
                    <span class="swatch type-${t}"></span>
                    <span class="legend-name">${TYPE_NAMES[t]}</span>
                    <span class="legend-count">${stats.byType[t] || 0}</span>
                  </label>
                </li>`).join('')}
            </ul>
            <label class="labels-toggle">
              <input type="checkbox" class="labels-check" ${labelsOn ? 'checked' : ''}>
              Auto-display <span class="legend-count highlight-count">${stats.ranked}</span>
            </label>
            <button type="button" class="zoom-all">Zoom to all</button>
          </div>`;

        L.DomEvent.disableClickPropagation(box);
        L.DomEvent.disableScrollPropagation(box);
        return box;
    };

    panel.addTo(map);
    wirePanel(map.getContainer().querySelector('.map-panel'));
}

function wirePanel(box) {
    // collapse / expand (matters on phones, where the panel would cover the map)
    const toggle = box.querySelector('.panel-toggle');
    toggle.addEventListener('click', () => {
        const open = box.classList.toggle('open');
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    // the legend is the filter: one checkbox per type
    box.querySelectorAll('.type-check').forEach(chk => {
        chk.addEventListener('change', () => {
            const type = chk.dataset.type;
            shown[type] = chk.checked;
            if (chk.checked) layers[type].addTo(map); else map.removeLayer(layers[type]);
            chk.closest('.legend-item').classList.toggle('is-off', !chk.checked);
            layoutLabels();
        });
    });

    // highlights on / off
    box.querySelector('.labels-check').addEventListener('change', (e) => {
        labelsOn = e.target.checked;
        layoutLabels();
    });

    // zoom to everything
    box.querySelector('.zoom-all').addEventListener('click', () => {
        const pts = entries.filter(e => shown[e.type]).map(e => e.coords);
        if (pts.length) map.fitBounds(L.latLngBounds(pts), { padding: [40, 40] });
    });
}

// --------------------------------------------------------------------------- navigation

function openFromHash() {
    const slug = decodeURIComponent(location.hash.replace(/^#/, ''));
    if (!slug) return;
    const entry = entries.find(e => e.slug === slug);
    if (entry) {
        map.setView(entry.coords, Math.max(INITIAL_VIEW.zoom, 9));
        entry.marker.openPopup();
    }
}

// --------------------------------------------------------------------------- lightbox
//
//  Clicking a card's thumbnail shows the full-size photo over the map rather
//  than navigating away. One overlay, reused; Escape or a click anywhere on the
//  backdrop closes it.

let lightbox = null;

function openLightbox(src, caption) {
    if (!lightbox) {
        lightbox = document.createElement('div');
        lightbox.className = 'travel-lightbox';
        lightbox.innerHTML =
            '<button class="lightbox-close" type="button" aria-label="Close">&#10005;</button>' +
            '<figure><img alt=""><figcaption></figcaption></figure>';
        lightbox.addEventListener('click', (e) => {
            if (!e.target.closest('figure') || e.target.closest('.lightbox-close')) closeLightbox();
        });
        document.body.appendChild(lightbox);
    }
    lightbox.querySelector('img').src = src;
    lightbox.querySelector('figcaption').textContent = caption || '';
    lightbox.classList.add('is-open');
}

function closeLightbox() {
    if (lightbox) lightbox.classList.remove('is-open');
}

document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeLightbox(); });

// The camera glyph is a real <a href>, but relying on the browser to follow it
// does not survive the trip out of a Leaflet popup: the popup is torn down
// during the same click, and an anchor detached from the document mid-dispatch
// has its default action dropped. Leaflet also stops click propagation on
// popup content, so a listener on the map container may never see it at all.
//
// So the navigation is done here instead, from a capture-phase listener on the
// document -- it runs before any of that, on both the hover card and the click
// card. The href stays in the markup so middle-click, open-in-new-tab and
// right-click-copy all still behave like an ordinary link.
document.addEventListener('click', (e) => {
    const gallery = e.target.closest('.card-photos');
    if (!gallery || e.defaultPrevented || e.button !== 0) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;   // let the browser have it
    e.preventDefault();
    e.stopPropagation();
    window.location.assign(gallery.getAttribute('href'));
}, true);

// Cards live inside Leaflet's popups and tooltips, which come and go, so the
// click is caught on the map container instead of on each card.
function wireCardPhotos() {
    map.getContainer().addEventListener('click', (e) => {
        const link = e.target.closest('.card-photo');
        if (!link) return;
        e.preventDefault();
        e.stopPropagation();
        openLightbox(link.dataset.full, link.dataset.caption);
    });
}

function showError(message) {
    const box = document.createElement('div');
    box.className = 'map-error';
    box.textContent = message;
    map.getContainer().appendChild(box);
}

// ----------------------------------------------------------------------------- data

applyZoomBucket();

// Photo counts have to be in hand before any card is built, so both files are
// fetched together.
Promise.all([
    fetch('/data/travel.json').then(response => {
        if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
        return response.json();
    }),
    loadPhotoCounts()
])
    .then(([data]) => {
        // Photo counts have to include the neighbours before any card is built.
        countNearby(Object.values(data).flat()
            .filter(c => c.type === 'been')
            .map(c => ({ name: c.name, coords: c.coords })));

        const stats = { cities: 0, continents: 0, highlights: 0, ranked: 0, future: 0, byType: {} };

        Object.keys(data).forEach(continent => {
            if (!data[continent].length) return;
            if (data[continent].some(c => c.type === 'been')) stats.continents++;

            data[continent].forEach(loc => {
                const type = TYPES.includes(loc.type) ? loc.type : 'been';
                if (type === 'future') stats.future++; else stats.cities++;
                stats.byType[type] = (stats.byType[type] || 0) + 1;

                // Leaflet stacks markers by how far down the screen they sit,
                // so in a dense cluster a plain dot can bury a highlight. The
                // offsets put the dots worth seeing on top: highlights first,
                // then cities with something written about them. Overlapping
                // dots are within a few pixels of each other, so 1000 is more
                // than enough to outrank the position they'd otherwise get.
                const hasNote = (loc.message || '').trim().length >= NOTE_MIN_CHARS;
                const marker = L.marker(loc.coords, {
                    icon: dotIcon(type, loc.highlight, hasNote),
                    zIndexOffset: loc.highlight ? 2000 : (hasNote ? 1000 : 0),
                    riseOnHover: true
                }).bindPopup(cardHtml(loc), { maxWidth: 230, minWidth: 0 });

                const entry = {
                    name: loc.name,
                    slug: slugify(loc.name),
                    coords: loc.coords,
                    type,
                    rank: loc.rank,
                    marker,
                    tooltip: null
                };

                if (!loc.highlight) {
                    // Not permanent: Leaflet shows it on hover and hides it
                    // again, which is the job `title` used to do badly.
                    marker.bindTooltip(escapeHtml(loc.name), {
                        direction: 'top',
                        offset: [0, -10],
                        opacity: 1,
                        className: 'travel-name'
                    });
                }

                if (loc.highlight) {
                    stats.highlights++;
                    if (loc.rank != null) stats.ranked++;
                    // opacity 1: Leaflet writes its opacity option as an inline
                    // style, which would beat the stylesheet when a label needs
                    // to be hidden. Hiding is done with visibility in the CSS.
                    marker.bindTooltip(cardHtml(loc), {
                        permanent: true,
                        direction: 'top',
                        offset: [0, -12],
                        opacity: 1,
                        interactive: true,
                        className: 'travel-label'
                    });
                    entry.tooltip = marker.getTooltip();
                    // Hovering a highlight whose card is hidden brings it back
                    // for as long as the pointer is on the dot.
                    marker.on('mouseover', () => { peeking = entry; layoutLabels(); });
                    marker.on('mouseout', () => {
                        if (peeking === entry) { peeking = null; layoutLabels(); }
                    });
                    labelled.push(entry);
                }

                marker.on('popupopen', () => {
                    history.replaceState(null, '', '#' + entry.slug);
                    popupOpen = entry;
                    if (peeking === entry) peeking = null;
                    layoutLabels();
                });
                marker.on('popupclose', () => {
                    // Only clear the hash this popup put there. Leaflet closes
                    // the popup on the way out of a click that is navigating
                    // somewhere else, and an unconditional clear here rewrote
                    // the address bar back to /travel mid-navigation.
                    if (location.hash === '#' + entry.slug) {
                        history.replaceState(null, '', location.pathname);
                    }
                    if (popupOpen === entry) popupOpen = null;
                    // A tap never sends mouseout, so a stale peek would linger.
                    peeking = null;
                    layoutLabels();
                });

                marker.addTo(layers[type]);
                entries.push(entry);
            });
        });

        TYPES.forEach(t => layers[t].addTo(map));
        labelled.sort(byRank);

        buildPanel(stats);
        wireCardPhotos();
        markLoadedShapes();
        layoutLabels();
        openFromHash();
    })
    .catch(err => {
        console.error('Error loading travel data:', err);
        showError('The map data could not be loaded. Try reloading the page.');
    });

// ----------------------------------------------------------------------------- events

// One class swap. No geometry is written here, so there is nothing for
// Leaflet's render scheduling to be out of step with.
// A popup builds its own copy of the card, so its image needs the same nudge.
map.on('popupopen', (e) => revealImages(e.popup.getElement()));

map.on('zoomend', applyZoomBucket);
map.on('zoomend moveend', layoutLabels);

// A card grows when its photo arrives, and a tall photo narrows it. Neither is
// known until the image has loaded, so the class is set and the collision
// layout re-run at that point. Images load lazily and `load` doesn't bubble,
// so this listens on the way down.
function markShape(img) {
    if (!img.naturalWidth) return;
    const card = img.closest('.travel-card');
    if (card) card.classList.toggle('is-portrait', img.naturalHeight > img.naturalWidth);
}

map.getContainer().addEventListener('load', (e) => {
    if (e.target.tagName !== 'IMG') return;
    markShape(e.target);
    layoutLabels();
}, true);

// Anything already in the browser cache may never fire `load`.
function markLoadedShapes() {
    map.getContainer().querySelectorAll('.travel-card img').forEach(img => {
        if (img.complete) markShape(img);
    });
}

window.addEventListener('hashchange', openFromHash);

// Guard against Leaflet sizing itself against a stale layout
window.addEventListener('load', () => {
    map.invalidateSize();
    markLoadedShapes();
    layoutLabels();
});
