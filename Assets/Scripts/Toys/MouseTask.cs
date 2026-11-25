using UnityEngine;
using UnityEngine.AI;
using UnityEngine.XR.Interaction.Toolkit;
using UnityEngine.XR.Interaction.Toolkit.Interactables;
using UnityEngine.XR.Interaction.Toolkit.Interactors;

public class MouseTask : WorkshopTask
{
    enum State { Asleep, Running, Sniffing, Held, Calm }

    public NavMeshAgent agent;
    public Animator animator;
    public XRGrabInteractable grab;
    public Transform home;
    public float wanderRadius = 1.6f;
    public float fleeDistance = 1.0f;
    public Vector2 sniffSeconds = new Vector2(1.2f, 2.2f);

    static readonly int k_Running = Animator.StringToHash("Running");
    State m_State = State.Asleep;
    float m_SniffUntil;

    void Awake()
    {
        agent.enabled = false;
        grab.enabled = false;
        grab.selectEntered.AddListener(OnGrabbed);
        grab.selectExited.AddListener(OnReleased);
    }

    protected override void OnBegin()
    {
        grab.enabled = true;
        EnableAgent();
        Run(RandomPointNearHome());
    }

    void Update()
    {
        if (m_State == State.Running && !FleeIfPlayerClose() && !agent.pathPending &&
            agent.remainingDistance <= agent.stoppingDistance + 0.02f)
            Sniff();
        else if (m_State == State.Sniffing && (FleeIfPlayerClose() || Time.time >= m_SniffUntil))
            Run(RandomPointNearHome());
    }

    bool FleeIfPlayerClose()
    {
        var away = transform.position - Flow.Head.position;
        away.y = 0f;
        if (away.magnitude > fleeDistance)
            return false;
        // dash away, a bit off to the side so it doesn't get stuck in corners
        Run(transform.position + Quaternion.Euler(0f, Random.Range(-40f, 40f), 0f) * away.normalized * 1.2f);
        return true;
    }

    void Run(Vector3 target)
    {
        if (!NavMesh.SamplePosition(target, out var hit, 0.6f, NavMesh.AllAreas))
            hit.position = home.position;
        agent.isStopped = false;
        agent.SetDestination(hit.position);
        animator.SetBool(k_Running, true);
        if (m_State != State.Running && Random.value < 0.4f)
            Sounds.Play(s => s.squeak, transform.position, 0.6f, Random.Range(0.9f, 1.2f));
        m_State = State.Running;
    }

    void Sniff()
    {
        agent.isStopped = true;
        animator.SetBool(k_Running, false);
        m_State = State.Sniffing;
        m_SniffUntil = Time.time + Random.Range(sniffSeconds.x, sniffSeconds.y);
    }

    Vector3 RandomPointNearHome()
    {
        var offset = Random.insideUnitCircle * wanderRadius;
        return home.position + new Vector3(offset.x, 0f, offset.y);
    }

    void OnGrabbed(SelectEnterEventArgs args)
    {
        if (args.interactorObject is XRSocketInteractor)
            return;
        agent.enabled = false;
        animator.SetBool(k_Running, true);
        m_State = State.Held;
        Sounds.Play(s => s.squeak, transform.position, 0.8f, 1.2f);
        Flow.Log("Mouse caught");
        if (IsActive)
            Flow.toymaker.Say("You caught him! Put him down gently, he'll settle now.", 4f);
    }

    void OnReleased(SelectExitEventArgs args)
    {
        var p = transform.position;
        if (NavMesh.SamplePosition(new Vector3(p.x, 0f, p.z), out var hit, 2f, NavMesh.AllAreas))
            transform.position = hit.position;
        transform.rotation = Quaternion.Euler(0f, transform.eulerAngles.y, 0f);
        EnableAgent();
        agent.isStopped = true;
        animator.SetBool(k_Running, false);
        m_State = State.Calm;
        Complete();
    }

    void EnableAgent()
    {
        agent.enabled = true;
        agent.Warp(transform.position);
    }

    public override void PerformFinale()
    {
        if (m_State == State.Held)
            return;
        Run(home.position);
        m_State = State.Calm;
    }
}
