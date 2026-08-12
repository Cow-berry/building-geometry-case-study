// Minimal API client. Point at the backend; override with VITE_API_BASE if needed.
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function getHealth() {
  const res = await fetch(`${API_BASE}/api/v1/health`);
  if (!res.ok) throw new Error(`health check failed: ${res.status}`);
  return res.json();
}

export async function ensureDB() {
  await fetch(`${API_BASE}/api/v1/db/ensure`);
}

export async function purgeDB() {
  await fetch(`${API_BASE}/api/v1/db/purge`);
}

export async function createMassing(points, constraint, parent) {
  const payload = {points, constraint, parent};
  console.log("payload", payload);
  const res = await fetch(`${API_BASE}/api/v1/massing/create`, {
    method: "POST",
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });
  const res_json = await res.json();
  console.log("res json", res_json);
  return res_json;
}

export async function getAllMassings() {
  const res = await fetch(`${API_BASE}/api/v1/massing/get/all`);
  return await res.json();
}
