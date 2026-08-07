#!/usr/bin/env python3
"""
build_blog.py -- turn Markdown posts into themed blog pages for Korvanick.

Write each post as a Markdown file in  data/posts/<slug>.md  (next to
gallery.json and travel.json) with a small front-matter header:

    ---
    title: The Long Way Around
    date: 2024-08-12
    summary: One or two lines shown on the blog index.
    ---
    Your **Markdown** body goes here...

Then run:   python3 build_blog.py

It regenerates:
    <site>/blog.html          the index, posts listed newest-first
    <site>/blog/<slug>.html   one themed page per post

The index is an ordinary page file like books.html or travel.html, so it is
served at korvanick.com/blog by the same mechanism as every other page. Only
the individual posts sit in the blog/ subdirectory, giving korvanick.com/blog/<slug>.
Generated pages in <site>/blog/ that no longer have a matching .md file are
deleted, so renaming or removing a post leaves no orphan behind.

Backdating is just the `date:` field -- set it to whatever you like and the
post sorts into that spot as if it had been online since then.

No dependencies required. If the `markdown` package happens to be installed it
will be used (fuller Markdown support); otherwise a built-in renderer covers
headings, bold/italic, links, images, lists, quotes, code blocks and rules.
"""

import argparse, datetime, html, re, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
# Posts are content: they sit in data/ alongside gallery.json and travel.json.
# Resolved against the PROJECT ROOT (the parent of automation/), never against
# the detected output directory -- those are different levels now that the HTML
# pages live in pages/, and tying them together created a stray pages/data/.
PROJECT_ROOT = SCRIPT_DIR.parent
POSTS_SUBDIR = Path("data") / "posts"


def default_posts_dir():
    return PROJECT_ROOT / POSTS_SUBDIR
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
    slug = re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")
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

def head(title):
    # The theme is applied inline, before any stylesheet loads, so a light-mode
    # visitor never sees a dark flash. Kept byte-identical to the snippet in the
    # hand-written pages -- the localStorage key must match what nav.js writes.
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script>(function(){{try{{if(localStorage.getItem("theme")==="light")document.documentElement.setAttribute("data-theme","light");}}catch(e){{}}}})();</script>
  <title>{html.escape(title)} - Korvanick</title>
  <link rel="stylesheet" href="/css/styles.css">
  <link rel="stylesheet" href="/css/blog.css">
  <link rel="icon" href="/images/favicon/favicon.ico" type="image/x-icon">
  <script src="/scripts/nav.js" defer></script>
</head>"""

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
    return f"""{head('Blog')}
<body>
{NAV}
  <main class="blog-index">
    <h1 class="blog-title">Blog</h1>
    <ul class="post-list">
{body}
    </ul>
  </main>
</body>
</html>
"""

def nav_item(p, direction):
    """One side of the footer nav. `direction` is 'prev' (the older post) or
    'next' (the newer one). Renders an empty placeholder at the ends of the
    archive so the middle link stays centred."""
    if not p:
        return f'        <span class="post-nav-item {direction} empty"></span>'
    label = "&larr; Previous" if direction == "prev" else "Next &rarr;"
    return f"""        <a class="post-nav-item {direction}" href="/blog/{p['slug']}">
          <span class="post-nav-label">{label}</span>
          <span class="post-nav-title">{html.escape(p['title'])}</span>
          <span class="post-nav-date">{nice_date(p['date'])}</span>
        </a>"""


def render_post_nav(older, newer):
    return f"""      <nav class="post-nav">
{nav_item(older, "prev")}
        <a class="post-nav-home" href="/blog">All posts</a>
{nav_item(newer, "next")}
      </nav>"""


def render_post(p, older=None, newer=None):
    return f"""{head(p['title'])}
<body>
{NAV}
  <main class="post">
    <article>
      <a class="back-link" href="/blog">&larr; Blog</a>
      <h1 class="post-heading">{html.escape(p['title'])}</h1>
      <p class="post-meta">{nice_date(p['date'])}</p>
      <div class="post-body">
{p['body_html']}
      </div>
{render_post_nav(older, newer)}
    </article>
  </main>
</body>
</html>
"""


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Build the Korvanick blog from Markdown posts.")
    ap.add_argument("--site", help="directory that holds your .html pages (auto-detected otherwise)")
    ap.add_argument("--posts", help="directory of .md posts (default: <project>/data/posts)")
    args = ap.parse_args()

    site_dir = find_site_dir(args.site)
    posts_dir = (Path(args.posts).expanduser().resolve() if args.posts
                 else default_posts_dir())
    if not posts_dir.is_dir():
        sys.exit(f"No posts directory at {posts_dir} — create it and add .md files.")

    files = [f for f in sorted(posts_dir.glob("*.md")) if not f.name.startswith("_")]
    if not files:
        sys.exit(f"No .md files found in {posts_dir}.")

    print(f"Renderer: {RENDERER}")
    print(f"Posts:    {posts_dir}")
    print(f"Output:   {site_dir}\n")

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
            stale.unlink()
            print(f"  removed blog/{stale.name} (no matching .md)")

    (site_dir / "blog.html").write_text(render_index(posts), encoding="utf-8")
    print(f"\n  index blog.html   ({len(posts)} post{'s' if len(posts) != 1 else ''})")
    print("\nDone. Remember css/blog.css must be in place.")

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


if __name__ == "__main__":
    main()
