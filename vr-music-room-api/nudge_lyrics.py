"""Shift all lyric timestamps in a baked track JSON by a fixed offset.

Negative offset = lyrics appear earlier (use this if lyrics LAG the audio).
Positive offset = lyrics appear later  (use this if lyrics LEAD the audio).

Usage:
    python nudge_lyrics.py coldplay-yellow -1500
    python nudge_lyrics.py wham-last-christmas 500
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRACKS_DIR = HERE.parent / "Assets" / "Resources" / "MoodData" / "tracks"


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    slug = sys.argv[1]
    try:
        offset_ms = int(sys.argv[2])
    except ValueError:
        print(f"offset must be an integer (milliseconds), got: {sys.argv[2]}")
        sys.exit(1)

    path = TRACKS_DIR / f"{slug}.json"
    if not path.exists():
        print(f"Not found: {path}")
        available = sorted(p.stem for p in TRACKS_DIR.glob("*.json"))
        print("Available track slugs:")
        for a in available:
            print(f"  {a}")
        sys.exit(1)

    data = json.loads(path.read_text(encoding="utf-8"))
    lines = data.get("lyrics", {}).get("lines", []) or []
    if not lines:
        print(f"No lyrics in {slug}")
        return

    for line in lines:
        line["time_ms"] = max(0, int(line["time_ms"]) + offset_ms)

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Shifted {len(lines)} lines by {offset_ms}ms in {slug}")
    print(f"First line now at  {lines[0]['time_ms']}ms : {lines[0]['text'][:50]}")
    print(f"Last  line now at  {lines[-1]['time_ms']}ms : {lines[-1]['text'][:50]}")


if __name__ == "__main__":
    main()
