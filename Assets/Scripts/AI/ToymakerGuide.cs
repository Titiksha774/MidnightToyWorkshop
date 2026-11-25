using System.Collections;
using System.Linq;
using TMPro;
using UnityEngine;

public class ToymakerGuide : MonoBehaviour
{
    public GameFlow game;
    public OllamaChat ai;
    public Animator animator;

    public CanvasGroup bubble;
    public TMP_Text bubbleText;
    public Transform head;

    public CanvasGroup hintPanel;
    public float panelDistance = 2.2f;

    [TextArea(3, 6)]
    public string persona =
        "You are Tobias, a kind old toymaker in a cosy workshop at night. A visitor is helping you repair wind-up toys " +
        "before midnight. Answer in at most two short, warm sentences that suit all ages. Never use lists or emojis.";

    public int HintsAsked { get; private set; }

    enum Question { WhatNext, HowItWorks, AboutToy }

    Coroutine m_Speech;
    bool m_Thinking;

    void Start()
    {
        bubble.alpha = 0f;
        hintPanel.alpha = 0f;
        hintPanel.blocksRaycasts = false;
    }

    public void Say(string text, float seconds = 0f)
    {
        if (m_Speech != null)
            StopCoroutine(m_Speech);
        m_Speech = StartCoroutine(Speak(text, seconds > 0f ? seconds : 2.5f + text.Length * 0.055f));
    }

    IEnumerator Speak(string text, float seconds)
    {
        bubbleText.text = text;
        animator.SetTrigger("Talk");
        Sounds.Play(s => s.babble, bubble.transform.position, 0.5f, Random.Range(0.9f, 1.15f));
        yield return FadeBubble(1f);
        yield return new WaitForSeconds(seconds);
        yield return FadeBubble(0f);
        m_Speech = null;
    }

    IEnumerator FadeBubble(float to)
    {
        float from = bubble.alpha;
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.2f)
        {
            bubble.alpha = Mathf.Lerp(from, to, t);
            yield return null;
        }
        bubble.alpha = to;
    }

    public void Wave() => animator.SetTrigger("Wave");
    public void Celebrate() => animator.SetTrigger("Celebrate");

    public void AskWhatNext() => Ask(Question.WhatNext);
    public void AskHowItWorks() => Ask(Question.HowItWorks);
    public void AskAboutToy() => Ask(Question.AboutToy);

    void Ask(Question question)
    {
        if (m_Thinking)
            return;
        var task = game.CurrentTask;
        if (task == null)
        {
            Say(game.Current == GameFlow.State.Menu ? "Press Play when you're ready!" : "Everything is fixed. What a night!");
            return;
        }
        HintsAsked++;
        game.Log($"Hint asked: {question} ({task.title})");
        StartCoroutine(Answer(question, task));
    }

    IEnumerator Answer(Question question, WorkshopTask task)
    {
        string fallback = question switch
        {
            Question.WhatNext => task.hint,
            Question.HowItWorks => task.howItWorks,
            _ => $"{task.howItWorks} I made it many years ago, and it's still one of my favourites.",
        };
        if (!ai.IsAvailable)
        {
            Say(fallback);
            yield break;
        }

        m_Thinking = true;
        Say("Hmm, let me think...", 30f);
        string reply = null;
        yield return ai.Send(persona, Prompt(question, task), r => reply = r, _ => { });
        m_Thinking = false;
        Say(string.IsNullOrEmpty(reply) ? fallback : reply);
    }

    // tell the AI what's been done so far, so the hint actually fits
    string Prompt(Question question, WorkshopTask task)
    {
        var done = game.tasks.Where(t => t.IsDone).Select(t => t.title).ToArray();
        string progress = done.Length == 0 ? "Nothing is fixed yet." : "Already done: " + string.Join(", ", done) + ".";
        string ask = question switch
        {
            Question.WhatNext => $"The visitor asks what to do next. Give a friendly hint based on these facts, without adding new steps: {task.hint}",
            Question.HowItWorks => $"The visitor asks how this toy works. Explain the real mechanism simply, using these facts: {task.howItWorks}",
            _ => $"The visitor asks about this toy. Tell a tiny, charming story about it, mentioning how it works: {task.howItWorks}",
        };
        return $"Current job: {task.title}. {progress} {ask}";
    }

    void LateUpdate()
    {
        var bubbleTransform = bubble.transform;
        var toHead = bubbleTransform.position - head.position;
        toHead.y = 0f;
        if (toHead.sqrMagnitude > 0.0001f)
            bubbleTransform.rotation = Quaternion.LookRotation(toHead);

        var offset = hintPanel.transform.position - head.position;
        offset.y = 0f;
        bool near = offset.magnitude < panelDistance && game.Current == GameFlow.State.Playing;
        hintPanel.alpha = Mathf.MoveTowards(hintPanel.alpha, near ? 1f : 0f, Time.deltaTime * 4f);
        hintPanel.blocksRaycasts = hintPanel.interactable = hintPanel.alpha > 0.5f;
    }
}
