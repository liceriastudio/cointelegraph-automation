import os, glob, json, re, time, datetime, requests, random

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Per-run limit (env se override ho sakta hai)
MAX_ITEMS = int(os.environ.get("MAX_ITEMS", "2"))   # pehle 2 articles hi
PAUSE_SEC  = float(os.environ.get("PAUSE_SEC", "6"))  # har call ke beech pause

os.makedirs("rewritten", exist_ok=True)

def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def call_openai_with_retry(prompt, retries=5):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": MODEL,
        "temperature": 0.7,
        "messages": [
            {"role":"system","content":(
                "You are a careful crypto news editor. Rewrite fully in original wording (no copying), "
                "neutral, SEO-friendly. Add TL;DR, H2/H3, bullets. Return clean HTML only."
            )},
            {"role":"user","content": prompt}
        ]
    }
    delay = PAUSE_SEC
    for attempt in range(retries):
        r = requests.post(url, headers=headers, json=body, timeout=120)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        # 429/5xx → backoff
        if r.status_code in (429, 500, 502, 503, 504):
            wait = delay * (2 ** attempt) + random.uniform(0, 1.0)
            print(f"[WARN] HTTP {r.status_code}, retrying in {wait:.1f}s ...")
            time.sleep(wait)
            continue
        r.raise_for_status()
    # last try raise
    r.raise_for_status()
    return ""

def parse_frontmatter(md):
    if md.startswith("---"):
        end = md.find("\n---\n", 3)
        if end != -1:
            fm = md[4:end].splitlines()
            body = md[end+5:]
            meta = {}
            for line in fm:
                if ":" in line:
                    k,v = line.split(":",1)
                    meta[k.strip()] = v.strip().strip('"')
            return meta, body
    return {}, md

def main():
    if not OPENAI_API_KEY:
        raise SystemExit("OPENAI_API_KEY missing")
    files = sorted(glob.glob("drafts/*.md"))
    if not files:
        print("No drafts found"); return

    # Sirf pehle MAX_ITEMS process
    files = files[:MAX_ITEMS]

    total = 0
    for fp in files:
        md = read(fp)
        meta, body = parse_frontmatter(md)
        title = (meta.get("title") or "").strip()
        source = (meta.get("source") or "").strip()
        image_prompt = (meta.get("image_prompt") or "").strip()
        slug = (meta.get("slug") or re.sub(r'[^a-z0-9-]+','-', title.lower()).strip("-"))[:80] or "article"

        user_prompt = f"""TITLE: {title}
SOURCE: {source}
DRAFT MARKDOWN BODY:
{body}
Please output ONLY the article HTML (no <html> wrapper)."""

        html = call_openai_with_retry(user_prompt)

        out = {
            "title": title,
            "slug": slug,
            "source": source,
            "image_prompt": image_prompt,
            "meta_description": (body[:150]).replace("\n"," "),
            "html": html,
            "date": datetime.datetime.utcnow().strftime("%Y-%m-%d")
        }
        write(f"rewritten/{slug}.json", json.dumps(out, ensure_ascii=False, indent=2))
        total += 1
        print("Rewritten ->", slug)

        # polite pace
        time.sleep(PAUSE_SEC)

    print("Total:", total)

if __name__ == "__main__":
    main()
