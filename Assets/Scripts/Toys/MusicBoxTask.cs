using System.Collections;
using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit;
using UnityEngine.XR.Interaction.Toolkit.Interactors;

public class MusicBoxTask : WindUpTask
{
    public ToyPart crank;
    public PartSocket crankSocket;
    public Animator animator;
    public AudioSource tune;

    protected override void OnTaskBegin()
    {
        crank.Grab.enabled = true;
        crank.Grab.selectEntered.AddListener(OnCrankGrabbed);
        crankSocket.selectEntered.AddListener(OnCrankFitted);
    }

    void OnCrankGrabbed(SelectEnterEventArgs args)
    {
        if (!(args.interactorObject is XRSocketInteractor) && !crankSocket.IsFilled)
            PointAt(windTarget);
    }

    void OnCrankFitted(SelectEnterEventArgs args)
    {
        crankSocket.selectEntered.RemoveListener(OnCrankFitted);
        SocketLock.LockFittedParts(new[] { crankSocket });
        AcceptingWinds = true;
        Flow.toymaker.Say("Perfect fit! Now wind it up: three circles with your hand.", 4f);
    }

    protected override void OnWound() => StartCoroutine(PlayTune());

    IEnumerator PlayTune()
    {
        animator.SetTrigger("Open");
        yield return new WaitForSeconds(0.6f);
        tune.Play();
        yield return new WaitForSeconds(1.2f);
        Complete();
    }

    public override void PerformFinale()
    {
        if (!tune.isPlaying)
            tune.Play();
    }
}
