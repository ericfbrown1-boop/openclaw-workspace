# LinkedIn Post Polish + AI Graphic Skill
> Polish a draft LinkedIn post and generate a matching AI graphic. Delivers both via Telegram, ready to post.

## Trigger Phrases
Use this skill when Eric says any of:
- "polish this LinkedIn post"
- "LinkedIn post about [topic]"
- "help me with a LinkedIn post"
- "polish this for LinkedIn"
- "make this LinkedIn-ready"
- Or sends a multi-sentence draft and mentions "LinkedIn"

## What This Produces
1. **Polished text** — copy-paste ready for LinkedIn
2. **AI-generated graphic** — 1200x627px, saved to `~/Documents/linkedin-graphics/`
3. Both delivered via Telegram

## Execution Steps

### Step 1: Polish the Text

Use Claude Opus 4.6 to rewrite Eric's draft. Apply this system prompt internally:

```
You are a LinkedIn ghostwriter for Eric Brown, CFO & COO of Cohesity.

Eric's voice:
- Executive, confident, forward-thinking
- Uses concrete data and specific examples (never vague)
- Short, punchy sentences mixed with longer analytical ones
- No buzzword fluff ("synergy", "leverage", "paradigm shift" — never)
- Occasionally uses em dashes for emphasis
- Opens with a hook (bold claim, surprising stat, or provocative question)
- Closes with a clear takeaway or call to engagement
- Uses line breaks between ideas (LinkedIn formatting)
- 150-300 words optimal (LinkedIn algorithm favors this range)
- No hashtags in the body — add 3-5 relevant hashtags at the very end, separated by a blank line

Rewrite rules:
1. Keep the core message and any specific facts/numbers exactly as Eric wrote them
2. Strengthen the opening — first line must stop the scroll
3. Break into short paragraphs (1-3 sentences each) with blank lines between
4. Remove any corporate jargon or filler
5. End with either a question (drives comments) or a strong stance
6. Add 3-5 hashtags at the end (e.g. #AI #DataSecurity #CFO #Leadership)
```

**Output to Eric:** Present the polished text in a clean block, ready to copy-paste. If significant changes were made, briefly note what changed and why (1-2 sentences max).

### Step 2: Generate Image Prompt

From the polished text, craft a DALL-E 3 prompt. Use this template:

```
A professional, high-tech LinkedIn banner image. [TOPIC-SPECIFIC VISUAL].
Style: dark navy/black background with glowing blue and cyan accent lines,
abstract data visualization elements, subtle circuit board patterns.
Modern, clean, executive aesthetic. No text or words in the image.
Photorealistic lighting with volumetric glow effects.
Wide landscape composition, cinematic depth of field.
```

Replace `[TOPIC-SPECIFIC VISUAL]` with a visual metaphor for the post's theme. Examples:
- AI/ML topic → "Abstract neural network with glowing nodes and connections"
- Data security → "Digital shield with flowing data streams"
- Leadership → "Silhouette of a figure standing before a vast data landscape"
- Financial → "Holographic financial charts floating in space"
- Cloud/infrastructure → "Illuminated server architecture fading into clouds"

**Important:** Always include "No text or words in the image" — DALL-E tends to add garbled text otherwise.

### Step 3: Call DALL-E 3 API

Make this API call:

```bash
curl -s https://api.openai.com/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(cat ~/.openclaw/agents/main/agent/auth-profiles.json | python3 -c "import sys,json; print(json.load(sys.stdin)['profiles']['openai:default']['key'])")" \
  -d '{
    "model": "dall-e-3",
    "prompt": "<THE PROMPT FROM STEP 2>",
    "n": 1,
    "size": "1792x1024",
    "quality": "hd",
    "style": "vivid"
  }'
```

The response JSON contains `data[0].url` — download that image:

```bash
curl -sL "<IMAGE_URL>" -o /tmp/linkedin_raw.png
```

**If DALL-E fails:** Log the error. Try once more after 30 seconds. If still failing, notify Eric: "Image generation unavailable — post text is ready, I'll retry the graphic shortly."

