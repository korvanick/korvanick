/* ============================================================================
   Shared site header.

   One list of links, below, rendered into the empty <nav> that every page
   carries. Edit LINKS and the header changes everywhere at once, generated
   blog pages included -- no more hunting through eight files, and no more
   hiding a link with a CSS rule because one page still points somewhere old.

   Every page needs exactly two lines and nothing else:
       <script src="/scripts/nav.js" defer></script>   in <head>
       <nav></nav>                                     first thing in <body>

   Hrefs are absolute on purpose: "/books" resolves the same from /travel and
   from /blog/<slug>, while a bare "books" would resolve to /blog/books on a
   post page.

   This file also renders the theme switch, but it does NOT decide the theme
   at load. It runs with defer, which is after first paint -- a light-theme
   visitor would watch the site flash dark and then swap. The small inline
   script in every page's <head> does that job before anything is painted;
   this only draws the button and handles the click.
   ============================================================================ */
(function () {
const LINKS = [
    { href: "/",             label: "HOME"         },
    { href: "/professional", label: "PROFESSIONAL" },
    { href: "/projects",     label: "PROJECTS"     },
    { href: "/travel",       label: "TRAVEL"       },
    { href: "/gallery",      label: "PHOTOS"       },
    { href: "/books",        label: "BOOKS"        },
    { href: "/blog",         label: "BLOG"         }
  ];

  const nav = document.querySelector("body > nav");   // the site header, never a
                                                     // <nav> nested in content
  if (!nav) return;
  nav.textContent = "";          // drop anything static that was left behind
  nav.classList.add("js-nav");   // lets the CSS know the hamburger exists

  // --- theme switch -------------------------------------------------------
  // Appended before the hamburger so that on mobile, where both sit in the
  // flow, the order reads [theme][hamburger] from the right edge. On desktop
  // the CSS lifts it out of the flow entirely and the hamburger is hidden.
  const SUN = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/>' +
              '<path d="M12 2.2v2.4M12 19.4v2.4M2.2 12h2.4M19.4 12h2.4' +
              'M5.1 5.1l1.7 1.7M17.2 17.2l1.7 1.7M18.9 5.1l-1.7 1.7M6.8 17.2l-1.7 1.7"/></svg>';
  const MOON = '<svg viewBox="0 0 24 24" aria-hidden="true">' +
               '<path d="M20.5 14.6A8.5 8.5 0 1 1 9.4 3.5a6.8 6.8 0 0 0 11.1 11.1z"/></svg>';

  const themeBtn = document.createElement("button");
  themeBtn.className = "theme-toggle";
  themeBtn.type = "button";

  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
  }

  function paintThemeButton() {
    const dark = currentTheme() === "dark";
    // The button offers the theme you'd be switching TO, so it shows the sun
    // while you're in the dark, and says what pressing it does.
    themeBtn.innerHTML = dark ? SUN : MOON;
    const label = dark ? "Switch to light theme" : "Switch to dark theme";
    themeBtn.setAttribute("aria-label", label);
    themeBtn.setAttribute("title", label);
  }

  themeBtn.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    // Dark is the stylesheet's default, so it's the absence of the attribute.
    if (next === "light") document.documentElement.setAttribute("data-theme", "light");
    else document.documentElement.removeAttribute("data-theme");
    try { localStorage.setItem("theme", next); } catch (e) { /* private mode */ }
    paintThemeButton();
  });

  paintThemeButton();
  nav.appendChild(themeBtn);

  // --- hamburger toggle (hidden by CSS until the mobile breakpoint) ---
  const toggle = document.createElement("button");
  toggle.className = "nav-toggle";
  toggle.type = "button";
  toggle.setAttribute("aria-label", "Toggle menu");
  toggle.setAttribute("aria-expanded", "false");
  toggle.innerHTML = "&#9776;";                 // hamburger
  nav.appendChild(toggle);

  function setOpen(open) {
    nav.classList.toggle("open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.innerHTML = open ? "&#10005;" : "&#9776;";   // close / hamburger
  }

  toggle.addEventListener("click", () => setOpen(!nav.classList.contains("open")));
  nav.addEventListener("click", (e) => { if (e.target.tagName === "A") setOpen(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") setOpen(false); });

  // --- which section are we in? ---
  // First path segment only, so /blog/earth-expedition still lights up BLOG.
  function section(path) {
    const first = path.replace(/^\/+/, "").split("/")[0] || "";
    return first.replace(/\.html$/, "").toLowerCase() || "home";
  }
  const here = section(location.pathname);

  // --- render ---
  LINKS.forEach(({ href, label }) => {
    const a = document.createElement("a");
    a.href = href;
    a.textContent = label;
    if (section(href) === here) {
      a.classList.add("active");
      a.setAttribute("aria-current", "page");
    }
    nav.appendChild(a);
  });
})();
