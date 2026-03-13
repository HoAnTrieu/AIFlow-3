#!/usr/bin/env python3
import json
import queue
import signal
import socket
import socketserver
import sqlite3
import threading
from datetime import datetime

HOST = "127.0.0.1"
PORT = 9100
DB_PATH = r"robot_sorting.db"

WRITE_QUEUE = queue.Queue()
STOP_EVENT = threading.Event()


def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
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
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_robot_events_timestamp "
            "ON robot_events(timestamp_text)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_robot_events_robot "
            "ON robot_events(robot_id)"
        )
        conn.commit()
    finally:
        conn.close()


def validate_payload(payload: dict) -> dict:
    required_fields = [
        "robot_id",
        "timestamp",
        "status",
        "object_color_detected",
        "target_bin",
        "action_result",
        "confidence",
    ]

    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Missing field: {field}")

    robot_id = str(payload["robot_id"]).strip()
    timestamp_text = str(payload["timestamp"]).strip()
    status = str(payload["status"]).strip()
    object_color_detected = str(payload["object_color_detected"]).strip()
    target_bin = str(payload["target_bin"]).strip()
    action_result = str(payload["action_result"]).strip()

    try:
        confidence = float(payload["confidence"])
    except Exception as exc:
        raise ValueError("confidence must be numeric") from exc

    try:
        datetime.strptime(timestamp_text, "%Y-%m-%d_%H:%M:%S")
    except ValueError as exc:
        raise ValueError("timestamp must match YYYY-MM-DD_HH:MM:SS") from exc

    return {
        "robot_id": robot_id,
        "timestamp_text": timestamp_text,
        "status": status,
        "object_color_detected": object_color_detected,
        "target_bin": target_bin,
        "action_result": action_result,
        "confidence": confidence,
    }


def db_writer(db_path: str) -> None:
    conn = sqlite3.connect(db_path, timeout=10)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")

        while not STOP_EVENT.is_set() or not WRITE_QUEUE.empty():
            try:
                item = WRITE_QUEUE.get(timeout=0.5)
            except queue.Empty:
                continue

            if item is None:
                WRITE_QUEUE.task_done()
                break

            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO robot_events (
                        robot_id,
                        timestamp_text,
                        status,
                        object_color_detected,
                        target_bin,
                        action_result,
                        confidence,
                        received_at,
                        client_ip,
                        raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["robot_id"],
                        item["timestamp_text"],
                        item["status"],
                        item["object_color_detected"],
                        item["target_bin"],
                        item["action_result"],
                        item["confidence"],
                        item["received_at"],
                        item["client_ip"],
                        item["raw_json"],
                    ),
                )
                conn.commit()

                print(
                    f'[DB] saved | robot={item["robot_id"]} | '
                    f'time={item["timestamp_text"]} | '
                    f'color={item["object_color_detected"]} | '
                    f'bin={item["target_bin"]} | '
                    f'result={item["action_result"]} | '
                    f'conf={item["confidence"]:.2f}'
                )
            except Exception as exc:
                print(f"[DB] insert error: {exc}")
            finally:
                WRITE_QUEUE.task_done()
    finally:
        conn.close()


class TCPJsonHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        client_ip = self.client_address[0]
        print(f"[TCP] connected: {client_ip}")

        try:
            self.request.settimeout(3.0)

            # Mô hình hiện tại: 1 connection = 1 dòng JSON
            line = self.rfile.readline()

            if not line:
                return

            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                self._safe_write_json({"ok": False, "error": "Empty payload"})
                return

            payload = json.loads(text)
            data = validate_payload(payload)

            data["received_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data["client_ip"] = client_ip
            data["raw_json"] = text

            WRITE_QUEUE.put(data)

            self._safe_write_json({
                "ok": True,
                "message": "saved",
                "robot_id": data["robot_id"],
                "timestamp": data["timestamp_text"]
            })

        except socket.timeout:
            self._safe_write_json({"ok": False, "error": "Socket timeout"})
        except OSError as exc:
            # Windows hay gặp khi client đóng socket nhanh
            if getattr(exc, "winerror", None) not in (10053, 10054):
                print(f"[TCP] socket error from {client_ip}: {exc}")
        except json.JSONDecodeError:
            self._safe_write_json({"ok": False, "error": "Invalid JSON"})
        except ValueError as exc:
            self._safe_write_json({"ok": False, "error": str(exc)})
        except Exception as exc:
            print(f"[TCP] unexpected error from {client_ip}: {exc}")
            self._safe_write_json({"ok": False, "error": f"Server error: {exc}"})
        finally:
            print(f"[TCP] disconnected: {client_ip}")

    def _safe_write_json(self, payload: dict) -> None:
        try:
            msg = json.dumps(payload, ensure_ascii=False) + "\n"
            self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()
        except OSError as exc:
            if getattr(exc, "winerror", None) not in (10053, 10054):
                print(f"[TCP] write error: {exc}")
        except Exception as exc:
            print(f"[TCP] write error: {exc}")


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    init_db(DB_PATH)

    writer_thread = threading.Thread(target=db_writer, args=(DB_PATH,), daemon=True)
    writer_thread.start()

    server = ThreadedTCPServer((HOST, PORT), TCPJsonHandler)

    def shutdown_handler(signum, frame):
        print("\n[SYS] shutting down...")
        STOP_EVENT.set()
        try:
            server.shutdown()
        except Exception:
            pass
        try:
            server.server_close()
        except Exception:
            pass
        WRITE_QUEUE.put(None)

    signal.signal(signal.SIGINT, shutdown_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown_handler)

    print(f"[SYS] TCP JSON server listening on {HOST}:{PORT}")
    print(f"[SYS] SQLite DB: {DB_PATH}")

    try:
        server.serve_forever()
    finally:
        STOP_EVENT.set()
        WRITE_QUEUE.put(None)
        writer_thread.join(timeout=3)
        print("[SYS] stopped")


if __name__ == "__main__":
    main()