"""cài đặt môi trường ảo và thư viện:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt"""

import csv
import hmac
import io
import json
import math
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, Response, g, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "robot_sorting.db")
REFRESH_MS = int(os.environ.get("DASHBOARD_REFRESH_MS", "5000"))
RESET_DB_PASSWORD = os.environ.get("RESET_DB_PASSWORD", "23DRTA1")
MAX_PAGE_SIZE = int(os.environ.get("QUERY_MAX_PAGE_SIZE", "200"))
EXPORT_MAX_ROWS = int(os.environ.get("EXPORT_MAX_ROWS", "50000"))

app = Flask(__name__, template_folder=BASE_DIR)
app.config["JSON_AS_ASCII"] = False

ALLOWED_SORT_COLUMNS = {
    "id": "id",
    "timestamp_text": "timestamp_text",
    "robot_id": "robot_id",
    "status": "status",
    "object_color_detected": "object_color_detected",
    "target_bin": "target_bin",
    "action_result": "action_result",
    "confidence": "confidence",
    "received_at": "received_at",
    "client_ip": "client_ip",
    "event_ts": "event_ts",
}


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@app.errorhandler(ApiError)
def handle_api_error(err: ApiError):
    return jsonify({"ok": False, "error": err.message}), err.status_code


@app.errorhandler(404)
def handle_404(_err):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "Endpoint không tồn tại"}), 404
    return "Not Found", 404


@app.errorhandler(500)
def handle_500(err):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": f"Lỗi server: {err}"}), 500
    return "Internal Server Error", 500



def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()



def _connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn



def _column_names(conn: sqlite3.Connection, table_name: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [row[1] for row in rows]



def parse_timestamp_to_epoch(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    candidates = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
    ]
    for fmt in candidates:
        try:
            return int(datetime.strptime(text, fmt).timestamp())
        except ValueError:
            continue
    return None



def normalize_datetime_input(value: Optional[str], *, end_of_minute: bool = False) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    text = text.replace("T", " ")
    if len(text) == 16:
        text += ":59" if end_of_minute else ":00"
    return text



def init_db() -> None:
    conn = _connect_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS robot_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                robot_id TEXT NOT NULL,
                timestamp_text TEXT NOT NULL,
                status TEXT NOT NULL,
                object_color_detected TEXT NOT NULL,
                target_bin TEXT NOT NULL,
                action_result TEXT NOT NULL,
                confidence REAL NOT NULL,
                received_at TEXT NOT NULL,
                client_ip TEXT NOT NULL,
                raw_json TEXT NOT NULL
            )
            """
        )

        columns = _column_names(conn, "robot_events")
        if "event_ts" not in columns:
            conn.execute("ALTER TABLE robot_events ADD COLUMN event_ts INTEGER")

        conn.execute(
            "UPDATE robot_events SET event_ts = CAST(strftime('%s', replace(substr(timestamp_text, 1, 19), 'T', ' ')) AS INTEGER) WHERE event_ts IS NULL"
        )

        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_robot_events_time ON robot_events(timestamp_text)",
            "CREATE INDEX IF NOT EXISTS idx_robot_events_result ON robot_events(action_result)",
            "CREATE INDEX IF NOT EXISTS idx_robot_events_robot_id ON robot_events(robot_id)",
            "CREATE INDEX IF NOT EXISTS idx_robot_events_status ON robot_events(status)",
            "CREATE INDEX IF NOT EXISTS idx_robot_events_color ON robot_events(object_color_detected)",
            "CREATE INDEX IF NOT EXISTS idx_robot_events_target_bin ON robot_events(target_bin)",
            "CREATE INDEX IF NOT EXISTS idx_robot_events_received_at ON robot_events(received_at)",
            "CREATE INDEX IF NOT EXISTS idx_robot_events_event_ts ON robot_events(event_ts)",
            "CREATE INDEX IF NOT EXISTS idx_robot_events_robot_time ON robot_events(robot_id, timestamp_text)",
            "CREATE INDEX IF NOT EXISTS idx_robot_events_result_time ON robot_events(action_result, timestamp_text)",
        ]
        for statement in index_statements:
            conn.execute(statement)

        conn.commit()
    finally:
        conn.close()



def normalize_status(raw_status: str) -> str:
    mapping = {
        "SORTING": "RUNNING",
        "WAIT_OBJECT": "IDLE",
        "IDLE": "IDLE",
        "RUNNING": "RUNNING",
        "ERROR": "ERROR",
    }
    if not raw_status:
        return "UNKNOWN"
    return mapping.get(raw_status.upper(), raw_status.upper())



def safe_upper(value: Optional[str], fallback: str = "-") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text.upper() if text else fallback



def row_to_event(row: sqlite3.Row, include_raw: bool = False) -> Dict[str, Any]:
    event = {
        "id": row["id"],
        "timestamp_text": row["timestamp_text"],
        "robot_id": row["robot_id"],
        "status": row["status"],
        "display_status": normalize_status(row["status"]),
        "object_color_detected": safe_upper(row["object_color_detected"], "OTHER"),
        "target_bin": row["target_bin"],
        "action_result": safe_upper(row["action_result"], "-"),
        "confidence": float(row["confidence"]),
        "received_at": row["received_at"],
        "client_ip": row["client_ip"],
        "event_ts": row["event_ts"] if "event_ts" in row.keys() else None,
    }
    if include_raw:
        raw_json_text = row["raw_json"] if "raw_json" in row.keys() else ""
        event["raw_json"] = raw_json_text
        try:
            event["raw_data"] = json.loads(raw_json_text) if raw_json_text else None
        except json.JSONDecodeError:
            event["raw_data"] = raw_json_text
    return event



def get_latest_status(db: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    row = db.execute(
        """
        SELECT id, robot_id, timestamp_text, status, object_color_detected,
               target_bin, action_result, confidence, received_at, client_ip, event_ts
        FROM robot_events
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    return row_to_event(row) if row else None



