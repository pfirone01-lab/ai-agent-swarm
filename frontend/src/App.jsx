import { useEffect, useRef, useState } from "react";
import "./styles.css";
import PipelineRail from "./PipelineRail.jsx";
import { startRun, fetchRun } from "./api.js";

const PLACEHOLDER = `Write a sales email for a B2B SaaS company selling a project management tool.
Target audience: small business owners and startup founders.
Key benefits: increased team productivity, reduced project delays, affordable pricing.`;

function currentActivity(stages) {
  if (!stages) return null;
  const order = ["generator", "evaluator", "selector", "formatter"];
  for (const key of order) {
    const s = stages[key];
    if (s?.status === "running") return s.detail || `${key[0].toUpperCase()}${key.slice(1)} is working…`;
  }
  return null;
}

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [run, setRun] = useState(null);
  const [error, setError] = useState(null);
  const [launching, setLaunching] = useState(false);
  const pollRef = useRef(null);

  useEffect(() => {
    return () => clearInterval(pollRef.current);
  }, []);

  async function handleRun() {
    const effectivePrompt = prompt.trim() || PLACEHOLDER;
    setError(null);
    setLaunching(true);
    setRun(null);
    try {
      const { id } = await startRun(effectivePrompt);
      pollRef.current = setInterval(async () => {
        try {
          const state = await fetchRun(id);
          setRun(state);
          if (state.status !== "running") {
            clearInterval(pollRef.current);
          }
        } catch (e) {
          setError(e.message);
          clearInterval(pollRef.current);
        }
      }, 2000);
    } catch (e) {
      setError(e.message);
    } finally {
      setLaunching(false);
    }
  }

  const isRunning = run?.status === "running" || launching;
  const activity = currentActivity(run?.stages);

  return (
    <div className="page">
      <header className="hero">
        <p className="hero-kicker">Four agents, one email</p>
        <h1 className="hero-title">The Swarm</h1>
        <p className="hero-sub">
          Give it a brief. A generator drafts three sales emails, an evaluator scores
          them, a selector picks a winner, and a formatter polishes it for send —
          each one a real call to Gemini, chained together.
        </p>

        <div className="prompt-box">
          <textarea
            className="prompt-input"
            placeholder={PLACEHOLDER}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={5}
            disabled={isRunning}
          />
          <div className="prompt-row">
            <span className="prompt-hint">
              Each stage is throttled for the free API tier, so a full run takes
              a few minutes.
            </span>
            <button className="run-button" onClick={handleRun} disabled={isRunning}>
              {isRunning ? "Running…" : "Run the swarm"}
            </button>
          </div>
        </div>
        {error && <p className="error-banner">{error}</p>}
      </header>

      <main className="pipeline-section">
        <PipelineRail stages={run?.stages} />

        <div className="stage-detail">
          {!run && (
            <p className="stage-detail--empty">Send a prompt to wake the swarm.</p>
          )}

          {run?.status === "running" && (
            <p className="stage-detail--empty">
              {activity || "Working through the pipeline…"}
            </p>
          )}

          {run?.status === "error" && (
            <p className="stage-detail--empty" style={{ color: "var(--error)" }}>
              {run.error || "Something went wrong."}
            </p>
          )}

          {run?.status === "done" && run.final_email && (
            <>
              <p className="stage-detail-intro">Ready to send.</p>
              <pre className="final-email">{run.final_email}</pre>
            </>
          )}
        </div>
      </main>

      <footer className="page-footer">
        <span>Built as a portable pipeline — swap Gemini for another model without touching the stage logic.</span>
      </footer>
    </div>
  );
}
