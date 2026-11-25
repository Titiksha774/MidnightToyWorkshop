using TMPro;
using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit.Interactables;

public class HoverLabel : MonoBehaviour
{
    public string text;
    public float heightOffset = 0.04f;
    public float fontSize = 0.25f;

    TextMeshPro m_Label;
    XRBaseInteractable m_Interactable;
    Collider m_Collider;

    public bool IsGazed { get; set; }

    void Awake()
    {
        m_Interactable = GetComponent<XRBaseInteractable>();
        m_Collider = GetComponentInChildren<Collider>();

        var labelObject = new GameObject(name + " Label");
        m_Label = labelObject.AddComponent<TextMeshPro>();
        m_Label.text = string.IsNullOrEmpty(text) ? name : text;
        m_Label.fontSize = fontSize;
        m_Label.alignment = TextAlignmentOptions.Bottom;
        m_Label.rectTransform.sizeDelta = new Vector2(0.4f, 0.05f);
        m_Label.color = Color.white;
        m_Label.outlineWidth = 0.2f;
        m_Label.outlineColor = new Color32(30, 20, 10, 255);
        labelObject.SetActive(false);
    }

    void LateUpdate()
    {
        bool show = IsGazed || (m_Interactable != null && m_Interactable.isHovered && !m_Interactable.isSelected);
        if (m_Label.gameObject.activeSelf != show)
            m_Label.gameObject.SetActive(show);
        if (!show)
            return;

        var bounds = m_Collider != null ? m_Collider.bounds : new Bounds(transform.position, Vector3.zero);
        var labelTransform = m_Label.transform;
        labelTransform.position = new Vector3(bounds.center.x, bounds.max.y + heightOffset, bounds.center.z);
        var cam = Camera.main;
        if (cam != null)
            labelTransform.rotation = Quaternion.LookRotation(labelTransform.position - cam.transform.position);
    }

    void OnDisable()
    {
        IsGazed = false;
        if (m_Label != null)
            m_Label.gameObject.SetActive(false);
    }

    void OnDestroy()
    {
        if (m_Label != null)
            Destroy(m_Label.gameObject);
    }
}
