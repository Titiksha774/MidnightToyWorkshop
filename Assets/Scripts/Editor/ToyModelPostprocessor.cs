using System.Linq;
using UnityEditor;
using UnityEngine;

public class ToyModelPostprocessor : AssetPostprocessor
{
    public const string MaterialPath = "Assets/Materials/ToyPalette.mat";
    const string k_ModelsFolder = "Assets/Models/";
    const string k_PalettePath = "Assets/Materials/ToyPalette.png";

    void OnPreprocessModel()
    {
        if (!assetPath.StartsWith(k_ModelsFolder))
            return;

        var importer = (ModelImporter)assetImporter;
        if (!importer.importSettingsMissing)
            return;

        importer.materialImportMode = ModelImporterMaterialImportMode.None;
        importer.animationType = ModelImporterAnimationType.None;
        importer.importAnimation = false;
        importer.importBlendShapes = false;
        importer.importCameras = false;
        importer.importLights = false;
        importer.isReadable = false;
        importer.addCollider = false;
    }

    void OnPostprocessModel(GameObject root)
    {
        if (!assetPath.StartsWith(k_ModelsFolder))
            return;

        var material = AssetDatabase.LoadAssetAtPath<Material>(MaterialPath);
        if (material == null)
            return;

        foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
            renderer.sharedMaterials = Enumerable.Repeat(material, renderer.sharedMaterials.Length).ToArray();
    }

    void OnPreprocessTexture()
    {
        if (assetPath != k_PalettePath)
            return;

        var importer = (TextureImporter)assetImporter;
        importer.filterMode = FilterMode.Point;
        importer.mipmapEnabled = false;
        importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.sRGBTexture = true;
        importer.wrapMode = TextureWrapMode.Clamp;
    }
}
