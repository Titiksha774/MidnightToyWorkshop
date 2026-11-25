using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit.Inputs.Simulation;
using UnityEngine.XR.Management;

public static class HeadsetAutoSwitch
{
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void OnSceneLoaded()
    {
        var manager = XRGeneralSettings.Instance != null ? XRGeneralSettings.Instance.Manager : null;
        if (manager == null || manager.activeLoader == null)
        {
            Debug.Log("Headset: none found, using the XR Interaction Simulator (keyboard and mouse).");
            return;
        }

        // real headset is on, so the keyboard/mouse simulator gets out of the way
        foreach (var sim in Object.FindObjectsByType<XRInteractionSimulator>(FindObjectsInactive.Exclude, FindObjectsSortMode.None))
            sim.gameObject.SetActive(false);
        Debug.Log("Headset: " + manager.activeLoader.name + " running, simulator turned off.");
    }
}
