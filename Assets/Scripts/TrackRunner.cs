using UnityEngine;

public class TrackRunner : MonoBehaviour
{
    public Transform track;
    public float radiusX = 0.44f;
    public float radiusZ = 0.22f;
    public float railHeight = 0.777f;
    public float speed = 0.138f;
    public float startAngle = Mathf.PI / 2f;

    float m_Angle;

    void OnEnable() => m_Angle = startAngle;

    void Update()
    {
        // step by distance so it doesn't speed up round the tight ends of the oval
        float dx = -radiusX * Mathf.Sin(m_Angle), dz = radiusZ * Mathf.Cos(m_Angle);
        m_Angle = Mathf.Repeat(m_Angle + speed * Time.deltaTime / Mathf.Sqrt(dx * dx + dz * dz), 2f * Mathf.PI);
        PoseAt(m_Angle, out var position, out var rotation);
        transform.SetPositionAndRotation(position, rotation);
    }

    public void PoseAt(float angle, out Vector3 position, out Quaternion rotation)
    {
        var local = new Vector3(radiusX * Mathf.Cos(angle), railHeight, radiusZ * Mathf.Sin(angle));
        var tangent = new Vector3(-radiusX * Mathf.Sin(angle), 0f, radiusZ * Mathf.Cos(angle));
        position = track.TransformPoint(local);
        rotation = Quaternion.LookRotation(track.TransformDirection(tangent), track.up);
    }
}
