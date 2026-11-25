using System;
using UnityEngine;

public abstract class WorkshopTask : MonoBehaviour
{
    public string title;
    [TextArea(2, 4)] public string introLine;
    [TextArea(2, 4)] public string hint;
    [TextArea(2, 4)] public string howItWorks;
    public float clockTime = 23.25f;
    public Transform beaconTarget;

    public bool IsActive { get; private set; }
    public bool IsDone { get; private set; }
    public event Action<WorkshopTask> Completed;

    protected GameFlow Flow { get; private set; }

    public void Begin(GameFlow flow)
    {
        Flow = flow;
        IsActive = true;
        Flow.Log($"Task start: {title}");
        OnBegin();
    }

    protected abstract void OnBegin();

    public virtual void PerformFinale() { }

    protected void Complete()
    {
        if (IsDone)
            return;
        IsDone = true;
        IsActive = false;
        Flow.Log($"Task done: {title}");
        Completed?.Invoke(this);
    }

    protected void PointAt(Transform target)
    {
        beaconTarget = target;
        Flow.Beacon.Follow(target);
    }

    protected bool PlayerIsNear(Transform target, float metres)
    {
        var offset = target.position - Flow.Head.position;
        offset.y = 0f;
        return offset.sqrMagnitude <= metres * metres;
    }
}
