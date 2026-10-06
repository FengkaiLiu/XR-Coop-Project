"""
Mood Mapper v2 — AI-first with genre fallback

Priority order:
  1. AI analysis (Claude/Gemini) — best accuracy, understands context
  2. Audio features (Spotify) — good for energy/valence, but no cultural context
  3. Genre/tag matching (Last.fm + Spotify) — decent fallback, but too generic
"""

# ─── Color palettes by mood category ─────────────────────────────
MOOD_PALETTES = {
    "euphoric":   ["#FF1493", "#FFD700", "#FF69B4", "#FFA500"],
    "driving":    ["#FF4500", "#FF6347", "#DC143C", "#FF8C00"],
    "intense":    ["#8B0000", "#FF0000", "#1C1C1C", "#DC143C"],
    "groovy":     ["#9B59B6", "#E91E63", "#FF4081", "#FFEA00"],
    "melancholy": ["#1a1a3e", "#2d2d5e", "#4a4a8a", "#6a6aaa"],
    "dreamy":     ["#2d1b69", "#7b68ee", "#dda0dd", "#e6e6fa"],
    "warm":       ["#D2691E", "#DEB887", "#F4A460", "#CD853F"],
    "dark":       ["#0D0D0D", "#1A0A2E", "#2D0036", "#330000"],
    "smooth":     ["#2C1810", "#8B6914", "#D4A574", "#C9956B"],
    "ethereal":   ["#E8D5F5", "#C4B0FF", "#A8E6CF", "#DCD0FF"],
    "acoustic":   ["#8B7355", "#D2B48C", "#F5DEB3", "#DEB887"],
    "neutral":    ["#4A4A6A", "#6A6A8A", "#8A8AAA", "#3A3A5A"],
}

# ─── Genre → mood mapping (fallback only) ────────────────────────
GENRE_MOODS = {
    "metal":       {"primary": "dark",       "tags": ["dark", "intense"]},
    "death metal": {"primary": "dark",       "tags": ["dark", "intense", "driving"]},
    "black metal": {"primary": "dark",       "tags": ["dark", "intense"]},
    "punk":        {"primary": "intense",    "tags": ["intense", "driving"]},
    "hardcore":    {"primary": "intense",    "tags": ["intense", "dark", "driving"]},
    "jazz":        {"primary": "smooth",     "tags": ["smooth", "warm"]},
    "soul":        {"primary": "warm",       "tags": ["warm", "smooth"]},
    "r&b":         {"primary": "smooth",     "tags": ["smooth", "groovy"]},
    "blues":       {"primary": "melancholy", "tags": ["melancholy", "warm"]},
    "ambient":     {"primary": "ethereal",   "tags": ["ethereal", "dreamy"]},
    "classical":   {"primary": "ethereal",   "tags": ["ethereal"]},
    "lo-fi":       {"primary": "dreamy",     "tags": ["dreamy", "melancholy"]},
    "lofi":        {"primary": "dreamy",     "tags": ["dreamy", "melancholy"]},
    "chillhop":    {"primary": "dreamy",     "tags": ["dreamy", "groovy"]},
    "indie":       {"primary": "dreamy",     "tags": ["dreamy", "warm"]},
    "indie pop":   {"primary": "euphoric",   "tags": ["euphoric", "dreamy"]},
    "folk":        {"primary": "warm",       "tags": ["warm", "acoustic"]},
    "country":     {"primary": "warm",       "tags": ["warm"]},
    "pop":         {"primary": "euphoric",   "tags": ["euphoric", "groovy"]},
    "k-pop":       {"primary": "euphoric",   "tags": ["euphoric", "driving"]},
    "j-pop":       {"primary": "euphoric",   "tags": ["euphoric", "dreamy"]},
    "dance":       {"primary": "euphoric",   "tags": ["euphoric", "driving", "groovy"]},
    "edm":         {"primary": "driving",    "tags": ["driving", "euphoric"]},
    "electronic":  {"primary": "driving",    "tags": ["driving"]},
    "techno":      {"primary": "driving",    "tags": ["driving", "dark"]},
    "house":       {"primary": "groovy",     "tags": ["groovy", "driving"]},
    "hip hop":     {"primary": "groovy",     "tags": ["groovy"]},
    "rap":         {"primary": "groovy",     "tags": ["groovy", "intense"]},
    "trap":        {"primary": "dark",       "tags": ["dark", "groovy"]},
    "reggae":      {"primary": "warm",       "tags": ["warm", "groovy"]},
    "latin":       {"primary": "warm",       "tags": ["warm", "groovy"]},
    "rock":        {"primary": "intense",    "tags": ["intense"]},
    "alt rock":    {"primary": "intense",    "tags": ["intense", "dreamy"]},
    "grunge":      {"primary": "dark",       "tags": ["dark", "melancholy"]},
    "emo":         {"primary": "melancholy", "tags": ["melancholy", "intense"]},
    "acoustic":    {"primary": "warm",       "tags": ["warm", "acoustic"]},
    "singer-songwriter": {"primary": "warm", "tags": ["warm", "melancholy"]},
    # ── New: niche genres that were missing ──
    "vocaloid":    {"primary": "ethereal",   "tags": ["ethereal", "dreamy", "driving"]},
    "nightcore":   {"primary": "driving",    "tags": ["driving", "euphoric", "dreamy"]},
    "synth pop":   {"primary": "euphoric",   "tags": ["euphoric", "dreamy"]},
    "funk":        {"primary": "groovy",     "tags": ["groovy", "euphoric"]},
    "anime":       {"primary": "dreamy",     "tags": ["dreamy", "euphoric"]},
    "project sekai": {"primary": "ethereal", "tags": ["ethereal", "melancholy", "dreamy"]},
    "soft rock":   {"primary": "warm",       "tags": ["warm", "dreamy"]},
    "new wave":    {"primary": "driving",    "tags": ["driving", "dreamy"]},
    "city pop":    {"primary": "smooth",     "tags": ["smooth", "groovy", "warm"]},
    "shoegaze":    {"primary": "dreamy",     "tags": ["dreamy", "ethereal"]},
    "post-rock":   {"primary": "ethereal",   "tags": ["ethereal", "intense"]},
    "hyperpop":    {"primary": "euphoric",   "tags": ["euphoric", "driving", "intense"]},
}


