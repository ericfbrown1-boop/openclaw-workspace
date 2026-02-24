# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## TTS (ElevenLabs via sag)

- **Preferred voice:** Bella (hpp4J3VqNfWAUOO0d1Us)
  - Professional, bright, and warm
- **Voice ID:** hpp4J3VqNfWAUOO0d1Us
- **Command:** `sag -v hpp4J3VqNfWAUOO0d1Us "your text here"`
- **For files:** `sag -v hpp4J3VqNfWAUOO0d1Us -o output.mp3 "your text here"`

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
