using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class TVDisplayController : MonoBehaviour
{
    public static TVDisplayController Instance { get; private set; }

    [Header("UI References")]
    [SerializeField] private Image background;
    [SerializeField] private Image darkOverlay;
    [SerializeField] private TextMeshProUGUI songTitle;
    [SerializeField] private TextMeshProUGUI artistName;
    [SerializeField] private RawImage albumArt;

    [Header("Lyrics References")]
    [SerializeField] private TextMeshProUGUI currentLyricLine;
    [SerializeField] private TextMeshProUGUI nextLyricLine;
    [SerializeField] private TextMeshProUGUI prevLyricLine;

    [Header("Color Gradient")]
    [SerializeField] private float colorCycleDuration = 4f;
    [SerializeField] private float overlayAlpha = 0.55f;

    private Color[] _palette;
    private Coroutine _gradientCoroutine;

    // Lyrics state
    private List<LyricLine> _tvLines = new List<LyricLine>();
    private bool _tvSynced;
    private int _tvCurrentIndex = -1;
    private Coroutine _unsyncedCoroutine;

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
        background.color = Color.black;
        if (darkOverlay != null)
            darkOverlay.color = new Color(0, 0, 0, 0);
        songTitle.text = "";
        artistName.text = "";
        albumArt.gameObject.SetActive(false);
        ClearLyricLines();
    }

    void Update()
    {
        if (!_tvSynced || _tvLines.Count == 0 || ApiClient.Instance == null) return;

        float timeMs = ApiClient.Instance.CurrentTimeMs;
        for (int i = _tvLines.Count - 1; i >= 0; i--)
        {
            if (timeMs >= _tvLines[i].timeMs)
            {
                if (i != _tvCurrentIndex)
                {
                    _tvCurrentIndex = i;
                    UpdateLyricDisplay(i);
                }
                break;
            }
        }
    }

    public void UpdateDisplay(string song, string artist, string albumArtUrl, Color[] colorPalette)
    {
        songTitle.text = song;
        artistName.text = artist;
        _palette = colorPalette;

        var titleMarquee = songTitle.GetComponent<MarqueeText>();
        if (titleMarquee != null) titleMarquee.ResetScroll();
        var artistMarquee = artistName.GetComponent<MarqueeText>();
        if (artistMarquee != null) artistMarquee.ResetScroll();

        if (darkOverlay != null)
            darkOverlay.color = new Color(0, 0, 0, overlayAlpha);

        if (_gradientCoroutine != null)
            StopCoroutine(_gradientCoroutine);
        _gradientCoroutine = StartCoroutine(CycleBackgroundColor());

        LoadAlbumArt(albumArtUrl);
    }

    public void SetTVLyrics(bool synced, List<LyricLine> lines)
    {
        Debug.Log($"[TVDisplay] SetTVLyrics called - synced: {synced}, lines: {lines?.Count ?? 0}");
        StopTVLyrics();
        _tvLines = lines ?? new List<LyricLine>();
        _tvSynced = synced;

        if (_tvLines.Count == 0)
        {
            ClearLyricLines();
            if (currentLyricLine != null)
                currentLyricLine.text = "No lyrics available";
            return;
        }

        if (_tvSynced)
        {
            _tvCurrentIndex = -1;
            ClearLyricLines();
        }
        else
        {
            _unsyncedCoroutine = StartCoroutine(ScrollUnsyncedTV());
        }
    }

    private void UpdateLyricDisplay(int index)
    {
        if (prevLyricLine != null)
        {
            prevLyricLine.text = index > 0 ? _tvLines[index - 1].text : "";
            prevLyricLine.color = new Color(1, 1, 1, 0.35f);
        }

        if (currentLyricLine != null)
        {
            currentLyricLine.text = _tvLines[index].text;
            currentLyricLine.color = Color.white;
        }

        if (nextLyricLine != null)
        {
            nextLyricLine.text = index < _tvLines.Count - 1 ? _tvLines[index + 1].text : "";
            nextLyricLine.color = new Color(1, 1, 1, 0.35f);
        }
    }

    private IEnumerator ScrollUnsyncedTV()
    {
        int index = 0;
        while (true)
        {
            UpdateLyricDisplay(index);
            index = (index + 1) % _tvLines.Count;
            yield return new WaitForSeconds(3f);
        }
    }

    private void StopTVLyrics()
    {
        _tvCurrentIndex = -1;
        if (_unsyncedCoroutine != null)
        {
            StopCoroutine(_unsyncedCoroutine);
            _unsyncedCoroutine = null;
        }
    }

    private void ClearLyricLines()
    {
        if (prevLyricLine != null) prevLyricLine.text = "";
        if (currentLyricLine != null) currentLyricLine.text = "";
        if (nextLyricLine != null) nextLyricLine.text = "";
    }

    private IEnumerator CycleBackgroundColor()
    {
        if (_palette == null || _palette.Length == 0) yield break;

        int index = 0;
        while (true)
        {
            Color from = _palette[index];
            Color to = _palette[(index + 1) % _palette.Length];

            float elapsed = 0f;
            while (elapsed < colorCycleDuration)
            {
                float t = elapsed / colorCycleDuration;
                background.color = Color.Lerp(from, to, t);
                elapsed += Time.deltaTime;
                yield return null;
            }

            index = (index + 1) % _palette.Length;
        }
    }

    private void LoadAlbumArt(string resourcePath)
    {
        if (string.IsNullOrEmpty(resourcePath))
        {
            albumArt.texture = null;
            albumArt.gameObject.SetActive(false);
            return;
        }

        var tex = Resources.Load<Texture2D>(resourcePath);
        if (tex != null)
        {
            albumArt.texture = tex;
            albumArt.gameObject.SetActive(true);
        }
        else
        {
            albumArt.texture = null;
            albumArt.gameObject.SetActive(false);
            Debug.LogWarning($"[TVDisplay] No album art at Resources/{resourcePath}");
        }
    }
}