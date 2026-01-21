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
  <link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\" />
  <style>
    body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #0f172a; color: #e2e8f0; }
    header { padding: 16px 20px; background: #111827; border-bottom: 1px solid #1f2937; }
    h1 { margin: 0; font-size: 20px; }
    main { padding: 16px 20px; display: grid; gap: 16px; grid-template-columns: 360px 1fr; min-height: calc(100vh - 70px); }
    form { display: grid; gap: 12px; background: #111827; padding: 16px; border: 1px solid #1f2937; border-radius: 12px; position: sticky; top: 12px; }
    label { font-size: 13px; color: #cbd5e1; }
    input, button { width: 100%; padding: 10px 12px; border-radius: 8px; border: 1px solid #1f2937; background: #0b1221; color: #e2e8f0; }
    button { background: linear-gradient(135deg, #22d3ee, #6366f1); border: none; font-weight: 600; cursor: pointer; }
    button:hover { opacity: 0.92; }
    .panel { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 12px; display: grid; gap: 12px; height: calc(100vh - 90px); }
    #map { width: 100%; height: 70vh; border-radius: 12px; overflow: hidden; border: 1px solid #1f2937; }
    #overview-img { width: 100%; height: 70vh; object-fit: contain; border-radius: 12px; border: 1px solid #1f2937; background: #0b1221; }
    .status { font-size: 13px; color: #a5b4fc; min-height: 18px; }
    @media (max-width: 1100px) { main { grid-template-columns: 1fr; } .panel { height: auto; } #map, #overview-img { height: 60vh; } }
  </style>
</head>
<body>
  <header>
    <h1>Patrol Route Generator</h1>
    <div style=\"font-size: 13px; color: #9ca3af;\">Enter a place and vehicle count; routes will render on the live map and PNG.</div>
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
