using UnityEngine;

public class ClockHands : MonoBehaviour
{
    public float time = 23f;
    public Transform hourHand;
    public Transform minuteHand;
    public Vector3 faceNormal = Vector3.forward;

    Quaternion m_HourRest, m_MinuteRest;

    void Start()
    {
        m_HourRest = Quaternion.Inverse(transform.rotation) * hourHand.rotation;
        m_MinuteRest = Quaternion.Inverse(transform.rotation) * minuteHand.rotation;
    }

    void LateUpdate()
    {
        float hours = time % 12f;
        float minutes = (time - Mathf.Floor(time)) * 60f;
        hourHand.rotation = transform.rotation * Quaternion.AngleAxis(-hours * 30f, faceNormal) * m_HourRest;
        minuteHand.rotation = transform.rotation * Quaternion.AngleAxis(-minutes * 6f, faceNormal) * m_MinuteRest;
    }
}
