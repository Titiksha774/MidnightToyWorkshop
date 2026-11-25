using System.Collections;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class Chalkboard : MonoBehaviour
{
    public TMP_Text[] lines;
    public Image[] ticks;
    public Animator boardAnimator;

    static readonly Color k_Chalk = new Color(0.94f, 0.94f, 0.9f);
    static readonly Color k_Current = new Color(1f, 0.86f, 0.35f);
    static readonly Color k_Done = new Color(0.94f, 0.94f, 0.9f, 0.45f);

    int m_Count;

    public void Show(string[] titles)
    {
        m_Count = titles.Length;
        for (int i = 0; i < lines.Length; i++)
        {
            lines[i].gameObject.SetActive(i < titles.Length);
            ticks[i].gameObject.SetActive(false);
            if (i < titles.Length)
            {
                lines[i].text = $"{i + 1}. {titles[i]}";
                lines[i].color = k_Chalk;
            }
        }
    }

    public void SetCurrent(int index)
    {
        for (int i = 0; i < m_Count; i++)
        {
            if (!ticks[i].gameObject.activeSelf)
                lines[i].color = i == index ? k_Current : k_Chalk;
        }
    }

    public void Tick(int index)
    {
        lines[index].color = k_Done;
        lines[index].fontStyle |= FontStyles.Strikethrough;
        StartCoroutine(PopIn(ticks[index].transform));
        boardAnimator.SetTrigger("Wobble");
    }

    static IEnumerator PopIn(Transform tick)
    {
        tick.gameObject.SetActive(true);
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.35f)
        {
            float overshoot = 1f + 0.35f * Mathf.Sin(t * Mathf.PI) * (1f - t);
            tick.localScale = Vector3.one * Mathf.SmoothStep(0f, 1f, t) * overshoot;
            yield return null;
        }
        tick.localScale = Vector3.one;
    }
}
