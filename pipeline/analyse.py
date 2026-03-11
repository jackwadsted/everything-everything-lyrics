"""
analyse.py

Reads data/lyrics.json, generates sentence embeddings for each song,
computes pairwise cosine similarity, extracts themes via Claude,
and writes docs/graph_data.json ready for the d3.js frontend.
"""

import json
import re
import time
from pathlib import Path

import anthropic
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import os

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

INPUT_PATH = Path("../data/lyrics.json")
OUTPUT_PATH = Path("../docs/graph_data.json")

SIMILARITY_THRESHOLD = 0.5
MODEL_NAME = "all-MiniLM-L6-v2"

ALBUM_COLOURS = {
    "Man Alive":     "#4e79a7",
    "Arc":           "#f28e2b",
    "Get to Heaven": "#e15759",
    "A Fever Dream": "#76b7b2",
    "Raw Data Feel": "#59a14f",
    "Re-Animator":   "#edc948",
    "Mountainhead":  "#b07aa1",
}

THEME_TAXONOMY = [
  "apocalyptic imagery",
  "authenticity versus illusion",
  "biological transformation",
  "bodily autonomy loss",
  "capitalist dehumanization",
  "choice and agency",
  "collective delusion",
  "collective transcendence",
  "commodification of experience",
  "communication breakdown",
  "conformity and control",
  "consciousness fragmentation",
  "cosmic catastrophe",
  "cyclical decay",
  "death and mortality",
  "dehumanization",
  "desire for connection",
  "digital manipulation",
  "disconnection and alienation",
  "existential crisis",
  "exploitation of the masses",
  "identity dissolution",
  "inevitable destruction",
  "inherited trauma",
  "isolation and desperation",
  "loss of agency",
  "memory and trauma",
  "moral corruption",
  "mortality anxiety",
  "obsessive desire",
  "self-destruction",
  "societal collapse",
  "surveillance and paranoia",
  "systemic oppression",
  "toxic codependency",
  "transformation and metamorphosis"
]

# ---------------------------------------------------------------------------
# Lyrics cleaning
# ---------------------------------------------------------------------------

def clean_lyrics(lyrics: str) -> str:
    lyrics = re.sub(r'\[.*?\]', '', lyrics)
    lyrics = re.sub(r'^\d+\s*$', '', lyrics, flags=re.MULTILINE)
    lyrics = re.sub(r'\n{3,}', '\n\n', lyrics)
    return lyrics.strip()


# ---------------------------------------------------------------------------
# Theme extraction via Claude
# ---------------------------------------------------------------------------

def extract_themes(title: str, album: str, lyrics: str, client: anthropic.Anthropic) -> list[str]:
    """
    Ask Claude to tag a song with 3-5 themes from the fixed taxonomy.
    Returns a subset of THEME_TAXONOMY.
    """
    taxonomy_str = "\n".join(f"- {t}" for t in THEME_TAXONOMY)

    prompt = f"""Analyse the lyrics of "{title}" by Everything Everything (from the album "{album}") and select the 3-5 most relevant themes from the list below.

You MUST only return themes from this exact list — do not invent new ones or rephrase them:
{taxonomy_str}

Return ONLY a JSON array of the selected theme strings, exactly as written above. No explanation, no preamble.

Lyrics:
{lyrics[:3000]}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'^```\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    try:
        themes = json.loads(raw)
        if isinstance(themes, list):
            return [str(t) for t in themes]
    except json.JSONDecodeError:
        print(f"    WARNING: Could not parse themes for '{title}': {raw}")

    return []


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading lyrics...")
    with open(INPUT_PATH, encoding="utf-8") as f:
        songs = json.load(f)
    print(f"Loaded {len(songs)} songs")

    for song in songs:
        song["lyrics"] = clean_lyrics(song["lyrics"])

    # Generate embeddings
    print(f"\nGenerating embeddings with {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    lyrics_texts = [song["lyrics"] for song in songs]
    embeddings = model.encode(lyrics_texts, show_progress_bar=True)

    # Compute pairwise cosine similarity
    print("\nComputing similarity matrix...")
    sim_matrix = cosine_similarity(embeddings)

    # Extract themes via Claude
    print("\nExtracting themes via Claude...")
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    for i, song in enumerate(songs):
        print(f"  [{i+1}/{len(songs)}] {song['title']}")
        song["themes"] = extract_themes(
            song["title"], song["album"], song["lyrics"], client
        )
        time.sleep(0.2)  # Be polite to the API

    # Build nodes
    nodes = []
    for i, song in enumerate(songs):
        nodes.append({
            "id": i,
            "title": song["title"],
            "album": song["album"],
            "year": song["year"],
            "colour": ALBUM_COLOURS.get(song["album"], "#aaaaaa"),
            "themes": song["themes"],
        })

    # Build combined edges
    # Score = 0.5 * embedding_similarity + 0.5 * (shared_themes / max_possible_shared)
    # Max possible shared themes between two songs = min(len(themes_a), len(themes_b))
    COMBINED_THRESHOLD = 0.40
    LYRICAL_WEIGHT = 0.33
    THEMATIC_WEIGHT = 0.67

    edges = []
    for i in range(len(songs)):
        for j in range(i + 1, len(songs)):
            emb_score = float(sim_matrix[i][j])

            ti = set(songs[i]["themes"])
            tj = set(songs[j]["themes"])
            shared = list(ti & tj)
            max_possible = min(len(ti), len(tj)) if ti and tj else 1
            theme_score = len(shared) / max_possible if max_possible > 0 else 0

            combined = (LYRICAL_WEIGHT * emb_score) + (THEMATIC_WEIGHT * theme_score)

            if combined >= COMBINED_THRESHOLD:
                edges.append({
                    "source": i,
                    "target": j,
                    "weight": round(combined, 4),
                    "lyrical": round(emb_score, 4),
                    "thematic": round(theme_score, 4),
                    "shared_themes": shared,
                    "shared_count": len(shared),
                })

    print(f"\nBuilt {len(nodes)} nodes and {len(edges)} edges (threshold={COMBINED_THRESHOLD})")

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "nodes": nodes,
            "edges": edges,
        }, f, indent=2, ensure_ascii=False)

    print(f"Saved graph data to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()