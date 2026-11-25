using UnityEngine;

[RequireComponent(typeof(Light))]
public class FireFlicker : MonoBehaviour
{
    [Range(0f, 1f)] public float amount = 0.3f;
    public float speed = 6f;

    Light m_Light;
    float m_BaseIntensity;
    float m_Seed;

    void Awake()
    {
        m_Light = GetComponent<Light>();
        m_BaseIntensity = m_Light.intensity;
        m_Seed = Random.value * 100f;
    }

    void Update()
    {
        float n = Mathf.PerlinNoise(m_Seed, Time.time * speed) * 0.7f + Mathf.PerlinNoise(m_Seed + 7f, Time.time * speed * 2.3f) * 0.3f;
        m_Light.intensity = m_BaseIntensity * (1f - amount + 2f * amount * n);
    }
}
