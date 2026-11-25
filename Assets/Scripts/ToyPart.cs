using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit.Interactables;

[RequireComponent(typeof(XRGrabInteractable))]
public class ToyPart : MonoBehaviour
{
    public string partId;
    public string displayName;
    public float returnDistance = 0.75f;
    public float returnDelay = 4f;

    XRGrabInteractable m_Grab;
    Rigidbody m_Body;
    Vector3 m_HomePosition;
    Quaternion m_HomeRotation;
    float m_ReleasedAt = -1f;

    public XRGrabInteractable Grab => m_Grab != null ? m_Grab : m_Grab = GetComponent<XRGrabInteractable>();

    void Start()
    {
        m_Body = GetComponent<Rigidbody>();
        m_HomePosition = transform.position;
        m_HomeRotation = transform.rotation;
        Grab.selectEntered.AddListener(_ => m_ReleasedAt = -1f);
        Grab.selectExited.AddListener(_ => m_ReleasedAt = Time.time);
    }

    void Update()
    {
        if (Grab.isSelected)
            return;

        // dropped somewhere silly (or fell through the floor)? pop it back where it started
        bool fellOut = transform.position.y < -0.5f;
        bool leftBehind = m_ReleasedAt >= 0f && Time.time - m_ReleasedAt > returnDelay &&
                          (transform.position - m_HomePosition).sqrMagnitude > returnDistance * returnDistance;
        if (fellOut || leftBehind)
            ReturnHome();
    }

    void ReturnHome()
    {
        m_ReleasedAt = -1f;
        if (m_Body != null && !m_Body.isKinematic)
        {
            m_Body.linearVelocity = Vector3.zero;
            m_Body.angularVelocity = Vector3.zero;
        }
        transform.SetPositionAndRotation(m_HomePosition, m_HomeRotation);
        Sounds.Play(s => s.whoosh, m_HomePosition, 0.4f, 1.3f);
    }
}
