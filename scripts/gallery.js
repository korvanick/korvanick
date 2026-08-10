// ============================================================================
//  GALLERY
//
//  Reads /data/gallery.json (written by automation/update_gallery.py), which is
//  a list of { src, date } newest-first. Older files that were a plain list of
//  path strings still work -- the date is then read from the filename here.
//
//  The grid shows small thumbnails from images/gallery/thumbs/. The full-size
//  photo is only fetched when you open one, which is what keeps the page quick.
//
//  Deep links: /gallery#<slug> opens that photo, and opening any photo writes
//  its slug to the address bar. That is what lets the travel map link a city's
//  card straight to the full-size picture.
//
//  Slugs come from gallery.json (update_gallery.py writes them: the city where
//  the photo was taken, or a two-word petname). The filename without its
//  extension still resolves too, so links made before slugs existed keep
//  working and anything holding only a path can still address a photo.
//
//  City view: /gallery#city=rome-italy shows the photos taken there AND in any
//  city within NEARBY_KM of it, which is where a card on the travel map sends
//  you. Bellevue and Lake Forest Park are Seattle as far as browsing photos
//  goes. Coordinates come from travel.json; if that fetch fails the view falls
//  back to exact matches only. The lightbox then steps
//  through that city alone, and a line above the grid says what you are
//  looking at with the way back to everything.
//
//  There is no filtering UI on this page on purpose -- arriving from the map
//  is the only way in, and the grid is otherwise the whole gallery.
// ============================================================================

const THUMB_PREFIX = "/images/gallery/thumbs/";

const MONTHS = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"];

const NEARBY_KM = 20;   // must match the same constant in travel.js

let cities = [];      // [{ slug, name, coords }] from travel.json, for grouping
let allPhotos = [];   // everything in gallery.json
let photos = [];      // what is on screen: all of them, or one city's
let current = -1;     // index into `photos` of the open photo, -1 when closed
let loadToken = 0;    // guards against a slow load landing after a newer one

// "Rome, Italy" -> "rome-italy", matching the slugs travel.js builds
const citySlug = (name) => name.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

// ----------------------------------------------------------------------------- data

Promise.all([
    fetch("/data/gallery.json").then(r => r.json()),
    // Best effort: without it, a city view just shows that city alone.
    fetch("/data/travel.json").then(r => (r.ok ? r.json() : {})).catch(() => ({}))
])
    .then(([data, places]) => {
        allPhotos = data.map(normalize);
        cities = Object.values(places).flat()
            .filter(c => c && c.coords)
            .map(c => ({ slug: citySlug(c.name), name: c.name, coords: c.coords }));
        applyFilter();          // reads the hash, builds the grid
        openFromHash();
    })
    .catch(error => {
        // A console message is no use to a visitor: the page just looked empty
        // on purpose. Say what happened where they can see it.
        console.error("Error loading the gallery data:", error);
        showEmpty("The photos could not be loaded. Reloading the page usually fixes it.");
    });

// Message in place of the grid, for a failed load or a genuinely empty set.
function showEmpty(message) {
    const container = document.getElementById("galleryContainer");
    if (!container) return;
    container.innerHTML = "";
    const note = document.createElement("p");
    note.className = "gallery-empty";
    note.textContent = message;
    container.appendChild(note);
}

function kmApart(a, b) {
    const p1 = a[0] * Math.PI / 180, p2 = b[0] * Math.PI / 180;
    const dp = (b[0] - a[0]) * Math.PI / 180, dl = (b[1] - a[1]) * Math.PI / 180;
    const x = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
    return 6371 * 2 * Math.asin(Math.sqrt(x));
}

// Every city slug within NEARBY_KM of the one asked for, itself included.
function nearbySlugs(slug) {
    const target = cities.find(c => c.slug === slug);
    if (!target) return new Set([slug]);
    return new Set(cities
        .filter(c => kmApart(target.coords, c.coords) <= NEARBY_KM)
        .map(c => c.slug));
}

