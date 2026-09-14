// Landing page wiring: everything here talks to the FastAPI routes in src/main.py.

async function getJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url} -> ${res.status}`);
  return res.json();
}

async function loadStatus() {
  const el = document.getElementById("status");
  const justConnected = new URLSearchParams(location.search).has("connected");

  try {
    const data = await getJSON("/api/status");
    const connected = data.connected || justConnected;
    el.textContent = connected ? "Google account connected." : "Not connected yet.";
    el.className = "status " + (connected ? "ok" : "");
  } catch (err) {
    el.textContent = "Backend unreachable: " + err.message;
    el.className = "status bad";
  }
}

async function loadSleep() {
  const el = document.getElementById("sleep");

  try {
    const data = await getJSON("/api/sleep");
    if (!data.nights || data.nights.length === 0) {
      el.textContent = "No sleep data yet. Connect your account to start syncing.";
      return;
    }

    const rows = data.nights
      .map((n) => `<tr><td>${n.date}</td><td>${n.duration_hours} h</td></tr>`)
      .join("");
    el.className = "";
    el.innerHTML = `<table><tr><th>Date</th><th>Duration</th></tr>${rows}</table>`;
  } catch (err) {
    el.textContent = "Could not load sleep data: " + err.message;
  }
}

loadStatus();
loadSleep();
