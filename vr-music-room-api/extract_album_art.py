"""Extract embedded album art from MP3 ID3 tags into Unity Resources, and
patch each baked track JSON + library.json so Unity can load the texture via
Resources.Load<Texture2D>(album_art)."""
import json
import sys
from pathlib import Path

from mutagen.id3 import ID3, APIC

HERE = Path(__file__).resolve().parent
UNITY_ROOT = HERE.parent
AUDIO_DIR = UNITY_ROOT / "Assets" / "Audio"
MOOD_DIR = UNITY_ROOT / "Assets" / "Resources" / "MoodData"
TRACKS_DIR = MOOD_DIR / "tracks"
ART_DIR = MOOD_DIR / "art"


def extract_one(mp3_path: Path, slug: str) -> str:
    try:
        tags = ID3(str(mp3_path))
    except Exception as e:
        print(f"  no ID3 tags ({e})")
        return ""

    for frame in tags.values():
        if not isinstance(frame, APIC):
            continue
        mime = (frame.mime or "").lower()
        if "jpeg" in mime or "jpg" in mime:
            ext = "jpg"
        elif "png" in mime:
            ext = "png"
        else:
            ext = "jpg"
        out = ART_DIR / f"{slug}.{ext}"
        out.write_bytes(frame.data)
        print(f"  wrote {out.name}  ({len(frame.data) // 1024} KB, {mime})")
        return f"MoodData/art/{slug}"

    print("  no embedded album art in ID3")
    return ""


def main():
    ART_DIR.mkdir(parents=True, exist_ok=True)
    json_files = sorted(TRACKS_DIR.glob("*.json"))
    print(f"Scanning {len(json_files)} track JSONs in {TRACKS_DIR}")

    art_paths = {}
    for jp in json_files:
        data = json.loads(jp.read_text(encoding="utf-8"))
        slug = data["track_id"]
        audio_file = data.get("audio_file", "")
        mp3 = AUDIO_DIR / audio_file
        print(f"\n[{slug}]  {audio_file}")
        if not mp3.exists():
            print(f"  ! mp3 not found: {mp3}")
            continue

        art_path = extract_one(mp3, slug)
        art_paths[slug] = art_path

        data["track_info"]["album_art"] = art_path
        jp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    lib_path = MOOD_DIR / "library.json"
    lib = json.loads(lib_path.read_text(encoding="utf-8"))
    for entry in lib["tracks"]:
        entry["album_art"] = art_paths.get(entry["id"], "")
    lib_path.write_text(json.dumps(lib, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nUpdated library.json")


if __name__ == "__main__":
    main()
