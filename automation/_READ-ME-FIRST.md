# How to add a blog post

You'll do this rarely, so here's the whole routine in one place.

## The quick way
1. From the automation/ folder, run:  `python3 new_post.py`
2. Answer the prompts (title, date, summary). It creates a new `.md` file in
   `data/posts/` with the header already filled in.
3. Open that `.md` file and write your post in Markdown.
4. Run:  `python3 build_blog.py`
5. Upload the new/changed `.html` files (and any images) to the server.

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
Run `python3 build_blog.py` after any change — it rewrites `blog.html` and one
`<slug>.html` page per post. To delete a post, remove its `.md` and its generated
`.html`, then rebuild.

## Changing the site header
The header links live in one place: the `LINKS` list at the top of
`scripts/nav.js`. Edit that and every page changes, generated blog pages
included. The pages themselves only carry an empty `<nav></nav>`.

(Files in `data/posts/` starting with "_" are skipped as drafts.)
