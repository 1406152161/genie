import { useState, useEffect } from "react";

interface StageInfo {
  id: string;
  status: string;
  duration?: number;
}

export default function RunPage() {
  const [goal, setGoal] = useState("");
  const [pack, setPack] = useState("code");
  const [model, setModel] = useState("mock");
  const [running, setRunning] = useState(false);
  const [runId, setRunId] = useState("");
  const [stages, setStages] = useState<StageInfo[]>([]);
  const [status, setStatus] = useState("");

  useEffect(() => {
    if (!runId) return;
    const poll = setInterval(async () => {
      try {
        const res = await fetch(`/api/runs/${runId}`);
        const data = await res.json();
        setStatus(data.status || "");
        setStages(data.stages || []);
        if (data.status === "completed" || data.status === "failed") {
          clearInterval(poll);
          setRunning(false);
        }
      } catch { /* ignore */ }
    }, 1000);
    return () => clearInterval(poll);
  }, [runId]);

  const handleRun = async () => {
    if (!goal.trim()) return;
    setRunning(true);
    setStatus("running");
    setStages([]);
    try {
      const res = await fetch("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pack, goal, model }),
      });
      const data = await res.json();
      setRunId(data.id);
    } catch (e) {
      setRunning(false);
      setStatus("API connection failed - is the backend running?");
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>What should Genie build?</h2>
      <p style={{ color: "#8b949e", marginBottom: 12, fontSize: 14 }}>
        Describe what you want in one sentence. Genie will research, design,
        build, and verify the complete project.
      </p>

      <textarea
        className="input-box"
        rows={4}
        placeholder='e.g. "Build a novel writing AI tool with outline planning and character management"'
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        disabled={running}
      />

      <div className="row">
        <select value={pack} onChange={(e) => setPack(e.target.value)} disabled={running}>
          <option value="code">code (code generation)</option>
          <option value="pack">pack (create RolePack)</option>
        </select>
        <select value={model} onChange={(e) => setModel(e.target.value)} disabled={running}>
          <option value="mock">mock (free)</option>
          <option value="deepseek">deepseek</option>
          <option value="gpt4">gpt4</option>
        </select>
        <button className="btn" onClick={handleRun} disabled={running || !goal.trim()}>
          {running ? "Running..." : "Start"}
        </button>
      </div>

      {status && (
        <div style={{ marginTop: 24 }}>
          <p style={{ fontWeight: 600 }}>
            Status: {status === "completed" ? "[OK]" : status === "failed" ? "[ERR]" : "[...]"} {status}
          </p>
        </div>
      )}

      {stages.map((s) => (
        <div className="stage-card" key={s.id}>
          <div className="name">{s.id}: {s.status}</div>
          <div className="roles">
            <span className={`role-badge ${s.status === "completed" ? "done" : s.status === "running" ? "running" : "waiting"}`}>
              {s.status}
            </span>
            {s.duration != null && (
              <span style={{ fontSize: 12, color: "#8b949e" }}>{s.duration}s</span>
            )}
          </div>
        </div>
      ))}

      {status === "completed" && (
        <div className="result-box">
          [OK] Project complete! Check the output directory for your generated project.
        </div>
      )}
    </div>
  );
}
