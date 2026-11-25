using Unity.Burst;
using UnityEditor;
using UnityEngine;

[InitializeOnLoad]
static class DisableBurstInEditor
{
    static DisableBurstInEditor()
    {
        if (BurstCompiler.Options.EnableBurstCompilation)
        {
            BurstCompiler.Options.EnableBurstCompilation = false;
            Debug.Log("Burst compilation disabled for this project (Windows blocks Burst's DLLs on this PC).");
        }
    }
}
