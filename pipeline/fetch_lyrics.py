"""
fetch_lyrics.py

Fetches lyrics for all Everything Everything albums via the Genius REST API
and saves them to data/lyrics.json.

Uses the official api.genius.com endpoints for album/track lookup, and
lyricsgenius for lyrics scraping (the only part it does reliably).
"""

import json
import os
from pathlib import Path

import lyricsgenius
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GENIUS_TOKEN = os.environ.get("GENIUS_TOKEN")

ALBUMS = [
    {"title": "Man Alive",      "year": 2010, "genius_id": 62663},
    {"title": "Arc",            "year": 2013, "genius_id": 104009},
    {"title": "Get to Heaven",  "year": 2015, "genius_id": 119936},
    {"title": "A Fever Dream",  "year": 2017, "genius_id": 349991},
    {"title": "Re-Animator",    "year": 2020, "genius_id": 627061},
    {"title": "Raw Data Feel",  "year": 2022, "genius_id": 867889},
    {"title": "Mountainhead",   "year": 2024, "genius_id": 1092824},
]

OUTPUT_PATH = Path("data/lyrics.json")


def main():
    genius = lyricsgenius.Genius(
    os.environ.get("GENIUS_TOKEN"),
    remove_section_headers=True,
    sleep_time=0.5,
    retries=3,
    excluded_terms=["(Live)", "(Demo)", "(Remix)", "(Acoustic)"],
    verbose=True,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    all_songs = []

    for album in ALBUMS:
        print(f"\nFetching: {album['title']}")
        tracks = genius.album_tracks(album['genius_id'])

        for track in tracks['tracks']:
            song = track['song']
            print(f"\nFetching lyrics for: {song['title']}")

            lyrics = genius.lyrics(song_url=song['url'], 
                                   remove_section_headers=True)
            lyrics = lyrics.split('\n', 2)[-1]

            all_songs.append({
             "title": song['title'],
             "album": album["title"],
             "year": album["year"],
             "lyrics": lyrics,
            })

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_songs, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(all_songs)} songs to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()