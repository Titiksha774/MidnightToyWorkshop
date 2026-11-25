using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit;
using UnityEngine.XR.Interaction.Toolkit.Interactables;
using UnityEngine.XR.Interaction.Toolkit.Interactors;

public class PartSocket : XRSocketInteractor
{
    public string partId;

    public bool IsFilled => hasSelection;

    public override bool CanHover(IXRHoverInteractable interactable) => base.CanHover(interactable) && Matches(interactable);

    public override bool CanSelect(IXRSelectInteractable interactable) => base.CanSelect(interactable) && Matches(interactable);

    protected override void OnSelectEntered(SelectEnterEventArgs args)
    {
        base.OnSelectEntered(args);
        Sounds.Play(s => s.snap, transform.position, 0.8f, Random.Range(0.95f, 1.1f));
    }

    bool Matches(IXRInteractable interactable)
    {
        var part = interactable.transform.GetComponent<ToyPart>();
        return part != null && part.partId == partId;
    }
}