def map_mood(features: dict | None, genres: list, lastfm_tags: list = None, ai_analysis: dict = None) -> dict:
    """
    AI-first mood mapping.

    If AI analysis succeeded → use it directly (best accuracy).
    If AI failed → fall back to audio features + genre/tag matching.
    """

    # ════════════════════════════════════════════════════════════
    # PRIORITY 1: AI analysis (highest confidence)
    # ════════════════════════════════════════════════════════════
    if ai_analysis and ai_analysis.get("color_palette"):
        ai_tags = ai_analysis.get("mood_tags", [])
        ai_primary = ai_analysis.get("primary_mood", ai_tags[0] if ai_tags else "neutral")

        # Use AI colors directly
        ai_colors = ai_analysis["color_palette"]

        # Pick secondary from AI tags
        ai_secondary = ai_tags[1] if len(ai_tags) > 1 else ai_primary

        return {
            "primary": ai_primary,
            "secondary": ai_secondary,
            "tags": ai_tags,
            "color_palette": ai_colors,
            "atmosphere": ai_analysis.get("atmosphere", ""),
            "emotional_tone": ai_analysis.get("emotional_tone", ""),
            "energy_level": ai_analysis.get("energy_level", "medium"),
            "color_reasoning": ai_analysis.get("color_reasoning", ""),
            "source": "ai",
        }

    # ════════════════════════════════════════════════════════════
    # PRIORITY 2: Audio features + genre (Spotify data available)
    # ════════════════════════════════════════════════════════════
    all_tags = list(genres)
    if lastfm_tags:
        all_tags.extend(lastfm_tags)

    if features:
        return _map_from_features(features, all_tags)

    # ════════════════════════════════════════════════════════════
    # PRIORITY 3: Genre/tag matching only (no Spotify features)
    # ════════════════════════════════════════════════════════════
    return _map_from_genres(all_tags)


