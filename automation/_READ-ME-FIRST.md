# How to add a blog post or a project

Same routine for both, so there is only one thing to remember.

## The quick way
1. From the automation/ folder, run:  `python3 new_page.py`
2. It asks whether you want a post or a project, then asks the right questions
   and writes a `.md` file with the header already filled in.
3. It offers to open the file. Write the body in Markdown.
4. When you close the editor it offers to build. Say yes and you are done.

`publish.py` is the publish step: it reads every `.md` in `data/posts/` and
`data/projects/` and rewrites the HTML pages from scratch. Run it after ANY
change to any of those files. It is safe to run at any time — it always
produces the same pages from the same sources — and it refreshes `sitemap.xml`
on the way out.

## Editing something that already exists
There is no edit command, and there does not need to be one. Open the `.md`
file, change it, run `publish.py`:

    $EDITOR ../data/projects/farmos.md
    python3 publish.py

## Adding to a project: notes and log entries
Don't hand-edit the Markdown for this. Run:

    python3 add_entry.py                 pick a project, then pick what to add
    python3 add_entry.py farmos          jump straight to that project
    python3 add_entry.py farmos --log    skip the question too

It asks for what it needs, writes it into the right place, bumps `updated:` in
the front matter, keeps a `.md.bak` of the previous version, and offers to
publish.

Two kinds of entry, because they are different jobs:

    LOG    one dated line. What happened. Cheap to add, never expands.
    NOTE   a titled section of prose. What you decided, and why.

A log entry asks for the date (this month by default) and one line of text, and
goes in at the top of the list. A note asks for a heading, opens your editor for
the body, then offers to attach an image with alt text and a caption.

Editing something that already exists is still just opening the `.md` file. This
is only for adding, because adding is where the formatting rules bite:

- `## Log` must be the LAST heading in the file. Everything after it is read as
  log entries, so a note written below it silently disappears. `add_entry.py`
  puts notes above it for you.
- A heading with nothing under it is dropped, which is deliberate — you can
  sketch an outline in advance and only the filled-in parts ship.
- `2026-08` prints as "Aug 2026" wherever a date is shown.

Sections appear in the order they sit in the file, each gets its own link
target, and once a project has three or more a contents list appears above them
automatically.

Project images go in `images/projects/<slug>/`, NOT `images/gallery/` —
`update_gallery.py` walks the gallery folder looking for EXIF and would flag
every screenshot for review forever.

## A project's title image
Three front matter fields, all optional:

    image: /images/projects/korvanick/cover.png
    image_alt: What a screen reader should say about the picture
    image_caption: What everyone reads underneath it

`image` alone renders a bare picture. Add `image_caption` and it becomes a
figure with the caption centred beneath, styled the same as captions on images
inside the prose.

`image_alt` and `image_caption` are different jobs and neither replaces the
other — alt describes the picture for someone who cannot see it, the caption
says something about it to everyone. If you only write one, write the alt.

The same image is used as the thumbnail on /projects, cropped square.

## Renaming a post or a project
The URL comes from the `slug:` line in the front matter, not from the filename.
So renaming is one edit:

    slug: korvanick        ->    slug: this-site

Run `publish.py` and the old page is deleted, the new one written, and the
sitemap updated. If anything on the site still links to the old URL, the build
says so by name — fix those hrefs before you forget. Old links you shared
elsewhere will break; that part is unavoidable.

Leave `slug:` out entirely and the filename is used instead, which is how the
projects behaved before.

For a project, bump `updated:` when you add to the `## Log`. The build prints a
list of front-matter fields still left blank, so anything unfinished says so
every time you publish.

(Books are different — they live in `data/books.json`, so `add_book.py --edit`
is how you change one.)

## The manual way
Create a file in `data/posts/` called `your-slug.md` that starts with this header:

    ---
    title: Your Title Here
    date: 2024-08-12
    summary: One line shown on the blog index.
    ---

Then write the body below the second `---` line in Markdown.

## Backdating a post
The `date:` line is the only thing that decides where a post appears in the list.
Set it to any past date and the post reads as though it's been online since then.

## Adding photos
Put the image file in `images/blog/` on your site, then reference it on its own
line in the post. The bracket text becomes a caption under the photo:

    ![Sunrise over the ridge](/images/blog/sunrise.jpg)

An image placed inside a sentence stays inline, with no caption.

## Publishing / deleting
Run `python3 publish.py` after any change — it rewrites `blog.html` and one
`<slug>.html` page per post. To delete a post, remove its `.md` and its generated
`.html`, then rebuild.

## Changing the site header
The header links live in one place: the `LINKS` list at the top of
`scripts/nav.js`. Edit that and every page changes, generated blog pages
included. The pages themselves only carry an empty `<nav></nav>`.

(Files in `data/posts/` starting with "_" are skipped as drafts.)

## Adding photos
1. Copy the photos into `images/gallery/`.
2. Run:  `python3 update_gallery.py`

It makes the thumbnails, reads the date and GPS out of each photo, matches the
GPS to a city on the travel map, gives each one a slug, and rewrites
`data/gallery.json`.

Then it asks you for alt text, one photo at a time — a sentence describing what
is in the picture, for someone who cannot see it. Press Enter to skip a photo,
or type `stop` to stop being asked. Skipped photos come back next run.

    python3 update_gallery.py --alt       ask about every photo still missing it
    python3 update_gallery.py --no-alt    do not ask at all
    python3 update_gallery.py --dry-run   show what would happen, change nothing

If a photo's GPS matches no city on the map, it is listed in
`data/gallery-review.txt`. Add the city with `add_city.py`, then run
`update_gallery.py --reslug` so it picks up the proper slug.

## The sitemap
`auto_sitemap.py` rewrites `sitemap.xml` from whatever pages exist. You should
never need to run it: `publish.py` calls it at the end of every build, and a
daily systemd timer catches pages you edited by hand. To install the timer once:

    sudo cp automation/systemd/korvanick-sitemap.* /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now korvanick-sitemap.timer
    systemctl list-timers korvanick-sitemap.timer

## What is on the server
Only the plain scripts: `add_book.py`, `add_city.py`, `add_entry.py`, `new_page.py`,
`publish.py`, `auto_sitemap.py`, `update_gallery.py`. All of them are Python
standard library; `update_gallery.py` also needs ImageMagick.

`gallery.py` is deliberately NOT here. It needs Pillow, `requests` and a local
vision model, none of which belong on the web server. Keep it on the desktop
and point it at a copy if you ever want to batch-write alt text.
