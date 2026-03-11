"""
derive_taxonomy.py

One-off script that reads all themes from docs/graph_data.json,
asks Claude to consolidate them into a canonical taxonomy, and
prints the result for you to review and edit.

Once you're happy with the taxonomy, paste it into analyse.py as THEME_TAXONOMY.
"""

import json
from pathlib import Path
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

GRAPH_PATH = Path("../docs/graph_data.json")


def main():
    with open(GRAPH_PATH, encoding="utf-8") as f:
        graph = json.load(f)

    # Collect all unique themes across all songs
    all_themes = set()
    for node in graph["nodes"]:
        for theme in node.get("themes", []):
            all_themes.add(theme.strip().lower())

    print(f"Found {len(all_themes)} unique themes across the corpus\n")

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = f"""Below is a list of themes extracted from Everything Everything's lyrics across their full discography.

Your task is to consolidate these into a clean canonical taxonomy of 20-30 high-level themes. 

Rules:
- Merge near-duplicates and overly granular variants into single clear labels (e.g. "societal collapse and abandonment" and "societal collapse" → "societal collapse")
- Keep labels concise: 2-4 words maximum
- Preserve what's genuinely distinct and interesting about EE's lyrical content
- Don't invent new themes that aren't represented in the source list

Return ONLY a JSON array of theme strings. No explanation, no preamble.

Source themes:
{json.dumps(sorted(all_themes), indent=2)}"""

    print("Asking Claude to consolidate themes...\n")
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        taxonomy = json.loads(raw)
        print("Suggested taxonomy:\n")
        for i, theme in enumerate(taxonomy, 1):
            print(f"  {i:2}. {theme}")
        print(f"\nTotal: {len(taxonomy)} themes")
        print(
            "\nEdit this list as you see fit, then paste it into analyse.py as THEME_TAXONOMY."
        )

        # Also save to a file for easy editing
        out = Path("../data/taxonomy_draft.json")
        with open(out, "w") as f:
            json.dump(taxonomy, f, indent=2)
        print(f"\nDraft saved to {out}")

    except json.JSONDecodeError:
        print("Could not parse response. Raw output:")
        print(raw)


if __name__ == "__main__":
    main()
