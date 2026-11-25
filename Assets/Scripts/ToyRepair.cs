using System.Linq;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.XR.Interaction.Toolkit;

public class ToyRepair : MonoBehaviour
{
    public string toyName = "Toy";
    public PartSocket[] sockets;
    public InteractionLogger logger;
    public UnityEvent onRepaired;

    public bool IsRepaired { get; private set; }

    void OnEnable()
    {
        foreach (var socket in sockets)
        {
            socket.selectEntered.AddListener(OnPartFitted);
            socket.selectExited.AddListener(OnPartRemoved);
        }
    }

    void OnDisable()
    {
        foreach (var socket in sockets)
        {
            socket.selectEntered.RemoveListener(OnPartFitted);
            socket.selectExited.RemoveListener(OnPartRemoved);
        }
    }

    void OnPartFitted(SelectEnterEventArgs args)
    {
        logger?.Log($"Fitted {args.interactableObject.transform.name}");
        if (!IsRepaired && sockets.All(s => s.IsFilled))
        {
            IsRepaired = true;
            logger?.Log($"Repaired {toyName}");
            onRepaired?.Invoke();
        }
    }

    void OnPartRemoved(SelectExitEventArgs args) => logger?.Log($"Removed {args.interactableObject.transform.name}");
}
