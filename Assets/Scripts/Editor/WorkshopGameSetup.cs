using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using TMPro;
using Unity.AI.Navigation;
using Unity.InferenceEngine;
using Unity.XR.CoreUtils;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.AI;
using UnityEngine.EventSystems;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.XR.Interaction.Toolkit;
using UnityEngine.XR.Interaction.Toolkit.Interactables;
using UnityEngine.XR.Interaction.Toolkit.Locomotion.Teleportation;
using UnityEngine.XR.Interaction.Toolkit.UI;
using static GameUIBuilder;

public static class WorkshopGameSetup
{
    public const int Version = 12;
    public const string VersionKey = "MidnightToyWorkshop.GameSetupVersion";

    const string k_GameRoot = "Workshop Game";
    const string k_AnimFolder = "Assets/Art/Animation";
    const string k_MaterialFolder = "Assets/Art/Materials";
    const string k_NavMeshPath = "Assets/Scenes/Workshop_NavMesh.asset";
    const float k_TrayFloor = 0.908f;

    const float k_BoardCentreHeight = 1.3f, k_BoardFaceDepth = 0.11f, k_BoardTilt = 12f;

    class SceneRefs
    {
        public GameObject workshopV2, game, looseParts;
        public XROrigin origin;
        public Camera camera;
        public Transform head;
        public GestureRecognizer gestures;
        public InteractionLogger logger;
        public Sounds sounds;
        public Transform Pivot(string name) => workshopV2.transform.Find(name);
        public static Transform Instance(Transform pivot) => pivot.GetChild(0);
    }

    public static void Apply()
    {
        var s = new SceneRefs
        {
            workshopV2 = GameObject.Find("Workshop V2"),
            origin = Object.FindAnyObjectByType<XROrigin>(),
        };
        var plate = GameObject.Find("Workshop/Tools/Turntable/Turntable_Plate");
        var tray = GameObject.Find("Workshop/Tools/PartsTray");
        if (s.workshopV2 == null || s.origin == null || plate == null || tray == null)
        {
            Debug.LogError("Game setup: build the workshop first (Workshop > Build Workshop From Blender Art).");
            return;
        }

        foreach (var path in new[] { k_GameRoot, "Workshop/Toys", "Workshop/Toy Town", "EventSystem", "Navigation" })
        {
            var old = GameObject.Find(path);
            if (old != null)
                Object.DestroyImmediate(old);
        }
        foreach (Transform child in plate.transform.Cast<Transform>().ToArray())
        {
            if (child.name == "ToyTrain")
                Object.DestroyImmediate(child.gameObject);
        }

        s.camera = s.origin.Camera;
        s.head = s.camera.transform;
        s.game = new GameObject(k_GameRoot);
        try
        {
            Build(s, plate.transform, tray.transform);
        }
        catch
        {
            Object.DestroyImmediate(s.game);
            throw;
        }
        EditorSceneManager.MarkSceneDirty(s.game.scene);
        EditorSceneManager.SaveScene(s.game.scene);
        EditorPrefs.SetInt(VersionKey, Version);
        Debug.Log("Game setup: done. Press Play: start menu → five repairs → midnight finale.");
    }

    static void Build(SceneRefs s, Transform plate, Transform tray)
    {
        s.looseParts = new GameObject("Loose Parts");
        s.looseParts.transform.SetParent(s.game.transform);

        s.gestures = s.game.AddComponent<GestureRecognizer>();
        s.gestures.modelAsset = AssetDatabase.LoadAssetAtPath<ModelAsset>("Assets/ML/GestureClassifier.onnx");
        s.gestures.head = s.head;
        s.gestures.controller = s.origin.GetComponentsInChildren<Transform>(true).First(t => t.name == "Right Controller");
        s.logger = s.game.AddComponent<InteractionLogger>();
        s.logger.gestureRecognizer = s.gestures;
        if (s.camera.GetComponent<GazePointer>() == null)
            s.camera.gameObject.AddComponent<GazePointer>();
        CreateEventSystem();
        s.sounds = CreateSounds(s.game);
        AddLoop(s.game, "Music", 0.12f, playNow: true, spatial: false);
        AddLoop(s.Pivot("Fireplace").gameObject, "Fire", 0.45f, playNow: true);
        CreateEmbers(s.Pivot("Fireplace"));
        SetUpPostProcessing(s.camera);
        SetUpPlayerBounds(s);

        var flow = s.game.AddComponent<GameFlow>();
        flow.gestures = s.gestures;
        flow.logger = s.logger;
        flow.head = s.head;
        flow.clock = s.Pivot("CuckooClock").GetComponent<ClockHands>();
        flow.cuckooClock = SceneRefs.Instance(s.Pivot("CuckooClock")).GetComponent<Animator>();
        flow.finaleLights = new[] { "Fire Light", "Toy Town Light", "Desk Lamp Light" }
            .Select(n => s.workshopV2.transform.Find("Night Lights/" + n)?.GetComponent<Light>()).Where(l => l != null).ToArray();
        flow.confetti = CreateConfetti(s.game.transform);
        flow.sparkles = CreateSparkles(s.game.transform);
        flow.beacon = CreateBeacon(s);
        flow.chalkboard = CreateChalkboard(s);
        flow.toymaker = CreateToymaker(s, flow);
        flow.menus = CreateMenus(s, flow);

        var tasks = new GameObject("Tasks").transform;
        tasks.SetParent(s.game.transform);
        flow.tasks = new WorkshopTask[]
        {
            SetUpTrain(s, tasks, plate, tray),
            SetUpMusicBox(s, tasks),
            SetUpJackInTheBox(s, tasks),
            SetUpMouse(s),
            SetUpSoldier(s),
        };

        foreach (var button in s.game.GetComponentsInChildren<UnityEngine.UI.Button>(true))
            UnityEditor.Events.UnityEventTools.AddPersistentListener(button.onClick, s.sounds.PlayClick);
        BakeNavMesh(s);
    }

    static T NewTask<T>(Transform parent, string name, string title, string intro, string hint, string howItWorks,
        float clockTime) where T : WorkshopTask
    {
        var task = new GameObject(name).AddComponent<T>();
        task.transform.SetParent(parent);
        task.title = title;
        task.introLine = intro;
        task.hint = hint;
        task.howItWorks = howItWorks;
        task.clockTime = clockTime;
        return task;
    }

