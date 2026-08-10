// ============================================================================
//  BOOKS  —  render engine for the reading list.
//
//  THE DATA LIVES IN /data/books.json, not in this file. It is fetched at
//  startup, exactly the way travel.js reads /data/travel.json and gallery.js
//  reads /data/gallery.json. Edit books with:
//
//      python3 automation/add_book.py            # add
//      python3 automation/add_book.py --edit     # change tags, notes, order
//
//  Each book carries a `tags` array naming every category it belongs to:
//    "recently-completed" | "currently-reading" | "to-be-read" | "all-time-greats"
//  A book may hold several tags and then appears in each matching row.
//
//  `quote` optional — a passage from the book itself, shown above my notes.
//          Use it when the book says it better than I would.
//  `rank`  optional — favorites only; orders the all-time-greats row (1 first).
//  `year`  optional — reference only; nothing on this page renders it.
//
//  ORDER IS POSITION. books.json is stored oldest -> newest, and the engine
//  flips recently-completed / currently-reading / to-be-read to newest-first
//  for display. So "bump a book to the front of its row" means "move its object
//  to the end of the array" — which is what add_book.py --edit does for you.
//
//  Everything below sits inside one async function because the data now
//  arrives over the network: nothing can be built until the fetch resolves.
// ============================================================================

