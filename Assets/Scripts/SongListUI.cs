using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class SongListUI : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Transform contentParent;
    [SerializeField] private GameObject songItemPrefab;

    [Header("Loading State")]
    [SerializeField] private GameObject loadingText;

    void Start()
    {
        ApiClient.Instance.OnLibraryLoaded += PopulateList;
    }

    void OnDestroy()
    {
        if (ApiClient.Instance != null)
            ApiClient.Instance.OnLibraryLoaded -= PopulateList;
    }

    public void FetchLibrary()
    {
        if (loadingText != null) loadingText.SetActive(true);
        ClearList();
        ApiClient.Instance.FetchLibrary();
    }

    private void PopulateList(TrackListData data)
    {
        if (loadingText != null) loadingText.SetActive(false);
        ClearList();

        if (data.tracks == null || data.tracks.Length == 0)
        {
            Debug.LogWarning("[SongListUI] No tracks found");
            return;
        }

        foreach (var track in data.tracks)
        {
            GameObject item = Instantiate(songItemPrefab, contentParent);

            // Set song name
            TextMeshProUGUI songText = item.GetComponentInChildren<TextMeshProUGUI>();
            if (songText != null) songText.text = track.name;

            // Load album art
            RawImage albumArt = item.GetComponentInChildren<RawImage>();
            if (albumArt != null && !string.IsNullOrEmpty(track.album_art))
            {
                var tex = Resources.Load<Texture2D>(track.album_art);
                if (tex != null) albumArt.texture = tex;
            }

            // Set up button click
            string trackId = track.id;
            Button btn = item.GetComponent<Button>();
            if (btn != null)
            {
                // Highlight on select
                btn.onClick.AddListener(() =>
                {
                    Debug.Log($"[SongListUI] Selected: {track.name} ({trackId})");
                    ApiClient.Instance.AnalyzeTrack(trackId);
                });
            }
        }

        Debug.Log($"[SongListUI] Populated {data.tracks.Length} songs");
    }

    private void ClearList()
    {
        for (int i = contentParent.childCount - 1; i >= 0; i--)
        {
            Destroy(contentParent.GetChild(i).gameObject);
        }
    }
}