    static TrainTask SetUpTrain(SceneRefs s, Transform tasks, Transform plate, Transform tray)
    {
        var pivot = s.Pivot("SteamTrain");
        var instance = SceneRefs.Instance(pivot);
        Unpack(instance);
        var task = NewTask<TrainTask>(tasks, "1 Steam Train", "Fix the steam train",
            "First, the steam train! Its wheels, chimney, cowcatcher and key are in the tray. Fit them back on.",
            "The loose parts are in the tray on the left of the workbench. Fit each one where it belongs on the train " +
            "(a see-through outline shows the spot). When all five are on, circle your hand three times to wind the key.",
            "Winding the key tightens a coiled spring. As the spring unwinds it turns gears that drive the wheels, and the " +
            "coupling rods link the wheels so they all turn together, while the pistons slide in and out.",
            23.2f);

        var stand = plate.parent;
        stand.position = new Vector3(0.42f, stand.position.y, 0.68f);
        tray.position = new Vector3(-0.42f, tray.position.y, 0.68f);
        var plateBounds = plate.GetComponent<Renderer>().bounds;
        pivot.SetParent(plate, true);
        pivot.SetPositionAndRotation(new Vector3(plateBounds.center.x, plateBounds.max.y, plateBounds.center.z),
            Quaternion.Euler(0f, 90f, 0f));

        var runner = pivot.GetComponent<TrackRunner>();
        runner.enabled = false;
        task.runner = runner;
        task.trackParent = s.workshopV2.transform;
        task.windTarget = pivot;
        task.beaconTarget = tray;
        task.animator = instance.GetComponent<Animator>();
        new ControllerBuilder("SteamTrain", ToyFbx("SteamTrain"))
            .State("Stopped", isDefault: true).State("Drive").State("Whistle")
            .Trigger("Drive", "Drive").Trigger("Whistle", "Whistle").Then("Whistle", "Drive")
            .Assign(task.animator);

        var specs = new (string id, string label, string bone, string[] meshes, Vector2 offset, float yaw)[]
        {
            ("train_front_wheels", "Front wheels", "Axle_1",
                new[] { "Wheel1", "Wheel1_Tyre", "Wheel1_Hub", "Wheel1_CrankPin", "Wheel1_Spokes" }, new Vector2(-0.1f, -0.06f), 0f),
            ("train_back_wheels", "Back wheels", "Axle_3",
                new[] { "Wheel3", "Wheel3_Tyre", "Wheel3_Hub", "Wheel3_CrankPin", "Wheel3_Spokes" }, new Vector2(0.1f, -0.06f), 0f),
            ("train_chimney", "Chimney", "Body", new[] { "Chimney", "Chimney_Rim" }, new Vector2(-0.14f, 0.06f), 0f),
            ("train_cowcatcher", "Cowcatcher", "Body",
                new[] { "BufferBeam_Front", "Buffers_Front", "BufferHeads_Front", "Cowcatcher_Bars", "Cowcatcher_Rail" },
                new Vector2(0f, 0.06f), 0f),
            ("train_key", "Wind-up key", "Key", new[] { "Key_Shaft", "Key_Lobes" }, new Vector2(0.14f, 0.06f), 30f),
        };
        var sockets = new List<PartSocket>();
        foreach (var spec in specs)
        {
            var (part, socket) = MakeLoosePart(s, instance, spec.id, spec.label, spec.bone, spec.meshes, pivot.rotation);
            var spot = tray.position + new Vector3(spec.offset.x, 0f, spec.offset.y);
            PlaceOnFloor(part.transform, new Vector3(spot.x, k_TrayFloor, spot.z), spec.yaw);
            sockets.Add(socket);
        }

        task.chug = AddLoop(pivot.gameObject, "TrainChug", 0.45f, playNow: false);
        task.repair = task.gameObject.AddComponent<ToyRepair>();
        task.repair.toyName = "Steam train";
        task.repair.sockets = sockets.ToArray();
        task.repair.logger = s.logger;
        return task;
    }

    static MusicBoxTask SetUpMusicBox(SceneRefs s, Transform tasks)
    {
        var pivot = s.Pivot("MusicBox");
        var instance = SceneRefs.Instance(pivot);
        Unpack(instance);
        var task = NewTask<MusicBoxTask>(tasks, "2 Music Box", "Mend the music box",
            "The music box on the mantelpiece has lost its crank. I left it on the workbench. Can you take it over?",
            "The little brass crank is lying on the front of the workbench. Take it to the music box on the mantelpiece, " +
            "fit it into the side of the box, then circle your hand three times to wind it.",
            "Turning the crank winds a spring that slowly spins a brass drum. Tiny pins on the drum pluck the steel teeth " +
            "of a comb, and each tooth rings at its own note, so the pins play the tune.",
            23.4f);
        task.windTarget = pivot;
        task.windRange = 1.8f;
        task.animator = instance.GetComponent<Animator>();
        new ControllerBuilder("MusicBox", ToyFbx("MusicBox"))
            .State("Closed", isDefault: true).State("Open").State("Play")
            .Trigger("Open", "Open").Then("Open", "Play")
            .Assign(task.animator);
        task.tune = AddLoop(pivot.gameObject, "MusicBoxTune", 0.7f, playNow: false);

        var (crank, socket) = MakeLoosePart(s, instance, "music_crank", "Music box crank", "Crank",
            new[] { "Crank_Shaft", "Crank_Arm", "Crank_Knob" }, pivot.rotation, 0.15f);
        crank.transform.rotation = Quaternion.identity;
        PlaceOnFloor(crank.transform, new Vector3(0f, k_TrayFloor - 0.008f, 0.55f), 90f);
        crank.Grab.enabled = false;
        task.crank = crank;
        task.crankSocket = socket;
        task.beaconTarget = crank.transform;
        return task;
    }

    static JackInTheBoxTask SetUpJackInTheBox(SceneRefs s, Transform tasks)
    {
        var pivot = s.Pivot("JackInTheBox");
        var instance = SceneRefs.Instance(pivot);
        Unpack(instance);
        var task = NewTask<JackInTheBoxTask>(tasks, "3 Jack-in-the-box", "Fix the jack-in-the-box",
            "Oh dear, the jack-in-the-box has lost his hat, his lid and his crank! They're scattered round the workshop. " +
            "Follow the star.",
            "His jester hat is on the armchair, the crank is on the corner of the toy-town table and the lid is on the " +
            "fireplace hearth. Fit them onto the jack-in-the-box on the shelf, then circle your hand three times to wind it.",
            "The crank turns a little music wheel. When the tune reaches its end, a cam lifts the catch on the lid, and the " +
            "squashed spring pushes the jester up and out.",
            23.6f);
        task.windTarget = pivot;
        task.windRange = 1.8f;
        task.animator = instance.GetComponent<Animator>();
        new ControllerBuilder("JackInTheBox", ToyFbx("JackInTheBox"))
            .State("Idle", isDefault: true).State("Crank", speed: 0f).State("Pop")
            .Trigger("Pop", "Pop").Then("Pop", "Idle")
            .Assign(task.animator);

        var armchair = s.Pivot("Armchair");
        var town = s.Pivot("ToyTown");
        var fireplace = s.Pivot("Fireplace");
        var specs = new (string id, string label, string bone, string[] meshes, Vector3 spot, float yaw)[]
        {
            ("jack_crank", "Jack-in-the-box crank", "Crank", new[] { "Crank_Hub", "Crank_Shaft", "Crank_Arm", "Crank_Handle" },
                town.TransformPoint(new Vector3(0.42f, 0.765f, 0.36f)), 30f),
            ("jack_hat", "Jester hat", "Head", new[] { "Hat_Cap", "Hat_Horns", "Hat_Bells" },
                armchair.TransformPoint(new Vector3(0f, 0.515f, 0.05f)), -40f),
            ("jack_lid", "Jack-in-the-box lid", "Lid", new[] { "Lid", "Lid_Knob" },
                fireplace.TransformPoint(new Vector3(0.45f, 0.06f, 0.42f)), 20f),
        };
        var parts = new List<ToyPart>();
        var sockets = new List<PartSocket>();
        foreach (var spec in specs)
        {
            float snap = spec.id == "jack_lid" ? 0.08f : 0.15f;
            var (part, socket) = MakeLoosePart(s, instance, spec.id, spec.label, spec.bone, spec.meshes, pivot.rotation, snap);
            Unpose(part.transform, instance);
            PlaceOnFloor(part.transform, spec.spot, spec.yaw);
            parts.Add(part);
            sockets.Add(socket);
        }
        task.parts = parts.ToArray();
        task.beaconTarget = parts[0].transform;
        task.repair = task.gameObject.AddComponent<ToyRepair>();
        task.repair.toyName = "Jack-in-the-box";
        task.repair.sockets = sockets.ToArray();
        task.repair.logger = s.logger;
        return task;
    }

