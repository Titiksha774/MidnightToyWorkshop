using System.Collections;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;

public class MenuSystem : MonoBehaviour
{
    public GameFlow game;
    public HeadFollow follow;
    public CanvasGroup canvasGroup;
    public Sounds sounds;

    public GameObject startPanel;
    public GameObject pausePanel;
    public GameObject controlsPanel;
    public GameObject creditsPanel;
    public GameObject endPanel;
    public TMP_Text endSummary;

    InputAction m_PauseAction;
    GameObject m_Current;
    GameObject m_Previous;
    Coroutine m_Fade;
    bool m_Paused;

    void Awake()
    {
        m_PauseAction = new InputAction("Pause", InputActionType.Button);
        m_PauseAction.AddBinding("<XRController>{LeftHand}/{MenuButton}");
        m_PauseAction.AddBinding("<Keyboard>/escape");
        m_PauseAction.AddBinding("<Keyboard>/p");
        m_PauseAction.performed += _ => TogglePause();
    }

    void OnEnable() => m_PauseAction.Enable();

    void OnDisable()
    {
        m_PauseAction.Disable();
        SetPaused(false);
    }

    void OnDestroy() => m_PauseAction.Dispose();

    public void ShowStart() => Show(startPanel);

    public void HideAll() => Show(null);

    public void ShowEnd(int done, int total, float seconds, int hints)
    {
        endSummary.text =
            $"Toys repaired  <b>{done} / {total}</b>\n" +
            $"Time  <b>{Mathf.FloorToInt(seconds / 60f)}:{Mathf.FloorToInt(seconds % 60f):00}</b>\n" +
            $"Hints asked  <b>{hints}</b>";
        Show(endPanel);
    }

    void Show(GameObject panel)
    {
        foreach (var p in new[] { startPanel, pausePanel, controlsPanel, creditsPanel, endPanel })
            p.SetActive(p == panel);

        bool opening = panel != null && m_Current == null;
        m_Current = panel;
        game.SetMenuOpen(panel != null);
        if (opening)
        {
            follow.SnapInFront();
            sounds.PlayWhoosh();
        }

        if (m_Fade != null)
            StopCoroutine(m_Fade);
        m_Fade = StartCoroutine(Fade(panel != null));
    }

    IEnumerator Fade(bool visible)
    {
        canvasGroup.blocksRaycasts = canvasGroup.interactable = visible;
        if (visible)
            canvasGroup.gameObject.SetActive(true);
        float from = canvasGroup.alpha, to = visible ? 1f : 0f;
        for (float t = 0f; t < 1f; t += Time.unscaledDeltaTime / 0.25f)
        {
            canvasGroup.alpha = Mathf.Lerp(from, to, t);
            yield return null;
        }
        canvasGroup.alpha = to;
        if (!visible)
            canvasGroup.gameObject.SetActive(false);
    }

    void TogglePause()
    {
        if (game.Current != GameFlow.State.Playing && game.Current != GameFlow.State.Finale)
            return;
        if (m_Paused)
        {
            Resume();
            return;
        }
        SetPaused(true);
        Show(pausePanel);
        game.Log("Pause");
    }

    void SetPaused(bool paused)
    {
        m_Paused = paused;
        Time.timeScale = paused ? 0f : 1f;
        AudioListener.pause = paused;
    }

    public void Play()
    {
        HideAll();
        game.StartGame();
    }

    public void Resume()
    {
        SetPaused(false);
        HideAll();
        game.Log("Resume");
    }

    public void Restart() => Reload(skipMenu: true);

    public void MainMenu() => Reload(skipMenu: false);

    void Reload(bool skipMenu)
    {
        SetPaused(false);
        GameFlow.SkipMenuOnLoad = skipMenu;
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    }

    public void ShowControls() => ShowSubPage(controlsPanel);

    public void ShowCredits() => ShowSubPage(creditsPanel);

    void ShowSubPage(GameObject page)
    {
        m_Previous = m_Current;
        Show(page);
    }

    public void Back() => Show(m_Previous != null ? m_Previous : startPanel);

    public void Quit()
    {
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#else
        Application.Quit();
#endif
    }
}
