using UnityEngine;

public class GazePointer : MonoBehaviour
{
    public float maxDistance = 3f;
    public float radius = 0.02f;

    HoverLabel m_Current;

    void Update()
    {
        HoverLabel hitLabel = null;
        if (Physics.SphereCast(transform.position, radius, transform.forward, out var hit, maxDistance,
                Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore))
            hitLabel = hit.collider.GetComponentInParent<HoverLabel>();

        if (hitLabel == m_Current)
            return;
        if (m_Current != null)
            m_Current.IsGazed = false;
        m_Current = hitLabel;
        if (m_Current != null)
            m_Current.IsGazed = true;
    }

    void OnDisable()
    {
        if (m_Current != null)
            m_Current.IsGazed = false;
        m_Current = null;
    }
}