    // turn a loose part back to how it looked in Blender before the bone posed it (so the lid lies flat)
    static void Unpose(Transform part, Transform instance)
    {
        var mesh = part.GetComponentInChildren<MeshRenderer>().transform;
        part.rotation = instance.rotation * Quaternion.Inverse(mesh.rotation) * part.rotation;
    }

    static MouseTask SetUpMouse(SceneRefs s)
    {
        var pivot = s.Pivot("WindUpMouse");
        var instance = SceneRefs.Instance(pivot);
        var task = pivot.gameObject.AddComponent<MouseTask>();
        task.title = "Catch the clockwork mouse";
        task.introLine = "Oh dear, the noise woke the clockwork mouse! Catch him before he hides under the armchair!";
        task.hint = "He runs off when you get close, but he stops to sniff every now and then. Grab him with the grip " +
                    "button, close up or from a distance with the ray.";
        task.howItWorks = "A small spring drives the mouse's wheels through gears. One wheel is set at a slight angle, so " +
                          "instead of going straight he scurries about in curves.";
        task.clockTime = 23.75f;
        task.beaconTarget = pivot;
        task.animator = instance.GetComponent<Animator>();
        new ControllerBuilder("WindUpMouse", ToyFbx("WindUpMouse"))
            .State("Sniff", isDefault: true).State("Scurry")
            .Bool("Running", "Sniff", "Scurry")
            .Assign(task.animator);

        task.agent = AddAgent(pivot.gameObject, radius: 0.045f, height: 0.06f, speed: 0.55f, acceleration: 4f, turnSpeed: 720f);
        var body = pivot.gameObject.AddComponent<Rigidbody>();
        body.isKinematic = true;
        body.interpolation = RigidbodyInterpolation.Interpolate;
        var grab = pivot.gameObject.AddComponent<XRGrabInteractable>();
        grab.movementType = XRBaseInteractable.MovementType.Instantaneous;
        grab.useDynamicAttach = true;
        grab.throwOnDetach = false;
        task.grab = grab;
        pivot.gameObject.AddComponent<HoverLabel>().text = "Clockwork mouse";

        var home = new GameObject("Mouse Home").transform;
        home.SetParent(s.game.transform);
        home.position = new Vector3(pivot.position.x, 0f, pivot.position.z);
        task.home = home;
        return task;
    }

    static SoldierTask SetUpSoldier(SceneRefs s)
    {
        var pivot = s.Pivot("ToySoldier");
        var instance = SceneRefs.Instance(pivot);
        var task = pivot.gameObject.AddComponent<SoldierTask>();
        task.title = "Greet the tin soldier";
        task.introLine = "Last one! The tin soldier has started his night patrol. Look at him and give him a friendly wave.";
        task.hint = "Find the soldier marching on the floor, look at him and swipe your hand left or right to wave. Careful: " +
                    "if you push towards him, he'll topple over!";
        task.howItWorks = "His spring turns a little crank that rocks his legs forwards and backwards in turn, so he " +
                          "marches. The same rocking swings his arms, just like a real soldier.";
        task.clockTime = 23.9f;
        task.beaconTarget = pivot;
        task.animator = instance.GetComponent<Animator>();
        new ControllerBuilder("ToySoldier", ToyFbx("ToySoldier"))
            .State("Idle", isDefault: true).State("March").State("Salute").State("Fall").State("GetUp")
            .Bool("Marching", "Idle", "March")
            .Trigger("Salute", "Salute").Then("Salute", "Idle")
            .Trigger("Fall", "Fall").Trigger("GetUp", "GetUp", from: "Fall").Then("GetUp", "Idle")
            .Assign(task.animator);
        pivot.gameObject.AddComponent<HoverLabel>().text = "Tin soldier";

        task.agent = AddAgent(pivot.gameObject, radius: 0.045f, height: 0.21f, speed: 0.12f, acceleration: 1f, turnSpeed: 200f);
        task.marchSound = AddLoop(pivot.gameObject, "MarchLoop", 0.35f, playNow: false);
        var points = new GameObject("Soldier Patrol").transform;
        points.SetParent(s.game.transform);
        task.hopTarget = Point(points, "Landing", new Vector3(1.75f, 0f, -0.75f));
        task.patrol = new[]
        {
            Point(points, "A Toy town", new Vector3(1.75f, 0f, -0.35f)),
            Point(points, "B Door", new Vector3(0.4f, 0f, -1.6f)),
            Point(points, "C Armchair", new Vector3(-1.2f, 0f, -0.9f)),
            Point(points, "D Bench", new Vector3(0.2f, 0f, 0.15f)),
        };
        return task;
    }

    static (ToyPart part, PartSocket socket) MakeLoosePart(SceneRefs s, Transform instance, string id, string label,
        string boneName, string[] meshNames, Quaternion uprightRotation, float snapRadius = 0.08f)
    {
        var meshes = meshNames.Select(n => FindMesh(instance, n)).Where(t => t != null).ToArray();
        if (meshes.Length != meshNames.Length)
            Debug.LogWarning($"Game setup: {label}: some meshes were not found ({string.Join(", ", meshNames)}).");
        var bone = FindBone(instance, boneName);

        var bounds = WorldBounds(meshes);
        var partObject = new GameObject(label);
        partObject.transform.SetPositionAndRotation(bounds.center, uprightRotation);
        foreach (var mesh in meshes)
            mesh.SetParent(partObject.transform, true);

        var socketObject = new GameObject($"Socket {label}");
        socketObject.transform.SetParent(bone, false);
        socketObject.transform.SetPositionAndRotation(partObject.transform.position, partObject.transform.rotation);
        var trigger = socketObject.AddComponent<SphereCollider>();
        trigger.isTrigger = true;
        trigger.radius = Mathf.Max(snapRadius, bounds.extents.magnitude * 1.3f);
        var socket = socketObject.AddComponent<PartSocket>();
        socket.partId = id;
        socket.hoverSocketSnapping = true;
        socket.interactableHoverMeshMaterial = PreviewMaterial("SocketPreview", new Color(1f, 0.92f, 0.7f, 0.4f));
        socket.interactableCantHoverMeshMaterial = PreviewMaterial("SocketPreviewBlocked", new Color(1f, 0.3f, 0.25f, 0.3f));

        partObject.transform.SetParent(s.looseParts.transform, true);
        var box = partObject.AddComponent<BoxCollider>();
        var local = LocalBounds(partObject.transform);
        box.center = local.center;
        box.size = Vector3.Max(local.size + Vector3.one * 0.015f, Vector3.one * 0.04f);
        var body = partObject.AddComponent<Rigidbody>();
        body.mass = 0.1f;
        body.interpolation = RigidbodyInterpolation.Interpolate;
        body.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;
        var grab = partObject.AddComponent<XRGrabInteractable>();
        grab.movementType = XRBaseInteractable.MovementType.Instantaneous;
        grab.useDynamicAttach = true;
        grab.throwOnDetach = true;
        var part = partObject.AddComponent<ToyPart>();
        part.partId = id;
        part.displayName = label;
        partObject.AddComponent<HoverLabel>().text = label;
        return (part, socket);
    }

