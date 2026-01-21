# Patrol Route Generator

Web + CLI tool to cluster road networks into patrol zones and render PNG/JSON outputs with Leaflet and Flask.

## Prerequisites
- Python 3.10+
- Windows: PowerShell or CMD
- Recommended VS Code extensions: ms-python.python, ms-python.vscode-pylance, ms-toolsai.jupyter.

## Setup
1) Clone and enter the repo
```
git clone https://github.com/vindhyakaranth1/Route_Analysing.git
cd Route_Analysing/..
```
2) Create and activate venv (Windows)
```
python -m venv .venv
.\.venv\Scripts\activate
```
3) Install deps
```
pip install -r requirements.txt
```

## Run the web UI (Leaflet + Flask)
Option A: double-click on Windows
- Double-click `run_app.bat` in File Explorer. It will create/activate `.venv`, install deps, and start the server.
- When you see "Starting web server on http://localhost:5000 ...", open that URL in your browser.

Option B: manual shell
```
.\.venv\Scripts\activate
python web_app.py
```
- Open http://localhost:5000
- Enter a place (e.g., "Koramangala, Bengaluru, India") and vehicle count, click Generate.
- PNGs and JSON waypoints are written to outputs/<run_id>/.

## Run via CLI only
```
.\.venv\Scripts\activate
python Route_Analysing/real_routes.py --place "Pattangere, Bengaluru, Karnataka, India" --vehicles 4 --radius 2000
```
- Outputs: full_patrol_overview.png, vehicle_X_route.png, vehicle_X_waypoints.json under outputs/<run_id>/.

## Notes
- Geocoding fallback: if a polygon is not found, the code buffers the geocoded point (default 2000m). Adjust with --radius.
- Display simplification: routes shown in Leaflet are decimated for clarity; saved JSON/PNGs use full resolution.
- If Nominatim fails, try a broader/more specific place name or increase radius.
- Favicon 404 in the dev server is expected and harmless.

## Troubleshooting
- If `osmnx` download errors: retry with VPN/off-peak or provide a broader area name.
- If map looks empty: zoom out; check outputs folder for generated PNGs.
- If port 5000 is busy: set `PORT=5001` then run `python web_app.py`.

## Project files
- Backend + clustering: Route_Analysing/real_routes.py
- Flask + Leaflet UI: web_app.py
- Outputs: outputs/<run_id>/
