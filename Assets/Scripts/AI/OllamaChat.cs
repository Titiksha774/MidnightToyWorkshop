using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

public class OllamaChat : MonoBehaviour
{
    public string baseUrl = "http://localhost:11434";
    public string model = "llama3.2";
    public bool cpuOnly = true;
    public int maxTokens = 70;
    public int timeoutSeconds = 25;

    public bool IsAvailable { get; private set; }

    IEnumerator Start()
    {
        using (var request = UnityWebRequest.Get(baseUrl + "/api/tags"))
        {
            request.timeout = 3;
            yield return request.SendWebRequest();
            IsAvailable = request.result == UnityWebRequest.Result.Success && request.downloadHandler.text.Contains(model);
        }
        Debug.Log(IsAvailable
            ? $"Ollama: {model} found, the toymaker will answer with AI."
            : $"Ollama: not running or {model} not installed, the toymaker will use his built-in hints.");

        // load the model now so the first real question doesn't have to wait for it
        if (IsAvailable)
            yield return Send("You are warming up.", "Say ok.", _ => { }, _ => { });
    }

    public IEnumerator Send(string system, string user, Action<string> onReply, Action<string> onError)
    {
        if (!IsAvailable)
        {
            onError("Ollama is not available");
            yield break;
        }

        var body = new ChatRequest
        {
            model = model,
            stream = false,
            keep_alive = "20m",
            messages = new[]
            {
                new ChatMessage { role = "system", content = system },
                new ChatMessage { role = "user", content = user },
            },
            // num_gpu 0 keeps the model on the CPU so VR gets the whole GPU
            options = new ChatOptions { num_predict = maxTokens, temperature = 0.7f, num_gpu = cpuOnly ? 0 : 999 },
        };

        using (var request = new UnityWebRequest(baseUrl + "/api/chat", "POST"))
        {
            request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(JsonUtility.ToJson(body)));
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            request.timeout = timeoutSeconds;
            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                onError(request.error);
                yield break;
            }
            var reply = JsonUtility.FromJson<ChatResponse>(request.downloadHandler.text)?.message?.content;
            if (string.IsNullOrWhiteSpace(reply))
                onError("empty reply");
            else
                onReply(reply.Trim());
        }
    }

    [Serializable] class ChatMessage { public string role, content; }
    [Serializable] class ChatOptions { public int num_predict; public float temperature; public int num_gpu; }
    [Serializable] class ChatRequest { public string model; public ChatMessage[] messages; public bool stream; public string keep_alive; public ChatOptions options; }
    [Serializable] class ChatResponse { public ChatMessage message; }
}
