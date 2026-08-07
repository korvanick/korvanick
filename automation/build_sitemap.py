#!/usr/bin/env python3
"""Generate sitemap.xml for korvanick.com.

Walks the built HTML and writes <project>/sitemap.xml using the site's clean
URLs:

    index.html            ->  /
    pages/<name>.html     ->  /<name>
    pages/blog/<slug>.html->  /blog/<slug>

Zero dependencies. Run by hand, or let build_blog.py call build() after it
regenerates the blog.

    python3 automation/build_sitemap.py
    python3 automation/build_sitemap.py --dry-run
"""

import argparse
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

BASE_URL = "https://korvanick.com"

# Pages that exist on disk but must never be advertised.
EXCLUDE = {"hidden1", "contact", "404"}

PROJECT = Path(__file__).resolve().parent.parent
FRONT_DATE = re.compile(r"^date:\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE)


def mtime_date(path: Path) -> date:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).date()


def post_date(slug: str, posts_dir: Path, html: Path) -> date:
    """Published date from the source .md front matter; mtime as a fallback.

    build_blog.py rewrites every post's HTML on each run, so the generated
    file's mtime is always "today" and is useless as a lastmod.
    """
    src = posts_dir / f"{slug}.md"
    if src.exists():
        m = FRONT_DATE.search(src.read_text(encoding="utf-8")[:2000])
        if m:
            try:
                return date.fromisoformat(m.group(1))
            except ValueError:
                pass
    return mtime_date(html)


def collect(site_dir: Path, posts_dir: Path):
    """Return [(url_path, lastmod)] sorted with the homepage first."""
    entries = []

    index = PROJECT / "index.html"
    if index.exists():
        entries.append(("/", mtime_date(index)))
    else:
        print(f"warning: no index.html at {PROJECT}", file=sys.stderr)

    for html in sorted(site_dir.glob("*.html")):
        stem = html.stem
        if stem.startswith("_") or stem in EXCLUDE:
            continue
        entries.append((f"/{stem}", mtime_date(html)))

    blog_dir = site_dir / "blog"
    if blog_dir.is_dir():
        for html in sorted(blog_dir.glob("*.html")):
            stem = html.stem
            # blog/index.html is a stale artifact build_blog.py already flags.
            if stem.startswith("_") or stem in EXCLUDE or stem == "index":
                continue
            entries.append((f"/blog/{stem}", post_date(stem, posts_dir, html)))

    return entries


def render(entries) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, lastmod in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(BASE_URL + path)}</loc>")
        lines.append(f"    <lastmod>{lastmod.isoformat()}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def build(site_dir=None, posts_dir=None, out=None, dry_run=False) -> str:
    site_dir = Path(site_dir) if site_dir else PROJECT / "pages"
    posts_dir = Path(posts_dir) if posts_dir else PROJECT / "data" / "posts"
    out = Path(out) if out else PROJECT / "sitemap.xml"

    if not (site_dir / "books.html").exists():
        raise SystemExit(f"error: {site_dir} does not look like the pages dir")

    entries = collect(site_dir, posts_dir)
    xml = render(entries)

    if dry_run:
        print(xml, end="")
    else:
        out.write_text(xml, encoding="utf-8")
        print(f"sitemap: {len(entries)} urls -> {out}")
    return xml


def main():
    ap = argparse.ArgumentParser(description="Generate sitemap.xml")
    ap.add_argument("--site", help="pages dir (default: <project>/pages)")
    ap.add_argument("--posts", help="markdown dir (default: <project>/data/posts)")
    ap.add_argument("--out", help="output path (default: <project>/sitemap.xml)")
    ap.add_argument("--dry-run", action="store_true", help="print, don't write")
    args = ap.parse_args()
    build(args.site, args.posts, args.out, args.dry_run)


if __name__ == "__main__":
    main()
