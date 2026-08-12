#!/usr/bin/env python3
"""
publish.py -- turn Markdown into themed blog and project pages for korvanick.

This is the publish step. Run it after ANY change to a .md file in data/posts/
or data/projects/. It rebuilds every page from every source file each time, so
it is always safe to run and always produces the same result.

Two collections, one script. Both read Markdown out of data/ and write themed
HTML into the pages/ tree; they differ in front matter, sort order and page
anatomy, so they get separate renderers rather than one with a pile of flags.

Write each post as a Markdown file in  data/posts/<slug>.md  (next to
gallery.json and travel.json) with a small front-matter header:

    ---
    title: The Long Way Around
    date: 2024-08-12
    summary: One or two lines shown on the blog index.
    ---
    Your **Markdown** body goes here...

Projects live in  data/projects/<slug>.md  and use flat front matter -- the
parser here splits each line on its first colon, so no nested keys:

    ---
    title: Fiscal auditor
    summary: One line shown on the projects index.
    status: in-motion         in-motion | at-rest
    started: 2026-03          YYYY-MM, YYYY, or anything else (shown as written)
    updated: 2026-08
    built_with: Claude, Python, SQLite
    repo: https://github.com/...
    live: https://...
    weight: 5                 optional; orders within a status group
    ---
    Leading paragraphs become the state-of-play block.

    ## A heading with nothing under it is dropped

    ## Log
    - 2026-08 — What changed.

Then run:   python3 publish.py                both collections
            python3 publish.py --only projects

It regenerates:
    <site>/blog.html              the index, posts listed newest-first
    <site>/blog/<slug>.html       one themed page per post
    <site>/projects.html          the index, grouped active then shelved
    <site>/projects/<slug>.html   one themed page per project

The index is an ordinary page file like books.html or travel.html, so it is
served at korvanick.com/blog by the same mechanism as every other page. Only
the individual posts sit in the blog/ subdirectory, giving korvanick.com/blog/<slug>.
Generated pages in <site>/blog/ that no longer have a matching .md file are
deleted, so renaming or removing a post leaves no orphan behind.

Backdating is just the `date:` field -- set it to whatever you like and the
post sorts into that spot as if it had been online since then.

Projects sort by status, then by `weight` if given, then by `updated` newest
first. Empty headings are dropped from project bodies, so you can outline the
whole essay up front without shipping empty sections.

No dependencies required. If the `markdown` package happens to be installed it
will be used (fuller Markdown support); otherwise a built-in renderer covers
headings, bold/italic, links, images, lists, quotes, code blocks and rules.
"""

import argparse, datetime, html, json, re, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
# Posts are content: they sit in data/ alongside gallery.json and travel.json.
# Resolved against the PROJECT ROOT (the parent of automation/), never against
# the detected output directory -- those are different levels now that the HTML
# pages live in pages/, and tying them together created a stray pages/data/.
PROJECT_ROOT = SCRIPT_DIR.parent
POSTS_SUBDIR = Path("data") / "posts"
PROJECTS_SUBDIR = Path("data") / "projects"


def default_posts_dir():
    return PROJECT_ROOT / POSTS_SUBDIR


def default_projects_dir():
    return PROJECT_ROOT / PROJECTS_SUBDIR
# posts now live in <site>/blog/, so the only name that could clash is index
RESERVED = {"index"}

# ---------------------------------------------------------------- Markdown rendering
try:
    import markdown as _markdown
    def render_markdown(text):
        return _markdown.markdown(text, extensions=["fenced_code", "tables", "sane_lists"])
    RENDERER = "python-markdown"
except Exception:
    RENDERER = "built-in"

    def _inline(text):
        text = html.escape(text, quote=False)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1">', text)
        text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
        text = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"<em>\1</em>", text)
        return text

    def render_markdown(text):
        lines = text.replace("\r\n", "\n").split("\n")
        out, i, n = [], 0, len(lines)
        para = []

        def flush_para():
            if para:
                out.append("<p>" + "<br>".join(_inline(l) for l in para) + "</p>")
                para.clear()

        while i < n:
            line = lines[i]
            stripped = line.strip()

            if stripped.startswith("```"):                       # fenced code
                flush_para()
                i += 1
                buf = []
                while i < n and not lines[i].strip().startswith("```"):
                    buf.append(lines[i]); i += 1
                i += 1
                out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
                continue

            if not stripped:                                     # blank line
                flush_para(); i += 1; continue

            if re.match(r"^(---|\*\*\*|___)$", stripped):         # horizontal rule
                flush_para(); out.append("<hr>"); i += 1; continue

            m = re.match(r"^(#{1,6})\s+(.*)$", stripped)          # heading
            if m:
                flush_para()
                level = len(m.group(1))
                out.append(f"<h{level}>{_inline(m.group(2).strip())}</h{level}>")
                i += 1; continue

            if stripped.startswith(">"):                         # blockquote
                flush_para()
                buf = []
                while i < n and lines[i].strip().startswith(">"):
                    buf.append(re.sub(r"^\s*>\s?", "", lines[i])); i += 1
                out.append("<blockquote>" + "<br>".join(_inline(b) for b in buf) + "</blockquote>")
                continue

            if re.match(r"^[-*+]\s+", stripped):                 # unordered list
                flush_para()
                buf = []
                while i < n and re.match(r"^[-*+]\s+", lines[i].strip()):
                    buf.append(re.sub(r"^[-*+]\s+", "", lines[i].strip())); i += 1
                out.append("<ul>" + "".join(f"<li>{_inline(b)}</li>" for b in buf) + "</ul>")
                continue

            if re.match(r"^\d+\.\s+", stripped):                 # ordered list
                flush_para()
                buf = []
                while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                    buf.append(re.sub(r"^\d+\.\s+", "", lines[i].strip())); i += 1
                out.append("<ol>" + "".join(f"<li>{_inline(b)}</li>" for b in buf) + "</ol>")
                continue

            para.append(stripped); i += 1                        # paragraph text

        flush_para()
        return "\n".join(out)


