using System.Collections.Generic;
using Unity.InferenceEngine;
using UnityEngine;

public class GestureRecognizer : MonoBehaviour
{
    public static readonly string[] Classes = { "Idle", "Swipe Left", "Swipe Right", "Swipe Up", "Swipe Down", "Push", "Wind Up" };

    public ModelAsset modelAsset;
    public Transform controller;
    public Transform head;
    public float window = 0.5f;
    public float interval = 0.1f;
    [Range(0f, 1f)] public float minConfidence = 0.8f;
    public float cooldown = 0.6f;

    public event System.Action<string, float> GestureRecognized;

    Worker m_Worker;
    readonly Queue<(float time, Vector3 position)> m_Samples = new Queue<(float, Vector3)>();
    readonly float[] m_Features = new float[4];
    float m_NextInference;

    void Start()
    {
        m_Worker = new Worker(ModelLoader.Load(modelAsset), BackendType.CPU);
    }

    void Update()
    {
        if (controller == null || head == null)
            return;

        // rig-space positions, so walking or turning the rig doesn't look like a swipe
        float now = Time.time;
        m_Samples.Enqueue((now, controller.localPosition));
        while (m_Samples.Count > 0 && now - m_Samples.Peek().time > window)
            m_Samples.Dequeue();

        if (now < m_NextInference || m_Samples.Count < 2 || now - m_Samples.Peek().time < window * 0.9f)
            return;
        m_NextInference = now + interval;

        int best = Classify(out float confidence);
        if (best != 0 && confidence >= minConfidence)
        {
            GestureRecognized?.Invoke(Classes[best], confidence);
            m_Samples.Clear();
            m_NextInference = now + cooldown;
        }
    }

    int Classify(out float confidence)
    {
        Vector3 first = default, previous = default;
        float pathLength = 0f;
        bool isFirst = true;
        foreach (var sample in m_Samples)
        {
            if (!isFirst)
                pathLength += Vector3.Distance(previous, sample.position);
            else
                first = sample.position;
            previous = sample.position;
            isFirst = false;
        }

        Vector3 worldMove = controller.parent != null ? controller.parent.TransformDirection(previous - first) : previous - first;
        Vector3 local = head.InverseTransformDirection(worldMove);
        m_Features[0] = local.x;
        m_Features[1] = local.y;
        m_Features[2] = local.z;
        m_Features[3] = pathLength;

        using var input = new Tensor<float>(new TensorShape(1, 4), m_Features);
        m_Worker.Schedule(input);
        float[] probabilities = (m_Worker.PeekOutput() as Tensor<float>).DownloadToArray();

        int best = 0;
        for (int i = 1; i < probabilities.Length; i++)
        {
            if (probabilities[i] > probabilities[best])
                best = i;
        }
        confidence = probabilities[best];
        return best;
    }

    void OnDestroy() => m_Worker?.Dispose();
}
