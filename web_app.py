from __future__ import annotations

import os
from flask import Flask, jsonify, request
from Route_Analysing.real_routes import generate_routes

app = Flask(__name__, static_folder="outputs", static_url_path="/outputs")


def _build_urls(run_id: str, vehicle_count: int):
    overview_url = f"/outputs/{run_id}/full_patrol_overview.png"
    vehicles = []
    for vid in range(1, vehicle_count + 1):
        vehicles.append(
            {
                "id": vid,
                "route_image": f"/outputs/{run_id}/vehicle_{vid}_route.png",
                "waypoints_json": f"/outputs/{run_id}/vehicle_{vid}_waypoints.json",
            }
        )
    return overview_url, vehicles


@app.post("/api/routes")
def api_routes():
    data = request.get_json(silent=True) or {}
    place = data.get("place", "").strip()
    vehicles = data.get("vehicles", 1)

    if not place:
        return jsonify({"error": "place is required"}), 400

    try:
        vehicles = int(vehicles)
        if vehicles < 1:
            raise ValueError
    except Exception:
        return jsonify({"error": "vehicles must be a positive integer"}), 400

    try:
        result = generate_routes(place, vehicles)
    except Exception as exc:  # pragma: no cover - surfaced to client
        return jsonify({"error": str(exc)}), 500

    overview_url, vehicles_meta = _build_urls(result["run_id"], vehicles)

    payload = {
        "run_id": result["run_id"],
        "geocode_source": result["geocode_source"],
        "overview_url": overview_url,
        "center": result.get("center", {}),
        "vehicles": [],
    }

    colors = ["red", "blue", "green", "orange", "purple", "yellow", "cyan"]

    for meta in vehicles_meta:
        vid = meta["id"]
        payload["vehicles"].append(
            {
                "id": vid,
                "color": colors[(vid - 1) % len(colors)],
                "route_image": meta["route_image"],
                "waypoints_json": meta["waypoints_json"],
            "waypoints": result["waypoints"].get(vid, []),
            "display_waypoints": result.get("display_waypoints", {}).get(vid, result["waypoints"].get(vid, [])),
            }
        )

    return jsonify(payload)


@app.get("/")
def index():
    return INDEX_HTML