def add_figures(html_str):
    """A standalone image on its own line becomes a <figure>. The image may be
    wrapped in a link -- ![alt](img "caption") inside [ ]( ) still gets picked
    up. The caption is the Markdown title if one is given, otherwise the alt
    text, so alt can stay descriptive for screen readers while the visible
    caption says something else. Images inside a sentence are left inline."""
    pattern = re.compile(
        r'<p>\s*'
        r'(?:(<a\b[^>]*>)\s*)?'      # optional opening link
        r'(<img\b[^>]*>)'            # the image itself
        r'(?:\s*(</a>))?'            # its matching close, if there was one
        r'\s*</p>'
    )

    def repl(m):
        open_a, img, close_a = m.group(1), m.group(2), m.group(3)
        if bool(open_a) != bool(close_a):
            return m.group(0)        # unbalanced link -- leave the paragraph alone
        title = re.search(r'title="([^"]*)"', img)
        alt = re.search(r'alt="([^"]*)"', img)
        text = (title.group(1) if title else (alt.group(1) if alt else "")).strip()
        caption = f"<figcaption>{text}</figcaption>" if text else ""
        inner = f"{open_a}{img}{close_a}" if open_a else img
        return f"<figure>{inner}{caption}</figure>"

    return pattern.sub(repl, html_str)


