using System;
using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(AudioSource))]
public class ApiClient : MonoBehaviour
{
    public static ApiClient Instance { get; private set; }

    [Header("Audio")]
    [SerializeField] private AudioClip[] audioClips;

    [Header("References")]
    [SerializeField] private RoomColorController roomColorController;

    [Header("Resources (under Assets/Resources)")]
    [SerializeField] private string libraryResourcePath = "MoodData/library";
    [SerializeField] private string tracksResourceFolder = "MoodData/tracks";

    public event Action<TrackListData> OnLibraryLoaded;

    private AudioSource _audioSource;
    private Dictionary<string, AudioClip> _clipsByName;

    public float CurrentTimeMs =>
        _audioSource != null && _audioSource.clip != null
            ? _audioSource.time * 1000f
            : 0f;

    public bool IsPlaying => _audioSource != null && _audioSource.isPlaying;

    void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;

        _audioSource = GetComponent<AudioSource>();
        _audioSource.playOnAwake = false;
        _audioSource.loop = false;

        BuildClipIndex();
    }

    void Start()
    {
        FetchLibrary();
    }

    private void BuildClipIndex()
    {
        _clipsByName = new Dictionary<string, AudioClip>();
        if (audioClips == null) return;
        foreach (var c in audioClips)
            if (c != null) _clipsByName[c.name] = c;
        Debug.Log($"[ApiClient] Indexed {_clipsByName.Count} audio clips");
    }

    // ── Public API ───────────────────────────────────────────────

    public void FetchLibrary()
    {
        var ta = Resources.Load<TextAsset>(libraryResourcePath);
        if (ta == null)
        {
            Debug.LogError($"[ApiClient] Cannot load TextAsset at Resources/{libraryResourcePath}.json");
            return;
        }

        try
        {
            var data = JsonUtility.FromJson<TrackListData>(ta.text);
            Debug.Log($"[ApiClient] Library loaded: {data.tracks.Length} tracks");
            OnLibraryLoaded?.Invoke(data);
        }
        catch (Exception e)
        {
            Debug.LogError($"[ApiClient] Library parse error: {e.Message}");
        }
    }

    public void AnalyzeTrack(string trackId)
    {
        string path = $"{tracksResourceFolder}/{trackId}";
        var ta = Resources.Load<TextAsset>(path);
        if (ta == null)
        {
            Debug.LogError($"[ApiClient] Cannot load TextAsset at Resources/{path}.json");
            return;
        }

        AnalyzeData data;
        try
        {
            data = JsonUtility.FromJson<AnalyzeData>(ta.text);
        }
        catch (Exception e)
        {
            Debug.LogError($"[ApiClient] Track parse error: {e.Message}");
            return;
        }

        ApplyAnalysis(data);
        PlayClipFor(data);
    }

    public void PausePlayback()
    {
        if (_audioSource != null && _audioSource.isPlaying)
            _audioSource.Pause();

        var controls = FindObjectOfType<PlaybackControlsUI>();
        if (controls != null) controls.SetPlayingState(false);
    }

    public void ResumePlayback()
    {
        if (_audioSource != null && _audioSource.clip != null)
            _audioSource.UnPause();

        var controls = FindObjectOfType<PlaybackControlsUI>();
        if (controls != null) controls.SetPlayingState(true);
    }

    // ── Internals ────────────────────────────────────────────────

    private void ApplyAnalysis(AnalyzeData data)
    {
        Color[] colors = ParseColors(data.mood.color_palette);
        float energy = EnergyToFloat(data.mood.energy_level);
        string atmosphere = string.IsNullOrEmpty(data.mood.atmosphere)
            ? data.mood.primary
            : data.mood.atmosphere;

        Debug.Log($"[ApiClient] {data.track_info.name} | mood={data.mood.primary} | atmosphere={atmosphere} | energy={energy}");

        if (roomColorController != null)
            roomColorController.ApplyMoodData(atmosphere, colors, energy);

        if (TVDisplayController.Instance != null)
        {
            TVDisplayController.Instance.UpdateDisplay(
                data.track_info.name,
                data.track_info.artist,
                data.track_info.album_art ?? "",
                colors
            );
        }

        if (data.lyrics != null && data.lyrics.lines != null)
        {
            var lines = new List<LyricLine>(data.lyrics.lines.Length);
            foreach (var l in data.lyrics.lines)
                lines.Add(new LyricLine { timeMs = l.time_ms, text = l.text });

            if (FloatingLyricsController.Instance != null)
                FloatingLyricsController.Instance.SetLyrics(data.lyrics.synced, lines);
            if (TVDisplayController.Instance != null)
                TVDisplayController.Instance.SetTVLyrics(data.lyrics.synced, lines);
        }
    }

    private void PlayClipFor(AnalyzeData data)
    {
        string stem = StripExtension(data.audio_file);
        if (string.IsNullOrEmpty(stem))
        {
            Debug.LogError($"[ApiClient] Track JSON for '{data.track_id}' has no audio_file field");
            return;
        }

        if (!_clipsByName.TryGetValue(stem, out var clip))
        {
            Debug.LogError(
                $"[ApiClient] No AudioClip named '{stem}'. " +
                $"Drag '{data.audio_file}' into ApiClient.audioClips in the Inspector.");
            return;
        }

        _audioSource.clip = clip;
        _audioSource.time = 0f;
        _audioSource.Play();

        var controls = FindObjectOfType<PlaybackControlsUI>();
        if (controls != null) controls.SetPlayingState(true);
    }

    // ── Helpers ──────────────────────────────────────────────────

    private static string StripExtension(string filename)
    {
        if (string.IsNullOrEmpty(filename)) return "";
        int dot = filename.LastIndexOf('.');
        return dot >= 0 ? filename.Substring(0, dot) : filename;
    }

    private Color[] ParseColors(string[] palette)
    {
        if (palette == null || palette.Length == 0) return new[] { Color.gray };
        var colors = new Color[palette.Length];
        for (int i = 0; i < palette.Length; i++)
        {
            string hex = palette[i];
            if (!hex.StartsWith("#")) hex = "#" + hex;
            ColorUtility.TryParseHtmlString(hex, out colors[i]);
        }
        return colors;
    }

    private float EnergyToFloat(string energy)
    {
        switch (energy)
        {
            case "high": return 0.85f;
            case "medium": return 0.5f;
            case "low": return 0.2f;
            default: return 0.5f;
        }
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.L))
        {
            Debug.Log("[ApiClient] L pressed — reload library");
            FetchLibrary();
        }
    }
}

// ── Data classes (match shape produced by bake_demo_data.py) ────

[Serializable]
public class TrackListData { public TrackItem[] tracks; }

[Serializable]
public class TrackItem
{
    public string id;
    public string audio_file;
    public string name;
    public string artist;
    public string album_art;
    public int duration_ms;
}

[Serializable]
public class AnalyzeData
{
    public string track_id;
    public string audio_file;
    public TrackInfo track_info;
    public MoodInfo mood;
    public LyricsData lyrics;
}

[Serializable]
public class TrackInfo
{
    public string name;
    public string artist;
    public string album_art;
    public int duration_ms;
}

[Serializable]
public class MoodInfo
{
    public string primary;
    public string secondary;
    public string[] tags;
    public string[] color_palette;
    public string atmosphere;
    public string emotional_tone;
    public string energy_level;
    public string source;
}

[Serializable]
public class LyricsData
{
    public bool synced;
    public LyricsLine[] lines;
}

[Serializable]
public class LyricsLine
{
    public int time_ms;
    public string text;
}
