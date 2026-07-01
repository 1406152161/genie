const BASE = "/api";

export async function createRun(pack: string, goal: string, model: string) {
  const res = await fetch(`${BASE}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pack, goal, model }),
  });
  return res.json();
}

export async function getRun(runId: string) {
  const res = await fetch(`${BASE}/runs/${runId}`);
  return res.json();
}

export async function listRuns() {
  const res = await fetch(`${BASE}/runs`);
  return res.json();
}
