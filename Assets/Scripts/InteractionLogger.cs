using System;
using System.IO;
using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit.Interactables;

public class InteractionLogger : MonoBehaviour
{
    public GestureRecognizer gestureRecognizer;

    string m_LogPath;
    float m_StartTime;
    bool m_Stopping;

    void Start()
    {
        var folder = Path.Combine(Application.persistentDataPath, "Logs");
        Directory.CreateDirectory(folder);
        m_LogPath = Path.Combine(folder, $"session_{DateTime.Now:yyyyMMdd_HHmmss}.csv");
        File.WriteAllText(m_LogPath, "seconds,event\n");
        m_StartTime = Time.time;

        foreach (var interactable in FindObjectsByType<XRBaseInteractable>(FindObjectsSortMode.None))
        {
            string objectName = interactable.name;
            interactable.hoverEntered.AddListener(_ => Log("Hover " + objectName));
            interactable.selectEntered.AddListener(args =>
            {
                if (!(args.interactorObject is PartSocket))
                    Log("Grab " + objectName);
            });
        }

        if (gestureRecognizer != null)
            gestureRecognizer.GestureRecognized += (gesture, confidence) => Log($"Gesture {gesture} ({confidence:P0})");
        Log("Session start");
    }

    // leaving play mode pops parts out of their sockets, no point logging that
    void OnApplicationQuit() => m_Stopping = true;
    void OnDisable() => m_Stopping = true;

    public void Log(string message)
    {
        if (!m_Stopping && m_LogPath != null)
            File.AppendAllText(m_LogPath, $"{Time.time - m_StartTime:F2},{message.Replace(',', ';')}\n");
    }
}