def get_color_counts(db: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = db.execute(
        """
        SELECT UPPER(COALESCE(object_color_detected, 'OTHER')) AS color,
               COUNT(*) AS count
        FROM robot_events
        GROUP BY UPPER(COALESCE(object_color_detected, 'OTHER'))
        ORDER BY count DESC, color ASC
        """
    ).fetchall()
    return [{"label": row["color"], "count": row["count"]} for row in rows]



def get_result_counts(db: sqlite3.Connection) -> Tuple[List[Dict[str, Any]], int]:
    rows = db.execute(
        """
        SELECT LOWER(COALESCE(action_result, 'unknown')) AS result,
               COUNT(*) AS count
        FROM robot_events
        GROUP BY LOWER(COALESCE(action_result, 'unknown'))
        ORDER BY count DESC, result ASC
        """
    ).fetchall()
    total = sum(row["count"] for row in rows)
    items = []
    for row in rows:
        pct = (row["count"] / total * 100.0) if total else 0.0
        items.append({
            "label": row["result"].upper(),
            "count": row["count"],
            "pct": round(pct, 2),
        })
    return items, total



def get_recent_events(db: sqlite3.Connection, limit: int = 50) -> List[Dict[str, Any]]:
    rows = db.execute(
        """
        SELECT id, timestamp_text, robot_id, status, object_color_detected,
               target_bin, action_result, confidence, received_at, client_ip, event_ts
        FROM robot_events
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [row_to_event(row) for row in rows]



def get_last_error(db: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    row = db.execute(
        """
        SELECT id, timestamp_text, robot_id, status, object_color_detected,
               target_bin, action_result, confidence, received_at, client_ip, event_ts
        FROM robot_events
        WHERE LOWER(action_result) = 'fail'
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    return row_to_event(row) if row else None



def get_recent_fail_count(db: sqlite3.Connection, window: int = 50) -> int:
    row = db.execute(
        """
        SELECT COUNT(*) AS fail_count
        FROM (
            SELECT action_result
            FROM robot_events
            ORDER BY id DESC
            LIMIT ?
        ) t
        WHERE LOWER(action_result) = 'fail'
        """,
        (window,),
    ).fetchone()
    return row["fail_count"] if row else 0



def parse_int_arg(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = request.args.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ApiError(f"Tham số {name} không hợp lệ") from exc
    return max(minimum, min(maximum, value))



def build_event_filters(args) -> Tuple[str, List[Any], Dict[str, Any]]:
    robot_id = args.get("robot_id", "").strip()
    status = args.get("status", "").strip()
    action_result = args.get("action_result", "").strip()
    color = args.get("color", "").strip()
    target_bin = args.get("target_bin", "").strip()
    client_ip = args.get("client_ip", "").strip()
    start_time = normalize_datetime_input(args.get("start_time", ""), end_of_minute=False)
    end_time = normalize_datetime_input(args.get("end_time", ""), end_of_minute=True)
    min_confidence = args.get("min_confidence", "").strip()
    max_confidence = args.get("max_confidence", "").strip()
    keyword = args.get("keyword", "").strip()

    clauses: List[str] = []
    params: List[Any] = []

    if robot_id:
        clauses.append("robot_id = ?")
        params.append(robot_id)
    if status:
        clauses.append("UPPER(status) = UPPER(?)")
        params.append(status)
    if action_result:
        clauses.append("UPPER(action_result) = UPPER(?)")
        params.append(action_result)
    if color:
        clauses.append("UPPER(object_color_detected) = UPPER(?)")
        params.append(color)
    if target_bin:
        clauses.append("target_bin = ?")
        params.append(target_bin)
    if client_ip:
        clauses.append("client_ip = ?")
        params.append(client_ip)
    if start_time:
        clauses.append("timestamp_text >= ?")
        params.append(start_time)
    if end_time:
        clauses.append("timestamp_text <= ?")
        params.append(end_time)
    if min_confidence:
        try:
            clauses.append("confidence >= ?")
            params.append(float(min_confidence))
        except ValueError as exc:
            raise ApiError("min_confidence không hợp lệ") from exc
    if max_confidence:
        try:
            clauses.append("confidence <= ?")
            params.append(float(max_confidence))
        except ValueError as exc:
            raise ApiError("max_confidence không hợp lệ") from exc
    if keyword:
        like = f"%{keyword}%"
        clauses.append(
            "(robot_id LIKE ? OR status LIKE ? OR object_color_detected LIKE ? OR target_bin LIKE ? OR action_result LIKE ? OR client_ip LIKE ? OR raw_json LIKE ? OR timestamp_text LIKE ?)"
        )
        params.extend([like, like, like, like, like, like, like, like])

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    applied_filters = {
        "robot_id": robot_id,
        "status": status,
        "action_result": action_result,
        "color": color,
        "target_bin": target_bin,
        "client_ip": client_ip,
        "start_time": start_time,
        "end_time": end_time,
        "min_confidence": min_confidence,
        "max_confidence": max_confidence,
        "keyword": keyword,
    }
    return where_sql, params, applied_filters



def get_query_summary(db: sqlite3.Connection, where_sql: str, params: List[Any]) -> Dict[str, Any]:
    row = db.execute(
        f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN UPPER(action_result) = 'SUCCESS' THEN 1 ELSE 0 END) AS success_count,
            SUM(CASE WHEN UPPER(action_result) = 'FAIL' THEN 1 ELSE 0 END) AS fail_count,
            AVG(confidence) AS avg_confidence,
            MIN(timestamp_text) AS min_time,
            MAX(timestamp_text) AS max_time
        FROM robot_events
        {where_sql}
        """,
        params,
    ).fetchone()

    top_color_row = db.execute(
        f"""
        SELECT UPPER(COALESCE(object_color_detected, 'OTHER')) AS label, COUNT(*) AS count
        FROM robot_events
        {where_sql}
        GROUP BY UPPER(COALESCE(object_color_detected, 'OTHER'))
        ORDER BY count DESC, label ASC
        LIMIT 1
        """,
        params,
    ).fetchone()

    top_robot_row = db.execute(
        f"""
        SELECT robot_id AS label, COUNT(*) AS count
        FROM robot_events
        {where_sql}
        GROUP BY robot_id
        ORDER BY count DESC, label ASC
        LIMIT 1
        """,
        params,
    ).fetchone()

    total = row["total"] or 0
    success_count = row["success_count"] or 0
    fail_count = row["fail_count"] or 0

    return {
        "total": total,
        "success_count": success_count,
        "fail_count": fail_count,
        "success_pct": round(success_count * 100.0 / total, 2) if total else 0.0,
        "fail_pct": round(fail_count * 100.0 / total, 2) if total else 0.0,
        "avg_confidence": round(float(row["avg_confidence"]), 4) if row["avg_confidence"] is not None else None,
        "min_time": row["min_time"],
        "max_time": row["max_time"],
        "top_color": {"label": top_color_row["label"], "count": top_color_row["count"]} if top_color_row else None,
        "top_robot": {"label": top_robot_row["label"], "count": top_robot_row["count"]} if top_robot_row else None,
    }



def fetch_events(
    db: sqlite3.Connection,
    *,
    page: int,
    page_size: int,
    sort_by: str,
    sort_dir: str,
    include_raw: bool,
) -> Dict[str, Any]:
    where_sql, params, applied_filters = build_event_filters(request.args)
    sort_column = ALLOWED_SORT_COLUMNS.get(sort_by, "id")
    sort_direction = "ASC" if sort_dir.lower() == "asc" else "DESC"

    count_sql = f"SELECT COUNT(*) AS total FROM robot_events {where_sql}"
    total = db.execute(count_sql, params).fetchone()["total"]

    offset = (page - 1) * page_size
    rows = db.execute(
        f"""
        SELECT id, timestamp_text, robot_id, status, object_color_detected,
               target_bin, action_result, confidence, received_at, client_ip, raw_json, event_ts
        FROM robot_events
        {where_sql}
        ORDER BY {sort_column} {sort_direction}, id DESC
        LIMIT ? OFFSET ?
        """,
        params + [page_size, offset],
    ).fetchall()

    summary = get_query_summary(db, where_sql, params)

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(1, math.ceil(total / page_size)) if page_size else 1,
        "sort_by": sort_by,
        "sort_dir": sort_direction.lower(),
        "filters": applied_filters,
        "summary": summary,
        "items": [row_to_event(row, include_raw=include_raw) for row in rows],
    }



def get_filter_options(db: sqlite3.Connection) -> Dict[str, List[str]]:
    def distinct_values(column: str) -> List[str]:
        rows = db.execute(
            f"SELECT DISTINCT {column} AS value FROM robot_events WHERE TRIM(COALESCE({column}, '')) <> '' ORDER BY value ASC"
        ).fetchall()
        return [str(row["value"]) for row in rows]

    return {
        "robot_ids": distinct_values("robot_id"),
        "statuses": distinct_values("status"),
        "results": distinct_values("action_result"),
        "colors": distinct_values("object_color_detected"),
        "target_bins": distinct_values("target_bin"),
        "client_ips": distinct_values("client_ip"),
    }



def compare_password(password: str) -> bool:
    return hmac.compare_digest(password or "", RESET_DB_PASSWORD)



def reset_database() -> int:
    conn = _connect_db()
    try:
        count = conn.execute("SELECT COUNT(*) AS c FROM robot_events").fetchone()["c"]
        conn.execute("DELETE FROM robot_events")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'robot_events'")
        conn.commit()
        conn.execute("VACUUM")
        return count
    finally:
        conn.close()


@app.route("/")
def index():
    return render_template("index.html", refresh_ms=REFRESH_MS)


@app.route("/query")
def query_page():
    return render_template("query.html", max_page_size=MAX_PAGE_SIZE)


@app.route("/api/health")
def health():
    db = get_db()
    total = db.execute("SELECT COUNT(*) AS c FROM robot_events").fetchone()["c"]
    return jsonify({
        "ok": True,
        "db_path": DB_PATH,
        "total_events": total,
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "refresh_ms": REFRESH_MS,
    })


@app.route("/api/dashboard")
def api_dashboard():
    db = get_db()

    latest = get_latest_status(db)
    color_counts = get_color_counts(db)
    result_counts, total_results = get_result_counts(db)
    recent_events = get_recent_events(db, limit=50)
    last_error = get_last_error(db)
    recent_fail_count = get_recent_fail_count(db, window=50)

    total_events = db.execute("SELECT COUNT(*) AS c FROM robot_events").fetchone()["c"]

    success_pct = 0.0
    fail_pct = 0.0
    for item in result_counts:
        if item["label"] == "SUCCESS":
            success_pct = item["pct"]
        elif item["label"] == "FAIL":
            fail_pct = item["pct"]

    if fail_pct >= 10:
        fail_alert = "critical"
    elif fail_pct >= 5:
        fail_alert = "warning"
    else:
        fail_alert = "normal"

    return jsonify({
        "ok": True,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_events": total_events,
        "latest": latest,
        "sorting_statistics": color_counts,
        "result_statistics": result_counts,
        "success_pct": round(success_pct, 2),
        "fail_pct": round(fail_pct, 2),
        "fail_alert": fail_alert,
        "recent_fail_count_50": recent_fail_count,
        "recent_events": recent_events,
        "last_error": last_error,
        "total_result_rows": total_results,
    })


@app.route("/api/filter-options")
def api_filter_options():
    db = get_db()
    return jsonify({"ok": True, "options": get_filter_options(db)})


@app.route("/api/events")
def api_events():
    db = get_db()
    page = parse_int_arg("page", 1, 1, 1000000)
    page_size = parse_int_arg("page_size", 50, 1, MAX_PAGE_SIZE)
    sort_by = request.args.get("sort_by", "id").strip() or "id"
    sort_dir = request.args.get("sort_dir", "desc").strip() or "desc"
    if sort_by not in ALLOWED_SORT_COLUMNS:
        raise ApiError("sort_by không hợp lệ")
    if sort_dir.lower() not in {"asc", "desc"}:
        raise ApiError("sort_dir phải là asc hoặc desc")

    payload = fetch_events(
        db,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
        include_raw=True,
    )
    payload["ok"] = True
    return jsonify(payload)


@app.route("/api/events/export")
def export_events():
    db = get_db()
    sort_by = request.args.get("sort_by", "id").strip() or "id"
    sort_dir = request.args.get("sort_dir", "desc").strip() or "desc"
    if sort_by not in ALLOWED_SORT_COLUMNS:
        raise ApiError("sort_by không hợp lệ")
    if sort_dir.lower() not in {"asc", "desc"}:
        raise ApiError("sort_dir phải là asc hoặc desc")

    where_sql, params, _filters = build_event_filters(request.args)
    sort_column = ALLOWED_SORT_COLUMNS.get(sort_by, "id")
    sort_direction = "ASC" if sort_dir.lower() == "asc" else "DESC"

    rows = db.execute(
        f"""
        SELECT id, timestamp_text, robot_id, status, object_color_detected,
               target_bin, action_result, confidence, received_at, client_ip, event_ts, raw_json
        FROM robot_events
        {where_sql}
        ORDER BY {sort_column} {sort_direction}, id DESC
        LIMIT ?
        """,
        params + [EXPORT_MAX_ROWS],
    ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "timestamp_text",
        "robot_id",
        "status",
        "display_status",
        "object_color_detected",
        "target_bin",
        "action_result",
        "confidence",
        "received_at",
        "client_ip",
        "event_ts",
        "raw_json",
    ])
    for row in rows:
        event = row_to_event(row, include_raw=True)
        writer.writerow([
            event["id"],
            event["timestamp_text"],
            event["robot_id"],
            event["status"],
            event["display_status"],
            event["object_color_detected"],
            event["target_bin"],
            event["action_result"],
            event["confidence"],
            event["received_at"],
            event["client_ip"],
            event["event_ts"],
            event.get("raw_json", ""),
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"robot_events_{timestamp}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(csv_bytes, mimetype="text/csv; charset=utf-8", headers=headers)


@app.route("/api/admin/reset-db", methods=["POST"])
def api_reset_db():
    data = request.get_json(silent=True) or {}
    password = str(data.get("password", ""))
    confirm = str(data.get("confirm", "")).strip().upper()

    if not compare_password(password):
        raise ApiError("Mật khẩu reset DB không đúng", status_code=403)
    if confirm != "RESET":
        raise ApiError("Thiếu xác nhận RESET", status_code=400)

    removed_count = reset_database()
    return jsonify({
        "ok": True,
        "message": "Đã reset database thành công",
        "removed_count": removed_count,
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=9123, debug=True)
