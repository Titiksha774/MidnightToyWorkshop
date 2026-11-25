using System.Collections;
using UnityEngine;
using UnityEngine.AI;

public class SoldierTask : WorkshopTask
{
    public NavMeshAgent agent;
    public Animator animator;
    public AudioSource marchSound;
    public Transform[] patrol;
    public Transform hopTarget;
    public float waveRange = 3f;
    public float pushRange = 1.3f;

    static readonly int k_Marching = Animator.StringToHash("Marching");
    int m_Waypoint;
    bool m_Marching;
    bool m_Busy;

    void Awake() => agent.enabled = false;

    protected override void OnBegin()
    {
        Flow.Gestures.GestureRecognized += OnGesture;
        StartCoroutine(HopDown());
    }

    void OnDestroy()
    {
        if (Flow != null && Flow.Gestures != null)
            Flow.Gestures.GestureRecognized -= OnGesture;
    }

    IEnumerator HopDown()
    {
        m_Busy = true;
        yield return new WaitForSeconds(1f);
        Vector3 start = transform.position, end = hopTarget.position;
        Quaternion startRot = transform.rotation, endRot = Quaternion.LookRotation(Flat(end - start));
        for (float t = 0f; t < 1f; t += Time.deltaTime / 1.1f)
        {
            float eased = Mathf.SmoothStep(0f, 1f, t);
            transform.SetPositionAndRotation(Vector3.Lerp(start, end, eased) + Vector3.up * (Mathf.Sin(t * Mathf.PI) * 0.25f),
                Quaternion.Slerp(startRot, endRot, eased));
            yield return null;
        }
        agent.enabled = true;
        agent.Warp(end);
        m_Busy = false;
        March();
    }

    void March()
    {
        m_Marching = true;
        agent.isStopped = false;
        agent.SetDestination(patrol[m_Waypoint].position);
        animator.SetBool(k_Marching, true);
        marchSound.Play();
    }

    void StopMarching()
    {
        m_Marching = false;
        agent.isStopped = true;
        animator.SetBool(k_Marching, false);
        marchSound.Stop();
    }

    void Update()
    {
        if (!m_Marching || agent.pathPending || agent.remainingDistance > agent.stoppingDistance + 0.02f)
            return;
        m_Waypoint = (m_Waypoint + 1) % patrol.Length;
        agent.SetDestination(patrol[m_Waypoint].position);
    }

    void OnGesture(string gesture, float confidence)
    {
        if (m_Busy || !agent.enabled || Vector3.Dot(Flow.Head.forward, (transform.position - Flow.Head.position).normalized) < 0.55f)
            return;
        float distance = Vector3.Distance(Flat3(transform.position), Flat3(Flow.Head.position));
        if ((gesture == "Swipe Left" || gesture == "Swipe Right") && distance <= waveRange)
            StartCoroutine(Salute());
        else if (gesture == "Push" && distance <= pushRange)
            StartCoroutine(FallOver());
    }

    IEnumerator Salute()
    {
        m_Busy = true;
        Flow.Log("Soldier salute");
        StopMarching();
        var from = transform.rotation;
        var goal = Quaternion.LookRotation(Flat(Flow.Head.position - transform.position));
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.4f)
        {
            transform.rotation = Quaternion.Slerp(from, goal, Mathf.SmoothStep(0f, 1f, t));
            yield return null;
        }
        animator.SetTrigger("Salute");
        yield return new WaitForSeconds(1.6f);
        if (IsActive)
        {
            Flow.toymaker.Say("He likes you! A proper salute.", 3f);
            Complete();
        }
        m_Busy = false;
        March();
    }

    IEnumerator FallOver()
    {
        m_Busy = true;
        Flow.Log("Soldier pushed over");
        StopMarching();
        animator.SetTrigger("Fall");
        Sounds.Play(s => s.clatter, transform.position);
        Flow.toymaker.Say("Oops! Gently, he's only made of tin.", 3f);
        yield return new WaitForSeconds(2.4f);
        animator.SetTrigger("GetUp");
        yield return new WaitForSeconds(1.7f);
        m_Busy = false;
        March();
    }

    public override void PerformFinale()
    {
        if (agent.enabled && !m_Busy)
            StartCoroutine(Salute());
    }

    static Vector3 Flat(Vector3 v)
    {
        v.y = 0f;
        return v.sqrMagnitude > 0.0001f ? v.normalized : Vector3.forward;
    }

    static Vector3 Flat3(Vector3 v) => new Vector3(v.x, 0f, v.z);
}