# ---------------------------------------------------------------- front matter + files
def slugify(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


def parse_post(path):
    raw = path.read_text(encoding="utf-8")
    meta, body = {}, raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            header = raw[3:end].strip()
            body = raw[end + 4:].lstrip("\n")
            for line in header.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip()
    slug = slugify(meta.get("slug") or path.stem)   # `slug:` wins, filename otherwise
    title = meta.get("title", path.stem)
    summary = meta.get("summary", "")
    date_str = meta.get("date", "")
    try:
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        print(f"  ! {path.name}: missing/invalid date (use YYYY-MM-DD) — sorting it last")
        date = datetime.date.min
    return {"slug": slug, "title": title, "summary": summary,
            "date": date, "body_html": add_figures(render_markdown(body))}


def find_site_dir(explicit):
    if explicit:
        d = Path(explicit).expanduser().resolve()
        if not d.is_dir():
            sys.exit(f"Not a directory: {d}")
        return d
    root = SCRIPT_DIR.parent
    hits = [p for p in root.rglob("books.html") if "node_modules" not in p.parts]
    if hits:
        return hits[0].parent
    return root


def nice_date(d):
    return f"{d:%B} {d.day}, {d.year}" if d != datetime.date.min else "Undated"


# ---------------------------------------------------------------- templates
# The header is rendered by scripts/nav.js from its own list of links, so the
# generated pages just leave it an empty element. Adding or renaming a page
# means editing LINKS in nav.js, not this file.
NAV = """  <nav></nav>"""

BASE_URL = "https://korvanick.com"
AUTHOR = "Nick Korhonen"
AUTHOR_URL = f"{BASE_URL}/professional"


def meta_block(path, title, description="", kind="website", published=""):
    """Description, canonical and Open Graph for a generated page.

    This is why it lives in the generator rather than in the HTML: every post
    and project written from here gets it without anyone remembering to.
    `description` comes from the front matter `summary`, which is already
    written for every post and shown on the index.
    """
    url = f"{BASE_URL}{path}"
    desc = " ".join(description.split())
    lines = []
    if desc:
        lines.append(f'  <meta name="description" content="{html.escape(desc, quote=True)}">')
    lines.append(f'  <link rel="canonical" href="{url}">')
    lines.append(f'  <meta property="og:type" content="{kind}">')
    lines.append('  <meta property="og:site_name" content="korvanick">')
    lines.append(f'  <meta property="og:url" content="{url}">')
    lines.append(f'  <meta property="og:title" content="{html.escape(title, quote=True)}">')
    if desc:
        lines.append(f'  <meta property="og:description" content="{html.escape(desc, quote=True)}">')
    if published:
        lines.append(f'  <meta property="article:published_time" content="{published}">')
        lines.append(f'  <meta property="article:author" content="{AUTHOR}">')
    return "\n".join(lines) + "\n"


def json_ld(payload):
    """Structured data. Built with json.dumps rather than a format string so a
    quote or an accent in a title can never break out of the block."""
    payload = {"@context": "https://schema.org", **payload}
    return ('  <script type="application/ld+json">\n  '
            + json.dumps(payload, indent=2, ensure_ascii=False).replace("\n", "\n  ")
            + "\n  </script>\n")


def head(title, extra_css=(), meta="", structured=""):
    # The theme is applied inline, before any stylesheet loads, so a light-mode
    # visitor never sees a dark flash. Kept byte-identical to the snippet in the
    # hand-written pages -- the localStorage key must match what nav.js writes.
    extra = "".join(f'  <link rel="stylesheet" href="{c}">\n' for c in extra_css)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script>(function(){{try{{if(localStorage.getItem("theme")==="light")document.documentElement.setAttribute("data-theme","light");}}catch(e){{}}}})();</script>
  <title>{html.escape(title)} - korvanick</title>
{meta}  <link rel="stylesheet" href="/css/styles.css">
  <link rel="stylesheet" href="/css/blog.css">
{extra}  <link rel="icon" href="/images/favicon/favicon.ico" type="image/x-icon">
  <link rel="alternate" type="application/atom+xml" title="korvanick blog" href="/feed.xml">
  <script src="/scripts/nav.js" defer></script>
{structured}</head>"""

def render_index(posts):
    items = []
    for p in posts:
        summary = f'<span class="post-summary">{html.escape(p["summary"])}</span>' if p["summary"] else ""
        items.append(f"""    <li class="post-item">
      <a class="post-link" href="/blog/{p['slug']}">
        <span class="post-date">{nice_date(p['date'])}</span>
        <span class="post-name">{html.escape(p['title'])}</span>
        {summary}
      </a>
    </li>""")
    body = "\n".join(items) if items else '    <li class="post-item empty">No posts yet.</li>'
    meta = meta_block("/blog", "Blog",
                      "Writing by Nick Korhonen: travel, engineering and whatever "
                      "else is holding his attention.")
    ld = json_ld({
        "@type": "Blog",
        "name": "Blog",
        "url": f"{BASE_URL}/blog",
        "author": {"@type": "Person", "name": AUTHOR, "url": AUTHOR_URL},
        "blogPost": [{"@type": "BlogPosting",
                      "headline": q["title"],
                      "datePublished": q["date"].isoformat(),
                      "url": f"{BASE_URL}/blog/{q['slug']}"} for q in posts],
    })
    return f"""{head('Blog', meta=meta, structured=ld)}
<body>
{NAV}
  <main class="blog-index">
    <!-- Hidden, like the headings on /books and /photos: a dated list of
         titled pieces announces itself. The <h1> stays so the document has a
         heading and a screen reader has somewhere to land. -->
    <h1 class="visually-hidden">Blog</h1>
    <ul class="post-list">
{body}
    </ul>
  </main>
</body>
</html>
"""

def nav_item(p, direction, base, meta):
    """One side of the footer nav. `direction` is 'prev' or 'next'; which
    neighbour each one points at is the caller's decision, because the two
    collections order themselves differently -- see the notes in build_posts
    and build_projects. Renders an empty placeholder at the ends of the list so
    the middle link stays centred.

    `base` is the collection URL and `meta` a function returning the small line
    under the title -- a date for posts, status plus date for projects."""
    if not p:
        return f'        <span class="post-nav-item {direction} empty"></span>'
    label = "&larr; Previous" if direction == "prev" else "Next &rarr;"
    return f"""        <a class="post-nav-item {direction}" href="{base}/{p['slug']}">
          <span class="post-nav-label">{label}</span>
          <span class="post-nav-title">{html.escape(p['title'])}</span>
          <span class="post-nav-date">{meta(p)}</span>
        </a>"""


def render_footer_nav(prev, nxt, base, home_label, meta):
    """The prev / all / next block at the foot of a post or a project. One
    function and one set of classes for both, so the two collections cannot
    drift apart visually -- blog.css owns the styling and is loaded on project
    pages too."""
    return f"""      <nav class="post-nav">
{nav_item(prev, "prev", base, meta)}
        <a class="post-nav-home" href="{base}">{home_label}</a>
{nav_item(nxt, "next", base, meta)}
      </nav>"""


def render_post_nav(older, newer):
    return render_footer_nav(older, newer, "/blog", "All posts",
                             lambda p: nice_date(p["date"]))


def render_post(p, older=None, newer=None):
    meta = meta_block(f"/blog/{p['slug']}", p["title"], p["summary"],
                      kind="article", published=p["date"].isoformat())
    ld = json_ld({
        "@type": "BlogPosting",
        "headline": p["title"],
        "datePublished": p["date"].isoformat(),
        "url": f"{BASE_URL}/blog/{p['slug']}",
        **({"description": " ".join(p["summary"].split())} if p["summary"] else {}),
        "author": {"@type": "Person", "name": AUTHOR, "url": AUTHOR_URL},
        "mainEntityOfPage": f"{BASE_URL}/blog/{p['slug']}",
    })
    return f"""{head(p['title'], meta=meta, structured=ld)}
<body>
{NAV}
  <main class="post">
    <article>
      <a class="back-link" href="/blog">&larr; Blog</a>
      <h1 class="post-heading">{html.escape(p['title'])}</h1>
      <p class="post-meta"><time datetime="{p['date'].isoformat()}">{nice_date(p['date'])}</time></p>
      <div class="post-body">
{p['body_html']}
      </div>
{render_post_nav(older, newer)}
    </article>
  </main>
</body>
</html>
"""


# ---------------------------------------------------------------- projects
STATUS_ORDER = ["in-motion", "at-rest"]
# Two states, deliberately. The KEYS are what the front matter carries, so
# changing a label here never touches a single .md file.
#
# "In motion" / "At rest" rather than active/shelved: every word that pairs with
# "Active" gets read as its negative, so shelved, set aside and every synonym
# landed as "gave up". A symmetric pair has no negative pole -- a body at rest
# has not failed at anything, it is simply not moving. What a reader wants to
# know beyond that is already beside each project: its summary, and its date.
STATUS_LABEL = {"in-motion": "In motion", "at-rest": "At rest"}

# How long a project can go untouched before the page stops calling it live.
# Three months fits the way these actually get worked on: a burst, then months
# of nothing, then another burst.
STALE_AFTER_MONTHS = 3


def derive_status(key):
    """A project with no `status:` is described by its own dates. Recent work
    means in motion, nothing for a season means at rest.

    An explicit `status:` in the front matter still wins, for the case dates
    cannot see: a project logged this month because the decision was to shelve
    it."""
    if not key:
        return "in-motion"
    try:
        year, month = (int(part) for part in key.split("-")[:2])
    except ValueError:
        return "in-motion"
    # A bare year parses to month 00. Read it as the end of that year, so a
    # vague date is never treated as staler than it might be.
    month = min(max(month, 1), 12)
    today = datetime.date.today()
    elapsed = (today.year - year) * 12 + (today.month - month)
    return "in-motion" if elapsed < STALE_AFTER_MONTHS else "at-rest"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def month_label(raw):
    """Dates on a project are only ever as precise as they really are. YYYY-MM
    prints as 'Mar 2026', a bare year prints as itself, and anything else --
    'TODO', 'summer 2024' -- is shown exactly as written rather than guessed at.
    Returns (display, sort_key); unparseable values sort last."""
    raw = (raw or "").strip()
    if not raw:
        return "", ""
    m = re.match(r"^(\d{4})-(\d{1,2})", raw)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12:
            return f"{MONTHS[mo - 1]} {y}", f"{y:04d}-{mo:02d}"
    if re.match(r"^\d{4}$", raw):
        return raw, f"{raw}-00"
    return raw, ""


def strip_empty_headings(text):
    """Drop a heading that has no content beneath it, so an outline written in
    advance doesn't ship as a row of empty sections. A heading is kept if any
    non-blank line before the next heading of the same or higher level has real
    content in it."""
    lines = text.replace("\r\n", "\n").split("\n")
    keep, i, n = [], 0, len(lines)
    while i < n:
        m = re.match(r"^(#{1,6})\s+", lines[i])
        if not m:
            keep.append(lines[i]); i += 1; continue
        level = len(m.group(1))
        j = i + 1
        has_body = False
        while j < n:
            nxt = re.match(r"^(#{1,6})\s+", lines[j])
            if nxt and len(nxt.group(1)) <= level:
                break
            if lines[j].strip():
                has_body = True
            j += 1
        if has_body:
            keep.append(lines[i])
        i += 1
    return "\n".join(keep)


def split_log(body):
    """Peel the trailing '## Log' section off the body. Entries look like
        - 2026-08 — What changed.
    and are returned as (date, text) pairs, newest first as written. An em dash
    or a double hyphen both work as the separator; an entry with neither keeps
    its whole line as the text."""
    m = re.search(r"^#{1,6}\s+Log\s*$", body, re.MULTILINE | re.IGNORECASE)
    if not m:
        return body, []
    before, after = body[:m.start()], body[m.end():]
    entries, ignored = [], []
    for line in after.splitlines():
        line = line.strip()
        if not line.startswith("-"):
            # Anything below '## Log' that is not a list item is discarded. That
            # used to happen in silence, which is exactly how a note written at
            # the end of the file disappears without a word.
            if line:
                ignored.append(line)
            continue
        item = line.lstrip("-").strip()
        parts = re.split(r"\s+(?:\u2014|--)\s+", item, maxsplit=1)
        if len(parts) == 2:
            when = parts[0].strip()
            # A scaffolded TODO must not reach the page, and the date should
            # read the same here as it does in the spec line above -- "Aug
            # 2026", not "2026-08".
            if when.lower() in PLACEHOLDERS:
                when = ""
            else:
                when = month_label(when)[0] or when
            entries.append((when, parts[1].strip()))
        else:
            entries.append(("", item))
    if ignored:
        DISCARDED.append((len(ignored), ignored[0]))
    return before, entries


# Values a scaffolder writes as a reminder. Treated as absent, and reported at
# the end of a build so they are easy to find.
PLACEHOLDERS = {"todo", "tbd", "tba", "{}", "[]", "-", "n/a"}

UNFILLED = []

# Lines found under '## Log' that were not log entries, so were thrown away.
DISCARDED = []


def parse_project(path):
    raw = path.read_text(encoding="utf-8")
    meta, body = {}, raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            for line in raw[3:end].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    v = v.strip()
                    # A scaffolded field nobody filled in must not reach the
                    # page. "Active - TODO -> Aug 2026" was live on five
                    # project pages because these passed straight through.
                    if v.lower() in PLACEHOLDERS:
                        v = ""
                    meta[k.strip().lower()] = v
            body = raw[end + 4:].lstrip("\n")

    body, log = split_log(body)
    body = strip_empty_headings(body)

    # Everything before the first heading is the state-of-play block; the rest
    # is the essay and gets the same .post-body treatment as a blog post.
    m = re.search(r"^#{1,6}\s+", body, re.MULTILINE)
    intro, essay = (body[:m.start()], body[m.start():]) if m else (body, "")

    for field in ("summary", "started", "updated", "built_with", "image"):
        if not meta.get(field):
            UNFILLED.append(f"{path.name}: {field}")

    started, started_key = month_label(meta.get("started"))
    updated, updated_key = month_label(meta.get("updated"))

    # Status is worked out from the dates unless the file says otherwise, so a
    # project goes quiet on its own rather than waiting to be told to.
    status = meta.get("status", "").strip().lower()
    if status and status not in STATUS_ORDER:
        print(f"  ! {path.name}: unknown status '{status}' -- deriving it instead")
        status = ""
    status = status or derive_status(updated_key or started_key)

    try:
        weight = int(meta.get("weight", ""))
    except ValueError:
        weight = 9999

    # Accept both "Claude, Python" and "[Claude, Python]". Every project file
    # on disk uses the bracketed form, and splitting it on commas alone put
    # "[Claude" and "SQLite]" on the page, brackets included.
    built = [b.strip() for b in meta.get("built_with", "").strip("[]").split(",")
             if b.strip()]
    links = [(label, meta[key]) for key, label in
             (("repo", "Repository"), ("live", "Live"), ("docs", "Docs"))
             if meta.get(key)]

    return {
        # The `slug:` line wins when present, so renaming a project is a
        # one-line edit rather than a file rename. Falls back to the filename,
        # which is what every project used before this field did anything.
        "slug": slugify(meta.get("slug") or path.stem),
        "title": meta.get("title", path.stem),
        # A picture of the thing, shown on the index card and above the page.
        # Any path works; /images/projects/<slug>/... keeps them out of the
        # photo gallery, which update_gallery.py walks looking for EXIF.
        "image": meta.get("image", ""),
        "image_alt": meta.get("image_alt", ""),
        # Optional. With one the cover becomes a <figure>; without, a bare <img>.
        # alt is what a screen reader hears, caption is what everyone reads --
        # so they are separate fields and neither substitutes for the other.
        "image_caption": meta.get("image_caption", ""),
        "summary": meta.get("summary", ""),
        "status": status, "weight": weight,
        "started": started, "updated": updated, "updated_key": updated_key,
        "built": built, "links": links,
        "intro_html": render_markdown(intro.strip()),
        "body_html": add_figures(render_markdown(essay)) if essay.strip() else "",
        "log": log,
    }


def spec_line(p):
    """Status, the dates at whatever precision they were given, and what the
    thing is built with. 'Built with' rather than 'Stack' on purpose: it says
    what went into the project, not what the author claims to command."""
    bits = [STATUS_LABEL[p["status"]]]
    # Same month at both ends is one date wearing an arrow. Fall through and
    # let it say "Started May 2026" instead of pointing at itself.
    if p["started"] and p["updated"] and p["started"] != p["updated"]:
        bits.append(f"{html.escape(p['started'])} &rarr; {html.escape(p['updated'])}")
    elif p["started"]:
        bits.append("Started " + html.escape(p["started"]))
    elif p["updated"]:
        # One bare date is ambiguous -- a reader cannot tell a start from a last
        # touch. Say which it is.
        bits.append("Updated " + html.escape(p["updated"]))
    if p["built"]:
        bits.append("Built with " + html.escape(", ".join(p["built"])))
    return " &middot; ".join(bits)


def project_nav_meta(p):
    """The small line under the title in the footer nav. Status first, because
    a walk down the index crosses from In motion into At rest and this is the
    line that says so before the click; a bare date would read like a
    publication date, which a project has not got. Prefers the last touch over
    the start -- it is the more recent fact and it is what the index sorted
    on."""
    bits = [STATUS_LABEL[p["status"]]]
    when = p["updated"] or p["started"]
    if when:
        bits.append(html.escape(when))
    return " &middot; ".join(bits)


def render_project_nav(prev, nxt):
    return render_footer_nav(prev, nxt, "/projects", "All projects",
                             project_nav_meta)


def render_projects_index(projects):
    groups = []
    for status in STATUS_ORDER:
        members = [p for p in projects if p["status"] == status]
        if not members:
            continue
        items = []
        for p in members:
            summary = (f'\n          <span class="project-summary">{html.escape(p["summary"])}</span>'
                       if p["summary"] else "")
            # Decorative here: the project name sits right beside it, so an alt
            # repeating the title would just be read out twice.
            cover = (f'\n          <img class="project-thumb" src="{html.escape(p["image"], quote=True)}" '
                     f'alt="" loading="lazy">' if p["image"] else "")
            items.append(f"""      <li class="project-item {p['status']}">
        <a class="project-link" href="/projects/{p['slug']}">{cover}
          <span class="project-name">{html.escape(p['title'])}</span>{summary}
          <span class="project-spec">{spec_line(p)}</span>
        </a>
      </li>""")
        groups.append(f"""    <h2 class="status-group">{STATUS_LABEL[status]}</h2>
    <ul class="project-list">
{chr(10).join(items)}
    </ul>""")
    body = "\n\n".join(groups) if groups else \
        '    <ul class="project-list">\n      <li class="project-item empty">Nothing here yet.</li>\n    </ul>'
    meta = meta_block("/projects", "Projects",
                      "Things Nick Korhonen is building, and the ones he has set aside.")
    ld = json_ld({
        "@type": "CollectionPage",
        "name": "Projects",
        "url": f"{BASE_URL}/projects",
        "author": {"@type": "Person", "name": AUTHOR, "url": AUTHOR_URL},
    })
    return f"""{head('Projects', ['/css/projects.css'], meta=meta, structured=ld)}
<body>
{NAV}
  <main class="projects-index">
    <!-- Hidden. The status headings and each project's own summary carry it. -->
    <h1 class="visually-hidden">Projects</h1>

{body}

  </main>
</body>
</html>
"""


def with_anchors(body_html):
    """Give every <h2> in a project body an id, and return a contents list.

    This is what stops a project page turning into one long block as sections
    accumulate: each decision is its own linkable section, and once there are a
    few of them a reader gets a list to jump from. Below three sections there is
    nothing worth listing, so nothing is emitted.
    """
    found = []

    def tag(m):
        text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        slug = slugify(text) or f"section-{len(found) + 1}"
        while slug in [s for s, _ in found]:
            slug += "-x"
        found.append((slug, text))
        return f'<h2 id="{slug}"{m.group(1)}>{m.group(2)}</h2>'

    body_html = re.sub(r"<h2([^>]*)>(.*?)</h2>", tag, body_html, flags=re.S)
    if len(found) < 3:
        return body_html, ""

    items = "\n".join(
        f'          <li><a href="#{slug}">{html.escape(text)}</a></li>' for slug, text in found)
    contents = ('      <nav class="project-contents" aria-label="Sections">\n'
                '        <ul>\n' + items + "\n        </ul>\n      </nav>\n")
    return body_html, contents


def render_project(p, prev=None, nxt=None):
    links = ""
    if p["links"]:
        joined = ' <span>&middot;</span> '.join(
            f'<a href="{html.escape(u, quote=True)}">{html.escape(n)}</a>' for n, u in p["links"])
        links = f'      <p class="project-links">{joined}</p>\n'

    intro = (f'      <div class="project-state">\n{p["intro_html"]}\n      </div>\n'
             if p["intro_html"] else "")
    body_html, contents = with_anchors(p["body_html"]) if p["body_html"] else ("", "")
    essay = (f'      <div class="post-body">\n{body_html}\n      </div>\n'
             if body_html else "")

    cover = ""
    if p["image"]:
        alt = p["image_alt"] or f'{p["title"]}'
        img = (f'<img class="project-cover" src="{html.escape(p["image"], quote=True)}" '
               f'alt="{html.escape(alt, quote=True)}">')
        if p["image_caption"]:
            cover = (f'      <figure class="project-cover-figure">{img}'
                     f'<figcaption>{html.escape(p["image_caption"])}</figcaption>'
                     f'</figure>\n')
        else:
            cover = f'      {img}\n'

    log = ""
    if p["log"]:
        rows = "\n".join(
            f'          <li><span class="log-date">{html.escape(d)}</span>'
            f'<span>{html.escape(t)}</span></li>' for d, t in p["log"])
        log = f"""      <div class="project-log">
        <h2>Log</h2>
        <ul>
{rows}
        </ul>
      </div>
"""

    meta = meta_block(f"/projects/{p['slug']}", p["title"], p["summary"], kind="article")
    ld = json_ld({
        "@type": "CreativeWork",
        "name": p["title"],
        "url": f"{BASE_URL}/projects/{p['slug']}",
        **({"description": " ".join(p["summary"].split())} if p["summary"] else {}),
        "author": {"@type": "Person", "name": AUTHOR, "url": AUTHOR_URL},
    })
    return f"""{head(p['title'], ['/css/projects.css'], meta=meta, structured=ld)}
<body>
{NAV}
  <main class="project">
    <article>
      <a class="back-link" href="/projects">&larr; Projects</a>
      <h1 class="project-heading">{html.escape(p['title'])}</h1>
      <p class="project-spec">{spec_line(p)}</p>
{links}{cover}{intro}{contents}{essay}{log}{render_project_nav(prev, nxt)}
    </article>
  </main>
</body>
</html>
"""


def build_projects(site_dir, projects_dir):
    files = [f for f in sorted(projects_dir.glob("*.md")) if not f.name.startswith("_")]
    if not files:
        print(f"  (no .md files in {projects_dir} — skipping projects)")
        return

    projects = []
    for f in files:
        p = parse_project(f)
        if p["slug"] in RESERVED:
            print(f"  ! {f.name}: slug '{p['slug']}' collides with an existing page — skipped")
            continue
        projects.append(p)

    # status group, then the manual pin, then most recently touched. An unknown
    # or missing `updated` sorts last within its group rather than first.
    projects.sort(key=lambda p: (STATUS_ORDER.index(p["status"]),
                                 p["weight"],
                                 p["updated_key"] == "",
                                 [-ord(c) for c in p["updated_key"]]))

    out_dir = site_dir / "projects"
    out_dir.mkdir(exist_ok=True)
    for i, p in enumerate(projects):
        # Reading order, not the blog's. On /blog, down the page means earlier
        # in time, so the one below is "Previous". A project list has no time
        # axis -- down the page just means the next one, and someone who
        # arrived from the top of the index expects "Next" to continue down it.
        #
        # The walk crosses the In motion / At rest boundary deliberately. The
        # status sits under the title in every card, so a reader is told which
        # group they are about to enter before they click.
        prev = projects[i - 1] if i > 0 else None
        nxt = projects[i + 1] if i + 1 < len(projects) else None
        (out_dir / f"{p['slug']}.html").write_text(
            render_project(p, prev, nxt), encoding="utf-8")
        print(f"  project projects/{p['slug']}.html   ({STATUS_LABEL[p['status']]})")

    warn_relative_images(projects, "projects")

    current = {p["slug"] for p in projects}
    for stale in sorted(out_dir.glob("*.html")):
        if stale.stem not in current:
            warn_inbound_links(site_dir, f"/projects/{stale.stem}")
            stale.unlink()
            print(f"  removed projects/{stale.name} (no matching .md)")

    (site_dir / "projects.html").write_text(render_projects_index(projects), encoding="utf-8")
    n = len(projects)
    print(f"\n  index projects.html   ({n} project{'s' if n != 1 else ''})")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Build the korvanick blog and projects pages from Markdown.")
    ap.add_argument("--site", help="directory that holds your .html pages (auto-detected otherwise)")
    ap.add_argument("--posts", help="directory of .md posts (default: <project>/data/posts)")
    ap.add_argument("--projects", help="directory of .md projects (default: <project>/data/projects)")
    ap.add_argument("--only", choices=["blog", "projects"],
                    help="build just one collection (default: both)")
    args = ap.parse_args()

    site_dir = find_site_dir(args.site)
    posts_dir = (Path(args.posts).expanduser().resolve() if args.posts
                 else default_posts_dir())
    projects_dir = (Path(args.projects).expanduser().resolve() if args.projects
                    else default_projects_dir())

    do_blog = args.only in (None, "blog")
    do_projects = args.only in (None, "projects")

    print(f"Renderer: {RENDERER}")
    print(f"Output:   {site_dir}\n")

    if do_projects:
        if projects_dir.is_dir():
            print(f"Projects: {projects_dir}")
            build_projects(site_dir, projects_dir)
            print()
        elif args.only == "projects":
            sys.exit(f"No projects directory at {projects_dir} — create it and add .md files.")

    if not do_blog:
        print("Done. Remember css/blog.css and css/projects.css must be in place.")
        finish(site_dir, posts_dir)
        return

    if not posts_dir.is_dir():
        sys.exit(f"No posts directory at {posts_dir} — create it and add .md files.")

    files = [f for f in sorted(posts_dir.glob("*.md")) if not f.name.startswith("_")]
    if not files:
        sys.exit(f"No .md files found in {posts_dir}.")

    print(f"Posts:    {posts_dir}")

    posts = []
    for f in files:
        p = parse_post(f)
        if p["slug"] in RESERVED:
            print(f"  ! {f.name}: slug '{p['slug']}' collides with an existing page — skipped")
            continue
        posts.append(p)

    posts.sort(key=lambda p: p["date"], reverse=True)   # newest first

    blog_dir = site_dir / "blog"
    blog_dir.mkdir(exist_ok=True)

    # posts is newest-first, so the OLDER neighbour sits later in the list and
    # the NEWER one sits earlier -- "previous" in the footer means earlier in time
    for i, p in enumerate(posts):
        # Chronological, so "Previous" is the older post -- the one further
        # DOWN a newest-first index. Projects flip this on purpose; see
        # build_projects.
        older = posts[i + 1] if i + 1 < len(posts) else None
        newer = posts[i - 1] if i > 0 else None
        (blog_dir / f"{p['slug']}.html").write_text(
            render_post(p, older, newer), encoding="utf-8")
        print(f"  post  blog/{p['slug']}.html   ({nice_date(p['date'])})")

    # any generated page without a matching .md is an orphan from a rename or
    # a deleted post -- remove it so it stops being reachable
    current = {p["slug"] for p in posts}
    for stale in sorted(blog_dir.glob("*.html")):
        if stale.stem not in current:
            warn_inbound_links(site_dir, f"/blog/{stale.stem}")
            stale.unlink()
            print(f"  removed blog/{stale.name} (no matching .md)")

    (site_dir / "blog.html").write_text(render_index(posts), encoding="utf-8")
    print(f"\n  index blog.html   ({len(posts)} post{'s' if len(posts) != 1 else ''})")
    write_feed(posts, PROJECT_ROOT / "feed.xml")
    warn_thumbnail_images(posts)
    warn_relative_images(posts, "blog")
    print("\nDone. Remember css/blog.css and css/projects.css must be in place.")

    # Earlier versions wrote the index and every post into the site root. Those
    # files are not ours to delete automatically, but a stale blog.html will be
    # served in preference to blog/index.html on most try_files setups, so it
    # matters that they get flagged.
    legacy = []
    stale_index = blog_dir / "index.html"
    if stale_index.exists():
        legacy.append(stale_index)
    for f in sorted(site_dir.glob("*.html")):
        try:
            if 'class="post-heading"' in f.read_text(encoding="utf-8", errors="ignore"):
                legacy.append(f)
        except OSError:
            pass
    if legacy:
        print("\nLeftovers from an earlier layout:")
        for f in legacy:
            print(f"  {f}")
        print("Safe to delete -- the index is blog.html and posts live in blog/.")

    finish(site_dir, posts_dir)


def warn_inbound_links(site_dir, url):
    """Shout if a page about to disappear is still linked from somewhere.

    Changing a slug renames the page, and the old URL stops existing. The build
    cannot fix a hand-written href for you, but it can refuse to let one rot
    quietly -- /professional links to /projects/korvanick, and nothing else on
    the site would have noticed that going away.
    """
    # Only hand-written pages count. blog.html, projects.html and everything
    # under those folders are rewritten by this same run, so they already carry
    # the NEW slug -- flagging them would be a false alarm on every rename, and
    # a warning that cries wolf gets ignored.
    generated = {"blog.html", "projects.html"}
    generated_dirs = {site_dir / "blog", site_dir / "projects"}

    holders = []
    seen = set()
    for root in (site_dir, site_dir.parent):
        for html in sorted(root.glob("*.html")) + sorted(root.glob("*/*.html")):
            if html in seen or html.name in generated or html.parent in generated_dirs:
                continue
            seen.add(html)
            try:
                if f'href="{url}"' in html.read_text(encoding="utf-8", errors="ignore"):
                    holders.append(html.name)
            except OSError:
                pass
    if holders:
        print(f"  ! {url} is going away but is still linked from: "
              + ", ".join(sorted(set(holders))))


def report_discarded():
    if not DISCARDED:
        return
    print("\n  ! text below '## Log' was DISCARDED -- everything after that heading")
    print("    is read as log entries. Move prose ABOVE the log heading:")
    for count, first in DISCARDED:
        snippet = first if len(first) <= 58 else first[:58] + "..."
        print(f"      {count} line{'s' if count != 1 else ''}, starting: {snippet}")


def report_unfilled():
    if not UNFILLED:
        return
    print(f"\nFront matter still to fill in ({len(UNFILLED)}):")
    for item in UNFILLED:
        print(f"  {item}")


# ------------------------------------------------------------------- feed
def write_feed(posts, out):
    """An Atom feed at /feed.xml, built from the same sorted list the index uses.

    Atom rather than RSS: dates are unambiguous ISO 8601 and every reader
    handles it. Full post bodies go in, so a reader shows the whole piece --
    the site is not selling clicks.

    The <id> values are permanent URLs. Reslugging a post therefore makes a
    reader treat it as a new entry; that is the same trade the URL change makes
    anyway, and it is the reason slugs are worth settling before publishing.
    """
    def tag(text):
        return html.escape(text or "", quote=False)

    updated = max((q["date"] for q in posts), default=None)
    stamp = f"{updated.isoformat()}T00:00:00Z" if updated else \
        datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    entries = []
    for q in posts:
        entries.append(f"""  <entry>
    <title>{tag(q['title'])}</title>
    <link href="{BASE_URL}/blog/{q['slug']}"/>
    <id>{BASE_URL}/blog/{q['slug']}</id>
    <updated>{q['date'].isoformat()}T00:00:00Z</updated>
    <summary>{tag(q['summary'])}</summary>
    <content type="html">{html.escape(q['body_html'])}</content>
  </entry>""")

    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>korvanick</title>
  <subtitle>Writing by {AUTHOR}</subtitle>
  <link href="{BASE_URL}/feed.xml" rel="self"/>
  <link href="{BASE_URL}/blog"/>
  <id>{BASE_URL}/blog</id>
  <updated>{stamp}</updated>
  <author><name>{AUTHOR}</name><uri>{AUTHOR_URL}</uri></author>
{chr(10).join(entries)}
</feed>
"""
    out.write_text(xml, encoding="utf-8")
    print(f"  feed  /feed.xml   ({len(posts)} entr{'y' if len(posts) == 1 else 'ies'})")


def warn_relative_images(items, kind):
    """A generated page lives one directory down -- /blog/<slug>, /projects/<slug>
    -- so a relative image path resolves against that folder, not the site root,
    and 404s. Easy to type, invisible until you look at the page."""
    import re as _re
    guilty = []
    for q in items:
        for src in _re.findall(r'<img[^>]+src="([^"]+)"', q.get("body_html", "")):
            if not src.startswith(("/", "http://", "https://", "data:")):
                guilty.append((q["slug"], src))
    if guilty:
        print(f"\n  ! relative image paths in {kind} -- these will 404. "
              f"Start the path with a slash:")
        for slug, src in guilty:
            print(f"      {slug}:  {src}  ->  /images/{kind}/{src}")


def warn_thumbnail_images(posts):
    """Gallery thumbnails are 500px on the long edge; the prose column is 700px.
    An image pasted straight from the gallery therefore renders upscaled and
    soft, which is easy to do and hard to notice."""
    guilty = [q["slug"] for q in posts if "/images/gallery/thumbs/" in q["body_html"]]
    if guilty:
        print("\n  ! these posts link a gallery THUMBNAIL, which upscales in the "
              "prose column:")
        for slug in guilty:
            print(f"      {slug}  -- drop '/thumbs' from the image path")


def finish(site_dir, posts_dir):
    """The two things that must happen however the build exits."""
    report_discarded()
    report_unfilled()
    refresh_sitemap(site_dir, posts_dir)


def refresh_sitemap(site_dir, posts_dir):
    """Rewrite sitemap.xml now that the pages have changed.

    This is the whole reason the sitemap stopped going stale: the only things
    that create or delete a page are this script and a text editor, and this
    script can just say so. Failure here is not worth losing a good build over,
    so it reports and carries on.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import auto_sitemap
        auto_sitemap.build(site_dir=site_dir, posts_dir=posts_dir)
    except Exception as e:
        print(f"\n  sitemap not updated: {e}")
        print("  run  python3 automation/auto_sitemap.py  when convenient")


if __name__ == "__main__":
    main()
