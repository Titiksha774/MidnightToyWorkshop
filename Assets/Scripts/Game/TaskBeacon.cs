using UnityEngine;

public class TaskBeacon : MonoBehaviour
{
    public Transform visual;
    public Transform head;
    public float heightAbove = 0.14f;
    public float bobHeight = 0.025f;

    Transform m_Target;
    Collider[] m_TargetColliders;

    public void Follow(Transform target)
    {
        m_Target = target;
        m_TargetColliders = target != null ? target.GetComponentsInChildren<Collider>() : null;
        visual.gameObject.SetActive(target != null);
        if (target != null)
            transform.position = TopOf(target);
    }

    void LateUpdate()
    {
        if (m_Target == null)
            return;

        var goal = TopOf(m_Target) + Vector3.up * (bobHeight * Mathf.Sin(Time.time * 2.5f));
        transform.position = Vector3.Lerp(transform.position, goal, 1f - Mathf.Exp(-8f * Time.deltaTime));

        var toHead = head.position - transform.position;
        toHead.y = 0f;
        if (toHead.sqrMagnitude > 0.0001f)
            transform.rotation = Quaternion.LookRotation(-toHead);
        visual.localRotation = Quaternion.Euler(0f, 0f, Mathf.Sin(Time.time * 1.7f) * 12f);
        visual.localScale = Vector3.one * (1f + 0.08f * Mathf.Sin(Time.time * 4f));
    }

    Vector3 TopOf(Transform target)
    {
        var top = target.position;
        bool found = false;
        foreach (var c in m_TargetColliders)
        {
            if (c == null || !c.enabled || c.isTrigger)
                continue;
            var b = c.bounds;
            top = found ? new Vector3(top.x, Mathf.Max(top.y, b.max.y), top.z) : new Vector3(b.center.x, b.max.y, b.center.z);
            found = true;
        }
        return top + Vector3.up * heightAbove;
    }
}