// Accepts either "/images/gallery/x.jpg" or { src: "...", date: "2026-04-05" }.
function normalize(item) {
    const src  = typeof item === "string" ? item : item.src;
    const name = src.split("/").pop();
    const date = (typeof item === "object" && item.date) || dateFromName(name);
    const fileSlug = name.replace(/\.[^.]+$/, "");
    const slug = (typeof item === "object" && item.slug) || fileSlug;
    const location = (typeof item === "object" && item.location) || "";
    const alt = (typeof item === "object" && item.alt) || "";
    return { src, thumb: THUMB_PREFIX + name, date, label: pretty(date),
             slug, fileSlug, location, alt };
}

// /gallery#20260726_202749 -> open that photo
function openFromHash() {
    const slug = decodeURIComponent(location.hash.replace(/^#/, ""));
    if (!slug || slug.includes("=")) return;            // a city view, not a photo
    let index = photos.findIndex(p => p.slug === slug);
    if (index === -1) index = photos.findIndex(p => p.fileSlug === slug);
    if (index !== -1) openModal(index);
}

// --------------------------------------------------------------------------- filters

function cityFromHash() {
    const hash = decodeURIComponent(location.hash.replace(/^#/, ""));
    return hash.startsWith("city=") ? hash.slice(5) : "";
}

function applyFilter() {
    const wanted = cityFromHash();
    const group = wanted ? nearbySlugs(wanted) : null;
    const match = group
        ? allPhotos.filter(p => p.location && group.has(citySlug(p.location)))
        : [];

    // An unknown city, or one with no photos, falls back to the whole gallery
    // rather than an empty page.
    photos = match.length ? match : allPhotos;

    const target = cities.find(c => c.slug === wanted);
    const others = match.length
        ? [...new Set(match.map(p => p.location))].filter(n => n !== (target ? target.name : ""))
        : [];
    showFilterBar(match.length ? (target ? target.name : match[0].location) : "",
                  photos.length, others);
    buildGrid();
}

function showFilterBar(city, count, others = []) {
    const container = document.getElementById("galleryContainer");
    document.querySelector(".gallery-filter")?.remove();
    if (!city) return;

    const bar = document.createElement("div");
    bar.className = "gallery-filter";

    const label = document.createElement("span");
    const name = document.createElement("strong");
    name.textContent = city;                      // never HTML from the data
    label.appendChild(name);
    label.append(` — ${count} photo${count === 1 ? "" : "s"}`);
    bar.appendChild(label);

    // Say so when the view is wider than the city named.
    if (others.length) {
        const also = document.createElement("span");
        also.className = "gallery-filter-also";
        also.textContent = "including " + others.join(", ");
        label.appendChild(also);
    }

    const clear = document.createElement("a");
    clear.href = "/gallery";
    clear.className = "gallery-filter-clear";
    clear.textContent = "Show all photos";
    clear.addEventListener("click", (e) => {
        e.preventDefault();
        history.replaceState(null, "", location.pathname);
        applyFilter();
    });
    bar.appendChild(clear);

    container.parentNode.insertBefore(bar, container);
}

// Phone filenames lead with the date: 20260405_142115.jpg -> 2026-04-05
function dateFromName(name) {
    const full = name.match(/^(\d{4})(\d{2})(\d{2})(?!\d)/);
    if (full) {
        const [, y, m, d] = full;
        if (+m >= 1 && +m <= 12 && +d >= 1 && +d <= 31) return `${y}-${m}-${d}`;
    }
    const year = name.match(/^((?:19|20)\d{2})(?!\d)/);
    return year ? year[1] : "";
}

function pretty(date) {
    if (!date) return "";
    if (date.length === 4) return date;
    const [y, m, d] = date.split("-");
    return `${MONTHS[+m - 1]} ${+d}, ${y}`;
}

// ----------------------------------------------------------------------------- grid

function buildGrid() {
    const container = document.getElementById("galleryContainer");
    container.innerHTML = "";

    if (!photos.length) {
        showEmpty("There are no photos here yet.");
        return;
    }

    const fragment = document.createDocumentFragment();
    let shownYear = null;

    photos.forEach((photo, index) => {
        const year = photo.date ? photo.date.slice(0, 4) : "Undated";
        if (year !== shownYear) {
            const heading = document.createElement("h2");
            heading.className = "gallery-year";
            heading.textContent = year;
            heading.id = "year-" + year;
            fragment.appendChild(heading);
            shownYear = year;
        }

        // A bare <img> with a click handler is a control only a mouse can
        // find. Wrapping it in a button costs one element and makes every
        // photo reachable by Tab and openable with Enter or Space; the button
        // takes its name from the image's alt text.
        const button = document.createElement("button");
        button.type = "button";
        button.className = "gallery-thumb";

        const img = document.createElement("img");
        img.src = encodeURI(photo.thumb);
        // The description if we have one, the date if not. Never an empty or
        // missing alt: an <img> with no alt attribute gets its filename read
        // aloud, which is worse than a date.
        img.alt = photo.alt || photo.label || "Photo";
        img.title = photo.label;
        img.className = "gallery-image";
        img.loading = "lazy";
        img.decoding = "async";

        button.appendChild(img);
        button.addEventListener("click", () => openModal(index, button));
        fragment.appendChild(button);
    });

    container.appendChild(fragment);
}

// ----------------------------------------------------------------------------- lightbox

function modalParts() {
    return {
        modal:   document.getElementById("imageModal"),
        image:   document.getElementById("modalImage"),
        caption: document.getElementById("caption"),
    };
}

function openModal(index, trigger) {
    const { modal, image, caption } = modalParts();
    if (index < 0 || index >= photos.length) return;

    // Stepping to the next photo re-enters this function with the lightbox
    // already up. Only a genuine open should touch focus.
    const wasClosed = current === -1;
    current = index;
    const photo = photos[index];

    showPhoto(modal, image, photo);
    image.alt = photo.alt || photo.label || "Photo";
    const parts = [photo.location, photo.label].filter(Boolean);
    parts.push(`${index + 1} of ${photos.length}`);
    caption.textContent = parts.join("   ·   ");

    modal.style.display = "flex";
    document.body.classList.add("modal-open");
    history.replaceState(null, "", "#" + photo.slug);
    ensureNavButtons(modal);
    updateNavButtons();
    preloadNeighbours(index);

    if (wasClosed) {
        // Dialog semantics are in gallery.html; this moves focus in, keeps Tab
        // inside, and puts the grid behind out of reach until it closes.
        SiteModal.open(modal, {
            initialFocus: modal.querySelector(".close"),
            returnFocus: trigger
        });
    }
}

// Swapping the src leaves the OLD photo on screen until the new one arrives,
// which reads as a frozen lightbox rather than a loading one. The previous
// image is cleared, a spinner takes its place, and the photo appears when it is
// actually ready. Jumping around the grid hits this every time; arrowing to a
// neighbour usually doesn't, because preloadNeighbours has already fetched it
// and the browser answers from cache before the spinner has faded in.
function showPhoto(modal, image, photo) {
    const token = ++loadToken;
    modal.classList.remove("is-error");
    modal.classList.add("is-loading");
    image.removeAttribute("src");          // don't sit on the last photo

    image.onload = () => {
        if (token === loadToken) modal.classList.remove("is-loading");
    };
    image.onerror = () => {
        if (token !== loadToken) return;
        modal.classList.remove("is-loading");
        modal.classList.add("is-error");
    };

    image.src = encodeURI(photo.src);

    // Already in cache: the load event may have fired before the handler above
    // was attached, so there would be nothing left to clear the spinner.
    if (image.complete && image.naturalWidth) modal.classList.remove("is-loading");
}

// Fetch the next and previous full-size photos quietly, so arrowing feels instant.
function preloadNeighbours(index) {
    [index - 1, index + 1].forEach(i => {
        if (i >= 0 && i < photos.length) new Image().src = encodeURI(photos[i].src);
    });
}

function step(delta) {
    const next = current + delta;
    if (next >= 0 && next < photos.length) openModal(next);
}

function closeModal() {
    const { modal } = modalParts();
    SiteModal.close(modal);        // before hiding: focus can't leave a hidden
    modal.style.display = "none";  // element cleanly
    document.body.classList.remove("modal-open");
    history.replaceState(null, "", location.pathname);
    current = -1;
}

// The spinner and the prev/next buttons are created here rather than in
// gallery.html, so the page markup doesn't need to change.
function ensureNavButtons(modal) {
    if (!modal.querySelector(".modal-spinner")) {
        const spinner = document.createElement("div");
        spinner.className = "modal-spinner";
        spinner.setAttribute("role", "status");
        spinner.setAttribute("aria-label", "Loading photo");
        modal.appendChild(spinner);
    }
    if (modal.querySelector(".gallery-nav")) return;

    const make = (cls, glyph, delta, label) => {
        const button = document.createElement("button");
        button.className = `gallery-nav ${cls}`;
        button.type = "button";
        button.innerHTML = glyph;
        button.setAttribute("aria-label", label);
        button.addEventListener("click", event => {
            event.stopPropagation();   // don't let it count as a background click
            step(delta);
        });
        modal.appendChild(button);
        return button;
    };

    make("prev", "&#10094;", -1, "Previous photo");
    make("next", "&#10095;", 1, "Next photo");
}

function updateNavButtons() {
    const { modal } = modalParts();
    const prev = modal.querySelector(".gallery-nav.prev");
    const next = modal.querySelector(".gallery-nav.next");
    // The class only stops the mouse (pointer-events: none). The keyboard could
    // still tab to a dead arrow, so set the real attribute too -- and hand
    // focus on before disabling the button that is holding it.
    setNavState(prev, current <= 0, next, modal);
    setNavState(next, current >= photos.length - 1, prev, modal);
}

function setNavState(button, off, fallback, modal) {
    if (!button) return;
    if (off && document.activeElement === button) {
        const target = (fallback && !fallback.disabled) ? fallback : modal.querySelector(".close");
        if (target) target.focus();
    }
    button.classList.toggle("disabled", off);
    button.disabled = off;
}

// ----------------------------------------------------------------------------- input

document.addEventListener("keydown", event => {
    if (current === -1) return;
    if (event.key === "Escape")     { closeModal(); }
    else if (event.key === "ArrowLeft")  { step(-1); }
    else if (event.key === "ArrowRight") { step(1); }
    else if (event.key === "Home")  { openModal(0); }
    else if (event.key === "End")   { openModal(photos.length - 1); }
    else return;
    event.preventDefault();
});

// Swipe on touch screens
let touchStartX = null;
document.addEventListener("touchstart", event => {
    if (current !== -1) touchStartX = event.touches[0].clientX;
}, { passive: true });

document.addEventListener("touchend", event => {
    if (current === -1 || touchStartX === null) return;
    const dx = event.changedTouches[0].clientX - touchStartX;
    touchStartX = null;
    if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
});

window.addEventListener("hashchange", () => { applyFilter(); openFromHash(); });

// The close button used to carry an inline onclick in gallery.html, which was
// the one thing on this page a Content-Security-Policy would have had to make
// an exception for. It is a real button now, wired here.
document.querySelector("#imageModal .close").addEventListener("click", closeModal);

// Click the dark background (but not the photo itself) to close
window.addEventListener("click", event => {
    if (event.target === document.getElementById("imageModal")) closeModal();
});
