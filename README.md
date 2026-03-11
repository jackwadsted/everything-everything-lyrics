# everything-everything-lyrics

An interactive graph visualisation of lyrical and thematic connections across Everything Everything's discography.

**[View it live](https://jackwadsted.github.io/everything-everything-lyrics)**

---

## How it works

The pipeline runs in three stages: lyrics fetching, analysis, and visualisation.

### 1. Fetch lyrics (`pipeline/fetch_lyrics.py`)

Pulls lyrics for all seven studio albums from the Genius API using hardcoded album IDs. The Genius search endpoint returns 403s due to Cloudflare, so tracks are fetched directly via album pages. Output is written to `data/lyrics.json` (gitignored).

Albums covered: *Man Alive*, *Arc*, *Get to Heaven*, *A Fever Dream*, *Re-Animator*, *Raw Data Feel*, *Mountainhead*.

### 2. Analyse (`pipeline/analyse.py`)

For each song:

- **Lyrical similarity:** lyrics are embedded using `sentence-transformers` (`all-MiniLM-L6-v2`) and cosine similarity is computed across all song pairs.
- **Thematic similarity:** Claude (Haiku) assigns 3-5 tags to each song from a fixed 36-theme taxonomy. Thematic similarity is the proportion of shared tags relative to the maximum possible overlap.

These two scores are combined into a single edge weight:

```
weight = 0.33 * lyrical_similarity + 0.67 * thematic_similarity
```

Edges below a threshold of `0.4` are discarded. The resulting nodes and edges are written to `docs/graph_data.json`.

### 3. Visualise (`docs/index.html`)

A d3.js force-directed graph. Edge colour and thickness scale with combined weight - stronger connections are brighter and thicker. Nodes are coloured by album.

- **Hover an edge:** see the connection strength breakdown and shared themes
- **Click a node:** open a detail panel showing the song's themes and its strongest connections
- **Broad / Tight slider:** filters edges by weight threshold; nodes with no surviving connections are hidden
- **Album legend:** click to show/hide individual albums

---

## Running the pipeline

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```
GENIUS_TOKEN=your_genius_token
ANTHROPIC_API_KEY=your_anthropic_key
```

Then:

```bash
python pipeline/fetch_lyrics.py   # writes data/lyrics.json
python pipeline/analyse.py        # writes docs/graph_data.json
```

> **Note:** `analyse.py` calls the Claude API once per song to extract themes. Themes are not cached between runs - if you only need to adjust edge weights, consider saving themes to `lyrics.json` to avoid repeat API calls.

---

## Roadmap

- **Search:** filter nodes by song title directly in the graph
- **EPs and non-album singles:** extend coverage beyond studio albums
- **Quiz mode:** given a set of themes and an album, guess the song

---

## Stack

- [`lyricsgenius`](https://github.com/johnwmillr/LyricsGenius) - Genius API client
- [`sentence-transformers`](https://www.sbert.net/) - lyrical embeddings
- [`anthropic`](https://github.com/anthropic-ai/anthropic-sdk-python) - theme extraction
- [`d3.js`](https://d3js.org/) - graph visualisation