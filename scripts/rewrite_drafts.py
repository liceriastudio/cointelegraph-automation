import os, glob, json, re, datetime, textwrap, requests

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

os.makedirs("rewritten", exist_ok=True)

def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def call_openai(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    data = {
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
    r = requests.post(url, headers=headers, json=data, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

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

        html = call_openai(user_prompt)

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
    print("Total:", total)

if __name__ == "__main__":
    main()
