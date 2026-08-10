---
title: korvanick.com
slug: korvanick
summary: A personal site built to replace social media, and a record of why each decision went the way it did.
status: in-motion
updated: 2026-08
built_with: [Claude, Gemini, Leaflet, Python, JS]
image: /images/projects/korvanick_original-home.png
image_alt: A screenshot of green webpage with the text "MAKE IT HAPPEN" and "DO IT RIGHT", along with a central image of an airplane wing.
image_caption: View of the first iteration of my site.
repo: https://github.com/Korvanick/Korvanick
live: https://korvanick.com
weight: 1
---

korvanick.com is the site you are reading. It is a personal reflection of who I am. A personal site targetting whatever seems interesting to me. It started as a personal learning project, but became something else over time. Most of the code was written by a language model. Most of the design choice are personal and intentional, and the content is predominantely my own.

## Initial website creation and ideas

This site was initially made to be a personal creative outlet outside of traditional social media platforms. I had already deleted, Facebook, Instagram, Snapchat, and others, but when people wanted to connect in a non-committal fashion, I had nothing to offer them except my phone number - this is my solution.
[note to self, add old photo of site here or in header]
## The EIA implementation

One of the first features I got really excited about. Many utilities has load-control programs to reduce demand during peak periods, and avoid having to over-build resources that only get used a few times a year - a very expensive solution. Reducing demand is typically voluntary and not very impactful over a short period of time.

With this in mind, rather than focus on true demand, my idea was to pull publicly available data through an API and automatically self-restrict energy useage by disabling certain site features when non-renewable power generation exceeded 50% of total power generation in my region. EIA had tools with allowed for this and I was able to pull data in hourly increments for the midwest, where the server is located. During periods of high demand, non-reneawbles often take up a large share as their output is controllable.

Now, does this really accomplish anything? No, not really. The energy consumption from a website with single digit views is negligible, and disabling a few minor features even more so. But it was a fun exercise, and gave me the opportunity to direct people towards resources that made them more aware of where their own energy was coming from.

## Retiring WriteFreely

My time using WriteFreely was short lived. Over the winter of 2025/2026 I spent six months traveling around the world. While doing so, I was taking a lot of personal notes and keeping more of a personal blog in my notes app. While I didn't publish at the time, I wanted to add a blog feature to my website after returning back to the US. To do so, I came across WriteFreely as a free and open-source tool which was pretty easy to set up on my server. The main downside - I didn't use it.

I had it running on my server for a few months, but never brought myself to log in and add my notes as blogs. I didn't really like that it took me away from my own site and the look didn't match the rest of what I was putting together. So, I decided to see if I could use Google Gemini to build from scratch and match my theming. It was a bit clunky at first, but an improvement over before. Eventually I started using Claude and took it a step further making it what it is today. 

This is really the moment I realized how easy these tools made it for making the CSS and HTML for my site. I'd been fighting that part of managing this since the creation. I mostly just wanted to share the photos I took or talk about things I was doing, not write the code. So from this point on, I was pretty much able to abondon the part I didn't like (making the site) and start working on what I did like (sharing things).
## Choosing the type

For the first year or two the whole site was set in a default sans font, and it was designed around that. In general, I wanted the site to be minimalist, black and white, kind of boring. It worked fine while there wasn't much to read on the site. Once the travel map and the blog started carrying real text, it began to feel like a soulless wall of it. I wanted something with more character that was still clean.

I tried EB Garamond first and liked it a great deal, but I could never make it sit
consistently with the rest of the site. Wonderful for a blog post. Not right for anything
else on the page.

Headings were set in Roboto for a long time, and Roboto was exactly what I had asked for:
clean and minimal. Then I noticed that every time I asked an AI for a clean, minimal
heading font, it recommended Roboto. Knowing it was the default answer rather than a
choice made it feel cheap, and not mine. That may turn out to be just as true of IBM Plex
and I have not caught it yet.

