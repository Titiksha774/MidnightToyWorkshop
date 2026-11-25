using System.Collections.Generic;
using UnityEngine.XR.Interaction.Toolkit.Filtering;
using UnityEngine.XR.Interaction.Toolkit.Interactables;
using UnityEngine.XR.Interaction.Toolkit.Interactors;

// while locked only sockets can hold things, hands can't
public class SocketLock : IXRSelectFilter, IXRHoverFilter
{
    public bool locked;

    public bool canProcess => true;

    public bool Process(IXRSelectInteractor interactor, IXRSelectInteractable interactable) => !locked || interactor is XRSocketInteractor;

    public bool Process(IXRHoverInteractor interactor, IXRHoverInteractable interactable) => !locked || interactor is XRSocketInteractor;

    public static void LockFittedParts(IEnumerable<PartSocket> sockets)
    {
        foreach (var socket in sockets)
        {
            foreach (var interactable in socket.interactablesSelected)
            {
                if (interactable is XRBaseInteractable part)
                    part.selectFilters.Add(new SocketLock { locked = true });
            }
        }
    }
}
