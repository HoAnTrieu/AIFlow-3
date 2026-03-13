Robot Sorting Dashboard (Flask + SQLite)

Run locally:
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  python app.py

Open:
  http://127.0.0.1:5000
  http://127.0.0.1:5000/query

Environment variables:
  ROBOT_DB_PATH=/path/to/robot_sorting.db
  DASHBOARD_REFRESH_MS=3000
  RESET_DB_PASSWORD=23DRTA1
  QUERY_MAX_PAGE_SIZE=200
  EXPORT_MAX_ROWS=50000

Main features:
  - Dashboard realtime
  - Query page with filter / paging / sort / summary
  - Export filtered data to CSV
  - View raw JSON for each event
  - Reset DB with password confirmation

API endpoints:
  GET  /api/health
  GET  /api/dashboard
  GET  /api/filter-options
  GET  /api/events
  GET  /api/events/export
  POST /api/admin/reset-db

Reset DB payload:
  {
    "password": "23DRTA1",
    "confirm": "RESET"
  }
