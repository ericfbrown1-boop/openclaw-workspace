---
name: competitive-intel
description: >
  Daily competitive intelligence for Rubrik, Commvault, and Veeam.
  Monitors pricing, product announcements, news, and stock movements.
  Feeds into 6 AM daily briefing.
---

# Competitive Intelligence Aggregator

## When to Use
- Daily briefing generation (6 AM PT)
- Eric asks about competitor activity
- Earnings season for Rubrik/Commvault/Veeam

## Competitors Tracked
- **Rubrik** (RBRK) — primary competitor
- **Commvault** (CVLT) — enterprise competitor
- **Veeam** (private) — mid-market competitor

## Workflow
1. Check stock prices (RBRK, CVLT)
2. Scan news feeds (Bloomberg, Reuters, TechCrunch, CRN)
3. Monitor competitor blogs/IR pages
4. Check for product announcements or pricing changes
5. Generate 3-5 bullet summary for daily briefing

## Integration
- Project Scraper (~/ProjectScraper/) for website crawling
- blogwatcher skill for RSS feeds
- Google Sheets for historical tracking

## Status: SKELETON — Implementation needed
