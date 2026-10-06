import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_song_with_ai(
    title: str,
    artist: str,
    genres: list,
    lastfm_tags: list,
    lyrics_sample: list,
) -> dict:
    """Use Gemini to analyze a song's title, artist, and lyrics for mood and color."""

    lyrics_text = "\n".join([line["text"] for line in lyrics_sample[:30]]) if lyrics_sample else "No lyrics available"

    prompt = f"""Analyze this song and suggest the visual mood and color palette for a VR music room experience.

Song: "{title}" by {artist}
Genres: {', '.join(genres) if genres else 'unknown'}
Community Tags: {', '.join(lastfm_tags[:10]) if lastfm_tags else 'none'}

Lyrics sample:
{lyrics_text}

Based on the title, artist style, genres, tags, and lyrics, respond ONLY with a JSON object (no markdown, no backticks, no preamble):
{{
  "mood_tags": ["tag1", "tag2", "tag3"],
  "primary_mood": "one word mood",
  "atmosphere": "a short 2-3 word visual atmosphere description like 'neon rain city' or 'sunset ocean calm' or 'dark cosmic void'",
  "color_palette": ["#hex1", "#hex2", "#hex3", "#hex4"],
  "color_reasoning": "brief explanation of why these colors fit",
  "energy_level": "low/medium/high",
  "emotional_tone": "one word like nostalgic, hopeful, melancholy, rebellious, dreamy, etc"
}}

Important:
- Choose colors that match the FEELING of the song, not just the genre
- A fast song can still have cool/blue colors if the lyrics are sad or nostalgic
- Consider the language and cultural context of the song
- The colors will be used to generate skyboxes and textures for a VR room
- Be creative and specific with the atmosphere description"""

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=prompt,
        )
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)

        return {
            "mood_tags": result.get("mood_tags", []),
            "primary_mood": result.get("primary_mood", ""),
            "atmosphere": result.get("atmosphere", ""),
            "color_palette": result.get("color_palette", []),
            "color_reasoning": result.get("color_reasoning", ""),
            "energy_level": result.get("energy_level", "medium"),
            "emotional_tone": result.get("emotional_tone", ""),
            "source": "ai_analysis",
        }

    except Exception as e:
        print(f"[AI Analyzer] Error: {e}")
        return None