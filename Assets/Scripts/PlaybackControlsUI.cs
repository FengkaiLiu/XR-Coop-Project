using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class PlaybackControlsUI : MonoBehaviour
{
    [Header("Button")]
    [SerializeField] private Button playPauseButton;

    [Header("Play/Pause Text")]
    [SerializeField] private TextMeshProUGUI playPauseText;

    private bool _isPlaying;

    void Start()
    {
        playPauseButton.onClick.AddListener(OnPlayPauseClicked);
        SetPlayingState(false);
    }

    private void OnPlayPauseClicked()
    {
        if (_isPlaying)
        {
            ApiClient.Instance.PausePlayback();
            SetPlayingState(false);
        }
        else
        {
            ApiClient.Instance.ResumePlayback();
            SetPlayingState(true);
        }
    }

    public void SetPlayingState(bool playing)
    {
        _isPlaying = playing;
        if (playPauseText != null)
            playPauseText.text = playing ? "Pause" : "Play";
    }
}