using System.Collections;
using UnityEngine;

public class RoomColorController : MonoBehaviour
{
    public static RoomColorController Instance { get; private set; }

    [Header("References")]
    [SerializeField] private SkyboxController skyboxController;

    [Header("Transition")]
    [SerializeField] private float transitionDuration = 2f;

    [Header("Light Intensity")]
    [SerializeField] private float minIntensity = 0.3f;
    [SerializeField] private float maxIntensity = 1.5f;

    [Header("Pulse Settings")]
    [SerializeField] private float basePulseSpeed = 1f;
    [SerializeField] private float pulseIntensityRange = 0.3f;
    [SerializeField] private float colorDriftSpeed = 0.15f;
    [SerializeField] private float colorDriftAmount = 0.08f;

    private Light[] _moodLights;
    private Coroutine[] _lightTransitions;

    // Live animation state
    private Color[] _baseColors;
    private float _baseIntensity;
    private float _energyLevel;
    private float _pulseSpeed;
    private bool _isAnimating;

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
        FindMoodLights();
    }

    void Update()
    {
        if (!_isAnimating || _moodLights == null || _baseColors == null) return;

        for (int i = 0; i < _moodLights.Length; i++)
        {
            if (_moodLights[i] == null) continue;

            // Each light pulses at slightly different phase
            float phase = i * 0.7f;
            float pulse = Mathf.Sin((Time.time + phase) * _pulseSpeed * Mathf.PI * 2f);

            // Intensity pulse ¡ª higher energy = bigger pulse
            float intensityPulse = pulse * pulseIntensityRange * _energyLevel;
            _moodLights[i].intensity = _baseIntensity + intensityPulse;

            // Subtle color drift ¡ª each light drifts independently
            float drift = Mathf.Sin((Time.time + phase * 1.3f) * colorDriftSpeed);
            Color baseColor = _baseColors[i % _baseColors.Length];

            // Drift toward a neighboring palette color
            int nextColorIdx = (i + 1) % _baseColors.Length;
            Color driftTarget = _baseColors[nextColorIdx];
            float driftT = (drift + 1f) * 0.5f * colorDriftAmount;
            _moodLights[i].color = Color.Lerp(baseColor, driftTarget, driftT);
        }
    }

    public void FindMoodLights()
    {
        GameObject[] lightObjects = GameObject.FindGameObjectsWithTag("MoodLight");
        _moodLights = new Light[lightObjects.Length];
        for (int i = 0; i < lightObjects.Length; i++)
        {
            _moodLights[i] = lightObjects[i].GetComponent<Light>();
        }
        _lightTransitions = new Coroutine[_moodLights.Length];

        Debug.Log($"[RoomColorController] Found {_moodLights.Length} mood lights");
    }

    public void ApplyMoodData(string atmosphere, Color[] colorPalette, float energyLevel)
    {
        _baseColors = colorPalette;
        _energyLevel = energyLevel;
        _baseIntensity = Mathf.Lerp(minIntensity, maxIntensity, energyLevel);

        // Pulse speed scales with energy: chill = slow, hype = fast
        _pulseSpeed = basePulseSpeed * (0.5f + energyLevel * 1.5f);

        ApplyMoodLights(colorPalette, energyLevel);

        Color primaryColor = colorPalette.Length > 0 ? colorPalette[0] : Color.gray;
        skyboxController.SetAtmosphere(atmosphere, primaryColor);

        _isAnimating = true;
    }

    private void ApplyMoodLights(Color[] colorPalette, float energyLevel)
    {
        if (_moodLights == null || _moodLights.Length == 0) return;

        for (int i = 0; i < _moodLights.Length; i++)
        {
            if (_moodLights[i] == null) continue;

            Color targetColor = colorPalette[i % colorPalette.Length];
            float targetIntensity = Mathf.Lerp(minIntensity, maxIntensity, energyLevel);

            if (_lightTransitions[i] != null)
                StopCoroutine(_lightTransitions[i]);

            _lightTransitions[i] = StartCoroutine(
                TransitionLight(_moodLights[i], targetColor, targetIntensity, transitionDuration)
            );
        }
    }

    private IEnumerator TransitionLight(Light light, Color targetColor, float targetIntensity, float duration)
    {
        Color startColor = light.color;
        float startIntensity = light.intensity;

        float elapsed = 0f;
        while (elapsed < duration)
        {
            float t = elapsed / duration;
            light.color = Color.Lerp(startColor, targetColor, t);
            light.intensity = Mathf.Lerp(startIntensity, targetIntensity, t);
            elapsed += Time.deltaTime;
            yield return null;
        }

        light.color = targetColor;
        light.intensity = targetIntensity;
    }

    public void ReapplyCurrentPalette()
    {
        FindMoodLights();
    }
}