(async function () {
    "use strict";

    // ------------------------------------------------------------------ data
    let myBooks;
    try {
        const res = await fetch("/data/books.json", { cache: "no-cache" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        myBooks = await res.json();
        if (!Array.isArray(myBooks)) throw new Error("books.json is not an array");
    } catch (err) {
        console.error("Could not load /data/books.json:", err);
        showLoadError();
        return;
    }

    // One visible failure beats four silently empty rows.
    function showLoadError() {
        const target = document.getElementById("recently-completed")
            || document.querySelector("main")
            || document.body;
        const p = document.createElement("p");
        p.className = "load-error";
        p.textContent = "Couldn't load the reading list. Try reloading the page.";
        target.appendChild(p);
    }



    // ============================================================================
    //  RENDER ENGINE  --  one horizontal coverflow carousel per category.
    //  The focused cover sits in front; two neighbours on each side recede,
    //  shrink, blur and fade before disappearing. Arrows, clicks, swipe and the
    //  keyboard all move the focus. Categories keep their column order, stacked
    //  top-to-bottom, because the engine fills the existing <div id> containers.
    // ============================================================================

    // `sort` decides the left-to-right order inside a row.
    // (a, b) => b.index - a.index  ==  reverse of storage order  ==  newest-added first,
    // since new books are always appended to the end of myBooks.
    const CATEGORIES = [
        { id: "recently-completed", sort: (a, b) => b.index - a.index },              // newest read first
        { id: "currently-reading",  sort: (a, b) => b.index - a.index },              // newest added first
        { id: "to-be-read",         sort: (a, b) => b.index - a.index },              // newest added first
        { id: "all-time-greats",    sort: (a, b) => (a.book.rank ?? 999) - (b.book.rank ?? 999) },
    ];

    // ============================================================================
    //  DEEP LINKING  —  /books#the-glass-hotel focuses that book and opens it.
    //
    //  Slugs come from the title, so a link stays valid as long as the title does.
    //  Renaming a book changes its link; the cover filename is unaffected.
    // ============================================================================

    function slugifyTitle(title) {
        return String(title)
            .normalize("NFKD")
            .replace(/[\u0300-\u036f]/g, "")     // strip accents
            .toLowerCase()
            .replace(/[^a-z0-9\s-]/g, "")         // drop punctuation
            .trim()
            .replace(/[\s_-]+/g, "-")
            .replace(/^-+|-+$/g, "");
    }

    // index -> slug, with -2, -3 suffixes if two books ever share a title
    const bookSlugs = (() => {
        const used = new Set();
        return myBooks.map(book => {
            const base = slugifyTitle(book.title) || "book";
            let slug = base, n = 2;
            while (used.has(slug)) slug = `${base}-${n++}`;
            used.add(slug);
            return slug;
        });
    })();

    const slugToIndex = new Map(bookSlugs.map((slug, i) => [slug, i]));

    // bookIndex -> { categoryId: focusFunction }, filled in by buildCarousel
    const focusRegistry = new Map();

    // A book can sit in several rows. Favorites win, then recently completed.
    const FOCUS_PRIORITY = ["all-time-greats", "recently-completed",
                            "currently-reading", "to-be-read"];

    function focusBook(bookIndex) {
        const rows = focusRegistry.get(bookIndex);
        if (!rows) return false;
        for (const categoryId of FOCUS_PRIORITY) {
            if (rows[categoryId]) { rows[categoryId](); return true; }
        }
        return false;
    }

    // Everything below is interpolated into markup, so it has to be escaped.
    // Nothing in books.json currently contains a quote or an ampersand, which
    // is exactly why this would have gone unnoticed until the first title that
    // did -- a `"` in a title would have ended the alt attribute early.
    const COVERS = "/images/bookCovers/";      // absolute, like every other path
    const MISSING_COVER = COVERS + "question-mark.jpg";

    function esc(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }

    function bookCard(book, index) {
        const authorLine = book.author ? `<p>by ${esc(book.author)}</p>` : "";
        const summary    = book.summary ? `<div class="summary">${esc(book.summary)}</div>` : "";
        return `
            <div class="book" data-index="${index}">
                <div class="book-cover">
                    <img data-src="${esc(COVERS + book.cover)}" alt="${esc(book.title)}" loading="lazy" />
                    ${summary}
                </div>
                <div class="book-info">
                    <h3>${esc(book.title)}</h3>
                    ${authorLine}
                </div>
            </div>
        `;
    }

    function buildCarousel(column, entries, categoryId) {
        const carousel = document.createElement("div");
        carousel.className = "carousel";
        carousel.tabIndex = 0;                         // focusable, so arrow keys work
        // A row is a custom widget: it needs to say what it is and what it
        // holds, or a screen reader announces an unlabelled focusable box.
        carousel.setAttribute("role", "group");
        carousel.setAttribute("aria-roledescription", "carousel");
        const heading = column.querySelector("h2");
        if (heading) carousel.setAttribute("aria-label", heading.textContent.trim());
        carousel.innerHTML = `
            <button class="arrow left" aria-label="Previous book" type="button">&#8249;</button>
            <div class="stage"></div>
            <button class="arrow right" aria-label="Next book" type="button">&#8250;</button>
        `;
        const stage    = carousel.querySelector(".stage");
        const leftBtn  = carousel.querySelector(".arrow.left");
        const rightBtn = carousel.querySelector(".arrow.right");
        stage.innerHTML = entries.map(e => bookCard(e.book, e.index)).join("");
        const cards = Array.from(stage.children);

        // The missing-cover fallback used to be an inline onerror= attribute in
        // the markup above. That is the same thing as the gallery's old inline
        // onclick: the one item a Content-Security-Policy would have to make an
        // exception for. Bound here instead, so this page needs no exception.
        stage.querySelectorAll("img").forEach(img => {
            img.addEventListener("error", function onMissing() {
                img.removeEventListener("error", onMissing);   // don't loop if
                img.src = MISSING_COVER;                       // the fallback 404s too
            });
        });
        const n = cards.length;
        const LOAD_AHEAD = 3;   // load the focused cover + this many on each side
        let focus = 0;

        function update() {
            cards.forEach((card, i) => {
                const off = i - focus;
                let pos;
                if      (off ===  0) pos = "pos-0";
                else if (off === -1) pos = "pos-l1";
                else if (off ===  1) pos = "pos-r1";
                else if (off === -2) pos = "pos-l2";
                else if (off ===  2) pos = "pos-r2";
                else                 pos = off < 0 ? "pos-hidden-l" : "pos-hidden-r";
                card.className = "book " + pos;
                card.setAttribute("aria-hidden", pos.startsWith("pos-hidden") ? "true" : "false");

                // lazy-load covers only within a few steps of the focused book
                if (Math.abs(off) <= LOAD_AHEAD) {
                    const img = card.querySelector("img");
                    if (img && !img.dataset.loaded) {
                        img.src = img.dataset.src;
                        img.dataset.loaded = "1";
                    }
                }
            });
            // The class alone only stops the mouse (pointer-events: none); the
            // keyboard could still tab to a dead arrow and press it.
            setDisabled(leftBtn, focus === 0, rightBtn);
            setDisabled(rightBtn, focus === n - 1, leftBtn);
        }

        // Disabling the button that currently holds focus would drop focus to
        // the page body, so hand it to the other arrow on the way out.
        function setDisabled(button, off, fallback) {
            if (off && document.activeElement === button) {
                (fallback && !fallback.disabled ? fallback : carousel).focus();
            }
            button.classList.toggle("disabled", off);
            button.disabled = off;
        }

        function go(delta) {
            focus = Math.max(0, Math.min(n - 1, focus + delta));
            update();
        }

        leftBtn.addEventListener("click", () => go(-1));
        rightBtn.addEventListener("click", () => go(1));

        // click a side cover to bring it forward; click the focused cover to open it
        cards.forEach((card, i) => {
            card.addEventListener("click", () => {
                // Focus the row on the way in. The cards are plain <div>s, so a
                // mouse click leaves document.activeElement on <body> and the
                // modal would have nowhere to send focus back to on close.
                carousel.focus({ preventScroll: true });
                if (i === focus) openModal(parseInt(card.dataset.index, 10), true, carousel);
                else { focus = i; update(); }
            });
        });

        // arrow keys when the row is focused
        carousel.addEventListener("keydown", (e) => {
            if (e.key === "ArrowLeft")  { go(-1); e.preventDefault(); }
            if (e.key === "ArrowRight") { go( 1); e.preventDefault(); }
            if (e.key === "Home")       { go(-n); e.preventDefault(); }
            if (e.key === "End")        { go( n); e.preventDefault(); }
            // Without this the arrow keys move a highlight that cannot be acted
            // on: a keyboard could reach every book and open none of them.
            if (e.key === "Enter" || e.key === " ") {
                openModal(parseInt(cards[focus].dataset.index, 10), true, carousel);
                e.preventDefault();
            }
        });

        // touch swipe
        let startX = null;
        stage.addEventListener("touchstart", (e) => { startX = e.touches[0].clientX; }, { passive: true });
        stage.addEventListener("touchend", (e) => {
            if (startX === null) return;
            const dx = e.changedTouches[0].clientX - startX;
            if (Math.abs(dx) > 40) go(dx < 0 ? 1 : -1);
            startX = null;
        });

        // Register a way to bring each book to the front of THIS row, so a link
        // like /books#the-glass-hotel can focus it later. A book with several tags
        // registers once per row it appears in; FOCUS_PRIORITY picks between them.
        entries.forEach((e, i) => {
            if (!focusRegistry.has(e.index)) focusRegistry.set(e.index, {});
            focusRegistry.get(e.index)[categoryId] = () => {
                focus = i;
                update();
                carousel.scrollIntoView({ behavior: "smooth", block: "center" });
            };
        });

        column.appendChild(carousel);
        update();
    }

    CATEGORIES.forEach(cfg => {
        const column = document.getElementById(cfg.id);
        if (!column) return;
        const entries = myBooks
            .map((book, index) => ({ book, index }))
            .filter(e => e.book.tags.includes(cfg.id));
        if (cfg.sort) entries.sort(cfg.sort);
        if (entries.length === 0) { column.style.display = "none"; return; }
        buildCarousel(column, entries, cfg.id);
    });


    // --- MODAL POP-UP LOGIC ---
    const modal = document.getElementById("bookModal");
    const closeModalBtn = document.querySelector(".close-modal");

    function openModal(bookIndex, updateHash = true, returnFocus = null) {
        const selectedBook = myBooks[bookIndex];
        const cover = document.getElementById("modalCover");
        cover.src = COVERS + selectedBook.cover;
        // "Book Cover" told a screen reader nothing it didn't already know from
        // the heading beside it. The title does.
        cover.alt = `Cover of ${selectedBook.title}`;
        document.getElementById("modalTitle").innerText = selectedBook.title;
        document.getElementById("modalAuthor").innerText = selectedBook.author ? `by ${selectedBook.author}` : "";
        document.getElementById("modalSummary").innerText = selectedBook.summary || "";

        // A book can carry a passage from the book (`quote`), my own reaction
        // (`notes`), both, or neither.
        const quote = (selectedBook.quote || "").trim();
        const notes = (selectedBook.notes || "").trim();

        const quoteEl = document.getElementById("modalQuote");
        quoteEl.textContent = quote;
        quoteEl.hidden = !quote;

        document.getElementById("modalNotes").textContent =
            notes || "I haven't written any notes for this book yet!";
        // Only apologise for missing notes when there is nothing else to show.
        document.getElementById("modalNotesBlock").hidden = !notes && Boolean(quote);
        modal.style.display = "block";

        // Dialog semantics are in books.html; this moves focus in, keeps Tab
        // inside, and puts the page behind out of reach until it closes.
        SiteModal.open(modal, {
            initialFocus: closeModalBtn,
            returnFocus: returnFocus
        });

        // Put the slug in the address bar so the URL can just be copied.
        // replaceState rather than pushState: opening books shouldn't stack up
        // history entries the back button has to walk through.
        if (updateHash) {
            history.replaceState(null, "", "#" + bookSlugs[bookIndex]);
        }
    }

    function closeModal() {
        SiteModal.close(modal);          // before hiding: focus can't leave a
        modal.style.display = "none";    // hidden element cleanly
        if (location.hash) {
            history.replaceState(null, "", location.pathname + location.search);
        }
    }

    closeModalBtn.addEventListener("click", closeModal);
    // addEventListener rather than window.onclick: assigning the property
    // silently replaces whatever else on the page wanted the same hook.
    window.addEventListener("click", (event) => {
        if (event.target === modal) closeModal();
    });
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && modal.style.display === "block") closeModal();
    });


    // --- DEEP LINK ENTRY POINT ---
    // Runs last, once every carousel exists and the modal element is bound.
    function openFromHash() {
        const slug = decodeURIComponent(location.hash.replace(/^#/, ""));
        if (!slug) return;
        const bookIndex = slugToIndex.get(slug);
        if (bookIndex === undefined) return;   // unknown slug: leave the page as-is
        focusBook(bookIndex);
        openModal(bookIndex, false);           // hash is already correct
    }

    openFromHash();
    window.addEventListener("hashchange", openFromHash);
})();
