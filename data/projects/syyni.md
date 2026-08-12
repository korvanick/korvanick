---
title: Syyni
slug: syyni
summary: A tool that pulls public government financial data and identifies and researches spending irregularities.
started: 2026-04
updated: 2026-08
built_with: [Claude, Python, SQLite]
image: /images/projects/syyni_schema.png
image_alt: The SQL schema for the transactions table, listing columns for date, vendor, amount in cents, agency, category, fund, description, fiscal year and source, followed by four indexes.
image_caption: The table everything else gets normalized into.
weight: 5
---

Syyni (sue-nee) is Finnish for a close inspection or scrutiny, and is a program that
captures, distills, and reports fraud, waste, and abuse across different levels of
government. The primary target is municipalities, where the scrutiny is thinnest and the
data is hardest to get. Cities, counties, school districts and utilities all keep their
books differently, so a tool general enough to point at any of them might be more useful in
the longer run.

The part I want to focus on most is correlating what a government spent against the quality
of what the public got. Spending alone tells you very little, and most public-finance
tooling stops there.

## Understanding the scope

I've had a lot of ideas about this project, and the scope could so easily expand
indefinitely. Ultimately I want to reduce the amount of public money that gets misspent,
and do it in an automated, unconventional way. From the initial idea, the tool will consist
of four parts.

1. Resource identification. Finding the publicly available data.
2. Data cleaning, parsing, and normalization. Taking in data in any format and putting out
   something consistent and easy to compare.
3. Deep analysis. What the data means. Identifying anomalies and comparing one government
   against another.
4. Narrative development and outreach.

Parts two and three need to be built and refined before the others, with data input and
outreach done manually in the meantime. In the future I would love to run the whole thing
with OpenClaw, which is part of why the idea came up in the first place.

## Log

- 2026-08 -- Reworking design architecture and scope.
- 2026-05 -- Initial experimentation with CLI tool for data collection.
- 2026-04 -- Ideation for a public spending analysis tool.
