---
title: korvanick.com
slug: korvanick
summary: A personal site built to replace social media, and a record of why each decision went the way it did.
updated: 2026-08
started: 2024-12
built_with: [Claude, Gemini, Leaflet, Python, JS]
image: /images/projects/korvanick_original-home.png
image_alt: A screenshot of green webpage with the text "MAKE IT HAPPEN" and "DO IT RIGHT", along with a central image of an airplane wing.
image_caption: View of the first iteration of my site.
repo: https://github.com/korvanick/korvanick
live: https://korvanick.com
weight: 1
---

korvanick.com is the site you are reading. It is a personal reflection of who I am, and an ongoing representation of who I want to be. It started as a personal learning project, but became something else over time. It was cool to have a domain, put some words on a server, and click a link to see the poorly formatted text show up almost anywhere in the world. Now, most of the HTML and code is written by a language model. I'm okay with that, because it has enabled this site to become so much more than what it was or ever would have been. Most of the design choices are personal and intentional, and the content is predominantly my own.

A secondary purpose was to have a personal creative outlet outside of traditional social media platforms. I had already deleted all the mainstream accounts, but then when people wanted to connect in a non-committal fashion, I had nothing to offer them except my phone number. This is my solution.

## Letting the model write the code

I'd been fighting the CSS and HTML side of this since the site was created in 2024. I mostly just wanted to share the photos I took or talk about things I was doing, not write the code. The blog is where that changed.

Over the winter of 2025/2026 I spent six months traveling around the world. While doing so I was taking a lot of personal notes and keeping more of a personal blog in my notes app. I didn't publish at the time, but I wanted to add a blog feature to my website after returning back to the US. I came across WriteFreely, a free and open-source tool which was pretty easy to set up on my server. The main downside is that I didn't use it. I had it running for a few months, but never brought myself to log in and add my notes as blogs. I didn't really like that it took me away from my site, that it never felt like my own, and that the look didn't match the rest of what I was putting together.

So I decided to see if I could use Google Gemini to build one from scratch and match my theming. It was a bit clunky at first, but an improvement over what I had, and most importantly it stuck with my site theming. Eventually I started using Claude and took it a step further, making it what it is today. From that point on I was pretty much able to abandon the part I didn't like and start working on what I did like. I've written more about [where I land on using AI](/ai-use).

## Choosing the fonts

For the first year or so the whole site was set in a low effort sans font (I think Roboto) and designed around that. In general, I wanted the site to be minimalist, black and white (actually green, for a little bit, then grey) and kind of boring. It worked fine while there wasn't much to read on the site, but once the travel map and the blog started carrying more words, it began to feel like a soulless wall of text. I wanted something with more character that was still refined.

I found some websites that compared a bunch of them side by side, but only came away with a few I liked. I tried EB Garamond as a primary font first and liked it a great deal for reading blogs, but I could never make it feel right with the rest of the site. I also tried Montserrat a little bit, which looks Googlish to me and did not match what I was looking for outside of headings.

