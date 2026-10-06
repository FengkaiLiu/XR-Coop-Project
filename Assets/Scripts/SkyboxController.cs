using System.Collections;
using UnityEngine;

public class SkyboxController : MonoBehaviour
{
    [SerializeField] private float transitionDuration = 2f;
    private Material _skyMat;
    private Coroutine _activeTransition;

    void Start()
    {
        _skyMat = RenderSettings.skybox;
    }

    public void SetAtmosphere(string atmosphere, Color primaryColor)
    {
        Color targetColor;
        float targetExposure;

        switch (atmosphere)
        {
            case "dreamy":
                targetColor = new Color(0.4f, 0.3f, 0.6f);
                targetExposure = 0.8f;
                break;

            case "energetic":
                targetColor = new Color(0.8f, 0.3f, 0.1f);
                targetExposure = 1.2f;
                break;

            case "melancholic":
                targetColor = new Color(0.15f, 0.18f, 0.25f);
                targetExposure = 0.5f;
                break;

            case "serene":
                targetColor = new Color(0.3f, 0.5f, 0.7f);
                targetExposure = 1.0f;
                break;

            default:
                targetColor = primaryColor;
                targetExposure = 1.0f;
                break;
        }

        // Stop any ongoing transition before starting a new one
        if (_activeTransition != null)
            StopCoroutine(_activeTransition);

        _activeTransition = StartCoroutine(
            TransitionSkybox(targetColor, targetExposure, transitionDuration)
        );
    }

    private IEnumerator TransitionSkybox(Color targetColor, float targetExposure, float duration)
    {
        Color startColor = _skyMat.GetColor("_SkyColor");
        float startExposure = _skyMat.GetFloat("_Exposure");

        float elapsed = 0f;
        while (elapsed < duration)
        {
            float t = elapsed / duration;
            _skyMat.SetColor("_SkyColor", Color.Lerp(startColor, targetColor, t));
            _skyMat.SetFloat("_Exposure", Mathf.Lerp(startExposure, targetExposure, t));
            DynamicGI.UpdateEnvironment();
            elapsed += Time.deltaTime;
            yield return null;
        }

        // Ensure final values are exact
        _skyMat.SetColor("_SkyColor", targetColor);
        _skyMat.SetFloat("_Exposure", targetExposure);
        DynamicGI.UpdateEnvironment();

        _activeTransition = null;
    }
}