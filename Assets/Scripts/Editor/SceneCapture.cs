using System.IO;
using UnityEditor;
using UnityEngine;

[InitializeOnLoad]
public static class SceneCapture
{
    static readonly (string name, Vector3 eye, Vector3 target, float fov)[] k_Views =
    {
        ("PlayerView", new Vector3(0f, 1.6f, -0.1f), new Vector3(0.1f, 1.0f, 1.5f), 75f),
        ("Wide", new Vector3(1.8f, 1.9f, -1.6f), new Vector3(-0.6f, 0.9f, 1.2f), 70f),
        ("Fireside", new Vector3(-0.4f, 1.3f, -1.0f), new Vector3(-2.6f, 0.8f, 0.9f), 60f),
        ("Toymaker", new Vector3(0.3f, 1.5f, 0.0f), new Vector3(1.15f, 1.2f, 0.95f), 50f),
        ("ToyTown", new Vector3(1.3f, 1.45f, -0.2f), new Vector3(2.42f, 0.8f, -0.5f), 60f),
        ("Mantel", new Vector3(-1.6f, 1.55f, 0.6f), new Vector3(-2.52f, 1.42f, 0.9f), 45f),
    };

    static SceneCapture()
    {
        if (SessionState.GetBool("Workshop.CaptureDone", false))
            return;
        SessionState.SetBool("Workshop.CaptureDone", true);
        EditorApplication.delayCall += Capture;
    }

    [MenuItem("Workshop/Capture Preview Images")]
    public static void Capture()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode)
            return;

        var folder = Path.Combine(Directory.GetCurrentDirectory(), "Captures");
        Directory.CreateDirectory(folder);
        var go = new GameObject("Capture Camera") { hideFlags = HideFlags.HideAndDontSave };
        var cam = go.AddComponent<Camera>();
        cam.nearClipPlane = 0.02f;
        cam.farClipPlane = 50f;
        var rt = new RenderTexture(1600, 900, 24, RenderTextureFormat.ARGB32);
        cam.targetTexture = rt;
        try
        {
            foreach (var (name, eye, target, fov) in k_Views)
            {
                cam.fieldOfView = fov;
                go.transform.SetPositionAndRotation(eye, Quaternion.LookRotation(target - eye));
                cam.Render();
                RenderTexture.active = rt;
                var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
                tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
                tex.Apply();
                File.WriteAllBytes(Path.Combine(folder, name + ".png"), tex.EncodeToPNG());
                Object.DestroyImmediate(tex);
            }
            Debug.Log("Scene capture: saved preview images to " + folder);
        }
        finally
        {
            RenderTexture.active = null;
            cam.targetTexture = null;
            Object.DestroyImmediate(rt);
            Object.DestroyImmediate(go);
        }
    }
}
