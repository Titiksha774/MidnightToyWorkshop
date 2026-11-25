using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;

[InitializeOnLoad]
public static class WorkshopV2Layout
{
    const string k_ScenePath = "Assets/Scenes/Workshop.unity";
    const string k_LayoutPath = "Assets/Art/workshop_layout.json";
    const string k_AnimFolder = "Assets/Art/Animation";
    const string k_RootName = "Workshop V2";

    [Serializable] class AssetEntry { public string asset, fbx; public float[] position; public float yaw; }
    [Serializable] class LightEntry { public string name, type; public float[] position, rotation, color; public float intensity, range; }
    [Serializable] class RoomEntry { public float width, depth, height, wall, doorX; }
    [Serializable] class Layout { public RoomEntry room; public AssetEntry[] assets; public LightEntry[] lights; }

    static double s_GiveUpTime;
    static RoomEntry s_Room;

    static bool KeepWaiting()
    {
        if (s_GiveUpTime == 0)
            s_GiveUpTime = EditorApplication.timeSinceStartup + 180;
        return EditorApplication.timeSinceStartup < s_GiveUpTime;
    }

    static WorkshopV2Layout()
    {
        EditorApplication.delayCall += AutoBuildOnce;
    }

    class LayoutWatcher : AssetPostprocessor
    {
        static void OnPostprocessAllAssets(string[] imported, string[] deleted, string[] moved, string[] movedFrom)
        {
            if (imported.Any(p => p == k_LayoutPath || (p.StartsWith("Assets/Art/") && p.EndsWith(".fbx"))))
            {
                s_GiveUpTime = 0;
                EditorApplication.delayCall -= AutoBuildOnce;
                EditorApplication.delayCall += AutoBuildOnce;
            }
        }
    }

