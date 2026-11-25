using System.Collections;
using System.Linq;
using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit;
using UnityEngine.XR.Interaction.Toolkit.Interactors;

public class JackInTheBoxTask : WindUpTask
{
    public Animator animator;
    public ToyRepair repair;
    public ToyPart[] parts;

    static readonly int k_CrankState = Animator.StringToHash("Crank");
    float m_CrankTurn;

    protected override void OnTaskBegin()
    {
        foreach (var part in parts)
            part.Grab.selectEntered.AddListener(OnPartGrabbed);
        foreach (var socket in repair.sockets)
            socket.selectEntered.AddListener(_ => PointAtNextPart());
        repair.onRepaired.AddListener(OnRepaired);
        if (repair.IsRepaired)
            OnRepaired();
        else
            PointAtNextPart();
    }

    void OnPartGrabbed(SelectEnterEventArgs args)
    {
        if (!(args.interactorObject is XRSocketInteractor) && !repair.IsRepaired)
            PointAt(windTarget);
    }

    void PointAtNextPart()
    {
        if (repair.IsRepaired)
            return;
        var next = parts.FirstOrDefault(p => !p.Grab.interactorsSelecting.Any(i => i is XRSocketInteractor));
        PointAt(next != null ? next.transform : windTarget);
    }

    void OnRepaired()
    {
        if (AcceptingWinds || Winds > 0)
            return;
        SocketLock.LockFittedParts(repair.sockets);
        AcceptingWinds = true;
        PointAt(windTarget);
        Flow.toymaker.Say("He's all in one piece again! Now wind his crank: three circles with your hand.", 5f);
    }

    protected override void OnWind(int count) => StartCoroutine(TurnCrank(count / (float)windsNeeded));

    // the Crank clip sits at speed 0, so each wind just scrubs it a third of the way round
    IEnumerator TurnCrank(float to)
    {
        if (m_CrankTurn == 0f)
        {
            animator.CrossFade(k_CrankState, 0.35f, 0, 0f);
            yield return new WaitForSeconds(0.35f);
        }
        float from = m_CrankTurn;
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.45f)
        {
            m_CrankTurn = Mathf.Lerp(from, to, Mathf.SmoothStep(0f, 1f, t));
            animator.Play(k_CrankState, 0, m_CrankTurn % 1f);
            yield return null;
        }
        m_CrankTurn = to;
    }

    protected override void OnWound() => StartCoroutine(Pop());

    IEnumerator Pop()
    {
        yield return new WaitForSeconds(0.9f);
        PopOut();
        Flow.toymaker.Say("Pop goes the jester! Ha ha!", 3f);
        yield return new WaitForSeconds(1.6f);
        Complete();
    }

    void PopOut()
    {
        animator.SetTrigger("Pop");
        Sounds.Play(s => s.boing, windTarget.position);
    }

    public override void PerformFinale() => PopOut();
}
