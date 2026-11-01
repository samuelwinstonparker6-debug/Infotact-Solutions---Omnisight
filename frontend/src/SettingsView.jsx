import { useState, useEffect } from "react";
import {
  Sun,
  Moon,
  Palette,
  CheckCircle2,
  Trash2,
  RefreshCw,
  Zap,
  AlertCircle,
  Cpu,
  Key,
  GitBranch,
  Globe,
  Save,
  Check,
  Eye,
  EyeOff,
  ShieldCheck,
} from "lucide-react";

const API_BASE = typeof window !== "undefined" && (window.location.port === "5173" || window.location.port === "8000")
  ? "/api/v1"
  : "http://127.0.0.1:8000/api/v1";

const DEFAULT_MODELS = [
  {
    id: "gemini-2.5-flash",
    name: "Google Gemini 2.5 Flash",
    description: "Ultra-fast multimodal vision with sub-second token latency.",
    badge: "Fastest (Sub-10s)",
    cost: "$ / Low Cost",
  },
  {
    id: "gemini-3.8-flash",
    name: "Google Gemini 3.8 Flash (High)",
    description: "State-of-the-art vision reasoning with enhanced spatial accuracy.",
    badge: "Recommended",
    cost: "$$ / High Accuracy",
  },
  {
    id: "gemini-1.5-pro",
    name: "Google Gemini 1.5 Pro",
    description: "Deep multi-turn visual critique and complex layout repair.",
    badge: "Deep Reasoning",
    cost: "$$$ / Heavy Token",
  },
  {
    id: "gpt-4o",
    name: "OpenAI GPT-4o Vision",
    description: "Multi-provider high precision layout and visual defect detection.",
    badge: "Alternative VLM",
    cost: "$$$ / External",
  },
];

