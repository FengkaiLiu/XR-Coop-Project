using UnityEngine;
using TMPro;

/// <summary>
/// Scrolls TMP text horizontally when it overflows its container.
/// Attach to the same GameObject as TextMeshProUGUI.
/// </summary>
[RequireComponent(typeof(TextMeshProUGUI))]
public class MarqueeText : MonoBehaviour
{
    [SerializeField] private float scrollSpeed = 30f;
    [SerializeField] private float pauseAtStart = 2f;
    [SerializeField] private float pauseAtEnd = 1f;
    [SerializeField] private float gapWidth = 80f;

    private TextMeshProUGUI _text;
    private RectTransform _rect;
    private float _textWidth;
    private float _containerWidth;
    private float _scrollPos;
    private float _timer;
    private bool _needsScroll;

    private enum State { PauseStart, Scrolling, PauseEnd, Reset }
    private State _state;

    void Awake()
    {
        _text = GetComponent<TextMeshProUGUI>();
        _rect = GetComponent<RectTransform>();
        _text.overflowMode = TextOverflowModes.Overflow;
        _text.enableWordWrapping = false;
    }

    void LateUpdate()
    {
        _textWidth = _text.preferredWidth;
        _containerWidth = _rect.rect.width;
        _needsScroll = _textWidth > _containerWidth + 1f;

        if (!_needsScroll)
        {
            _text.margin = new Vector4(0, 0, 0, 0);
            _state = State.PauseStart;
            _timer = 0;
            return;
        }

        switch (_state)
        {
            case State.PauseStart:
                _text.margin = new Vector4(0, 0, 0, 0);
                _timer += Time.deltaTime;
                if (_timer >= pauseAtStart)
                {
                    _timer = 0;
                    _scrollPos = 0;
                    _state = State.Scrolling;
                }
                break;

            case State.Scrolling:
                _scrollPos += scrollSpeed * Time.deltaTime;
                _text.margin = new Vector4(-_scrollPos, 0, 0, 0);
                if (_scrollPos >= _textWidth - _containerWidth + gapWidth)
                {
                    _timer = 0;
                    _state = State.PauseEnd;
                }
                break;

            case State.PauseEnd:
                _timer += Time.deltaTime;
                if (_timer >= pauseAtEnd)
                {
                    _state = State.Reset;
                }
                break;

            case State.Reset:
                _scrollPos = 0;
                _text.margin = new Vector4(0, 0, 0, 0);
                _timer = 0;
                _state = State.PauseStart;
                break;
        }
    }

    /// <summary>
    /// Call when text content changes to restart scroll
    /// </summary>
    public void ResetScroll()
    {
        _scrollPos = 0;
        _timer = 0;
        _state = State.PauseStart;
        if (_text != null)
            _text.margin = new Vector4(0, 0, 0, 0);
    }
}