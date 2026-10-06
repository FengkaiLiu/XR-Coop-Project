using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class FloatingLyricsController : MonoBehaviour
{
    public static FloatingLyricsController Instance { get; private set; }

    [Header("References")]
    [SerializeField] private TextMeshPro lyricsText;

    [Header("Appearance")]
    [SerializeField] private float floatHeight = 0.5f;
    [SerializeField] private float bobAmplitude = 0.05f;
    [SerializeField] private float bobSpeed = 1f;
    [SerializeField] private float fadeInDuration = 0.3f;

    [Header("Unsynced Scroll Settings")]
    [SerializeField] private float unsyncedInterval = 3f;

    private List<LyricLine> _lines = new List<LyricLine>();
    private bool _isSynced;
    private int _currentLineIndex = -1;
    private Vector3 _basePosition;
    private Coroutine _unsyncedCoroutine;
    private Coroutine _fadeCoroutine;

    void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
    }

    void Start()
    {
        _basePosition = transform.localPosition;
        if (lyricsText != null)
            lyricsText.text = "";
    }

    void Update()
    {
        // Gentle bob animation (always runs)
        if (lyricsText != null && lyricsText.text != "")
        {
            float bob = Mathf.Sin(Time.time * bobSpeed) * bobAmplitude;
            transform.localPosition = _basePosition + Vector3.up * (floatHeight + bob);
        }

        if (_isSynced && _lines.Count > 0 && ApiClient.Instance != null)
        {
            UpdateLineAtTime(ApiClient.Instance.CurrentTimeMs);
        }
    }

    private void UpdateLineAtTime(float timeMs)
    {
        for (int i = _lines.Count - 1; i >= 0; i--)
        {
            if (timeMs >= _lines[i].timeMs)
            {
                if (i != _currentLineIndex)
                {
                    _currentLineIndex = i;
                    ShowLine(_lines[i].text);
                }
                break;
            }
        }
    }

    public void SetLyrics(bool synced, List<LyricLine> lines)
    {
        Stop();
        _lines = lines ?? new List<LyricLine>();
        _isSynced = synced;

        if (_lines.Count == 0)
        {
            ShowLine("No lyrics available");
            return;
        }

        if (_isSynced)
        {
            _currentLineIndex = -1;
            lyricsText.text = "";
            Debug.Log($"[Lyrics] Synced playback started with {_lines.Count} lines");
        }
        else
        {
            _unsyncedCoroutine = StartCoroutine(ScrollUnsynced());
            Debug.Log($"[Lyrics] Unsynced scroll started with {_lines.Count} lines");
        }
    }

    private IEnumerator ScrollUnsynced()
    {
        int index = 0;
        while (true)
        {
            ShowLine(_lines[index].text);
            index = (index + 1) % _lines.Count;
            yield return new WaitForSeconds(unsyncedInterval);
        }
    }

    private void ShowLine(string text)
    {
        if (lyricsText == null) return;
        if (_fadeCoroutine != null)
            StopCoroutine(_fadeCoroutine);
        _fadeCoroutine = StartCoroutine(FadeInLine(text));
    }

    private IEnumerator FadeInLine(string text)
    {
        lyricsText.text = text;
        float elapsed = 0f;
        Color color = lyricsText.color;

        while (elapsed < fadeInDuration)
        {
            float alpha = elapsed / fadeInDuration;
            lyricsText.color = new Color(color.r, color.g, color.b, alpha);
            elapsed += Time.deltaTime;
            yield return null;
        }
        lyricsText.color = new Color(color.r, color.g, color.b, 1f);
    }

    public void Stop()
    {
        _currentLineIndex = -1;
        if (_unsyncedCoroutine != null)
        {
            StopCoroutine(_unsyncedCoroutine);
            _unsyncedCoroutine = null;
        }
        if (_fadeCoroutine != null)
        {
            StopCoroutine(_fadeCoroutine);
            _fadeCoroutine = null;
        }
        if (lyricsText != null)
            lyricsText.text = "";
    }
}

[Serializable]
public class LyricLine
{
    public int timeMs;
    public string text;
}