export default function SettingsView({ theme, onThemeChange }) {
  const isDark = theme === "dark";

  // System settings state
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [selectedModel, setSelectedModel] = useState("gemini-3.8-flash");
  const [availableModels, setAvailableModels] = useState(DEFAULT_MODELS);
  const [geminiApiKey, setGeminiApiKey] = useState("");
  const [geminiConfigured, setGeminiConfigured] = useState(false);
  const [geminiMasked, setGeminiMasked] = useState("");
  const [showGeminiKey, setShowGeminiKey] = useState(false);

  const [githubToken, setGithubToken] = useState(() => localStorage.getItem("omnisight_github_token") || "");
  const [githubRepo, setGithubRepo] = useState(() => localStorage.getItem("omnisight_github_repo") || "");
  const [githubConfigured, setGithubConfigured] = useState(false);
  const [showGithubToken, setShowGithubToken] = useState(false);

  const [stagingUrl, setStagingUrl] = useState(() => localStorage.getItem("omnisight_target_url") || "http://localhost:8000/mock-app/index.html");

  const [savingSettings, setSavingSettings] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(null);

  // Cache clearing state
  const [clearing, setClearing] = useState(false);
  const [clearResult, setClearResult] = useState(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoadingSettings(true);
    try {
      const res = await fetch(`${API_BASE}/settings`);
      if (res.ok) {
        const data = await res.json();
        if (data.available_models && data.available_models.length > 0) {
          setAvailableModels(data.available_models);
        }
        if (data.gemini_model) {
          setSelectedModel(data.gemini_model);
        }
        setGeminiConfigured(Boolean(data.gemini_configured));
        setGeminiMasked(data.gemini_key_masked || "");
        setGithubConfigured(Boolean(data.github_configured));
        if (data.github_repo) setGithubRepo(data.github_repo);
        if (data.staging_url) setStagingUrl(data.staging_url);
      }
    } catch {
      // Fallback gracefully on local storage
    } finally {
      setLoadingSettings(false);
    }
  };

  const handleSaveSettings = async (overrideModel = null) => {
    setSavingSettings(true);
    setSaveSuccess(null);
    const modelToSave = overrideModel || selectedModel;

    const payload = {
      gemini_model: modelToSave,
      staging_url: stagingUrl.trim(),
    };
    if (geminiApiKey.trim()) {
      payload.gemini_api_key = geminiApiKey.trim();
    }
    if (githubToken.trim()) {
      payload.github_token = githubToken.trim();
    }
    if (githubRepo.trim()) {
      payload.github_repo = githubRepo.trim();
    }

    try {
      const res = await fetch(`${API_BASE}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (res.ok) {
        setGeminiConfigured(Boolean(data.gemini_configured));
        if (data.gemini_key_masked) setGeminiMasked(data.gemini_key_masked);
        setGithubConfigured(Boolean(data.github_configured));

        // Sync with browser localStorage for App.jsx
        if (githubToken.trim()) localStorage.setItem("omnisight_github_token", githubToken.trim());
        if (githubRepo.trim()) localStorage.setItem("omnisight_github_repo", githubRepo.trim());
        if (stagingUrl.trim()) localStorage.setItem("omnisight_target_url", stagingUrl.trim());

        setSaveSuccess({
          success: true,
          message: overrideModel
            ? `Active VLM model switched to ${modelToSave}!`
            : "System credentials & configuration successfully updated!",
        });
      } else {
        setSaveSuccess({
          success: false,
          message: data.detail || "Failed to update system settings.",
        });
      }
    } catch (err) {
      setSaveSuccess({
        success: false,
        message: err.message || "Network error while saving settings.",
      });
    } finally {
      setSavingSettings(false);
      setTimeout(() => setSaveSuccess(null), 4000);
    }
  };

  const handleModelSelect = (modelId) => {
    setSelectedModel(modelId);
    handleSaveSettings(modelId);
  };

  const handleClearCache = async () => {
    if (clearing) return;
    setClearing(true);
    setClearResult(null);
    try {
      const res = await fetch(`${API_BASE}/system/clear-cache`, {
        method: "POST",
      });
      const data = await res.json();

      if (typeof window !== "undefined") {
        try {
          if (window.performance && window.performance.clearResourceTimings) {
            window.performance.clearResourceTimings();
          }
          sessionStorage.clear();
          const targetUrlVal = localStorage.getItem("omnisight_target_url");
          const savedTheme = localStorage.getItem("omnisight_theme");
          const ghToken = localStorage.getItem("omnisight_github_token");
          const ghRepoVal = localStorage.getItem("omnisight_github_repo");
          localStorage.clear();
          if (targetUrlVal) localStorage.setItem("omnisight_target_url", targetUrlVal);
          if (savedTheme) localStorage.setItem("omnisight_theme", savedTheme);
          if (ghToken) localStorage.setItem("omnisight_github_token", ghToken);
          if (ghRepoVal) localStorage.setItem("omnisight_github_repo", ghRepoVal);
        } catch {
          // ignore storage clearing limitations
        }
      }

      setClearResult({
        success: true,
        message: data.message || "Cache and temporary files cleared successfully!",
        freedKb: data.freed_kb || 0,
        cleanedCount: data.cleaned_items_count || 0,
      });
    } catch (err) {
      setClearResult({
        success: false,
        message: err.message || "Failed to clear system cache.",
      });
    } finally {
      setClearing(false);
    }
  };

  return (
    <div style={{ maxWidth: "1000px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "2rem" }}>
      {/* ── Page Header Banner ── */}
      <div
        className="glass-panel"
        style={{
          padding: "2rem 2.5rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: isDark
            ? "linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(22, 25, 37, 0.8))"
            : "linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(255, 255, 255, 0.9))",
          borderRadius: "16px",
          border: "1px solid var(--border-glass)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "0.5rem" }}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                width: "38px",
                height: "38px",
                borderRadius: "10px",
                background: "rgba(99, 102, 241, 0.2)",
                color: "var(--accent-primary)",
              }}
            >
              <Cpu size={22} />
            </span>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>
              OmniSight System Settings & Models
            </h2>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.92rem", maxWidth: "600px" }}>
            Configure active Vision-Language Models, API credentials, target deployment repositories, and UI visual preferences.
          </p>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", alignItems: "flex-end" }}>
          <div
            style={{
              padding: "0.45rem 0.9rem",
              borderRadius: "9999px",
              background: geminiConfigured ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
              border: `1px solid ${geminiConfigured ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
              color: geminiConfigured ? "#34d399" : "#f87171",
              fontSize: "0.8rem",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
            }}
          >
            {geminiConfigured ? <ShieldCheck size={14} /> : <AlertCircle size={14} />}
            <span>{geminiConfigured ? "Gemini VLM Active" : "Gemini Key Missing"}</span>
          </div>
        </div>
      </div>

      {/* ── Save Notification Toast ── */}
      {saveSuccess && (
        <div
          className="animate-fade-in"
          style={{
            padding: "1rem 1.5rem",
            borderRadius: "12px",
            fontSize: "0.88rem",
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            background: saveSuccess.success ? "rgba(16, 185, 129, 0.12)" : "rgba(239, 68, 68, 0.12)",
            border: `1px solid ${saveSuccess.success ? "rgba(16, 185, 129, 0.35)" : "rgba(239, 68, 68, 0.35)"}`,
            color: saveSuccess.success ? "#34d399" : "#f87171",
          }}
        >
          {saveSuccess.success ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          <span style={{ fontWeight: 500 }}>{saveSuccess.message}</span>
        </div>
      )}

      {/* ── VLM Model Selector Section (Day 13 Requirement) ── */}
      <div
        className="glass-panel"
        style={{
          padding: "2.25rem",
          display: "flex",
          flexDirection: "column",
          gap: "1.5rem",
          borderRadius: "16px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.55rem", marginBottom: "0.35rem" }}>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "32px",
                  height: "32px",
                  borderRadius: "8px",
                  background: "rgba(99, 102, 241, 0.15)",
                  color: "var(--accent-primary)",
                }}
              >
                <Cpu size={18} />
              </span>
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)" }}>
                Vision-Language Model (VLM) Selector
              </h3>
            </div>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem", maxWidth: "620px" }}>
              Choose the multimodal vision intelligence engine that inspects multi-viewport screenshots and synthesizes self-healing CSS fixes.
            </p>
          </div>
          <span
            style={{
              padding: "0.35rem 0.85rem",
              borderRadius: "9999px",
              background: "rgba(99, 102, 241, 0.15)",
              color: "var(--accent-primary)",
              fontWeight: 600,
              fontSize: "0.78rem",
            }}
          >
            ACTIVE: {selectedModel}
          </span>
        </div>

        {/* Model Selection Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
          {availableModels.map((m) => {
            const isSelected = selectedModel === m.id;
            return (
              <div
                key={m.id}
                onClick={() => handleModelSelect(m.id)}
                style={{
                  cursor: "pointer",
                  padding: "1.25rem",
                  borderRadius: "12px",
                  background: isSelected
                    ? isDark ? "rgba(99, 102, 241, 0.15)" : "rgba(99, 102, 241, 0.08)"
                    : isDark ? "rgba(255, 255, 255, 0.02)" : "rgba(0, 0, 0, 0.02)",
                  border: isSelected ? "2px solid var(--accent-primary)" : "1px solid var(--border-glass)",
                  boxShadow: isSelected ? "0 0 16px rgba(99, 102, 241, 0.25)" : "none",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.65rem",
                  transition: "all 0.2s ease",
                  position: "relative",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span
                    style={{
                      fontSize: "0.72rem",
                      fontWeight: 600,
                      padding: "0.15rem 0.55rem",
                      borderRadius: "6px",
                      background: isSelected ? "var(--accent-primary)" : "rgba(255,255,255,0.08)",
                      color: isSelected ? "#ffffff" : "var(--text-muted)",
                    }}
                  >
                    {m.badge || "VLM"}
                  </span>
                  {isSelected && <CheckCircle2 size={16} color="var(--accent-primary)" />}
                </div>

                <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--text-primary)" }}>
                  {m.name}
                </div>

                <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.4, flexGrow: 1 }}>
                  {m.description}
                </div>

                <div style={{ paddingTop: "0.5rem", borderTop: "1px solid var(--border-glass)", fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 500 }}>
                  {m.cost || "Standard Tier"}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── API Credentials & Integration Management Card ── */}
      <div
        className="glass-panel"
        style={{
          padding: "2.25rem",
          display: "flex",
          flexDirection: "column",
          gap: "1.75rem",
          borderRadius: "16px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.55rem", marginBottom: "0.35rem" }}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                width: "32px",
                height: "32px",
                borderRadius: "8px",
                background: "rgba(16, 185, 129, 0.15)",
                color: "#10b981",
              }}
            >
              <Key size={18} />
            </span>
            <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)" }}>
              API Credentials & Repository Integration
            </h3>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem" }}>
            Credentials are securely persisted directly to the backend <code style={{ color: "var(--accent-primary)" }}>.env</code> file.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.5rem" }}>
          {/* Gemini API Key */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)", display: "flex", justifyContent: "space-between" }}>
              <span>Google Gemini API Key</span>
              {geminiConfigured && (
                <span style={{ fontSize: "0.75rem", color: "#34d399", fontWeight: 500 }}>
                  Active ({geminiMasked})
                </span>
              )}
            </label>
            <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
              <input
                type={showGeminiKey ? "text" : "password"}
                value={geminiApiKey}
                onChange={(e) => setGeminiApiKey(e.target.value)}
                placeholder={geminiConfigured ? "Update API Key (AIza...)" : "Enter Gemini API Key..."}
                style={{
                  width: "100%",
                  padding: "0.75rem 2.8rem 0.75rem 1rem",
                  borderRadius: "10px",
                  background: isDark ? "rgba(0, 0, 0, 0.3)" : "#ffffff",
                  border: "1px solid var(--border-glass)",
                  color: "var(--text-primary)",
                  fontSize: "0.88rem",
                  outline: "none",
                }}
              />
              <button
                type="button"
                onClick={() => setShowGeminiKey(!showGeminiKey)}
                style={{
                  position: "absolute",
                  right: "10px",
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                }}
              >
                {showGeminiKey ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Powers multi-viewport layout analysis and Tailwind CSS synthesis.
            </span>
          </div>

          {/* GitHub Access Token */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)", display: "flex", justifyContent: "space-between" }}>
              <span>GitHub Personal Access Token (PAT)</span>
              {githubConfigured && (
                <span style={{ fontSize: "0.75rem", color: "#34d399", fontWeight: 500 }}>
                  Configured
                </span>
              )}
            </label>
            <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
              <input
                type={showGithubToken ? "text" : "password"}
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder="ghp_yourPersonalAccessToken..."
                style={{
                  width: "100%",
                  padding: "0.75rem 2.8rem 0.75rem 1rem",
                  borderRadius: "10px",
                  background: isDark ? "rgba(0, 0, 0, 0.3)" : "#ffffff",
                  border: "1px solid var(--border-glass)",
                  color: "var(--text-primary)",
                  fontSize: "0.88rem",
                  outline: "none",
                }}
              />
              <button
                type="button"
                onClick={() => setShowGithubToken(!showGithubToken)}
                style={{
                  position: "absolute",
                  right: "10px",
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                }}
              >
                {showGithubToken ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Requires <code style={{ color: "var(--accent-primary)" }}>repo</code> scope to create branches and publish Pull Requests.
            </span>
          </div>

          {/* GitHub Target Repository */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <GitBranch size={15} />
              <span>Default GitHub Target Repo</span>
            </label>
            <input
              type="text"
              value={githubRepo}
              onChange={(e) => setGithubRepo(e.target.value)}
              placeholder="e.g. samuelwinstonparker6-debug/omnisight"
              style={{
                width: "100%",
                padding: "0.75rem 1rem",
                borderRadius: "10px",
                background: isDark ? "rgba(0, 0, 0, 0.3)" : "#ffffff",
                border: "1px solid var(--border-glass)",
                color: "var(--text-primary)",
                fontSize: "0.88rem",
                outline: "none",
              }}
            />
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Format: <code style={{ color: "var(--text-secondary)" }}>owner/repository</code>
            </span>
          </div>

          {/* Default Staging URL */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <Globe size={15} />
              <span>Default Target Staging URL</span>
            </label>
            <input
              type="text"
              value={stagingUrl}
              onChange={(e) => setStagingUrl(e.target.value)}
              placeholder="http://localhost:8000/mock-app/index.html"
              style={{
                width: "100%",
                padding: "0.75rem 1rem",
                borderRadius: "10px",
                background: isDark ? "rgba(0, 0, 0, 0.3)" : "#ffffff",
                border: "1px solid var(--border-glass)",
                color: "var(--text-primary)",
                fontSize: "0.88rem",
                outline: "none",
              }}
            />
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              The URL loaded by default in dashboard scans and testbench runs.
            </span>
          </div>
        </div>

        {/* Save Button */}
        <div style={{ display: "flex", justifyContent: "flex-end", paddingTop: "0.5rem" }}>
          <button
            onClick={() => handleSaveSettings()}
            disabled={savingSettings}
            className="btn"
            style={{
              padding: "0.75rem 1.75rem",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #6366f1, #4f46e5)",
              color: "#ffffff",
              fontWeight: 600,
              fontSize: "0.9rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              cursor: savingSettings ? "not-allowed" : "pointer",
              boxShadow: "0 4px 14px rgba(99, 102, 241, 0.35)",
              border: "none",
            }}
          >
            {savingSettings ? <RefreshCw size={17} className="animate-spin" /> : <Save size={17} />}
            <span>Save Configuration</span>
          </button>
        </div>
      </div>

      {/* ── Theme Mode Card ── */}
      <div
        className="glass-panel"
        style={{
          padding: "2.25rem",
          display: "flex",
          flexDirection: "column",
          gap: "1.75rem",
          borderRadius: "16px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.55rem", marginBottom: "0.35rem" }}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                width: "32px",
                height: "32px",
                borderRadius: "8px",
                background: "rgba(245, 158, 11, 0.15)",
                color: "#f59e0b",
              }}
            >
              <Palette size={18} />
            </span>
            <h3 style={{ fontSize: "1.2rem", fontWeight: 600, color: "var(--text-primary)" }}>
              Appearance & Theme
            </h3>
          </div>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
            Instantaneous theme switching across all dashboard views.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "1.25rem 1.75rem",
            background: isDark ? "rgba(0, 0, 0, 0.3)" : "rgba(0, 0, 0, 0.03)",
            borderRadius: "14px",
            border: "1px solid var(--border-glass)",
            flexWrap: "wrap",
            gap: "1.25rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <div
              onClick={() => onThemeChange("light")}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                cursor: "pointer",
                padding: "0.5rem 0.85rem",
                borderRadius: "8px",
                transition: "all 0.2s ease",
                background: !isDark ? "rgba(245, 158, 11, 0.15)" : "transparent",
                color: !isDark ? "#d97706" : "var(--text-muted)",
                fontWeight: !isDark ? 600 : 500,
              }}
            >
              <Sun size={18} />
              <span>Light Mode</span>
            </div>

            <button
              type="button"
              role="switch"
              aria-checked={isDark}
              aria-label="Toggle theme mode"
              onClick={() => onThemeChange(isDark ? "light" : "dark")}
              style={{
                position: "relative",
                width: "82px",
                height: "42px",
                borderRadius: "9999px",
                border: isDark ? "2px solid #6366f1" : "2px solid #f59e0b",
                background: isDark
                  ? "linear-gradient(135deg, #1e1b4b, #312e81)"
                  : "linear-gradient(135deg, #fef3c7, #fde68a)",
                cursor: "pointer",
                padding: 0,
                outline: "none",
                transition: "all 0.25s ease",
                boxShadow: isDark
                  ? "0 0 16px rgba(99, 102, 241, 0.4), inset 0 2px 4px rgba(0,0,0,0.5)"
                  : "0 0 16px rgba(245, 158, 11, 0.4), inset 0 2px 4px rgba(255,255,255,0.7)",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  top: "3px",
                  left: isDark ? "43px" : "3px",
                  width: "32px",
                  height: "32px",
                  borderRadius: "50%",
                  background: isDark
                    ? "linear-gradient(135deg, #6366f1, #4f46e5)"
                    : "linear-gradient(135deg, #fbbf24, #f59e0b)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#ffffff",
                  transition: "left 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)",
                }}
              >
                {isDark ? <Moon size={16} /> : <Sun size={17} />}
              </div>
            </button>

            <div
              onClick={() => onThemeChange("dark")}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                cursor: "pointer",
                padding: "0.5rem 0.85rem",
                borderRadius: "8px",
                transition: "all 0.2s ease",
                background: isDark ? "rgba(99, 102, 241, 0.15)" : "transparent",
                color: isDark ? "#818cf8" : "var(--text-muted)",
                fontWeight: isDark ? 600 : 500,
              }}
            >
              <Moon size={18} />
              <span>Dark Mode</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Clear Cache & System Optimization Section ── */}
      <div
        className="glass-panel"
        style={{
          padding: "2rem 2.25rem",
          display: "flex",
          flexDirection: "column",
          gap: "1.25rem",
          borderRadius: "16px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.55rem", marginBottom: "0.35rem" }}>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "30px",
                  height: "30px",
                  borderRadius: "8px",
                  background: "rgba(239, 68, 68, 0.15)",
                  color: "#ef4444",
                }}
              >
                <Trash2 size={16} />
              </span>
              <h3 style={{ fontSize: "1.15rem", fontWeight: 600, color: "var(--text-primary)" }}>
                Clear Temporary Files & Cache
              </h3>
            </div>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", maxWidth: "620px" }}>
              Purges temporary viewport screenshots, fixed code patches, server logs, browser resource timings, and Python bytecode caches.
            </p>
          </div>

          <button
            onClick={handleClearCache}
            disabled={clearing}
            className="btn"
            style={{
              padding: "0.7rem 1.4rem",
              borderRadius: "10px",
              background: isDark
                ? "linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.35))"
                : "linear-gradient(135deg, #fee2e2, #fecaca)",
              border: "1px solid rgba(239, 68, 68, 0.4)",
              color: isDark ? "#fca5a5" : "#b91c1c",
              fontWeight: 600,
              fontSize: "0.875rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              cursor: clearing ? "not-allowed" : "pointer",
              transition: "all 0.2s ease",
            }}
          >
            {clearing ? (
              <>
                <RefreshCw size={16} className="animate-spin" />
                <span>Purging Cache...</span>
              </>
            ) : (
              <>
                <Zap size={16} />
                <span>Clear Cache Now</span>
              </>
            )}
          </button>
        </div>

        {/* Clear Result Feedback Message */}
        {clearResult && (
          <div
            className="animate-fade-in"
            style={{
              padding: "0.9rem 1.25rem",
              borderRadius: "10px",
              fontSize: "0.85rem",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "1rem",
              background: clearResult.success ? "rgba(16, 185, 129, 0.12)" : "rgba(239, 68, 68, 0.12)",
              border: `1px solid ${clearResult.success ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
              color: clearResult.success ? "#34d399" : "#f87171",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
              {clearResult.success ? <CheckCircle2 size={16} color="#34d399" /> : <AlertCircle size={16} color="#f87171" />}
              <span>{clearResult.message}</span>
            </div>

            {clearResult.success && clearResult.cleanedCount > 0 && (
              <span
                style={{
                  fontSize: "0.75rem",
                  padding: "0.2rem 0.6rem",
                  borderRadius: "9999px",
                  background: "rgba(16, 185, 129, 0.2)",
                  fontWeight: 600,
                }}
              >
                Freed {clearResult.freedKb} KB ({clearResult.cleanedCount} items removed)
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
