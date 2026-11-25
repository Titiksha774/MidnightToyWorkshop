using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.PackageManager.UI;
using UnityEditor.SceneManagement;
using UnityEditor.XR.Management;
using UnityEditor.XR.Management.Metadata;
using UnityEditor.XR.OpenXR.Features;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.XR.Management;
using UnityEngine.XR.OpenXR;
using UnityEngine.XR.OpenXR.Features.Interactions;

[InitializeOnLoad]
public static class WorkshopProjectSetup
{
    const string k_XriPackage = "com.unity.xr.interaction.toolkit";
    const string k_TmpSettingsPath = "Assets/TextMesh Pro/Resources/TMP Settings.asset";
    const string k_LayerSettingsPath = "Assets/XRI/Settings/Resources/InteractionLayerSettings.asset";
    const string k_ScenePath = "Assets/Scenes/Workshop.unity";
    const string k_RigPrefabName = "XR Origin (XR Rig)";
    const string k_SimulatorPrefabName = "XR Interaction Simulator";
    const int k_TeleportLayer = 31;

    static WorkshopProjectSetup()
    {
        EditorApplication.delayCall += RunWhenReady;
    }

    [MenuItem("Workshop/Run Project Setup")]
    static void RunFromMenu()
    {
        SessionState.SetInt("Workshop.SampleImportAttempts", 0);
        Run();
    }

