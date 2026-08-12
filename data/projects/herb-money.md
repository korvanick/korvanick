---
title: Herb Money
slug: herb-money
summary: A real-time dashboard that displays which Old School RuneScape (OSRS) herbs are most profitable to degrime.
started: 2026-05
updated: 2026-08
built_with: [Gemini, Python, prices.runescape.wiki API]
image: /images/projects/herb-money_wiki-degrime.png
image_alt: A close crop of the Degrime animation. A large green herb icon outlined in cyan hovers above a character standing with both arms raised.
image_caption: The Degrime animation. Source: oldschool.runescape.wiki
weight: 4
---

Herb Money solved a problem that didn't really exist, and ended up being more useful than
expected.

The OSRS wiki's
[money making guide](https://oldschool.runescape.wiki/w/Money_making_guide) introduced me
to casting Degrime, and to a lot of other processing-for-gp tasks. The night I discovered
it, processing Kwuarm showed a profit of around 2.5M gp/hr, over double what I was making
processing logs. What the guide doesn't tell you is that it assumes a tick perfection I
could not match, and that herb margins vary drastically throughout the day. My first try
came out worse than what I had been doing, under 1M gp/hr, and I did not have enough
capital to buy in bulk, which slowed me down further due to buying in small batches.

So why build a tool? The [Degrime page](https://oldschool.runescape.wiki/w/Degrime) has a cost
analysis table, which I started using next to pick the best herbs on any given day. This
honestly works okay, but it is not updated frequently enough to capture price fluctuations that
occur throughout the day. Sticking with the herb that page recommends as highest profit can be
a complete waste of time, and can lose money outright if you aren't working out the actual cost
by hand. There is almost always a better herb found using real-time prices than from a daily
wiki update. So I started using the wiki's real-time price site instead, with a tab open for every
herb, clean and grimy, and eventually decided to try building a tool using Gemini and calling
the wiki's API to display everything at once.

## Processing herbs

The process is pretty simple if you're not familiar. First you need grimy herbs, bought
from the Grand Exchange or already sitting in your bank. At the scale required to be
meaningfully profitable, purchasing is the only viable option.

You also need the Arceuus spellbook, an earth staff, and nature runes kept in your
inventory or a rune pouch. If you don't have an altar of your own, the
[house party](https://oldschool.runescape.wiki/w/House_party) worlds always have someone
hosting with an occult altar open. Degrime costs four earth and two nature runes per cast,
and the staff supplies the earth runes, so natures are the only ones you ever pay for. One
cast cleans every grimy herb in your inventory and takes 8 ticks, or 4.8 seconds.

The rune pouch takes an inventory slot, which is why a cast cleans 27 herbs rather than 28.
In all, perfect processing takes 10 ticks per inventory:

*   **8 ticks** - Degrime cast
*   **1 tick** - deposit clean herbs
*   **1 tick** - withdraw grimy herbs

![Casting Degrime in the crowded Grand Exchange area, with the Magic and Herblore experience drops from one inventory floating beside my character.](/images/projects/herb-money_degrime.png "Casting Degrime on a full inventory.")

It's a really simple process, it just requires a lot of upfront capital to purchase enough
herbs in bulk to be worthwhile. The trick to maximizing profit is to always be slow-buying the
highest-margin herbs while also avoiding the low-volume ones. Buy low and sell high. The tool
handles both of those. Knowing where a price is heading next comes from experience. (Just think
how successful I could be if I dedicated this much time to actual trading.)

## The tool

The dashboard is one table, a row per herb, sorted by hourly profit. It shows the buy
price, both sell prices, the margin on each, the profit per hour, and how much of that herb
has traded in the last hour. Anything under 2,000 an hour gets flagged, so a high margin on a
herb nobody is trading doesn't trick me.

![A terminal dashboard listing fourteen herbs, with columns for buy price, both sell prices, colored direction arrows, the margin on each, hourly profit and hourly volume. Most rows show a profit in green, and the last one is red.](/images/projects/herb-money_dashboard.png "Dashboard showing price changes, margins, and one herb running at a loss.")

Beside the prices is a colored arrow and magnitude highlighting anything that just moved,
and which way. Green is good and red is bad, which means the colors run opposite between
the two columns: a rising buy price is working against me, a rising sell price is working
for me.

While processing I keep the dashboard on one side of the monitor, automatically refreshing
every minute. If something makes a big jump, I can put a buy order on whatever has just dropped
in price, or dump volume before it crashes.

## The calculation

The calculation is pretty simple. The API pulls in the latest buying and selling prices for
each herb, and shows the margin between the two.

On the buy side the only price that matters is the low one, because I place offers and wait
rather than buying instantly. On the sell side the high price is the one to aim for, but the
tool calculates the profit at both prices and ranks on the low one, because that is what you
actually get if you need to dump inventory in a hurry. A 100 gp gap between those two selling
prices can be enough to make a herb too risky to bother with.

Since every herb cleans at the same rate, profit is based entirely on margin, runes (also
pulled in by API), and taxes. As of writing this, I discovered the tool had the GE tax
hardcoded at 1%, which has actually been 2% for a while. The error is 1% of the clean
herb's price, so it grows with how expensive the herb is, which means all my Snapdragon
processing was much less profitable than the tool was telling me. That will need to be
corrected with any revisions.

The tool (just like the wiki) assumes a tick-perfect clean rate of 16,200 herbs an hour.
Realistically, with error, time making buying and selling orders on the GE, and getting
distracted watching YouTube, I manage 67-80% of that. I've debated whether to keep it at
the perfect rate and do the math in my head, allow user input for a percentage of
perfection, or find a way to track it within the game client and calculate actual profit.
Ultimately though, the focus should be on optimal processing, buying, and selling rather
than on calculating how much money you are making.

## Tool in practice

Capital comes first, and you need quite a bit. What the tool does is make the capital you
have worth more than it would be on many other processing tasks in the game, like logs or
smelting. It also earned me quite a bit of Herblore experience, which I needed anyway. I
went from around 60 to 80 over five to seven days, though I had started before the tool
existed. The experience rate is the same either way. What the tool changed was the profit.

After building the tool, I spent three days running Degrime non-stop. I was fortunate
enough to be able to borrow 100M gp from a friend to get started, but I think this would
have been nearly as profitable with around 30-50M gp, and avoiding more expensive herbs
like Snapdragon, since they eat all your working capital and you can miss better buying
opportunities if you can't dump them at a good price.

I started off just doing whatever was the most profitable, with many herbs often sitting at
around 2M gp/hr, but given my rate was only 67-80% of tick perfect, I started only buying
when the profit was 3-5M gp/hr (actual rate of 2-4M gp/hr). Over the course of the three
days I had earned 60M gp, was able to give the *small* 100M loan back to my friend, with
interest, and bought myself the Osmumten's fang I had been dreaming of. Don't calculate how
many hours that took me each day.

## Buying and selling

Purchasing and selling strategically is very important to maximize profits, which is what
the tool really helps with and could still be improved on. Basically I would place buy
orders 1 gp above whatever the most recent sale was, to out-bid anyone else trying to do
something similar. As people quick-sell, I get all of the herbs. Sometimes if it felt like
I was fighting someone, I'd let them get their order fulfilled at a slightly higher price
intentionally, thinking they may only be buying 1,000 for potions and nowhere near the
four-hour buy limit, which runs somewhere between 11,000 and 13,000 depending on the herb.
Sometimes this worked and other times it didn't.

Overnight I'd place large buy orders 100-200 gp below the current low buying price. They
were often filled by morning, and that discounted herb pile was worth an extra 1-2M gp
across the hour or so it took to clean through it.

Two things would make it better, and both carry the same problem. Tracking how much volume
actually fills at a given price would tell me whether raising my bid is worth it instead of
guessing. A plugin could take it further and set buy and sell prices on the GE *almost*
automatically, the same way flipping tools do. But the second I make this that accessible,
the margins go with it, and it turns into a bidding war with diminishing returns. If you're
lucky enough to stumble across this, go and see what the current rates are.

I'm almost at a point skill-wise where mid-game bossing is brainless, so that will be more
profitable soon anyway.

## Log

- 2026-08 -- Corrected 2% tax, allow user input for filtering, minor feature additions.
- 2026-08 -- Put the tool under git and published the repository on GitHub.
- 2026-05 -- Created the first version of the tool with Gemini.