Eventually I found Newsreader. The site now uses <span class="in-newsreader">Newsreader</span> for reading, <span class="in-public-sans">Public Sans</span> for structure, and <span class="in-plex-mono">IBM Plex Mono</span> for the small stuff. Who knew that IBM had their own [type family](https://www.ibm.com/plex/)? I stuck with just the Plex Mono rather than the whole family, because I really like the feel of Newsreader. All of the fonts I use are served from this domain rather than from Google, which keeps my traffic and yours out of Google's logs.

## The Energy Information Administration (EIA) implementation

Connecting to the EIA API was one of the first features I got really excited about. Many utilities have load-control programs to reduce demand during peak periods, and avoid having to over-build resources that only get used a few times a year. Over-building is a very expensive solution. Reducing demand is typically voluntary and not very impactful over a short period of time.

With this concept in mind, one I am very familiar with at work, rather than focus on demand, my idea was to pull publicly available data through an API and automatically self-restrict energy usage by disabling certain site features when non-renewable power generation exceeded 50% of total power generation in my region. The API data allowed for this and I was able to pull it in hourly increments for the Midwest, where the server is located.

Now, does this really accomplish anything? No, not really. The energy consumption from a website with single digit views is negligible, and disabling a few minor features even more so. But it was a fun exercise, and gave me the opportunity to direct people toward resources that made them more aware of where their own energy was coming from.

## Site overhaul and adding the projects page

Okay, lots of changes over a short period of time, so I'm just going to give you the big ones.

The travel page was a lot of work, and is my favorite. Any city I have something to say about gets a white outline on its dot, and the ones I care most about get a card with a photo in it. Some of those cards display on their own and the rest only appear when you hover the dot, so the map reads cleanly at a glance but has more in it for anyone who goes looking. When a card wants to display and loses the space to a neighbor, its dot picks up a slow glow instead, so nothing is ever hidden without some hint that it is there. That layering is the part I like most. Putting together the text and identifying which cities I had something to say about from my notes took a looong time.

![Two travel map cards open at once, one over Prague and one over Trencin, each with a photo and a short note, on a dark map of central Europe scattered with blue dots.](/images/projects/korvanick_travel-highlights.png)

Oh, and just adding all the travel dots took forever. Over 200 new locations in a JSON file. I had been curating the list for a while, even updating it manually while I was traveling, but kept missing some, and getting the naming convention to look consistent took some effort too. I used Claude to pull the metadata from my photos over the last couple of years and fill in whatever I had missed. "Future Adventures" are basically just spots I had highlighted on Google Maps from talking about travel with people at hostels.

I went back and forth a lot on color for the travel dots, which might eventually drive site theming as a whole. I tried purple instead of blue because I've always liked purple/green combinations, however it felt right to switch back to blue and did so. Blue and green are not quite as good for color blindness accessibility, but the shape and glow animations should be differentiating enough.

![Screenshot of color selection comparison](/images/projects/korvanick_color-selector.jpg)

Adding links from the travel page to a filtered gallery view is also something I really like. Cities near each other are grouped on purpose, so you can see places like Bellevue and Seattle at the same time. I've decided that this is the only way I want to be able to filter photos, going from the location on the travel page. The default gallery page is sorted by date, and I want to keep the page minimal. Adding a filter at the top ruined it for me. Maybe I'll change my mind again in the future.

Speaking of the photos page, I mostly had that how I wanted it already, but I added year headings, some optimizations to the photo viewer and page loading, and alt text on every photo. The alt text was generated locally with the qwen3-vl:32b-instruct model through Ollama, in one pass of all photos that took about 30 minutes. Some came back with the wrong name or a caption I didn't like and had to be corrected by hand. Going forward, alt text will get added when the photo does, so this was a one-time thing.

The data cleanup was slower. A lot of photos were missing EXIF data, so they had to be reviewed manually for location tagging, and some dates had to be estimated because they were screenshots or messages from other people.

I added a projects page because a certain Belgian friend keeps bugging me to write my book I haven't started yet, but I told her I was busy working on other projects (like this website) and it wasn't going to be a priority for a bit. She wanted to know what my other projects were, so here you are. I'm really glad I added it though, as it's the type of thing that will motivate me to keep the ideas moving forward.

One interesting thing to note: during the travel page overhaul I added accessibility features like different dot shapes for places I have been versus places I have not, filled against open. Without me specifying it while building the projects page, Claude applied the same logic to in motion versus at rest. It makes me question whether my initial assertion that the design choices are my own still holds true, because I hadn't even thought about that for that page.

## Log
- 2026-08 -- Added a projects page.
- 2026-08 -- Generated alt text for the whole photo gallery in one pass, using a vision model running locally.
- 2026-08 -- Accessibility pass: focus trapping in every modal, keyboard access to the book carousels and the photo grid, real buttons in place of clickable spans.
- 2026-08 -- Linked the travel map to the gallery. Clicking a city opens the photos taken there.
- 2026-08 -- Rebuilt the travel map: a basemap that follows the theme, a new dot palette, tiered highlight cards, and a height that adapts to the window.
- 2026-08 -- Added a light theme and a switch in the header. Dark stays the default.
- 2026-08 -- Fixed the homepage video on iPhone, which had been taking over the whole screen instead of playing in place.
- 2026-08 -- Typography overhaul. Newsreader, Public Sans and IBM Plex Mono self-hosted, along with a copy of the Leaflet map library. Nothing on the site loads from someone else's server anymore.
- 2026-08 -- Added deep links across the site.
- 2026-08 -- Put the whole site under git and pushed it to GitHub. Added security headers at Apache.
- 2026-07 -- Retired WriteFreely and replaced it with a blog generated from Markdown files.
- 2026-07 -- Removed the contact page.
- 2026-07 -- Reorganized the books page and backfilled everything read since 2020.
- 2026-07 -- Photo loading optimizations and interface work on the gallery.
- 2026-07 -- Visual overhaul of the professional page.
- 2026-03 -- Added a blog, using WriteFreely.
- 2025-09 -- Major usability improvements to the gallery.
- 2025-05 -- First photos actually loading in the gallery.
- 2025-04 -- Added the travel page using Leaflet.
- 2025-01 -- Added an EIA API that disabled media on the site automatically when the regional grid was majority non-renewable.
- 2025-01 -- Added the professional, gallery, books and contact pages.
- 2024-12 -- Site initialized.