INDEX_HTML = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Patrol Route Generator</title>
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />
  <link href=\"https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Manrope:wght@500;600;700&display=swap\" rel=\"stylesheet\" />
  <link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\" />
  <style>
    :root {
      --bg: #050816;
      --panel: #0c1427;
      --panel-border: #1f2a3d;
      --text: #e8edf7;
      --muted: #9fb0c8;
      --accent: #22d3ee;
      --accent-2: #a855f7;
      --glow: 0 15px 45px rgba(168, 85, 247, 0.28);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: 'Manrope', 'Space Grotesk', 'Segoe UI', sans-serif;
      background: radial-gradient(circle at 18% 18%, rgba(79, 70, 229, 0.18) 0, rgba(5,8,22,0.8) 38%),
          radial-gradient(circle at 82% 12%, rgba(34,211,238,0.2) 0, rgba(5,8,22,0.9) 36%),
          #050816;
      color: var(--text);
    }
    header {
      padding: 26px 32px;
      border-bottom: 1px solid var(--panel-border);
      background: linear-gradient(135deg, rgba(34,211,238,0.08), rgba(168,85,247,0.12));
      backdrop-filter: blur(8px);
      box-shadow: 0 12px 40px rgba(0,0,0,0.35);
    }
    h1 { margin: 0; font-size: 30px; letter-spacing: -0.01em; }
    .subtitle { margin-top: 8px; color: var(--muted); font-size: 16px; }
    main {
      padding: 26px 32px 34px;
      display: grid;
      gap: 18px;
      grid-template-columns: 400px 1fr;
      min-height: calc(100vh - 90px);
      max-width: 1400px;
      margin: 0 auto;
    }
    form {
      display: grid;
      gap: 16px;
      background: var(--panel);
      padding: 20px 20px 18px;
      border: 1px solid var(--panel-border);
      border-radius: 14px;
      position: sticky;
      top: 18px;
      box-shadow: 0 20px 70px rgba(0,0,0,0.45), 0 12px 30px rgba(34,211,238,0.08);
    }
    label { font-size: 15px; color: var(--muted); font-weight: 600; }
    input, button {
      width: 100%;
      padding: 13px 15px;
      border-radius: 11px;
      border: 1px solid var(--panel-border);
      background: #0b1428;
      color: var(--text);
      font-size: 16px;
    }
    input:focus { outline: 2px solid var(--accent-2); box-shadow: 0 0 0 6px rgba(34,211,238,0.12); }
    button {
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      border: none;
      font-weight: 800;
      letter-spacing: 0.015em;
      cursor: pointer;
      transition: transform 120ms ease, box-shadow 120ms ease, opacity 120ms ease;
      box-shadow: var(--glow);
    }
    button:hover { opacity: 0.92; transform: translateY(-1px); }
    button:active { transform: translateY(0); }
    .panel {
      background: var(--panel);
      border: 1px solid var(--panel-border);
      border-radius: 14px;
      padding: 16px;
      display: grid;
      gap: 12px;
      height: calc(100vh - 120px);
      box-shadow: 0 24px 80px rgba(0,0,0,0.45);
    }
    #map { width: 100%; height: 70vh; border-radius: 12px; overflow: hidden; border: 1px solid var(--panel-border); }
    #overview-img { width: 100%; height: 70vh; object-fit: contain; border-radius: 12px; border: 1px solid var(--panel-border); background: #090f1c; }
    .status { font-size: 15px; color: var(--accent); min-height: 22px; font-weight: 600; }
    @media (max-width: 1200px) { main { grid-template-columns: 1fr; } .panel { height: auto; } #map, #overview-img { height: 64vh; } form { position: static; } }
    @media (max-width: 720px) { header, main { padding: 16px; } h1 { font-size: 24px; } #map, #overview-img { height: 58vh; } }
  </style>
</head>
<body>
  <header>
    <h1>Patrol Route Generator</h1>
    <div class=\"subtitle\">Enter a place and vehicle count; routes will render on the live map and downloadable PNG/JSON outputs.</div>
  </header>
  <main>
    <form id=\"route-form\">
      <div>
        <label for=\"place\">Place</label>
        <input id=\"place\" name=\"place\" placeholder=\"e.g., Koramangala, Bengaluru, India\" required />
      </div>
      <div>
        <label for=\"vehicles\">Vehicles (zones)</label>
        <input id=\"vehicles\" name=\"vehicles\" type=\"number\" min=\"1\" value=\"4\" required />
      </div>
      <button type=\"submit\">Generate Routes</button>
      <div class=\"status\" id=\"status\"></div>
    </form>

    <div class=\"panel\" style=\"display: grid; gap: 12px;\">
      <div id=\"map\"></div>
      <img id=\"overview-img\" alt=\"Overview PNG will appear here\" />
    </div>
  </main>

  <script src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\"></script>
  <script>
    const form = document.getElementById('route-form');
    const statusEl = document.getElementById('status');
    const overviewImg = document.getElementById('overview-img');
    let map = L.map('map').setView([12.9716, 77.5946], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
    let layers = [];

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const place = document.getElementById('place').value.trim();
      const vehicles = parseInt(document.getElementById('vehicles').value, 10);
      if (!place) {
        statusEl.textContent = 'Place is required';
        return;
      }
      statusEl.textContent = 'Generating routes...';
      try {
        const res = await fetch('/api/routes', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ place, vehicles })
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.error || 'Request failed');
        }
        renderResult(data);
        statusEl.textContent = `Done. Source: ${data.geocode_source}`;
      } catch (err) {
        statusEl.textContent = err.message;
      }
    });

    function clearLayers() {
      layers.forEach(l => map.removeLayer(l));
      layers = [];
    }

    function renderResult(data) {
      overviewImg.src = data.overview_url;
      if (data.center && data.center.lat && data.center.lon) {
        map.setView([data.center.lat, data.center.lon], 14);
      }
      clearLayers();
      (data.vehicles || []).forEach(v => {
        const coords = (v.display_waypoints || v.waypoints || []).map(([lat, lon]) => [lat, lon]);
        if (!coords.length) return;
        const line = L.polyline(coords, { color: v.color || 'red', weight: 3 }).addTo(map);
        layers.push(line);
      });
    }
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
