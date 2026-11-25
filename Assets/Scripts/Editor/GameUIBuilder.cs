using TMPro;
using UnityEditor;
using UnityEditor.Events;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.XR.Interaction.Toolkit.UI;

static class GameUIBuilder
{
    public const string UIFolder = "Assets/Art/UI/";
    public const float MetresPerPixel = 0.001f;

    public static readonly Color Cream = new Color32(246, 238, 221, 250);
    public static readonly Color Walnut = new Color32(59, 36, 22, 255);
    public static readonly Color WalnutSoft = new Color32(110, 78, 55, 255);
    public static readonly Color Berry = new Color32(178, 58, 43, 255);
    public static readonly Color Wood = new Color32(96, 62, 40, 255);
    public static readonly Color Gold = new Color32(255, 210, 74, 255);
    public static readonly Color ChalkWhite = new Color32(240, 240, 230, 255);

    public static UnityEngine.Sprite Sprite(string name) => AssetDatabase.LoadAssetAtPath<UnityEngine.Sprite>(UIFolder + name + ".png");

    public static Canvas WorldCanvas(string name, Transform parent, Vector2 sizePixels, Camera eventCamera, bool interactive)
    {
        var go = new GameObject(name, typeof(RectTransform));
        go.transform.SetParent(parent, false);
        var canvas = go.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.WorldSpace;
        canvas.worldCamera = eventCamera;
        var rect = (RectTransform)go.transform;
        rect.sizeDelta = sizePixels;
        rect.localScale = Vector3.one * MetresPerPixel;
        go.AddComponent<UnityEngine.UI.CanvasScaler>().dynamicPixelsPerUnit = 3f;
        if (interactive)
        {
            go.AddComponent<TrackedDeviceGraphicRaycaster>();
            go.AddComponent<UnityEngine.UI.GraphicRaycaster>();
        }
        return canvas;
    }

    public static RectTransform Rect(string name, Transform parent, Vector2 position, Vector2 size)
    {
        var go = new GameObject(name, typeof(RectTransform));
        go.transform.SetParent(parent, false);
        var rect = (RectTransform)go.transform;
        rect.anchoredPosition = position;
        rect.sizeDelta = size;
        return rect;
    }

    public static RectTransform Stretch(RectTransform rect)
    {
        rect.anchorMin = Vector2.zero;
        rect.anchorMax = Vector2.one;
        rect.offsetMin = rect.offsetMax = Vector2.zero;
        return rect;
    }

    public static UnityEngine.UI.Image Image(string name, Transform parent, string sprite, Color color, Vector2 position, Vector2 size,
        bool sliced = false)
    {
        var image = Rect(name, parent, position, size).gameObject.AddComponent<UnityEngine.UI.Image>();
        image.sprite = Sprite(sprite);
        image.color = color;
        image.type = sliced ? UnityEngine.UI.Image.Type.Sliced : UnityEngine.UI.Image.Type.Simple;
        image.raycastTarget = false;
        return image;
    }

    public static RectTransform Panel(string name, Transform parent, Vector2 size)
    {
        var root = Rect(name, parent, Vector2.zero, size);
        Image("Shadow", root, "Shadow", new Color(0f, 0f, 0f, 0.45f), new Vector2(0f, -14f), size + new Vector2(70f, 70f), true);
        Image("Edge", root, "Rounded", Walnut, Vector2.zero, size + new Vector2(10f, 10f), true);
        var face = Image("Face", root, "Rounded", Cream, Vector2.zero, size, true);
        face.raycastTarget = true;
        return root;
    }

    public static TMP_Text Text(string name, Transform parent, string text, float size, Color color, Vector2 position,
        Vector2 box, TextAlignmentOptions align = TextAlignmentOptions.Center, FontStyles style = FontStyles.Normal)
    {
        var tmp = Rect(name, parent, position, box).gameObject.AddComponent<TextMeshProUGUI>();
        tmp.text = text;
        tmp.fontSize = size;
        tmp.color = color;
        tmp.alignment = align;
        tmp.fontStyle = style;
        tmp.textWrappingMode = TextWrappingModes.Normal;
        tmp.raycastTarget = false;
        return tmp;
    }

    public static UnityEngine.UI.Button Button(string name, Transform parent, string label, string icon, Color color, Vector2 position,
        Vector2 size, UnityAction onClick)
    {
        var rect = Rect(name, parent, position, size);
        var background = rect.gameObject.AddComponent<UnityEngine.UI.Image>();
        background.sprite = Sprite("Rounded");
        background.type = UnityEngine.UI.Image.Type.Sliced;
        background.color = Color.white;

        var button = rect.gameObject.AddComponent<UnityEngine.UI.Button>();
        var colors = button.colors;
        colors.normalColor = color;
        colors.highlightedColor = Color.Lerp(color, Color.white, 0.22f);
        colors.selectedColor = color;
        colors.pressedColor = Color.Lerp(color, Color.black, 0.2f);
        colors.fadeDuration = 0.08f;
        button.colors = colors;
        button.targetGraphic = background;
        UnityEventTools.AddPersistentListener(button.onClick, onClick);

        float iconSize = size.y * 0.46f;
        if (!string.IsNullOrEmpty(icon))
            Image("Icon", rect, icon, Cream, new Vector2(-size.x / 2f + size.y * 0.55f, 0f), new Vector2(iconSize, iconSize));
        Text("Label", rect, label, size.y * 0.4f, Cream, new Vector2(string.IsNullOrEmpty(icon) ? 0f : size.y * 0.25f, 0f),
            new Vector2(size.x - size.y, size.y), TextAlignmentOptions.Center, FontStyles.Bold);
        return button;
    }
}