### Step 4: Crop to LinkedIn Dimensions

DALL-E 3 outputs 1792x1024. Crop to 1200x627 (LinkedIn optimal):

```bash
python3 -c "
from PIL import Image
img = Image.open('/tmp/linkedin_raw.png')
# Center crop to 1200x627 aspect ratio, then resize
w, h = img.size
target_ratio = 1200 / 627
current_ratio = w / h
if current_ratio > target_ratio:
    new_w = int(h * target_ratio)
    left = (w - new_w) // 2
    img = img.crop((left, 0, left + new_w, h))
else:
    new_h = int(w / target_ratio)
    top = (h - new_h) // 2
    img = img.crop((0, top, w, top + new_h))
img = img.resize((1200, 627), Image.LANCZOS)
img.save('/tmp/linkedin_final.png', quality=95)
print('Cropped to 1200x627')
"
```

Then save to the output directory:

```bash
mkdir -p ~/Documents/linkedin-graphics
DATESTAMP=$(date +%Y%m%d-%H%M)
SLUG=$(echo "<TOPIC>" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | head -c 30)
cp /tmp/linkedin_final.png ~/Documents/linkedin-graphics/${DATESTAMP}-${SLUG}.png
```

### Step 5: Deliver via Telegram

**Send the polished text:**
```
openclaw message send --channel telegram --message "📝 LinkedIn Post — Ready to Post

<POLISHED TEXT HERE>

---
Image saved to: ~/Documents/linkedin-graphics/<filename>.png"
```

**Send the image:**
```
openclaw message send --channel telegram --attachment ~/Documents/linkedin-graphics/<filename>.png --message "LinkedIn graphic for your post"
```

## Eric's Style Reference

**Good openings (Eric's voice):**
- "Most CFOs are still running their AI strategy on spreadsheets. Here's why that's a problem."
- "We just closed Q1. The number that surprised me most wasn't revenue — it was this."
- "I've sat in 200+ board meetings. The ones that actually move the needle have one thing in common."

**Bad openings (NOT Eric's voice):**
- "Excited to share some thoughts on the future of AI!" ← too generic
- "In today's rapidly evolving landscape..." ← corporate filler
- "🚀 Big news! 🎉" ← not executive tone

**Structural patterns Eric uses:**
- Hook → Context → Insight → Data/Example → Takeaway → Question
- Short paragraphs (1-3 sentences)
- Occasional numbered lists for frameworks
- Em dashes for emphasis — like this

## Image Style Guide

| Element | Specification |
|---------|--------------|
| Dimensions | 1200 × 627 px |
| Background | Dark navy (#0A1628) to black gradient |
| Accents | Electric blue (#00B4D8), cyan (#06D6A0), subtle purple (#7B68EE) |
| Elements | Abstract data viz, circuit patterns, glowing nodes, light trails |
| Style | Clean, modern, executive — NOT cluttered or "techy stock photo" |
| Text in image | NEVER — LinkedIn overlays the post text; image text looks amateurish |
| Mood | Futuristic, confident, authoritative |

## Fallback: Stable Diffusion on PowerSpec

If DALL-E is unavailable (API down, quota exceeded, key revoked):

1. SSH to PowerSpec: `ssh powerspec` (100.67.128.123)
2. Use the local SD XL model:
```bash
ssh powerspec "cd /opt/stable-diffusion && python3 generate.py \
  --prompt '<PROMPT FROM STEP 2>' \
  --width 1200 --height 627 \
  --steps 30 --cfg 7.5 \
  --output /tmp/linkedin_sd.png"
scp powerspec:/tmp/linkedin_sd.png ~/Documents/linkedin-graphics/<filename>.png
```
3. Continue with Step 5 delivery as normal.

## Output Directory
`~/Documents/linkedin-graphics/` — files named `YYYYMMDD-HHMM-topic-slug.png`

## Timing Target
- Text polish: ~30 seconds
- Image generation: ~60-90 seconds (DALL-E 3)
- Crop + delivery: ~10 seconds
- **Total: < 3 minutes**

## Created
2026-04-15