def _map_from_features(features: dict, genres: list) -> dict:
    """Map mood from Spotify audio features + genre tags."""
    energy = features.get("energy", 0.5)
    valence = features.get("valence", 0.5)
    tempo = features.get("tempo", 120)
    danceability = features.get("danceability", 0.5)
    acousticness = features.get("acousticness", 0.5)
    instrumentalness = features.get("instrumentalness", 0.0)
    mode = features.get("mode", 1)

    tags = []

    # Primary mood from energy + valence grid
    if energy > 0.6 and valence > 0.6:
        primary = "euphoric"
    elif energy > 0.6 and valence <= 0.4:
        primary = "intense"
    elif energy <= 0.4 and valence > 0.6:
        primary = "warm"
    elif energy <= 0.4 and valence <= 0.4:
        primary = "melancholy"
    else:
        primary = "neutral"

    tags.append(primary)

    if tempo > 140:
        tags.append("driving")
    elif tempo < 80:
        tags.append("dreamy")

    if danceability > 0.7:
        tags.append("groovy")
    if acousticness > 0.7:
        tags.append("acoustic")
    if instrumentalness > 0.5:
        tags.append("instrumental")
    if mode == 0:
        tags.append("somber")

    # Add genre-based tags (lower priority, just supplements)
    genre_str = " ".join(genres).lower()
    for keyword, tag in {
        "metal": "dark", "jazz": "smooth", "ambient": "ethereal",
        "classical": "ethereal", "punk": "intense", "lo-fi": "dreamy",
        "lofi": "dreamy", "r&b": "smooth", "soul": "warm",
        "electronic": "driving", "indie": "dreamy", "hip hop": "groovy",
        "rap": "groovy", "pop": "euphoric", "blues": "melancholy",
        "folk": "warm", "country": "warm", "vocaloid": "ethereal",
        "funk": "groovy", "nightcore": "driving",
    }.items():
        if keyword in genre_str and tag not in tags:
            tags.append(tag)

    secondary = tags[1] if len(tags) > 1 else primary

    color_palette = _blend_palette(primary, secondary)

    return {
        "primary": primary,
        "secondary": secondary,
        "tags": tags,
        "color_palette": color_palette,
        "atmosphere": "",
        "emotional_tone": "",
        "energy_level": "high" if energy > 0.66 else ("low" if energy < 0.33 else "medium"),
        "color_reasoning": f"Based on audio features (energy={energy:.2f}, valence={valence:.2f})",
        "source": "audio_features",
    }





def _map_from_genres(genres: list) -> dict:
    """Fallback: map mood purely from genre/tag strings."""
    genre_str = " ".join(genres).lower()

    # Score each mood by counting matching genres
    mood_scores = {}
    for genre_key, mood_info in GENRE_MOODS.items():
        if genre_key in genre_str:
            for tag in mood_info["tags"]:
                mood_scores[tag] = mood_scores.get(tag, 0) + 1

    if not mood_scores:
        return {
            "primary": "neutral",
            "secondary": "neutral",
            "tags": ["neutral"],
            "color_palette": MOOD_PALETTES["neutral"],
            "atmosphere": "",
            "emotional_tone": "",
            "energy_level": "medium",
            "color_reasoning": "No matching genres found — using neutral",
            "source": "fallback",
        }

    # Sort by score — highest voted mood wins
    sorted_moods = sorted(mood_scores.items(), key=lambda x: -x[1])
    primary = sorted_moods[0][0]
    secondary = sorted_moods[1][0] if len(sorted_moods) > 1 else primary

    # Collect all unique tags
    all_tags = list(dict.fromkeys([m[0] for m in sorted_moods]))

    color_palette = _blend_palette(primary, secondary)

    return {
        "primary": primary,
        "secondary": secondary,
        "tags": all_tags,
        "color_palette": color_palette,
        "atmosphere": "",
        "emotional_tone": "",
        "energy_level": "medium",
        "color_reasoning": f"Based on genre/tag voting: {dict(sorted_moods[:5])}",
        "source": "genre_tags",
    }


def _blend_palette(primary: str, secondary: str) -> list:
    """Blend two mood palettes: 3 colors from primary + 1 from secondary."""
    p1 = MOOD_PALETTES.get(primary, MOOD_PALETTES["neutral"])
    p2 = MOOD_PALETTES.get(secondary, MOOD_PALETTES["neutral"])
    return p1[:3] + [p2[0]]