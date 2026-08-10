---
title: Fraud-bot
slug: fraud-bot
summary: A tool that pulls public government financial data and looks for spending irregularities.
status: at-rest
updated: 2026-08
built_with: [Claude, Python, SQLite]
weight: 5
---

A CLI that syncs public financial disclosures into a local database and scans them. The
first source is Washington state's checkbook data, because states publish well; the actual
target is municipalities, where the scrutiny is thinnest and the data is hardest to get.

The idea I care about is the third step: correlating what a government spent against the
quality of what it got. Road budget against road condition. Spending alone tells you very
little, and most public-finance tooling stops there.

I don't intend to charge anyone for this. Billing a government to audit itself means the
fee comes out of the same taxpayer money, and I might find nothing.

## What it does

## Why municipalities

## The bias problem

## Log
- 2026-08 -- Reworking design architecture and scope.
- 2026-08 — Initial experimentation with CLI tool.
- 2026-03 — Ideation for fraud-bot tool.
