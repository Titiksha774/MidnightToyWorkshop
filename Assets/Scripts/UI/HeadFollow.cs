using UnityEngine;

public class HeadFollow : MonoBehaviour
{
    public Transform head;
    public float distance = 1.4f;
    public float heightOffset = -0.12f;
    public float followAngle = 30f;
    public float smoothing = 5f;

    bool m_Following;

    public void SnapInFront()
    {
        var goal = Goal();
        transform.SetPositionAndRotation(goal, Facing(goal));
        m_Following = false;
    }

    void LateUpdate()
    {
        if (Vector3.Angle(Flat(head.forward), Flat(transform.position - head.position)) > followAngle)
            m_Following = true;
        if (!m_Following)
            return;

        // unscaled time so the menu still moves while the game is paused
        var goal = Goal();
        float k = 1f - Mathf.Exp(-smoothing * Time.unscaledDeltaTime);
        transform.position = Vector3.Lerp(transform.position, goal, k);
        transform.rotation = Quaternion.Slerp(transform.rotation, Facing(transform.position), k);
        if ((transform.position - goal).sqrMagnitude < 0.0004f)
            m_Following = false;
    }

    Vector3 Goal() => head.position + Flat(head.forward) * distance + Vector3.up * heightOffset;

    Quaternion Facing(Vector3 position) => Quaternion.LookRotation(Flat(position - head.position), Vector3.up);

    static Vector3 Flat(Vector3 v)
    {
        v.y = 0f;
        return v.sqrMagnitude > 0.0001f ? v.normalized : Vector3.forward;
    }
}
