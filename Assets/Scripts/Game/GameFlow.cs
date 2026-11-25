using System.Collections;
using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit.Interactables;

public class GameFlow : MonoBehaviour
{
    public enum State { Menu, Playing, Finale, Ended }

    public WorkshopTask[] tasks;

    public GestureRecognizer gestures;
    public InteractionLogger logger;
    public ToymakerGuide toymaker;
    public TaskBeacon beacon;
    public Chalkboard chalkboard;
    public MenuSystem menus;
    public ClockHands clock;
    public Transform head;

    public Animator cuckooClock;
    public ParticleSystem confetti;
    public ParticleSystem sparkles;
    public Light[] finaleLights;
    public float finaleSeconds = 10f;

    public static bool SkipMenuOnLoad;

    public State Current { get; private set; } = State.Menu;
    public WorkshopTask CurrentTask { get; private set; }
    public float PlaySeconds { get; private set; }

    public GestureRecognizer Gestures => gestures;
    public TaskBeacon Beacon => beacon;
    public Transform Head => head;

    readonly SocketLock m_MenuLock = new SocketLock();
    int m_TaskIndex = -1;
    int m_TasksDone;
    float m_ClockFrom = 23f, m_ClockTo = 23f, m_ClockStart;

    void Awake()
    {
        foreach (var interactable in FindObjectsByType<XRBaseInteractable>(FindObjectsInactive.Include, FindObjectsSortMode.None))
        {
            interactable.selectFilters.Add(m_MenuLock);
            interactable.hoverFilters.Add(m_MenuLock);
        }
        foreach (var task in tasks)
            task.Completed += OnTaskCompleted;

        clock.time = 23f;
        chalkboard.Show(System.Array.ConvertAll(tasks, t => t.title));
        beacon.Follow(null);
    }

    void Start()
    {
        if (!SkipMenuOnLoad)
        {
            menus.ShowStart();
            return;
        }
        SkipMenuOnLoad = false;
        menus.HideAll();
        StartGame();
    }

    public void StartGame()
    {
        if (Current != State.Menu)
            return;
        Current = State.Playing;
        Log("Game start");
        StartCoroutine(Intro());
    }

    IEnumerator Intro()
    {
        toymaker.Wave();
        toymaker.Say("Oh, hello! The toys broke on the way to tonight's delivery. Can you help me fix them before midnight?", 6f);
        yield return new WaitForSeconds(6.5f);
        NextTask();
    }

    void NextTask()
    {
        m_TaskIndex++;
        if (m_TaskIndex >= tasks.Length)
        {
            StartCoroutine(Finale());
            return;
        }

        CurrentTask = tasks[m_TaskIndex];
        chalkboard.SetCurrent(m_TaskIndex);
        beacon.Follow(CurrentTask.beaconTarget);
        if (!string.IsNullOrEmpty(CurrentTask.introLine))
            toymaker.Say(CurrentTask.introLine, 7f);
        CurrentTask.Begin(this);
    }

    void OnTaskCompleted(WorkshopTask task)
    {
        m_TasksDone++;
        chalkboard.Tick(System.Array.IndexOf(tasks, task));
        SweepClockTo(task.clockTime);
        if (task.beaconTarget != null)
        {
            sparkles.transform.position = task.beaconTarget.position + Vector3.up * 0.15f;
            sparkles.Play();
            Sounds.Play(s => s.sparkle, sparkles.transform.position);
        }
        beacon.Follow(null);
        StartCoroutine(AfterTask());
    }

    IEnumerator AfterTask()
    {
        toymaker.Celebrate();
        yield return new WaitForSeconds(3f);
        NextTask();
    }

    IEnumerator Finale()
    {
        Current = State.Finale;
        CurrentTask = null;
        Log("Midnight finale");
        SweepClockTo(24f);
        toymaker.Say("Listen... it's midnight! Every toy is working again. Thank you!", 6f);
        yield return new WaitForSeconds(2.5f);

        cuckooClock.SetTrigger("Cuckoo");
        Sounds.Play(s => s.cuckoo, cuckooClock.transform.position);
        confetti.Play();
        foreach (var task in tasks)
            task.PerformFinale();
        toymaker.Celebrate();
        StartCoroutine(BrightenLights());

        yield return new WaitForSeconds(finaleSeconds);
        Current = State.Ended;
        Log($"Game end: {PlaySeconds:F0} s, {toymaker.HintsAsked} hints");
        menus.ShowEnd(m_TasksDone, tasks.Length, PlaySeconds, toymaker.HintsAsked);
    }

    IEnumerator BrightenLights()
    {
        var start = System.Array.ConvertAll(finaleLights, l => l.intensity);
        for (float t = 0f; t < 1f; t += Time.deltaTime / 3f)
        {
            for (int i = 0; i < finaleLights.Length; i++)
                finaleLights[i].intensity = start[i] * Mathf.Lerp(1f, 1.6f, Mathf.SmoothStep(0f, 1f, t));
            yield return null;
        }
    }

    void SweepClockTo(float time)
    {
        m_ClockFrom = clock.time;
        m_ClockTo = time;
        m_ClockStart = Time.time;
    }

    void Update()
    {
        if (Current == State.Playing || Current == State.Finale)
            PlaySeconds += Time.deltaTime;
        float t = Mathf.Clamp01((Time.time - m_ClockStart) / 2.5f);
        clock.time = Mathf.Lerp(m_ClockFrom, m_ClockTo, Mathf.SmoothStep(0f, 1f, t));
    }

    public void SetMenuOpen(bool open)
    {
        m_MenuLock.locked = open;
        gestures.enabled = !open;
    }

    public void Log(string message) => logger?.Log(message);
}