    static void AutoBuildOnce()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode || !File.Exists(k_LayoutPath))
            return;
        if (EditorSceneManager.GetActiveScene().path != k_ScenePath)
            return;
        var layout = JsonUtility.FromJson<Layout>(File.ReadAllText(k_LayoutPath));
        var inScene = new HashSet<string>(UnityEngine.Object.FindObjectsByType<Transform>(FindObjectsInactive.Include,
            FindObjectsSortMode.None).Select(t => t.name));
        bool built = GameObject.Find(k_RootName) != null && layout.assets.All(a => inScene.Contains(a.asset));
        var game = UnityEngine.Object.FindAnyObjectByType<GameFlow>();
        bool gameReady = game != null && game.tasks != null && game.tasks.Length > 0 &&
                         EditorPrefs.GetInt(WorkshopGameSetup.VersionKey, 0) == WorkshopGameSetup.Version;
        if (built && gameReady)
            return;

        if (!Ready(layout))
        {
            if (KeepWaiting())
                EditorApplication.delayCall += AutoBuildOnce;
            return;
        }
        Build();
    }

    static bool Ready(Layout layout)
    {
        if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            return false;
        if (AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/Materials/Wood_Oak.mat") == null ||
            AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/Materials/Felt_Green.mat") == null)
            return false;
        foreach (var entry in layout.assets)
        {
            var importer = AssetImporter.GetAtPath(entry.fbx) as ModelImporter;
            if (importer == null || AssetDatabase.LoadAssetAtPath<GameObject>(entry.fbx) == null)
                return false;
            if (importer.importAnimation && Clips(entry.fbx).Length == 0)
                return false;
        }
        return true;
    }

    [MenuItem("Workshop/Build Workshop From Blender Art")]
    public static void Build()
    {
        var layout = JsonUtility.FromJson<Layout>(File.ReadAllText(k_LayoutPath));
        var scene = EditorSceneManager.GetActiveScene();
        if (scene.path != k_ScenePath)
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
                return;
            scene = EditorSceneManager.OpenScene(k_ScenePath);
        }

        foreach (var path in new[] { k_RootName, "Workshop/Room", "Workshop/Workbench", "Workshop/Tools/DeskLamp",
                                     "Workshop/Toymaker", "Desk Lamp Light", "Moonlight",
                                     "Workshop/Tools/Turntable/Turntable_Plate/SteamTrain" })
        {
            var old = GameObject.Find(path);
            if (old != null)
                UnityEngine.Object.DestroyImmediate(old);
        }

        var root = new GameObject(k_RootName);
        s_Room = layout.room;
        var (correction, mirror) = MeasureImportCorrection();
        foreach (var entry in layout.assets)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(entry.fbx);
            if (prefab == null)
            {
                Debug.LogWarning($"Phase 1 layout: missing {entry.fbx}");
                continue;
            }
            var pivot = new GameObject(entry.asset);
            pivot.transform.SetParent(root.transform);
            pivot.transform.SetPositionAndRotation(V(entry.position), Quaternion.Euler(0f, entry.yaw, 0f));
            var instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            instance.transform.SetParent(pivot.transform, false);
            instance.transform.localRotation = correction;
            instance.transform.localScale = mirror;
            Configure(entry.asset, pivot, instance, entry.fbx);
        }

        var lights = new GameObject("Night Lights");
        lights.transform.SetParent(root.transform);
        foreach (var l in layout.lights)
        {
            var go = new GameObject(l.name);
            go.transform.SetParent(lights.transform);
            go.transform.position = V(l.position);
            var light = go.AddComponent<Light>();
            light.color = new Color(l.color[0], l.color[1], l.color[2]);
            light.intensity = l.intensity;
            if (l.type == "Directional")
            {
                light.type = LightType.Directional;
                go.transform.rotation = Quaternion.Euler(l.rotation[0], l.rotation[1], l.rotation[2]);
                light.shadows = LightShadows.Soft;
            }
            else
            {
                light.type = LightType.Point;
                light.range = l.range;
                light.shadows = LightShadows.None;
                if (l.name.Contains("Fire") || l.name.Contains("Candle"))
                    go.AddComponent<FireFlicker>().amount = l.name.Contains("Fire") ? 0.35f : 0.15f;
            }
        }

        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
        RenderSettings.ambientSkyColor = new Color(0.10f, 0.11f, 0.17f);
        RenderSettings.ambientEquatorColor = new Color(0.08f, 0.07f, 0.07f);
        RenderSettings.ambientGroundColor = new Color(0.03f, 0.025f, 0.02f);

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        Selection.activeGameObject = root;
        Debug.Log($"Workshop layout: built {layout.assets.Length} Blender assets (furniture, toys, chalkboard).");
        WorkshopGameSetup.Apply();
        SceneCapture.Capture();
    }

    static (Quaternion rotation, Vector3 mirror) MeasureImportCorrection()
    {
        var room = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Art/Environment/WorkshopRoom.fbx");
        var probe = (GameObject)UnityEngine.Object.Instantiate(room);
        try
        {
            Vector3 Local(string name)
            {
                var r = probe.GetComponentsInChildren<Renderer>().FirstOrDefault(x => x.name.StartsWith(name));
                return r == null ? Vector3.zero : probe.transform.InverseTransformPoint(r.bounds.center);
            }
            Vector3 window = Local("Window_Glass"), door = Local("Door_Planks");
            float wallLine = s_Room.depth / 2f + s_Room.wall / 2f;
            Vector3 wantWindow = new Vector3(0f, 1.85f, wallLine), wantDoor = new Vector3(-s_Room.doorX, 0.99f, -(wallLine - 0.02f));

            var mirror = Vector3.one;
            var rotation = Solve(window, door, wantWindow, wantDoor);
            if ((rotation * door - wantDoor).magnitude > 0.2f)
            {
                mirror = new Vector3(-1f, 1f, 1f);
                rotation = Solve(Vector3.Scale(window, mirror), Vector3.Scale(door, mirror), wantWindow, wantDoor);
            }
            Debug.Log($"Phase 1 layout: imported room probe — window {window}, door {door}; correction {rotation.eulerAngles}, mirror {mirror}.");
            return (rotation, mirror);
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(probe);
        }
    }

    static Quaternion Solve(Vector3 a1, Vector3 a2, Vector3 b1, Vector3 b2) =>
        Quaternion.LookRotation(b1, b2) * Quaternion.Inverse(Quaternion.LookRotation(a1, a2));

    static Vector3 V(float[] p) => new Vector3(p[0], p[1], p[2]);

    static void Configure(string asset, GameObject pivot, GameObject instance, string fbx)
    {
        switch (asset)
        {
            case "WorkshopRoom":
                SetStatic(pivot);
                float w = s_Room.width, d = s_Room.depth, h = s_Room.height;
                Box(pivot, new Vector3(0f, -0.05f, 0f), new Vector3(w + 0.4f, 0.1f, d + 0.4f));
                Box(pivot, new Vector3(-w / 2f - 0.1f, h / 2f, 0f), new Vector3(0.2f, h, d + 0.4f));
                Box(pivot, new Vector3(w / 2f + 0.1f, h / 2f, 0f), new Vector3(0.2f, h, d + 0.4f));
                Box(pivot, new Vector3(0f, h / 2f, d / 2f + 0.1f), new Vector3(w + 0.4f, h, 0.2f));
                Box(pivot, new Vector3(0f, h / 2f, -d / 2f - 0.1f), new Vector3(w + 0.4f, h, 0.2f));
                break;
            case "Workbench":
                Box(pivot, new Vector3(0f, 0.865f, 0f), new Vector3(1.8f, 0.07f, 0.8f));
                Box(pivot, new Vector3(0f, 0.42f, 0f), new Vector3(1.7f, 0.84f, 0.7f));
                Animate(instance, fbx, "Workbench", "Close", ("Open", false));
                break;
            case "Fireplace":
                Box(pivot, new Vector3(0f, 1.4f, 0.2f), new Vector3(1.32f, 2.8f, 0.4f));
                Box(pivot, new Vector3(0f, 1.33f, 0.36f), new Vector3(1.5f, 0.06f, 0.42f));
                Box(pivot, new Vector3(0f, 0.03f, 0.31f), new Vector3(1.5f, 0.06f, 0.62f));
                Animate(instance, fbx, "Fireplace", "Flicker");
                break;
            case "Armchair":
                SetStatic(pivot);
                Box(pivot, new Vector3(0f, 0.25f, 0f), new Vector3(0.82f, 0.5f, 0.78f));
                Box(pivot, new Vector3(0f, 0.7f, -0.3f), new Vector3(0.78f, 0.45f, 0.2f));
                break;
            case "CuckooClock":
                FitBox(pivot);
                Animate(instance, fbx, "CuckooClock", "Tick", ("Cuckoo", true));
                var hands = pivot.AddComponent<ClockHands>();
                hands.hourHand = Find(instance.transform, "Hour");
                hands.minuteHand = Find(instance.transform, "Minute");
                hands.time = 23f;
                hands.faceNormal = Vector3.forward;
                break;
            case "DeskLamp":
                SetStatic(pivot);
                Box(pivot, new Vector3(0f, 0.02f, 0f), new Vector3(0.2f, 0.04f, 0.2f));
                break;
            case "Toymaker":
                FitBox(pivot);
                Animate(instance, fbx, "Toymaker", "Idle", ("Talk", true), ("Wave", true), ("Point", true), ("Celebrate", true));
                break;

            case "ToyTown":
                Box(pivot, new Vector3(0f, 0.7525f, 0f), new Vector3(1.3f, 0.025f, 0.9f));
                Box(pivot, new Vector3(0f, 0.35f, 0f), new Vector3(1.22f, 0.7f, 0.82f));
                Animate(instance, fbx, "ToyTown", "Spin", ("Signal", true));
                break;
            case "SteamTrain":
                FitBox(pivot);
                Animate(instance, fbx, "SteamTrain", "Drive", ("Whistle", true), ("Idle", false));
                var runner = pivot.AddComponent<TrackRunner>();
                runner.track = pivot.transform.parent.Find("ToyTown");
                break;
            case "MusicBox":
                FitBox(pivot);
                Animate(instance, fbx, "MusicBox", "Play", ("Open", false), ("Close", false));
                break;
            case "JackInTheBox":
                FitBox(pivot);
                Animate(instance, fbx, "JackInTheBox", "Idle", ("Pop", true), ("Crank", false));
                break;
            case "ToySoldier":
                FitBox(pivot);
                Animate(instance, fbx, "ToySoldier", "Idle", ("March", false), ("Salute", true), ("Fall", false));
                break;
            case "Chalkboard":
                FitBox(pivot);
                Animate(instance, fbx, "Chalkboard", "Still", ("Wobble", true));
                break;
            case "WindUpMouse":
                FitBox(pivot);
                Animate(instance, fbx, "WindUpMouse", "Sniff", ("Scurry", false));
                break;
            default:
                SetStatic(pivot);
                FitBox(pivot);
                break;
        }
    }

    static void Animate(GameObject instance, string fbx, string name, string defaultState, params (string clip, bool returns)[] triggered)
    {
        Directory.CreateDirectory(k_AnimFolder);
        var path = $"{k_AnimFolder}/{name}.controller";
        AssetDatabase.DeleteAsset(path);
        var controller = AnimatorController.CreateAnimatorControllerAtPath(path);
        var machine = controller.layers[0].stateMachine;
        var clips = Clips(fbx);

        var home = machine.AddState(defaultState);
        home.motion = clips.FirstOrDefault(c => c.name == defaultState);
        machine.defaultState = home;

        foreach (var (clipName, returns) in triggered)
        {
            controller.AddParameter(clipName, AnimatorControllerParameterType.Trigger);
            var state = machine.AddState(clipName);
            state.motion = clips.FirstOrDefault(c => c.name == clipName);
            var to = machine.AddAnyStateTransition(state);
            to.AddCondition(AnimatorConditionMode.If, 0f, clipName);
            to.duration = 0.15f;
            to.canTransitionToSelf = false;
            if (returns)
            {
                var back = state.AddTransition(home);
                back.hasExitTime = true;
                back.exitTime = 0.95f;
                back.duration = 0.2f;
            }
        }

        var animator = instance.GetComponent<Animator>();
        if (animator == null)
            animator = instance.AddComponent<Animator>();
        animator.runtimeAnimatorController = controller;
        animator.applyRootMotion = false;
    }

    static AnimationClip[] Clips(string fbx) =>
        AssetDatabase.LoadAllAssetsAtPath(fbx).OfType<AnimationClip>().Where(c => !c.name.StartsWith("__preview__")).ToArray();

    static Transform Find(Transform root, string name) =>
        root.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name);

    static void SetStatic(GameObject go)
    {
        foreach (var t in go.GetComponentsInChildren<Transform>(true))
            t.gameObject.isStatic = true;
    }

    static void Box(GameObject go, Vector3 center, Vector3 size)
    {
        var box = go.AddComponent<BoxCollider>();
        box.center = center;
        box.size = size;
    }

    static void FitBox(GameObject go)
    {
        var renderers = go.GetComponentsInChildren<Renderer>();
        if (renderers.Length == 0)
            return;
        var toLocal = go.transform.worldToLocalMatrix;
        var bounds = new Bounds(toLocal.MultiplyPoint3x4(renderers[0].bounds.center), Vector3.zero);
        foreach (var r in renderers)
        {
            var b = r.bounds;
            for (int i = 0; i < 8; i++)
            {
                var corner = b.center + Vector3.Scale(b.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
                bounds.Encapsulate(toLocal.MultiplyPoint3x4(corner));
            }
        }
        Box(go, bounds.center, bounds.size);
    }
}
