const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8787";

export async function startRun(prompt) {
  const res = await fetch(`${API_URL}/api/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Could not start the run.");
  }
  return res.json();
}

export async function fetchRun(id) {
  const res = await fetch(`${API_URL}/api/runs/${id}`);
  if (!res.ok) {
    throw new Error("Could not fetch run status.");
  }
  return res.json();
}
