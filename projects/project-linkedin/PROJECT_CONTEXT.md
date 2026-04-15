# Project LinkedIn — AI-Powered LinkedIn Post Polish + Graphic Generator

## Owner
Eric Brown — CFO & COO, Cohesity

## Goal
Build a reusable workflow that:
1. Accepts a draft LinkedIn post from Eric (via Telegram or direct input)
2. Reviews and tunes the post for tone, impact, and LinkedIn best practices
3. Generates a high-quality AI/tech-themed graphic to accompany the post
4. Delivers both polished copy + graphic as ready-to-post output

## Usage Flow
Eric sends a draft → Jarvis polishes the text → generates a graphic → delivers both

## Constraints
- Must run entirely on MacBook (no PowerSpec needed for this)
- Graphic generation: use an available API (OpenAI DALL-E 3, Stability AI, or similar)
- Output: polished text (copy/paste ready) + image file (1200x627px LinkedIn optimal)
- Turn-around: < 3 minutes from draft to ready-to-post
- Eric's voice must be preserved — professional, direct, data-driven, no fluff

## Stack Options (Planner to decide best approach)
- Text polish: Claude Opus 4.6 (already available)
- Image gen: OpenAI DALL-E 3 (openai key available) or Stable Diffusion (PowerSpec GPU)
- Delivery: Telegram image + text, or save to ~/Documents/ and notify

## Success Criteria
- Polished post ready to copy-paste to LinkedIn
- Graphic is 1200x627 (LinkedIn optimal aspect ratio), high quality, AI/tech themed
- Turnaround < 3 min
- Repeatable — Eric can use this for every LinkedIn post going forward

## Project Codename
Project LinkedIn

## Created
2026-04-15
