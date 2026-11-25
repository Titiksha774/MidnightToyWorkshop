using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class PlayerBounds : MonoBehaviour
{
    public Transform head;
    public float headRadius = 0.12f;
    public float bumpCooldown = 0.6f;

    SphereCollider m_Probe;
    readonly Collider[] m_Hits = new Collider[16];
    float m_LastBump = -10f;

    void Awake()
    {
        var probe = new GameObject("Head Probe");
        probe.transform.SetParent(transform, false);
        m_Probe = probe.AddComponent<SphereCollider>();
        m_Probe.isTrigger = true;
        m_Probe.radius = headRadius;
    }

    // walking for real can put your head through a wall, so slide the whole rig back out
    void LateUpdate()
    {
        var position = head.position;
        m_Probe.transform.position = position;
        int count = Physics.OverlapSphereNonAlloc(position, headRadius, m_Hits, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
        var push = Vector3.zero;
        for (int i = 0; i < count; i++)
        {
            var other = m_Hits[i];
            if (other.attachedRigidbody != null || other.transform.IsChildOf(transform))
                continue;
            if (Physics.ComputePenetration(m_Probe, position, Quaternion.identity, other, other.transform.position,
                    other.transform.rotation, out var direction, out var distance))
                push += direction * distance;
        }
        push.y = 0f;
        if (push.sqrMagnitude < 0.000001f)
            return;
        transform.position += push;
        Bump(position);
    }

    // the thumbstick moves us with the character controller, which tells us when it hits something
    void OnControllerColliderHit(ControllerColliderHit hit)
    {
        if (hit.normal.y < 0.5f && hit.rigidbody == null)
            Bump(hit.point);
    }

    void Bump(Vector3 where)
    {
        if (Time.time - m_LastBump < bumpCooldown)
            return;
        m_LastBump = Time.time;
        Sounds.Play(s => s.bump, where, 0.7f, Random.Range(0.9f, 1.1f));
    }
}
