using UnityEngine;

public abstract class WindUpTask : WorkshopTask
{
    public int windsNeeded = 3;
    public Transform windTarget;
    public float windRange = 2f;

    protected int Winds { get; private set; }
    protected bool AcceptingWinds { get; set; }

    static readonly string[] k_Counts = { "One!", "Two!", "Three!", "Four!", "Five!" };
    float m_TooFarSaidAt = -10f;

    protected override void OnBegin()
    {
        Flow.Gestures.GestureRecognized += OnGesture;
        OnTaskBegin();
    }

    protected abstract void OnTaskBegin();
    protected virtual void OnWind(int count) { }
    protected abstract void OnWound();

    void OnGesture(string gesture, float confidence)
    {
        if (!AcceptingWinds || gesture != "Wind Up")
            return;

        if (!PlayerIsNear(windTarget, windRange))
        {
            if (Time.time - m_TooFarSaidAt > 5f)
            {
                Flow.toymaker.Say("Good winding! Stand a little closer to the toy, though.", 3f);
                m_TooFarSaidAt = Time.time;
            }
            return;
        }

        Winds++;
        Flow.Log($"Wind {Winds}/{windsNeeded} ({title})");
        Sounds.Play(s => s.wind, windTarget.position);
        if (Winds <= k_Counts.Length)
            Flow.toymaker.Say(k_Counts[Winds - 1], 1.2f);
        OnWind(Winds);

        if (Winds >= windsNeeded)
        {
            AcceptingWinds = false;
            Flow.Gestures.GestureRecognized -= OnGesture;
            OnWound();
        }
    }

    protected virtual void OnDestroy()
    {
        if (Flow != null && Flow.Gestures != null)
            Flow.Gestures.GestureRecognized -= OnGesture;
    }
}
