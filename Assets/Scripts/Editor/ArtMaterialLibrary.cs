using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

[InitializeOnLoad]
public static class ArtMaterialLibrary
{
    const string k_Folder = "Assets/Art/Materials";
    const string k_Json = k_Folder + "/materials.json";

    [Serializable]
    class Entry
    {
        public string name, albedo, normal;
        public float[] tint, emission;
        public float metallic, smoothness, alpha, emissionStrength, bump = 0.5f;
        public bool emissionFromAlbedo;
    }

    [Serializable]
    class Library
    {
        public Entry[] materials;
    }

    static ArtMaterialLibrary()
    {
        EditorApplication.delayCall += BuildIfOutdated;
    }

    static void BuildIfOutdated()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode || !File.Exists(k_Json))
            return;
        if (EditorApplication.isCompiling || EditorApplication.isUpdating)
        {
            EditorApplication.delayCall += BuildIfOutdated;
            return;
        }

        var stamp = k_Folder + "/.built";
        if (File.Exists(stamp) && File.GetLastWriteTimeUtc(stamp) >= File.GetLastWriteTimeUtc(k_Json))
            return;
        Build();
        File.WriteAllText(stamp, DateTime.UtcNow.ToString("o"));
    }

    [MenuItem("Workshop/Rebuild Art Materials")]
    public static void Build()
    {
        var library = JsonUtility.FromJson<Library>(File.ReadAllText(k_Json));
        var lit = Shader.Find("Universal Render Pipeline/Lit");
        foreach (var e in library.materials)
        {
            var path = $"{k_Folder}/{e.name}.mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null)
            {
                material = new Material(lit);
                AssetDatabase.CreateAsset(material, path);
            }

            var albedo = string.IsNullOrEmpty(e.albedo) ? null : AssetDatabase.LoadAssetAtPath<Texture2D>(e.albedo);
            var normal = string.IsNullOrEmpty(e.normal) ? null : AssetDatabase.LoadAssetAtPath<Texture2D>(e.normal);
            material.SetTexture("_BaseMap", albedo);
            material.SetColor("_BaseColor", new Color(e.tint[0], e.tint[1], e.tint[2], e.alpha));
            material.SetFloat("_Metallic", e.metallic);
            material.SetFloat("_Smoothness", e.smoothness);

            material.SetTexture("_BumpMap", normal);
            material.SetFloat("_BumpScale", e.bump);
            SetKeyword(material, "_NORMALMAP", normal != null);

            bool emissive = e.emissionFromAlbedo || e.emission[0] + e.emission[1] + e.emission[2] > 0f;
            if (emissive)
            {
                var colour = e.emissionFromAlbedo
                    ? Color.white * e.emissionStrength * 0.6f
                    : new Color(e.emission[0], e.emission[1], e.emission[2]) * 0.25f;
                material.SetColor("_EmissionColor", colour);
                material.SetTexture("_EmissionMap", e.emissionFromAlbedo ? albedo : null);
                material.globalIlluminationFlags = MaterialGlobalIlluminationFlags.BakedEmissive;
            }
            SetKeyword(material, "_EMISSION", emissive);

            bool transparent = e.alpha < 1f;
            material.SetFloat("_Surface", transparent ? 1f : 0f);
            material.SetFloat("_Blend", 0f);
            material.SetFloat("_SrcBlend", transparent ? (float)BlendMode.SrcAlpha : (float)BlendMode.One);
            material.SetFloat("_DstBlend", transparent ? (float)BlendMode.OneMinusSrcAlpha : (float)BlendMode.Zero);
            material.SetFloat("_ZWrite", transparent ? 0f : 1f);
            material.renderQueue = transparent ? (int)RenderQueue.Transparent : -1;
            material.SetOverrideTag("RenderType", transparent ? "Transparent" : "Opaque");
            SetKeyword(material, "_SURFACE_TYPE_TRANSPARENT", transparent);

            material.enableInstancing = true;
            EditorUtility.SetDirty(material);
        }
        AssetDatabase.SaveAssets();
        foreach (var folder in new[] { "Assets/Art/Environment", "Assets/Art/Characters", "Assets/Art/Toys" })
        {
            if (AssetDatabase.IsValidFolder(folder))
                AssetDatabase.ImportAsset(folder, ImportAssetOptions.ImportRecursive | ImportAssetOptions.ForceUpdate);
        }
        Debug.Log($"Art materials: built {library.materials.Length} URP materials from materials.json.");
    }

    static void SetKeyword(Material material, string keyword, bool on)
    {
        if (on)
            material.EnableKeyword(keyword);
        else
            material.DisableKeyword(keyword);
    }
}
