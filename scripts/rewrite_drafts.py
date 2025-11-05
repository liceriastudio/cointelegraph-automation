import os, json
from openai import OpenAI
from slugify import slugify

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

input_folder = "drafts"
output_folder = "rewritten"
os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if not filename.endswith(".md"):
        continue

    with open(os.path.join(input_folder, filename), "r") as f:
        content = f.read()

    prompt = f"Rewrite this crypto news article in a fresh, SEO-friendly style. Keep facts same but reword sentences naturally:\n\n{content}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert crypto journalist."},
            {"role": "user", "content": prompt}
        ]
    )

    rewritten_text = response.choices[0].message.content
    new_filename = slugify(filename.replace('.md', '')) + "-rewritten.md"

    with open(os.path.join(output_folder, new_filename), "w") as out:
        out.write(rewritten_text)

print("✅ All drafts rewritten and saved to 'rewritten/' folder")
