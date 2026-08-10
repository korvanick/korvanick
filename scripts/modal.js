// ============================================================================
//  MODAL  —  shared dialog behaviour for the site's overlays.
//
//  Three overlays use this: the book details modal (books.js), the gallery
//  lightbox (gallery.js), and the full-size photo over the travel map
//  (travel.js). Each still owns its own showing and hiding; this file handles
//  only the parts that are identical everywhere and easy to get subtly wrong.
//
//    dialog semantics   role="dialog" + aria-modal="true", so a screen reader
//                       announces an overlay instead of reading straight past
//                       it. Set here only if the markup hasn't already said
//                       so -- books.html and gallery.html carry their own.
//
//    focus in           focus moves into the overlay on open, so the next Tab
//                       lands inside it rather than at the top of the page.
//
//    focus trap         Tab and Shift+Tab cycle within the overlay instead of
//                       wandering into the page behind it.
//
//    background inert   every other top-level element is marked `inert`, so
//                       neither the pointer, the tab order, nor a screen
//                       reader's own reading cursor can reach the page under
//                       the overlay. aria-hidden goes on as well: `inert` is
//                       widely supported now, but the older attribute costs
//                       nothing and covers what isn't.
//
//    focus back         closing returns focus to whatever opened it, so the
//                       keyboard doesn't lose its place.
//
//  The travel map's Leaflet POPUPS deliberately do not use this. A popup is
//  not modal -- the map stays live underneath and a click outside dismisses
//  it -- so trapping focus in one would be a lie told to a screen reader.
//  travel.js gives popups dialog semantics and focus handling on their own.
//
//  Load before the page script that uses it (document order is enough, both
//  can be deferred).
// ============================================================================

window.SiteModal = (function () {
    "use strict";

    var FOCUSABLE = [
        "a[href]",
        "button:not([disabled])",
        "input:not([disabled])",
        "select:not([disabled])",
        "textarea:not([disabled])",
        "[tabindex]:not([tabindex='-1'])"
    ].join(",");

    // overlay element -> what has to be undone when it closes
    var open = new Map();

    // Only what is actually on screen: a lightbox's prev/next buttons are real
    // elements even while hidden, and tabbing to one you cannot see is the
    // same bug this file exists to fix.
    function focusable(root) {
        return Array.prototype.slice.call(root.querySelectorAll(FOCUSABLE))
            .filter(function (el) {
                return el.offsetWidth || el.offsetHeight || el.getClientRects().length;
            });
    }

    function focus(el) {
        if (!el) return;
        try { el.focus({ preventScroll: true }); } catch (e) { el.focus(); }
    }

    function onTab(overlay, event) {
        var items = focusable(overlay);
        if (!items.length) { event.preventDefault(); focus(overlay); return; }

        var first = items[0];
        var last = items[items.length - 1];
        var active = document.activeElement;

        // Focus escaped -- e.g. the button holding it was just disabled.
        if (!overlay.contains(active)) {
            event.preventDefault();
            focus(event.shiftKey ? last : first);
            return;
        }
        if (event.shiftKey && active === first) { event.preventDefault(); focus(last); }
        else if (!event.shiftKey && active === last) { event.preventDefault(); focus(first); }
    }

    return {
        isOpen: function (overlay) {
            return open.has(overlay);
        },

        // options:
        //   label         aria-label, if the markup doesn't carry one
        //   labelledBy    id of the element naming the dialog (wins over label)
        //   initialFocus  element to focus; defaults to the first focusable one
        //   returnFocus   element to focus on close; defaults to whatever had
        //                 focus at open time. Worth passing explicitly: a mouse
        //                 click on a plain <div> leaves document.activeElement
        //                 on <body>, which is nothing to go back to.
        open: function (overlay, options) {
            if (!overlay || open.has(overlay)) return;
            var opts = options || {};

            if (!overlay.hasAttribute("role")) overlay.setAttribute("role", "dialog");
            overlay.setAttribute("aria-modal", "true");
            if (opts.labelledBy && !overlay.hasAttribute("aria-labelledby")) {
                overlay.setAttribute("aria-labelledby", opts.labelledBy);
            } else if (opts.label && !overlay.hasAttribute("aria-label") &&
                       !overlay.hasAttribute("aria-labelledby")) {
                overlay.setAttribute("aria-label", opts.label);
            }

            var active = document.activeElement;
            var returnFocus = opts.returnFocus ||
                (active && active !== document.body ? active : null);

            // Put the rest of the page out of reach. Anything already inert or
            // already aria-hidden is left alone, so it stays that way after.
            var hidden = [];
            Array.prototype.forEach.call(document.body.children, function (child) {
                if (child === overlay || child.contains(overlay)) return;
                if (child.inert) return;
                child.inert = true;
                var hadAria = child.hasAttribute("aria-hidden");
                if (!hadAria) child.setAttribute("aria-hidden", "true");
                hidden.push({ el: child, hadAria: hadAria });
            });

            var keydown = function (event) {
                if (event.key === "Tab") onTab(overlay, event);
            };
            // Capture: the page's own keydown listeners shouldn't get to act on
            // a Tab that is only moving focus around inside the overlay.
            document.addEventListener("keydown", keydown, true);

            var target = opts.initialFocus || focusable(overlay)[0];
            var borrowedTabindex = false;
            if (!target) {
                // Nothing focusable inside: focus the overlay itself so the
                // screen reader's cursor at least starts in the right place.
                target = overlay;
                if (!overlay.hasAttribute("tabindex")) {
                    overlay.setAttribute("tabindex", "-1");
                    borrowedTabindex = true;
                }
            }

            open.set(overlay, {
                returnFocus: returnFocus,
                hidden: hidden,
                keydown: keydown,
                borrowedTabindex: borrowedTabindex
            });

            // The caller has usually only just made the overlay visible, and a
            // display:none element cannot take focus. Wait for the paint.
            requestAnimationFrame(function () {
                if (open.has(overlay)) focus(target);
            });
        },

        close: function (overlay) {
            var state = open.get(overlay);
            if (!state) return;
            open.delete(overlay);

            document.removeEventListener("keydown", state.keydown, true);
            state.hidden.forEach(function (entry) {
                entry.el.inert = false;
                if (!entry.hadAria) entry.el.removeAttribute("aria-hidden");
            });
            overlay.removeAttribute("aria-modal");
            if (state.borrowedTabindex) overlay.removeAttribute("tabindex");

            if (state.returnFocus && document.contains(state.returnFocus)) {
                focus(state.returnFocus);
            }
        }
    };
})();