    static void PlaceOnFloor(Transform part, Vector3 where, float yaw)
    {
        part.rotation = Quaternion.Euler(0f, yaw, 0f) * part.rotation;
        part.position = new Vector3(where.x, part.position.y, where.z);
        var box = part.GetComponent<BoxCollider>();
        float lowest = float.MaxValue;
        for (int i = 0; i < 8; i++)
        {
            var corner = box.center + Vector3.Scale(box.size * 0.5f,
                new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
            lowest = Mathf.Min(lowest, part.TransformPoint(corner).y);
        }
        part.position += Vector3.up * (where.y + 0.001f - lowest);
    }

    class ControllerBuilder
    {
        readonly AnimatorController m_Controller;
        readonly AnimatorStateMachine m_Machine;
        readonly AnimationClip[] m_Clips;
        readonly Dictionary<string, AnimatorState> m_States = new Dictionary<string, AnimatorState>();

        public ControllerBuilder(string name, string fbx)
        {
            Directory.CreateDirectory(k_AnimFolder);
            string path = $"{k_AnimFolder}/{name}.controller";
            AssetDatabase.DeleteAsset(path);
            m_Controller = AnimatorController.CreateAnimatorControllerAtPath(path);
            m_Machine = m_Controller.layers[0].stateMachine;
            m_Clips = AssetDatabase.LoadAllAssetsAtPath(fbx).OfType<AnimationClip>()
                .Where(c => !c.name.StartsWith("__preview__")).ToArray();
        }

        public ControllerBuilder State(string name, bool isDefault = false, float speed = 1f)
        {
            var state = m_Machine.AddState(name);
            state.motion = m_Clips.FirstOrDefault(c => c.name == name);
            if (state.motion == null)
                Debug.LogWarning($"Game setup: no '{name}' clip in {m_Controller.name}.");
            state.speed = speed;
            if (isDefault)
                m_Machine.defaultState = state;
            m_States[name] = state;
            return this;
        }

        public ControllerBuilder Trigger(string parameter, string to, string from = null)
        {
            if (m_Controller.parameters.All(p => p.name != parameter))
                m_Controller.AddParameter(parameter, AnimatorControllerParameterType.Trigger);
            var transition = from == null ? m_Machine.AddAnyStateTransition(m_States[to]) : m_States[from].AddTransition(m_States[to]);
            transition.AddCondition(AnimatorConditionMode.If, 0f, parameter);
            transition.duration = 0.15f;
            transition.hasExitTime = false;
            transition.canTransitionToSelf = false;
            return this;
        }

        public ControllerBuilder Then(string from, string to)
        {
            var transition = m_States[from].AddTransition(m_States[to]);
            transition.hasExitTime = true;
            transition.exitTime = 0.95f;
            transition.duration = 0.2f;
            return this;
        }

        public ControllerBuilder Bool(string parameter, string off, string on)
        {
            m_Controller.AddParameter(parameter, AnimatorControllerParameterType.Bool);
            var go = m_States[off].AddTransition(m_States[on]);
            go.AddCondition(AnimatorConditionMode.If, 0f, parameter);
            go.hasExitTime = false;
            go.duration = 0.15f;
            var back = m_States[on].AddTransition(m_States[off]);
            back.AddCondition(AnimatorConditionMode.IfNot, 0f, parameter);
            back.hasExitTime = false;
            back.duration = 0.2f;
            return this;
        }

        public void Assign(Animator animator)
        {
            animator.runtimeAnimatorController = m_Controller;
            animator.applyRootMotion = false;
        }
    }

    static string ToyFbx(string toy) => $"Assets/Art/Toys/{toy}.fbx";

    static void Unpack(Transform instance)
    {
        if (PrefabUtility.IsPartOfPrefabInstance(instance))
            PrefabUtility.UnpackPrefabInstance(PrefabUtility.GetOutermostPrefabInstanceRoot(instance.gameObject),
                PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
    }

    static NavMeshAgent AddAgent(GameObject go, float radius, float height, float speed, float acceleration, float turnSpeed)
    {
        var agent = go.AddComponent<NavMeshAgent>();
        agent.agentTypeID = 0;
        agent.radius = radius;
        agent.height = height;
        agent.speed = speed;
        agent.acceleration = acceleration;
        agent.angularSpeed = turnSpeed;
        agent.stoppingDistance = 0.05f;
        agent.obstacleAvoidanceType = ObstacleAvoidanceType.LowQualityObstacleAvoidance;
        agent.enabled = false;
        return agent;
    }

    static void BakeNavMesh(SceneRefs s)
    {
        var settings = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/NavMeshAreas.asset")[0]);
        var agentType = settings.FindProperty("m_Settings").GetArrayElementAtIndex(0);
        agentType.FindPropertyRelative("agentRadius").floatValue = 0.05f;
        agentType.FindPropertyRelative("agentHeight").floatValue = 0.22f;
        agentType.FindPropertyRelative("agentClimb").floatValue = 0.02f;
        agentType.FindPropertyRelative("agentSlope").floatValue = 30f;
        settings.ApplyModifiedPropertiesWithoutUndo();

        foreach (var ignored in new[] { s.Pivot("WindUpMouse"), s.Pivot("ToySoldier"), s.origin.transform, s.looseParts.transform,
                     s.game.transform.Find("Teleport Floor") })
        {
            if (!ignored.TryGetComponent<NavMeshModifier>(out var modifier))
                modifier = ignored.gameObject.AddComponent<NavMeshModifier>();
            modifier.ignoreFromBuild = true;
        }

        var navigation = new GameObject("Navigation");
        navigation.transform.SetParent(s.game.transform);
        var surface = navigation.AddComponent<NavMeshSurface>();
        surface.collectObjects = CollectObjects.All;
        surface.useGeometry = NavMeshCollectGeometry.PhysicsColliders;
        surface.overrideVoxelSize = true;
        surface.voxelSize = 0.0167f;
        surface.BuildNavMesh();
        AssetDatabase.DeleteAsset(k_NavMeshPath);
        AssetDatabase.CreateAsset(surface.navMeshData, k_NavMeshPath);
    }

    static void CreateEventSystem()
    {
        foreach (var existing in Object.FindObjectsByType<EventSystem>(FindObjectsSortMode.None))
            Object.DestroyImmediate(existing.gameObject);
        var go = new GameObject("EventSystem", typeof(EventSystem), typeof(XRUIInputModule));
        go.transform.SetSiblingIndex(0);
    }

    static MenuSystem CreateMenus(SceneRefs s, GameFlow flow)
    {
        var root = new GameObject("Menus");
        root.transform.SetParent(s.game.transform);
        var menus = root.AddComponent<MenuSystem>();
        menus.game = flow;
        menus.sounds = s.sounds;

        var canvas = WorldCanvas("Menu Canvas", root.transform, new Vector2(1200f, 900f), s.camera, interactive: true);
        canvas.sortingOrder = 10;
        menus.canvasGroup = canvas.gameObject.AddComponent<CanvasGroup>();
        menus.canvasGroup.alpha = 0f;
        menus.follow = canvas.gameObject.AddComponent<HeadFollow>();
        menus.follow.head = s.head;
        canvas.transform.position = s.head.position + Vector3.forward * 1.4f;
        var c = canvas.transform;
        var button = new Vector2(500f, 92f);

        var start = Panel("Start Panel", c, new Vector2(780f, 750f));
        Image("Star", start, "Star", Gold, new Vector2(0f, 300f), new Vector2(64f, 64f));
        Text("Title", start, "Midnight Toy Workshop", 62f, Walnut, new Vector2(0f, 227f), new Vector2(720f, 80f), style: FontStyles.Bold);
        Text("Subtitle", start, "Repair the toys before the clock strikes twelve", 28f, WalnutSoft, new Vector2(0f, 167f),
            new Vector2(700f, 40f), style: FontStyles.Italic);
        Button("Play", start, "Play", "Icon_Play", Berry, new Vector2(0f, 65f), button, menus.Play);
        Button("Controls", start, "Controls", "Icon_Controls", Wood, new Vector2(0f, -45f), button, menus.ShowControls);
        Button("Credits", start, "Credits", "Star", Wood, new Vector2(0f, -155f), button, menus.ShowCredits);
        Button("Quit", start, "Quit", "Icon_Quit", Wood, new Vector2(0f, -265f), button, menus.Quit);
        menus.startPanel = start.gameObject;

        var pause = Panel("Pause Panel", c, new Vector2(720f, 640f));
        Image("Icon", pause, "Icon_Pause", Walnut, new Vector2(0f, 250f), new Vector2(54f, 54f));
        Text("Title", pause, "Paused", 60f, Walnut, new Vector2(0f, 185f), new Vector2(600f, 80f), style: FontStyles.Bold);
        Button("Resume", pause, "Resume", "Icon_Play", Berry, new Vector2(0f, 80f), button, menus.Resume);
        Button("Restart", pause, "Restart", "Icon_Restart", Wood, new Vector2(0f, -25f), button, menus.Restart);
        Button("Controls", pause, "Controls", "Icon_Controls", Wood, new Vector2(0f, -130f), button, menus.ShowControls);
        Button("Main Menu", pause, "Main menu", "Icon_Home", Wood, new Vector2(0f, -235f), button, menus.MainMenu);
        menus.pausePanel = pause.gameObject;

        menus.controlsPanel = CreateControlsPanel(c, menus).gameObject;
        menus.creditsPanel = CreateCreditsPanel(c, menus).gameObject;

        var end = Panel("End Panel", c, new Vector2(780f, 660f));
        Image("Glow", end, "Glow", new Color(1f, 0.85f, 0.4f, 0.6f), new Vector2(0f, 230f), new Vector2(220f, 220f));
        Image("Star", end, "Star", Gold, new Vector2(0f, 232f), new Vector2(100f, 100f));
        Text("Title", end, "Workshop restored!", 58f, Walnut, new Vector2(0f, 140f), new Vector2(720f, 80f), style: FontStyles.Bold);
        menus.endSummary = Text("Summary", end, "", 34f, WalnutSoft, new Vector2(0f, 20f), new Vector2(600f, 150f));
        menus.endSummary.lineSpacing = 18f;
        Button("Play Again", end, "Play again", "Icon_Restart", Berry, new Vector2(0f, -140f), button, menus.Restart);
        Button("Main Menu", end, "Main menu", "Icon_Home", Wood, new Vector2(0f, -248f), button, menus.MainMenu);
        menus.endPanel = end.gameObject;

        foreach (var panel in new[] { menus.startPanel, menus.pausePanel, menus.controlsPanel, menus.creditsPanel, menus.endPanel })
            panel.SetActive(false);
        return menus;
    }

    static RectTransform CreateControlsPanel(Transform parent, MenuSystem menus)
    {
        var panel = Panel("Controls Panel", parent, new Vector2(1160f, 840f));
        Text("Title", panel, "Controls", 58f, Walnut, new Vector2(0f, 360f), new Vector2(800f, 80f), style: FontStyles.Bold);

        var imageSize = new Vector2(960f, 540f);
        var imageCentre = new Vector2(0f, 75f);
        Image("Controllers", panel, "Controllers", Color.white, imageCentre, imageSize);

        var json = File.ReadAllText(UIFolder + "controller_callouts.json");
        var points = Regex.Matches(json, "\"(\\w+)\":\\s*\\[\\s*(-?[\\d.]+),\\s*(-?[\\d.]+)\\s*\\]")
            .Cast<Match>().ToDictionary(m => m.Groups[1].Value,
                m => new Vector2(float.Parse(m.Groups[2].Value, System.Globalization.CultureInfo.InvariantCulture),
                                 float.Parse(m.Groups[3].Value, System.Globalization.CultureInfo.InvariantCulture)));
        var labels = new (string point, string text)[]
        {
            ("left_menu", "Pause menu"), ("left_thumbstick", "Move"), ("left_trigger", "Select / press"), ("left_grip", "Grab"),
            ("right_thumbstick", "Turn · up to teleport"), ("right_trigger", "Select / press"), ("right_grip", "Grab"),
        };
        foreach (var side in new[] { "left", "right" })
        {
            float labelX = side == "left" ? -400f : 400f;
            float lastY = float.MaxValue;
            foreach (var (point, text) in labels.Where(l => l.point.StartsWith(side)).OrderByDescending(l => points[l.point].y))
            {
                var p = points[point];
                var dot = imageCentre + new Vector2((p.x - 0.5f) * imageSize.x, (p.y - 0.5f) * imageSize.y);
                float y = Mathf.Min(dot.y, lastY - 62f);
                lastY = y;
                var labelPos = new Vector2(labelX, y);
                Line(panel, dot, labelPos + new Vector2(side == "left" ? 115f : -115f, 0f));
                Image("Dot", panel, "Circle", Berry, dot, new Vector2(18f, 18f));
                Image("Pill", panel, "Rounded", Walnut, labelPos, new Vector2(240f, 50f), true);
                Text("Label", panel, text, 24f, Cream, labelPos, new Vector2(230f, 50f), style: FontStyles.Bold);
            }
        }

        var gestures = new[]
        {
            ("Circle your hand", "wind up a toy"),
            ("Swipe left / right", "wave at the soldier"),
            ("Push forward", "nudge the soldier"),
        };
        for (int i = 0; i < gestures.Length; i++)
        {
            var pos = new Vector2(-350f + 350f * i, -255f);
            Image("Gesture Card", panel, "Rounded", new Color(0.36f, 0.24f, 0.15f, 0.12f), pos, new Vector2(330f, 92f), true);
            Text("Gesture", panel, $"<b>{gestures[i].Item1}</b>\n<size=80%>{gestures[i].Item2}</size>", 27f, Walnut, pos,
                new Vector2(320f, 90f));
        }
        Button("Back", panel, "Back", "Icon_Back", Wood, new Vector2(0f, -360f), new Vector2(300f, 80f), menus.Back);
        return panel;
    }

    static RectTransform CreateCreditsPanel(Transform parent, MenuSystem menus)
    {
        var panel = Panel("Credits Panel", parent, new Vector2(760f, 760f));
        Text("Title", panel, "Credits", 58f, Walnut, new Vector2(0f, 310f), new Vector2(600f, 80f), style: FontStyles.Bold);
        var roles = new[] { "Game design", "Programming", "3D models & animation", "Sound & music", "UI design" };
        for (int i = 0; i < roles.Length; i++)
        {
            float y = 205f - i * 92f;
            Text("Role", panel, roles[i], 26f, WalnutSoft, new Vector2(0f, y + 18f), new Vector2(640f, 36f));
            Text("Name", panel, "Titiksha Raj Pandey", 36f, Walnut, new Vector2(0f, y - 16f), new Vector2(640f, 46f), style: FontStyles.Bold);
        }
        Text("Tools", panel, "Made with Unity, Blender and Ollama · Built with Llama", 22f, WalnutSoft, new Vector2(0f, -258f),
            new Vector2(680f, 34f), style: FontStyles.Italic);
        Button("Back", panel, "Back", "Icon_Back", Wood, new Vector2(0f, -325f), new Vector2(300f, 80f), menus.Back);
        return panel;
    }

    static void Line(Transform parent, Vector2 from, Vector2 to)
    {
        var line = Image("Line", parent, "Rounded", Berry, (from + to) / 2f, new Vector2(Vector2.Distance(from, to), 4f));
        line.rectTransform.localRotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(to.y - from.y, to.x - from.x) * Mathf.Rad2Deg);
    }

    static ToymakerGuide CreateToymaker(SceneRefs s, GameFlow flow)
    {
        var pivot = s.Pivot("Toymaker");
        var instance = SceneRefs.Instance(pivot);

        var root = new GameObject("Toymaker Guide");
        root.transform.SetParent(s.game.transform);
        var guide = root.AddComponent<ToymakerGuide>();
        guide.game = flow;
        guide.ai = root.AddComponent<OllamaChat>();
        guide.animator = instance.GetComponent<Animator>();
        guide.head = s.head;

        var bubbleCanvas = WorldCanvas("Speech Bubble", root.transform, new Vector2(700f, 260f), s.camera, interactive: false);
        bubbleCanvas.transform.position = pivot.position + Vector3.up * 2.08f + pivot.forward * 0.05f;
        guide.bubble = bubbleCanvas.gameObject.AddComponent<CanvasGroup>();
        guide.bubble.alpha = 0f;
        var bubble = bubbleCanvas.transform;
        var tail = Image("Tail", bubble, "Rounded", Walnut, new Vector2(0f, -112f), new Vector2(46f, 46f));
        tail.rectTransform.localRotation = Quaternion.Euler(0f, 0f, 45f);
        Image("Edge", bubble, "Rounded", Walnut, Vector2.zero, new Vector2(690f, 230f), true);
        Image("Face", bubble, "Rounded", Cream, Vector2.zero, new Vector2(680f, 220f), true);
        var tailFace = Image("Tail Face", bubble, "Rounded", Cream, new Vector2(0f, -106f), new Vector2(36f, 36f));
        tailFace.rectTransform.localRotation = Quaternion.Euler(0f, 0f, 45f);
        guide.bubbleText = Text("Text", bubble, "", 32f, Walnut, Vector2.zero, new Vector2(620f, 190f));

        var panelCanvas = WorldCanvas("Hint Panel", root.transform, new Vector2(560f, 460f), s.camera, interactive: true);
        var panelPos = pivot.position - pivot.right * 0.55f + pivot.forward * 0.25f + Vector3.up * 1.15f;
        var toPlayer = panelPos - new Vector3(0f, panelPos.y, 0f);
        panelCanvas.transform.SetPositionAndRotation(panelPos, Quaternion.LookRotation(new Vector3(toPlayer.x, 0f, toPlayer.z)));
        guide.hintPanel = panelCanvas.gameObject.AddComponent<CanvasGroup>();
        guide.hintPanel.alpha = 0f;
        var hint = Panel("Panel", panelCanvas.transform, new Vector2(540f, 440f));
        Image("Icon", hint, "Icon_Hint", Berry, new Vector2(-150f, 165f), new Vector2(54f, 54f));
        Text("Title", hint, "Ask Tobias", 44f, Walnut, new Vector2(30f, 165f), new Vector2(320f, 60f), TextAlignmentOptions.Left,
            FontStyles.Bold);
        var size = new Vector2(470f, 82f);
        Button("What Next", hint, "What do I do next?", null, Berry, new Vector2(0f, 60f), size, guide.AskWhatNext);
        Button("How It Works", hint, "How does it work?", null, Wood, new Vector2(0f, -40f), size, guide.AskHowItWorks);
        Button("About", hint, "Tell me about this toy", null, Wood, new Vector2(0f, -140f), size, guide.AskAboutToy);
        return guide;
    }

    static Chalkboard CreateChalkboard(SceneRefs s)
    {
        var pivot = s.Pivot("Chalkboard");
        var board = Find(SceneRefs.Instance(pivot), "Board");
        var chalkboard = pivot.gameObject.AddComponent<Chalkboard>();
        chalkboard.boardAnimator = SceneRefs.Instance(pivot).GetComponent<Animator>();

        var canvas = WorldCanvas("Chalk Writing", pivot, new Vector2(860f, 620f), s.camera, interactive: false);
        float tilt = k_BoardTilt * Mathf.Deg2Rad;
        var normal = new Vector3(0f, Mathf.Sin(tilt), Mathf.Cos(tilt));
        canvas.transform.localPosition = new Vector3(0f, k_BoardCentreHeight, k_BoardFaceDepth) + normal * 0.004f;
        canvas.transform.localRotation = Quaternion.LookRotation(-normal, new Vector3(0f, Mathf.Cos(tilt), -Mathf.Sin(tilt)));
        canvas.transform.SetParent(board, true);

        var c = canvas.transform;
        Text("Title", c, "Tonight's repairs", 54f, ChalkWhite, new Vector2(-40f, 235f), new Vector2(640f, 70f),
            style: FontStyles.Bold | FontStyles.Italic);
        Image("Underline", c, "Rounded", new Color(1f, 1f, 1f, 0.6f), new Vector2(-40f, 192f), new Vector2(420f, 5f));
        const int lines = 5;
        chalkboard.lines = new TMP_Text[lines];
        chalkboard.ticks = new UnityEngine.UI.Image[lines];
        for (int i = 0; i < lines; i++)
        {
            float y = 120f - i * 82f;
            chalkboard.lines[i] = Text($"Line {i + 1}", c, "", 40f, ChalkWhite, new Vector2(40f, y), new Vector2(680f, 70f),
                TextAlignmentOptions.Left, FontStyles.Italic);
            chalkboard.ticks[i] = Image($"Tick {i + 1}", c, "Check", new Color(0.65f, 1f, 0.6f), new Vector2(-355f, y),
                new Vector2(60f, 60f));
        }
        return chalkboard;
    }

    static TaskBeacon CreateBeacon(SceneRefs s)
    {
        var go = new GameObject("Guide Star");
        go.transform.SetParent(s.game.transform);
        var beacon = go.AddComponent<TaskBeacon>();
        beacon.head = s.head;
        beacon.visual = new GameObject("Visual").transform;
        beacon.visual.SetParent(go.transform, false);
        var canvas = WorldCanvas("Star", beacon.visual, new Vector2(170f, 170f), s.camera, interactive: false);
        Image("Glow", canvas.transform, "Glow", new Color(1f, 0.82f, 0.35f, 0.75f), Vector2.zero, new Vector2(170f, 170f));
        Image("Star", canvas.transform, "Star", Gold, Vector2.zero, new Vector2(90f, 90f));
        return beacon;
    }

    static Sounds CreateSounds(GameObject game)
    {
        var sounds = game.AddComponent<Sounds>();
        sounds.snap = Clip("Snap");
        sounds.wind = Clip("Wind");
        sounds.whistle = Clip("Whistle");
        sounds.boing = Clip("Boing");
        sounds.squeak = Clip("Squeak");
        sounds.clatter = Clip("Clatter");
        sounds.cuckoo = Clip("Cuckoo");
        sounds.click = Clip("Click");
        sounds.whoosh = Clip("Whoosh");
        sounds.babble = Clip("Babble");
        sounds.sparkle = Clip("Sparkle");
        sounds.bump = Clip("Bump");
        return sounds;
    }

    static AudioClip Clip(string name) => AssetDatabase.LoadAssetAtPath<AudioClip>($"Assets/Audio/{name}.wav");

    static AudioSource AddLoop(GameObject go, string clip, float volume, bool playNow, bool spatial = true)
    {
        var source = go.AddComponent<AudioSource>();
        source.clip = Clip(clip);
        source.loop = true;
        source.volume = volume;
        source.playOnAwake = playNow;
        source.spatialBlend = spatial ? 1f : 0f;
        source.minDistance = 0.5f;
        source.maxDistance = 10f;
        return source;
    }

    static void SetUpPlayerBounds(SceneRefs s)
    {
        var rig = s.origin.gameObject;
        foreach (var old in rig.GetComponents<PlayerBounds>())
            Object.DestroyImmediate(old);
        foreach (var extra in rig.GetComponents<NavMeshModifier>().Skip(1))
            Object.DestroyImmediate(extra);
        rig.AddComponent<PlayerBounds>().head = s.head;
        rig.GetComponent<CharacterController>().stepOffset = 0.1f;

        var room = s.Pivot("WorkshopRoom");
        var floor = room.GetComponents<BoxCollider>().OrderBy(b => b.size.y).First();
        var teleport = new GameObject("Teleport Floor");
        teleport.transform.SetParent(s.game.transform);
        teleport.transform.position = room.TransformPoint(floor.center + new Vector3(0f, 0.055f, 0f));
        var box = teleport.AddComponent<BoxCollider>();
        box.size = new Vector3(floor.size.x - 0.8f, 0.01f, floor.size.z - 0.8f);
        teleport.AddComponent<TeleportationArea>().interactionLayers = InteractionLayerMask.GetMask("Teleport");
    }

    static void SetUpPostProcessing(Camera camera)
    {
        camera.GetUniversalAdditionalCameraData().renderPostProcessing = true;
        var volume = Object.FindAnyObjectByType<Volume>();
        if (volume == null)
            volume = new GameObject("Global Volume").AddComponent<Volume>();
        volume.isGlobal = true;

        const string path = "Assets/Art/WorkshopPost.asset";
        AssetDatabase.DeleteAsset(path);
        var profile = ScriptableObject.CreateInstance<VolumeProfile>();
        AssetDatabase.CreateAsset(profile, path);
        var bloom = profile.Add<Bloom>();
        bloom.threshold.Override(0.95f);
        bloom.intensity.Override(0.7f);
        bloom.scatter.Override(0.65f);
        profile.Add<Tonemapping>().mode.Override(TonemappingMode.ACES);
        var vignette = profile.Add<Vignette>();
        vignette.intensity.Override(0.22f);
        vignette.smoothness.Override(0.5f);
        var colour = profile.Add<ColorAdjustments>();
        colour.postExposure.Override(0.25f);
        colour.saturation.Override(8f);
        foreach (var component in profile.components)
            AssetDatabase.AddObjectToAsset(component, profile);
        AssetDatabase.SaveAssets();
        volume.sharedProfile = profile;
    }

    static ParticleSystem CreateSparkles(Transform parent)
    {
        var ps = NewParticles("Sparkles", parent);
        var main = ps.main;
        main.duration = 1f;
        main.startLifetime = new ParticleSystem.MinMaxCurve(0.6f, 1.2f);
        main.startSpeed = new ParticleSystem.MinMaxCurve(0.2f, 0.6f);
        main.startSize = new ParticleSystem.MinMaxCurve(0.02f, 0.045f);
        main.startColor = new ParticleSystem.MinMaxGradient(new Color(1f, 0.85f, 0.4f), new Color(1f, 1f, 0.8f));
        main.gravityModifier = -0.05f;
        var emission = ps.emission;
        emission.rateOverTime = 0f;
        emission.SetBursts(new[] { new ParticleSystem.Burst(0f, 45) });
        var shape = ps.shape;
        shape.shapeType = ParticleSystemShapeType.Sphere;
        shape.radius = 0.08f;
        var shrink = ps.sizeOverLifetime;
        shrink.enabled = true;
        shrink.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0f, 1f, 1f, 0f));
        return ps;
    }

    static void CreateEmbers(Transform fireplace)
    {
        var ps = NewParticles("Embers", fireplace);
        ps.transform.localPosition = new Vector3(0f, 0.25f, 0.25f);
        var main = ps.main;
        main.loop = true;
        main.playOnAwake = true;
        main.startLifetime = new ParticleSystem.MinMaxCurve(1.5f, 3f);
        main.startSpeed = new ParticleSystem.MinMaxCurve(0.1f, 0.3f);
        main.startSize = new ParticleSystem.MinMaxCurve(0.006f, 0.014f);
        main.startColor = new ParticleSystem.MinMaxGradient(new Color(1f, 0.45f, 0.1f), new Color(1f, 0.75f, 0.3f));
        main.gravityModifier = -0.04f;
        var emission = ps.emission;
        emission.rateOverTime = 6f;
        var shape = ps.shape;
        shape.shapeType = ParticleSystemShapeType.Box;
        shape.scale = new Vector3(0.4f, 0.05f, 0.2f);
        var noise = ps.noise;
        noise.enabled = true;
        noise.strength = 0.08f;
        noise.frequency = 0.8f;
        var fade = ps.colorOverLifetime;
        fade.enabled = true;
        var gradient = new Gradient();
        gradient.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
            new[] { new GradientAlphaKey(1f, 0f), new GradientAlphaKey(1f, 0.6f), new GradientAlphaKey(0f, 1f) });
        fade.color = gradient;
    }

    static ParticleSystem NewParticles(string name, Transform parent)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        var ps = go.AddComponent<ParticleSystem>();
        ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        var main = ps.main;
        main.playOnAwake = false;
        main.loop = false;
        main.simulationSpace = ParticleSystemSimulationSpace.World;
        go.GetComponent<ParticleSystemRenderer>().sharedMaterial = SparkMaterial();
        return ps;
    }

    static Material SparkMaterial()
    {
        string path = $"{k_MaterialFolder}/Spark.mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material == null)
        {
            material = new Material(Shader.Find("Universal Render Pipeline/Particles/Unlit"));
            AssetDatabase.CreateAsset(material, path);
        }
        material.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(UIFolder + "Glow.png"));
        material.SetFloat("_Surface", 1f);
        material.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha);
        material.SetFloat("_DstBlend", (float)BlendMode.One);
        material.SetFloat("_ZWrite", 0f);
        material.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
        material.renderQueue = (int)RenderQueue.Transparent;
        EditorUtility.SetDirty(material);
        return material;
    }

    static ParticleSystem CreateConfetti(Transform parent)
    {
        var go = new GameObject("Midnight Confetti");
        go.transform.SetParent(parent);
        go.transform.position = new Vector3(0f, 2.85f, 0.6f);
        var ps = go.AddComponent<ParticleSystem>();
        ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);

        var main = ps.main;
        main.playOnAwake = false;
        main.loop = false;
        main.duration = 2f;
        main.startLifetime = 8f;
        main.startSpeed = new ParticleSystem.MinMaxCurve(0.05f, 0.35f);
        main.startSize = new ParticleSystem.MinMaxCurve(0.015f, 0.03f);
        main.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
        main.gravityModifier = 0.1f;
        main.simulationSpace = ParticleSystemSimulationSpace.World;
        main.maxParticles = 600;
        var colours = new Gradient { mode = GradientMode.Fixed };
        colours.SetKeys(new[]
        {
            new GradientColorKey(new Color(0.85f, 0.2f, 0.15f), 0.2f), new GradientColorKey(new Color(1f, 0.8f, 0.2f), 0.4f),
            new GradientColorKey(new Color(0.2f, 0.45f, 0.85f), 0.6f), new GradientColorKey(new Color(0.25f, 0.65f, 0.35f), 0.8f),
            new GradientColorKey(new Color(1f, 0.6f, 0.75f), 1f),
        }, new[] { new GradientAlphaKey(1f, 0f), new GradientAlphaKey(1f, 1f) });
        main.startColor = new ParticleSystem.MinMaxGradient(colours) { mode = ParticleSystemGradientMode.RandomColor };

        var emission = ps.emission;
        emission.rateOverTime = 0f;
        emission.SetBursts(new[] { new ParticleSystem.Burst(0f, 260), new ParticleSystem.Burst(0.7f, 200) });
        var shape = ps.shape;
        shape.shapeType = ParticleSystemShapeType.Box;
        shape.scale = new Vector3(3.6f, 0.05f, 3.2f);
        var spin = ps.rotationOverLifetime;
        spin.enabled = true;
        spin.z = new ParticleSystem.MinMaxCurve(-4f, 4f);
        var noise = ps.noise;
        noise.enabled = true;
        noise.strength = 0.12f;
        noise.frequency = 0.6f;
        var collision = ps.collision;
        collision.enabled = true;
        collision.type = ParticleSystemCollisionType.World;
        collision.mode = ParticleSystemCollisionMode.Collision3D;
        collision.dampen = 1f;
        collision.bounce = 0f;
        collision.quality = ParticleSystemCollisionQuality.Low;

        var material = AssetDatabase.LoadAssetAtPath<Material>($"{k_MaterialFolder}/Confetti.mat");
        if (material == null)
        {
            material = new Material(Shader.Find("Universal Render Pipeline/Particles/Unlit"));
            AssetDatabase.CreateAsset(material, $"{k_MaterialFolder}/Confetti.mat");
        }
        material.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(UIFolder + "Rounded.png"));
        material.SetFloat("_AlphaClip", 1f);
        material.SetFloat("_Cutoff", 0.5f);
        material.EnableKeyword("_ALPHATEST_ON");
        EditorUtility.SetDirty(material);
        go.GetComponent<ParticleSystemRenderer>().sharedMaterial = material;
        return ps;
    }

    static Material PreviewMaterial(string name, Color color)
    {
        string path = $"{k_MaterialFolder}/{name}.mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material == null)
        {
            material = new Material(Shader.Find("Universal Render Pipeline/Unlit"));
            AssetDatabase.CreateAsset(material, path);
        }
        material.SetColor("_BaseColor", color);
        material.SetFloat("_Surface", 1f);
        material.SetFloat("_Blend", 0f);
        material.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha);
        material.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
        material.SetFloat("_ZWrite", 0f);
        material.SetOverrideTag("RenderType", "Transparent");
        material.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
        material.renderQueue = (int)RenderQueue.Transparent;
        EditorUtility.SetDirty(material);
        return material;
    }

    static Transform Find(Transform root, string name) =>
        root.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name);

    static Transform FindMesh(Transform root, string name) =>
        root.GetComponentsInChildren<Renderer>(true).FirstOrDefault(r => r.name == name)?.transform;

    static Transform FindBone(Transform root, string name) =>
        root.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name && t.GetComponent<Renderer>() == null);

    static Transform Point(Transform parent, string name, Vector3 position)
    {
        var t = new GameObject(name).transform;
        t.SetParent(parent);
        t.position = position;
        return t;
    }

    static Bounds WorldBounds(Transform[] parts)
    {
        var renderers = parts.SelectMany(p => p.GetComponentsInChildren<Renderer>(true)).ToArray();
        var bounds = renderers.Length > 0 ? renderers[0].bounds : new Bounds(parts[0].position, Vector3.zero);
        foreach (var r in renderers)
            bounds.Encapsulate(r.bounds);
        return bounds;
    }

    static Bounds LocalBounds(Transform root)
    {
        var toLocal = root.worldToLocalMatrix;
        bool first = true;
        var result = new Bounds();
        foreach (var filter in root.GetComponentsInChildren<MeshFilter>(true))
        {
            var mb = filter.sharedMesh.bounds;
            var m = toLocal * filter.transform.localToWorldMatrix;
            for (int i = 0; i < 8; i++)
            {
                var corner = m.MultiplyPoint3x4(mb.center + Vector3.Scale(mb.extents,
                    new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1)));
                if (first)
                {
                    result = new Bounds(corner, Vector3.zero);
                    first = false;
                }
                else
                {
                    result.Encapsulate(corner);
                }
            }
        }
        return result;
    }
}
