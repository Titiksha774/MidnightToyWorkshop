using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

public class ArtImport : AssetPostprocessor
{
    const string k_ArtFolder = "Assets/Art/";
    static readonly string[] k_Animated =
    {
        "Toymaker", "CuckooClock", "Fireplace", "Workbench",
        "SteamTrain", "MusicBox", "JackInTheBox", "ToySoldier", "WindUpMouse", "ToyTown", "Chalkboard",
    };
    static readonly string[] k_LoopingClips =
    {
        "Idle", "Talk", "Tick", "Flicker",
        "Drive", "Play", "Crank", "March", "Sniff", "Scurry", "Spin",
    };

    static bool IsArtModel(string path) => path.StartsWith(k_ArtFolder) && path.EndsWith(".fbx");
    static bool IsAnimated(string path) => k_Animated.Contains(Path.GetFileNameWithoutExtension(path));

    void OnPreprocessModel()
    {
        if (!IsArtModel(assetPath))
            return;

        var importer = (ModelImporter)assetImporter;
        importer.bakeAxisConversion = true;
        importer.importCameras = false;
        importer.importLights = false;
        importer.importBlendShapes = false;
        importer.isReadable = false;
        importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
        importer.materialLocation = ModelImporterMaterialLocation.InPrefab;

        bool animated = IsAnimated(assetPath);
        importer.animationType = animated ? ModelImporterAnimationType.Generic : ModelImporterAnimationType.None;
        importer.importAnimation = animated;
    }

    void OnPreprocessAnimation()
    {
        if (!IsArtModel(assetPath) || !IsAnimated(assetPath))
            return;

        var importer = (ModelImporter)assetImporter;
        var clips = importer.defaultClipAnimations;
        foreach (var clip in clips)
        {
            var name = clip.takeName.Contains("|") ? clip.takeName.Substring(clip.takeName.LastIndexOf('|') + 1) : clip.takeName;
            clip.name = name;
            clip.loopTime = k_LoopingClips.Contains(name);
        }
        importer.clipAnimations = clips;
    }

    Material OnAssignMaterialModel(Material material, Renderer renderer)
    {
        if (!IsArtModel(assetPath))
            return null;
        return AssetDatabase.LoadAssetAtPath<Material>($"{k_ArtFolder}Materials/{material.name}.mat");
    }

    void OnPreprocessTexture()
    {
        if (assetPath.StartsWith(k_ArtFolder + "UI/"))
        {
            var ui = (TextureImporter)assetImporter;
            ui.textureType = TextureImporterType.Sprite;
            ui.spriteImportMode = SpriteImportMode.Single;
            ui.alphaIsTransparency = true;
            ui.mipmapEnabled = true;
            ui.wrapMode = TextureWrapMode.Clamp;
            ui.maxTextureSize = 2048;
            string file = Path.GetFileNameWithoutExtension(assetPath);
            ui.spriteBorder = file == "Rounded" ? new Vector4(48, 48, 48, 48)
                : file == "Shadow" ? new Vector4(56, 56, 56, 56) : Vector4.zero;
            return;
        }
        if (!assetPath.StartsWith(k_ArtFolder + "Textures/"))
            return;

        var importer = (TextureImporter)assetImporter;
        importer.maxTextureSize = 1024;
        if (assetPath.EndsWith("_normal.png"))
        {
            importer.textureType = TextureImporterType.NormalMap;
        }
        else
        {
            importer.textureType = TextureImporterType.Default;
            importer.sRGBTexture = true;
        }
    }
}
