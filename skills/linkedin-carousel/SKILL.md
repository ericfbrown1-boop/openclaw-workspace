# LinkedIn Carousel Skill
> Create professional LinkedIn carousel posts (PDF) from a theme + source materials. Output is a ready-to-upload PDF.

## Trigger Phrases
Use this skill when Eric says any of:
- "create a LinkedIn carousel"
- "make me a LinkedIn deck"
- "LinkedIn carousel about [topic]"
- "turn this into a LinkedIn carousel"
- "create slides for LinkedIn"

## What This Produces
A **PDF file** (5-8 slides, 1080×1080px square format) ready to upload directly to LinkedIn as a document/carousel post. No third-party tools needed.

## LinkedIn Carousel Specs (2026)
- **Format:** PDF (preferred) or PPTX
- **Dimensions:** 1080×1080px (square, best for mobile) or 1080×1350px (portrait)
- **File size:** Under 100MB (typically 1-5MB)
- **Slides:** 5-8 optimal (up to 20 allowed, but 8-12 max recommended)
- **Upload path:** LinkedIn post → "Document" attachment → upload PDF
- **Font:** Minimum 18pt for body, 28pt+ for headers (mobile readability)

## Proven Slide Structure (High Engagement)

| Slide | Purpose | Content |
|-------|---------|---------|
| 1 | **Hook** | Bold claim, specific number, or surprising fact. Makes people swipe. |
| 2 | **Problem/Context** | Why this matters. Set the stakes. |
| 3-5 | **Content** | One key idea per slide. Short bullets. Visual if possible. |
| 6 | **Key Takeaway** | The single most important insight. |
| 7 | **CTA** | "Save this post", "Comment your thoughts", "Follow for more" |
| (8) | **About** | Optional: Eric's name, title, company, LinkedIn handle |

## Required Inputs from Eric
1. **Theme/Topic** — what the carousel is about (e.g. "AI agents in enterprise software")
2. **Source materials** — paste article text, URL, notes, or say "use the Sanjay blog post"
3. **Tone** — Professional / Thought Leader / Educational (default: Professional thought leader)
4. **Audience** — Who is this for? (default: Enterprise tech executives, CFOs, COOs)
5. **CTA preference** — What action do you want readers to take?

## Execution Steps

### Step 1: Generate Slide Content
Use Claude to draft slide-by-slide content from the source materials:
- Slide 1: Hook — bold headline that stops the scroll
- Slides 2-6: One insight per slide, max 40 words each
- Slide 7: CTA slide
- Keep language punchy, no corporate jargon

### Step 2: Generate PDF via Python (python-pptx → PDF)
Use the script at `skills/linkedin-carousel/scripts/generate_carousel.py`:

```bash
python3 skills/linkedin-carousel/scripts/generate_carousel.py \
  --title "Your Hook Title" \
  --slides slides.json \
  --output ~/Desktop/linkedin_carousel.pdf \
  --theme cohesity
```

### Step 3: Deliver
- Save PDF to `~/Desktop/linkedin_carousel_<topic>_<date>.pdf`
- Send to Eric via Telegram with caption: "Ready to upload — go to LinkedIn → Start a post → Document"
- Also save to Dropbox `/Jarvis Reports/LinkedIn Carousels/`

## Brand Guidelines (Eric Brown / Cohesity)
- **Primary color:** Deep blue (#0A2540) + white text
- **Accent:** Cohesity teal (#00B4D8) or orange (#FF6B35)
- **Font:** Clean sans-serif (Arial, Helvetica, or Inter)
- **Logo:** Include "Cohesity" text or logo on slides 1 and last slide
- **Eric's title:** CFO & COO, Cohesity
- **Handle:** @EricBrown (add to CTA slide)

## Python Dependencies
```
pip install python-pptx reportlab Pillow
```

## Best Practices (from research)
- **Hook with a number:** "3 reasons AI won't eat software" outperforms "Why AI won't eat software"
- **One idea per slide:** Never more than 3 bullet points
- **High contrast:** Dark background + white text = mobile-friendly
- **Consistent layout:** Same header position on every slide
- **Tease in caption:** The LinkedIn post caption should say "swipe to see #3" — creates curiosity
- **Save CTA:** "Save this post" drives 4x more reach than just "like"
- **Portrait mode:** 1080×1350 performs slightly better on mobile than square

## Quick Mode (No PDF — Just Copy)
If Eric just wants text content without generating a PDF:
> Draft all slide copy as a numbered list, formatted for easy paste into Canva or PowerPoint.
