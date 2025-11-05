import json, os, glob, datetime
from slugify import slugify

# latest JSON dhundo
files = sorted(glob.glob("output/*.json"))
if not files:
    print("No JSON found"); raise SystemExit(0)
latest = files[-1]
data = json.load(open(latest, "r", encoding="utf-8"))

def md(article):
    title = (article.get("title") or "").strip()
    link = (article.get("link") or "").strip()
    summary = (article.get("summary") or "").strip()
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    slug = (slugify(title)[:80] or slugify(link)[:80] or "news-"+now)
    img_prompt = f"A clean modern illustration of: {title}. Abstract shapes, soft lighting, no logos/trademarks, editorial style."
    meta = summary[:150].replace('"', '')

    body = f"""---
title: "{title}"
date: {now}
slug: "{slug}"
meta_description: "{meta}"
tags: ["crypto","news"]
source: "{link}"
image_prompt: "{img_prompt}"
---

## TL;DR
- {summary[:200] or "Key points will be added after rewrite."}

## Kya naya hai
- (facts yahan add honge)

## Background
(short context)

## Sources
- {link}
"""
    return slug, body

os.makedirs("drafts", exist_ok=True)
made = 0
for a in data:
    slug, body = md(a)
    fn = f"drafts/{slug}.md"
    if not os.path.exists(fn):
        with open(fn, "w", encoding="utf-8") as f:
            f.write(body)
        made += 1
print("Drafts created:", made)
