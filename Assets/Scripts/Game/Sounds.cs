using System;
using UnityEngine;

public class Sounds : MonoBehaviour
{
    public static Sounds Instance { get; private set; }

    public AudioClip snap, wind, whistle, boing, squeak, clatter, cuckoo, click, whoosh, babble, sparkle, bump;

    AudioSource m_Ui;

    void Awake()
    {
        Instance = this;
        m_Ui = gameObject.AddComponent<AudioSource>();
        m_Ui.playOnAwake = false;
        m_Ui.ignoreListenerPause = true;
    }

    public static void Play(Func<Sounds, AudioClip> pick, Vector3 position, float volume = 1f, float pitch = 1f)
    {
        if (Instance == null)
            return;
        var clip = pick(Instance);
        var go = new GameObject(clip.name);
        go.transform.position = position;
        var source = go.AddComponent<AudioSource>();
        source.clip = clip;
        source.volume = volume;
        source.pitch = pitch;
        source.spatialBlend = 1f;
        source.minDistance = 0.5f;
        source.maxDistance = 12f;
        source.Play();
        Destroy(go, clip.length / pitch + 0.1f);
    }

    public void PlayClick() => m_Ui.PlayOneShot(click, 0.6f);

    public void PlayWhoosh() => m_Ui.PlayOneShot(whoosh, 0.5f);
}