What settled it was consistency across a family rather than any single face. IBM Plex
covers serif, sans and mono from one design, which is what I needed. It is open source and
free. And IBM appears in the source material for another part of this site, which is not a
reason, but it did not hurt.

The site now runs on Newsreader for reading, Public Sans for structure, and IBM Plex Mono
for the small metadata — dates, counts, captions. I also considered Newsreader paired with
one other family and may still switch if I get bored of this.

## Why the fonts are self-hosted

Loading a font from Google's servers means the visitor's browser asks Google for it, and
that request carries their IP address. In January 2022 the Regional Court of Munich ruled
that this violates the GDPR, and ordered a site operator to pay a visitor €100 in damages.

The reasoning is the part worth repeating. The court did not weigh the benefit of the
service against the cost to the visitor. It held that because the fonts can be hosted
locally, sending the IP address to Google in the first place has no legitimate interest
behind it at all. There is no trade-off to argue about when the alternative is free and
takes an afternoon.

So the fonts are served from this domain. Fourteen woff2 files, Latin and Latin Extended
only, about 660 KB in total.

The wider point is that every third-party asset is a request the visitor did not choose to
make. Loading this site now makes no external connections at all, with one exception: the
travel map fetches its tiles from a basemap provider. That one I have not solved.

## The travel map palette

## Alt text for every photo

## Accessibility

## Adding the projects page

Went back and forth a lot on colour, settled on purple because I've always liked green/purple combinations, however it felt right to switch back to blue. Blue and green also look good together. Not quite as good for colour blindness accessibility, but the shape and glow animations should be differentiating enough.

Data cleanup - many photos were missing exif data which meant they needed to be manually reviewed for location tagging. Some dates also needed to be estimated as they were screenshots or messages from others.

Alt text was generated using the qwen3 instruct model in one pass. I didn't add this until there were around 370 photos, and one pass took around 20 minutes. Some of them had the wrong name and had to be manually corrected as well.

![Screenshot of color selection comparison](/images/projects/image2.png "Interactive color selecting tool")

## What I've learned directing it
I'm adding this test just to see if it goes where I want it to.

## Log
- 2026-08 — Added a projects page.
- 2026-08 — Generated alt text for the whole photo gallery in one pass, using a vision model running locally.
- 2026-08 — Accessibility pass: focus trapping in every modal, keyboard access to the book carousels and the photo grid, real buttons in place of clickable spans.
- 2026-08 — Linked the travel map to the gallery. Clicking a city opens the photos taken there.
- 2026-08 — Audited every location on the travel map, and added the places I still want to go.
- 2026-08 — Rebuilt the travel map: a basemap that follows the theme, a new dot palette, and a height that adapts to the window.
- 2026-08 — Added a light theme and a switch in the header. Dark stays the default.
- 2026-08 — Typography overhaul: Newsreader, Public Sans and IBM Plex Mono site-wide.
- 2026-08 — Self-hosted the fonts and vendored Leaflet. No third-party runtime scripts left.
- 2026-08 — Deep links across the site. Every book, city and photo has its own URL.
- 2026-08 — Put the whole site under git and pushed it to GitHub. Added security headers at Apache.
- 2026-07 — Retired WriteFreely and replaced it with a blog generated from Markdown files.
- 2026-07 — Removed the contact page.
- 2026-07 — Reorganised the books page and backfilled everything read since 2020.
- 2026-07 — Photo loading optimisations and interface work on the gallery.
- 2026-07 — Visual overhaul of the professional page, and rewrote what was on it.
- 2026-03 — Added a blog, running on WriteFreely.
- 2025-09 — Major usability improvements to the gallery.
- 2025-05 — First photos actually loading in the gallery. About twenty of them.
- 2025-04 — Added the travel page, built on Leaflet.
- 2025-01 — Added an EIA API hook that dropped media from the site automatically when the regional grid was running on non-renewables.
- 2025-01 — Added the professional, gallery, books and contact pages.
- 2024-12 — Site initialised.