    static void RunWhenReady()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode)
            return;

        if (EditorApplication.isCompiling || EditorApplication.isUpdating)
        {
            EditorApplication.delayCall += RunWhenReady;
            return;
        }

        Run();
    }

    static void Run()
    {
        bool imported = ImportTmpEssentials() | ImportXriSamples();
        if (imported)
        {
            Debug.Log("Workshop setup: importing TextMesh Pro / XR samples, setup will continue automatically...");
            EditorApplication.delayCall += RunWhenReady;
            return;
        }

        EnsureTeleportLayer();
        ConfigureOpenXR();
        EnsureToyPaletteMaterial();
        CreateWorkshopSceneIfMissing();
    }

    static void EnsureToyPaletteMaterial()
    {
        var palette = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Materials/ToyPalette.png");
        if (palette == null || AssetDatabase.LoadAssetAtPath<Material>(ToyModelPostprocessor.MaterialPath) != null)
            return;

        var material = new Material(Shader.Find("Universal Render Pipeline/Lit"));
        material.SetTexture("_BaseMap", palette);
        material.SetColor("_BaseColor", Color.white);
        material.SetFloat("_Smoothness", 0.35f);
        material.enableInstancing = true;
        AssetDatabase.CreateAsset(material, ToyModelPostprocessor.MaterialPath);

        AssetDatabase.ImportAsset("Assets/Models", ImportAssetOptions.ImportRecursive | ImportAssetOptions.ForceUpdate);
        Debug.Log("Workshop setup: created ToyPalette material and applied it to all models.");
    }

    static bool ImportTmpEssentials()
    {
        if (File.Exists(k_TmpSettingsPath) || SessionState.GetBool("Workshop.TmpImported", false))
            return false;

        SessionState.SetBool("Workshop.TmpImported", true);
        TMPro.TMP_PackageResourceImporter.ImportResources(true, false, false);
        return true;
    }

    static bool ImportXriSamples()
    {
        var package = UnityEditor.PackageManager.PackageInfo.FindForAssetPath($"Packages/{k_XriPackage}");
        int attempts = SessionState.GetInt("Workshop.SampleImportAttempts", 0);
        if (package == null || attempts >= 3)
            return false;

        bool importedAny = false;
        foreach (var sample in Sample.FindByPackage(k_XriPackage, package.version))
        {
            bool wanted = sample.displayName == "Starter Assets" || sample.displayName == "XR Interaction Simulator";
            if (wanted && !sample.isImported)
            {
                sample.Import(Sample.ImportOptions.HideImportWindow);
                importedAny = true;
            }
        }

        if (importedAny)
        {
            SessionState.SetInt("Workshop.SampleImportAttempts", attempts + 1);
            AssetDatabase.Refresh();
        }
        return importedAny;
    }

    static void EnsureTeleportLayer()
    {
        var settings = AssetDatabase.LoadAssetAtPath<ScriptableObject>(k_LayerSettingsPath);
        if (settings == null)
            return;

        var serialized = new SerializedObject(settings);
        var names = serialized.FindProperty("m_LayerNames");
        if (names == null || names.arraySize <= k_TeleportLayer)
            return;

        var layer = names.GetArrayElementAtIndex(k_TeleportLayer);
        if (layer.stringValue == "Teleport")
            return;

        layer.stringValue = "Teleport";
        serialized.ApplyModifiedPropertiesWithoutUndo();
        AssetDatabase.SaveAssets();
        Debug.Log("Workshop setup: Interaction Layer 31 set to 'Teleport'.");
    }

    static void ConfigureOpenXR()
    {
        const BuildTargetGroup target = BuildTargetGroup.Standalone;

        EditorBuildSettings.TryGetConfigObject(XRGeneralSettings.k_SettingsKey, out XRGeneralSettingsPerBuildTarget perTarget);
        if (perTarget == null)
        {
            var guid = AssetDatabase.FindAssets("t:XRGeneralSettingsPerBuildTarget").FirstOrDefault();
            if (guid != null)
                perTarget = AssetDatabase.LoadAssetAtPath<XRGeneralSettingsPerBuildTarget>(AssetDatabase.GUIDToAssetPath(guid));
        }
        if (perTarget == null)
        {
            if (!AssetDatabase.IsValidFolder("Assets/XR"))
                AssetDatabase.CreateFolder("Assets", "XR");
            perTarget = ScriptableObject.CreateInstance<XRGeneralSettingsPerBuildTarget>();
            AssetDatabase.CreateAsset(perTarget, "Assets/XR/XRGeneralSettingsPerBuildTarget.asset");
        }
        EditorBuildSettings.AddConfigObject(XRGeneralSettings.k_SettingsKey, perTarget, true);

        if (perTarget.ManagerSettingsForBuildTarget(target) == null)
            perTarget.CreateDefaultManagerSettingsForBuildTarget(target);

        var general = XRGeneralSettingsPerBuildTarget.XRGeneralSettingsForBuildTarget(target);
        var manager = general.Manager;
        bool changed = false;

        if (!general.InitManagerOnStart)
        {
            general.InitManagerOnStart = true;
            EditorUtility.SetDirty(general);
            changed = true;
        }

        if (!manager.activeLoaders.Any(loader => loader is OpenXRLoader))
        {
            XRPackageMetadataStore.AssignLoader(manager, typeof(OpenXRLoader).FullName, target);
            changed = true;
        }

        FeatureHelpers.RefreshFeatures(target);
        var openXR = OpenXRSettings.GetSettingsForBuildTargetGroup(target);
        if (openXR != null)
        {
            changed |= EnableFeature(openXR.GetFeature<OculusTouchControllerProfile>());
            changed |= EnableFeature(openXR.GetFeature<MetaQuestTouchPlusControllerProfile>());
        }

        if (changed)
        {
            AssetDatabase.SaveAssets();
            Debug.Log("Workshop setup: OpenXR enabled for PC with Oculus Touch + Meta Quest Touch Plus controller profiles.");
        }
    }

    static bool EnableFeature(UnityEngine.XR.OpenXR.Features.OpenXRFeature feature)
    {
        if (feature == null || feature.enabled)
            return false;
        feature.enabled = true;
        EditorUtility.SetDirty(feature);
        return true;
    }

    static void CreateWorkshopSceneIfMissing()
    {
        if (File.Exists(k_ScenePath))
            return;

        var rigPrefab = FindPrefab(k_RigPrefabName);
        if (rigPrefab == null)
            return;

        if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
            return;

        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        var rig = (GameObject)PrefabUtility.InstantiatePrefab(rigPrefab, scene);
        rig.transform.position = Vector3.zero;
        var simulatorPrefab = FindPrefab(k_SimulatorPrefabName);
        if (simulatorPrefab != null)
            PrefabUtility.InstantiatePrefab(simulatorPrefab, scene);

        var sun = new GameObject("Moonlight").AddComponent<Light>();
        sun.type = LightType.Directional;
        sun.color = new Color(0.65f, 0.72f, 1f);
        sun.intensity = 0.35f;
        sun.shadows = LightShadows.Soft;
        sun.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

        var lamp = new GameObject("Desk Lamp Light").AddComponent<Light>();
        lamp.type = LightType.Point;
        lamp.color = new Color(1f, 0.78f, 0.5f);
        lamp.intensity = 3f;
        lamp.range = 4f;
        lamp.shadows = LightShadows.None;
        lamp.transform.position = new Vector3(0.4f, 1.6f, 0.9f);

        RenderSettings.ambientMode = AmbientMode.Trilight;
        RenderSettings.ambientSkyColor = new Color(0.22f, 0.2f, 0.25f);
        RenderSettings.ambientEquatorColor = new Color(0.18f, 0.14f, 0.12f);
        RenderSettings.ambientGroundColor = new Color(0.08f, 0.06f, 0.05f);

        var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>("Assets/Settings/SampleSceneProfile.asset");
        if (profile != null)
        {
            var volume = new GameObject("Global Volume").AddComponent<Volume>();
            volume.isGlobal = true;
            volume.sharedProfile = profile;
        }

        var placeholders = new GameObject("Placeholders");
        var floorMaterial = GetMaterial("Placeholder_Floor", new Color(0.32f, 0.22f, 0.15f));
        var woodMaterial = GetMaterial("Placeholder_Wood", new Color(0.55f, 0.36f, 0.2f));

        var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Floor";
        floor.transform.SetParent(placeholders.transform);
        floor.transform.localScale = new Vector3(0.8f, 1f, 0.8f);
        floor.GetComponent<Renderer>().sharedMaterial = floorMaterial;
        floor.isStatic = true;

        var bench = new GameObject("Workbench (placeholder)");
        bench.transform.SetParent(placeholders.transform);
        bench.transform.position = new Vector3(0f, 0f, 0.75f);
        Box(bench, "Top", new Vector3(0f, 0.87f, 0f), new Vector3(1.6f, 0.06f, 0.8f), woodMaterial);
        foreach (var x in new[] { -0.72f, 0.72f })
        foreach (var z in new[] { -0.32f, 0.32f })
            Box(bench, "Leg", new Vector3(x, 0.42f, z), new Vector3(0.08f, 0.84f, 0.08f), woodMaterial);

        EditorSceneManager.SaveScene(scene, k_ScenePath);

        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(k_ScenePath, true) };
        Debug.Log("Workshop setup: created Assets/Scenes/Workshop.unity — press Play to test.");
    }

    static void Box(GameObject parent, string name, Vector3 localPosition, Vector3 size, Material material)
    {
        var box = GameObject.CreatePrimitive(PrimitiveType.Cube);
        box.name = name;
        box.transform.SetParent(parent.transform, false);
        box.transform.localPosition = localPosition;
        box.transform.localScale = size;
        box.GetComponent<Renderer>().sharedMaterial = material;
        box.isStatic = true;
    }

    static GameObject FindPrefab(string name)
    {
        if (!AssetDatabase.IsValidFolder("Assets/Samples"))
            return null;

        return AssetDatabase.FindAssets("t:Prefab", new[] { "Assets/Samples" })
            .Select(AssetDatabase.GUIDToAssetPath)
            .Where(path => Path.GetFileNameWithoutExtension(path) == name)
            .Select(AssetDatabase.LoadAssetAtPath<GameObject>)
            .FirstOrDefault();
    }

    static Material GetMaterial(string name, Color color)
    {
        var path = $"Assets/Materials/{name}.mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material == null)
        {
            material = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            material.SetColor("_BaseColor", color);
            AssetDatabase.CreateAsset(material, path);
        }
        return material;
    }
}
