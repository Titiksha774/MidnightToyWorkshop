using System.Collections;
using UnityEngine;

public class TrainTask : WindUpTask
{
    public ToyRepair repair;
    public Animator animator;
    public TrackRunner runner;
    public Transform trackParent;
    public AudioSource chug;

    protected override void OnTaskBegin()
    {
        repair.onRepaired.AddListener(OnRepaired);
        if (repair.IsRepaired)
            OnRepaired();
    }

    void OnRepaired()
    {
        if (AcceptingWinds || Winds > 0)
            return;
        AcceptingWinds = true;
        PointAt(windTarget);
        Flow.toymaker.Say("Every part is back on! Now wind the key: circle your hand three times.", 5f);
    }

    protected override void OnWound()
    {
        SocketLock.LockFittedParts(repair.sockets);
        StartCoroutine(ComeAlive());
    }

    IEnumerator ComeAlive()
    {
        animator.SetTrigger("Drive");
        chug.Play();
        Flow.toymaker.Say("Choo choo! Off it goes!", 3f);

        var train = runner.transform;
        train.SetParent(trackParent, true);
        Vector3 startPos = train.position;
        Quaternion startRot = train.rotation;
        runner.PoseAt(runner.startAngle, out var endPos, out var endRot);
        for (float t = 0f; t < 1f; t += Time.deltaTime / 1.4f)
        {
            float eased = Mathf.SmoothStep(0f, 1f, t);
            train.SetPositionAndRotation(Vector3.Lerp(startPos, endPos, eased) + Vector3.up * (Mathf.Sin(t * Mathf.PI) * 0.18f),
                Quaternion.Slerp(startRot, endRot, eased));
            yield return null;
        }
        runner.enabled = true;
        Complete();
    }

    public override void PerformFinale()
    {
        animator.SetTrigger("Whistle");
        Sounds.Play(s => s.whistle, runner.transform.position, 0.7f);
    }
}
