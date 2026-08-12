---
title: Barn Brain
slug: barn-brain
summary: A running list of things that would make a small family dairy better, and the ones I can actually build.
started: 2026-03
updated: 2026-07
built_with: [farmOS, Docker, Arduino]
image: /images/projects/barn-brain_dairy-herd-monitor.jpg
image_alt: A wall-mounted Dairy Herd Monitor, a large circular chart divided into months and ringed with numbered scales, covered edge to edge with hundreds of small colored sticker tabs in red, yellow, blue and green, each hand-labeled with a cow number and a date. The board is stained and dusty, with spare stickers stuck around the outside.
image_caption: The record system Barn Brain is meant to replace.
weight: 2
---

Building things and making existing projects more efficient is a passion of mine. One of
the best opportunities I have to do that on my own is through the family farm.

I've been keeping a list of improvement ideas for my brother's farm. Most of them are not
software or electronics, and plenty of them have nothing to do with me. Yet my interest is the
digital technology. I like tinkering with servers and sensors, and I like perusing and trying
to understand the data they provide. The current system has none of it, and setting up Barn
Brain is my attempt to change that.

## What the farm needs and my solution

Heat detection is the first priority. It is difficult to know when animals are in heat or
should be, and on a dairy this size it is the problem that costs the most. Missing an
animal's heat means wasting feed on unproductive animals, and missing the chance to keep
the best animals in the herd.

Another new burden is an annual report covering every treatment given to every animal.
Entering the data is tedious, the notes it comes from are unorganized, and the time spent
assembling the report goes to something that serves an outside review rather than the farm.

This leads me toward a digital record system, which can replace the existing
sticker-on-a-calendar method and the photographs with a number and birth date written on
the back. Having all the information in one place would allow for animal-specific notes,
automated alerts, and exportable reports in a consistent format. farmOS seems like a reasonable
solution, and its module system will let me build on top of it for whatever I need, like a
heat detection system.

The heat detection will require hardware on top of that. An animal moves differently when
she is coming into heat, so the plan is placing activity beacons on nylon leg bands, with a
handful of small radios mounted down the length of the barn listening for them and passing
what they hear back to the server. The alert comes out of the data instead of out of
someone noticing. Similar technologies already exist, but the data is locked behind
subscriptions, proprietary software, and expensive collars that the entire herd would need.
My solution requires minimal sensors, can easily be moved between animals as needed, and is
much more affordable. Exactly what a small farm needs.

Since that network has to exist anyway, it also gives me a chance to try something new,
which admittedly will probably not work, and is not a priority for the farm since there is
limited use for the extra data at this scale. I can use the same setup to estimate how much
milk each cow produces without measuring any of it directly, using sensors and algorithms
instead of meters. As far as I know that would be the first of its kind. It's only a matter
of building and testing how close to reality it gets.

## Log

- 2026-07 -- Installed farmOS on offline server with local network device for testing and expansion.
- 2026-05 -- Purchased hardware for offline setup.
- 2026-03 -- Started. farmOS running in Docker for testing.
