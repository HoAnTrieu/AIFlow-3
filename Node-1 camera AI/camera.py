"""
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip # or python.exe -m pip install --upgrade pip
pip install -r requirements.txt
"""

import cv2
import json
import time
import socket
import numpy as np
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================
WINDOW_W = 640
WINDOW_H = 360

ROBOT_ID = "R01"
CAMERA_INDEX = 0
SEND_INTERVAL = 2.0  # seconds

DEFAULT_UDP_IP = "0.0.0.0"
DEFAULT_UDP_PORT = 9000

DEFAULT_DB_IP = "0.0.0.0"
DEFAULT_DB_PORT = 9100

BG_COLOR = "#efefef"
PANEL_BG = "#f7f7f7"
TEXT_FONT = ("Arial", 9)
TITLE_FONT = ("Times New Roman", 11, "bold")


# =========================================================
# APP
# =========================================================
class SortingSimulatorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Robot Sorting Simulator")
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_COLOR)

        # State
        self.fail_mode = False
        self.last_send_time = 0.0
        self.last_udp_packet = "-"
        self.last_json_packet = "-"
        self.last_net_status = "READY"

        # Variables
        self.udp_ip_var = tk.StringVar(value=DEFAULT_UDP_IP)
        self.udp_port_var = tk.StringVar(value=str(DEFAULT_UDP_PORT))
        self.db_ip_var = tk.StringVar(value=DEFAULT_DB_IP)
        self.db_port_var = tk.StringVar(value=str(DEFAULT_DB_PORT))

        # UDP socket
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Camera
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update_loop()
        self.root.mainloop()

    # =====================================================
    # UI
    # =====================================================
    def _build_ui(self):
        # ---- Left: Camera
        tk.Label(self.root, text="Camera", font=TITLE_FONT, bg=BG_COLOR).place(x=170, y=6)

        self.camera_frame = tk.Frame(self.root, bg="black", bd=2, relief="solid")
        self.camera_frame.place(x=8, y=28, width=388, height=214)

        self.camera_label = tk.Label(self.camera_frame, bg="#d9d9d9")
        self.camera_label.place(x=4, y=4, width=376, height=204)

        # ---- Left bottom: Packet display
        tk.Label(self.root, text="Gói tin gửi đi:", font=TITLE_FONT, bg=BG_COLOR).place(x=10, y=248)

        self.packet_box = tk.Text(
            self.root,
            font=("Consolas", 8),
            bg=PANEL_BG,
            bd=1,
            relief="solid",
            wrap=tk.WORD
        )
        self.packet_box.place(x=8, y=270, width=388, height=78)
        self.packet_box.insert("1.0", "Detected: - | Target bin: -\nUDP: -\nDB: -")
        self.packet_box.configure(state="disabled")

        # ---- Right: Buttons
        self.btn_fail = tk.Button(
            self.root,
            text="FAIL",
            font=("Times New Roman", 11, "bold"),
            fg="red",
            bg="white",
            bd=2,
            relief="solid",
            command=self.toggle_fail
        )
        self.btn_fail.place(x=410, y=10, width=102, height=34)

        self.btn_quit = tk.Button(
            self.root,
            text="QUIT",
            font=("Times New Roman", 11, "bold"),
            bg="white",
            bd=2,
            relief="solid",
            command=self.on_close
        )
        self.btn_quit.place(x=524, y=10, width=102, height=34)

        # ---- Right: Status label
        self.status_label = tk.Label(
            self.root,
            text="SYSTEM READY",
            font=("Arial", 9, "bold"),
            bg="#dff0d8",
            fg="#1f5f1f",
            bd=1,
            relief="solid"
        )
        self.status_label.place(x=410, y=50, width=216, height=24)

        # ---- Arm info
        self.arm_frame = tk.LabelFrame(
            self.root,
            text="Kết Nối Robot Arm",
            font=("Times New Roman", 10, "bold"),
            bg=BG_COLOR,
            bd=2,
            relief="solid"
        )
        self.arm_frame.place(x=408, y=84, width=220, height=78)

        tk.Label(self.arm_frame, text="IP", font=TEXT_FONT, bg=BG_COLOR).place(x=8, y=8)
        tk.Entry(self.arm_frame, textvariable=self.udp_ip_var, font=TEXT_FONT, bd=1, relief="solid").place(x=32, y=6, width=122, height=24)

        tk.Label(self.arm_frame, text="Port", font=TEXT_FONT, bg=BG_COLOR).place(x=160, y=8)
        tk.Entry(self.arm_frame, textvariable=self.udp_port_var, font=TEXT_FONT, bd=1, relief="solid").place(x=188, y=6, width=24, height=24)

        tk.Label(
            self.arm_frame,
            text="UDP -> LabVIEW Scan From String",
            font=("Arial", 8),
            bg=BG_COLOR,
            fg="#444444"
        ).place(x=8, y=38)

        # ---- DB info
        self.db_frame = tk.LabelFrame(
            self.root,
            text="Kết Nối DataBASE",
            font=("Times New Roman", 10, "bold"),
            bg=BG_COLOR,
            bd=2,
            relief="solid"
        )
        self.db_frame.place(x=408, y=170, width=220, height=78)

        tk.Label(self.db_frame, text="IP", font=TEXT_FONT, bg=BG_COLOR).place(x=8, y=8)
        tk.Entry(self.db_frame, textvariable=self.db_ip_var, font=TEXT_FONT, bd=1, relief="solid").place(x=32, y=6, width=122, height=24)

        tk.Label(self.db_frame, text="Port", font=TEXT_FONT, bg=BG_COLOR).place(x=160, y=8)
        tk.Entry(self.db_frame, textvariable=self.db_port_var, font=TEXT_FONT, bd=1, relief="solid").place(x=188, y=6, width=24, height=24)

        tk.Label(
            self.db_frame,
            text="TCP -> JSON lưu DB",
            font=("Arial", 8),
            bg=BG_COLOR,
            fg="#444444"
        ).place(x=8, y=38)

        # ---- History
        self.history_frame = tk.LabelFrame(
            self.root,
            text="Lịch sử gửi",
            font=("Times New Roman", 10, "bold"),
            bg=BG_COLOR,
            bd=2,
            relief="solid"
        )
        self.history_frame.place(x=408, y=256, width=220, height=92)

        self.history_box = scrolledtext.ScrolledText(
            self.history_frame,
            font=("Consolas", 7),
            bd=1,
            relief="solid",
            wrap=tk.WORD
        )
        self.history_box.place(x=6, y=4, width=204, height=58)
        self.history_box.configure(state="disabled")

    # =====================================================
    # TOGGLE FAIL
    # =====================================================
    def toggle_fail(self):
        self.fail_mode = not self.fail_mode
        if self.fail_mode:
            self.btn_fail.configure(bg="#ffd9d9")
        else:
            self.btn_fail.configure(bg="white")

    # =====================================================
    # CLASSICAL AI / MACHINE VISION
    # =====================================================
    def detect_object_and_color(self, frame):
        """
        Không dùng deep learning.
        Dùng:
        - HSV threshold
        - morphology
        - contour detection
        - dominant color scoring
        """
        blur = cv2.GaussianBlur(frame, (5, 5), 0)
        hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

        # Red
        red_lower1 = np.array([0, 110, 70])
        red_upper1 = np.array([10, 255, 255])
        red_lower2 = np.array([170, 110, 70])
        red_upper2 = np.array([180, 255, 255])

        # Green
        green_lower = np.array([40, 70, 70])
        green_upper = np.array([85, 255, 255])

        # Blue
        blue_lower = np.array([95, 80, 60])
        blue_upper = np.array([140, 255, 255])

        mask_red1 = cv2.inRange(hsv, red_lower1, red_upper1)
        mask_red2 = cv2.inRange(hsv, red_lower2, red_upper2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        mask_green = cv2.inRange(hsv, green_lower, green_upper)
        mask_blue = cv2.inRange(hsv, blue_lower, blue_upper)

        union_mask = cv2.bitwise_or(mask_red, mask_green)
        union_mask = cv2.bitwise_or(union_mask, mask_blue)

        kernel = np.ones((5, 5), np.uint8)
        union_mask = cv2.morphologyEx(union_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        union_mask = cv2.morphologyEx(union_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(union_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return {
                "found": False,
                "bbox": None,
                "color": "unknown",
                "confidence": 0.0
            }

        # Chọn contour lớn nhất đủ điều kiện
        h, w = frame.shape[:2]
        frame_area = h * w
        min_area = frame_area * 0.01

        best = None
        best_area = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area and area > best_area:
                best = cnt
                best_area = area

        if best is None:
            return {
                "found": False,
                "bbox": None,
                "color": "unknown",
                "confidence": 0.0
            }

        x, y, bw, bh = cv2.boundingRect(best)

        roi_red = mask_red[y:y + bh, x:x + bw]
        roi_green = mask_green[y:y + bh, x:x + bw]
        roi_blue = mask_blue[y:y + bh, x:x + bw]
        roi_union = union_mask[y:y + bh, x:x + bw]

        red_count = cv2.countNonZero(roi_red)
        green_count = cv2.countNonZero(roi_green)
        blue_count = cv2.countNonZero(roi_blue)
        total_count = max(cv2.countNonZero(roi_union), 1)

        counts = {
            "red": red_count,
            "green": green_count,
            "blue": blue_count
        }

        color = max(counts, key=counts.get)

        dominant_ratio = counts[color] / total_count
        fill_ratio = total_count / max(bw * bh, 1)

        confidence = (0.7 * dominant_ratio) + (0.3 * min(fill_ratio * 1.5, 1.0))
        confidence = round(min(max(confidence, 0.0), 0.99), 2)

        return {
            "found": True,
            "bbox": (x, y, bw, bh),
            "color": color,
            "confidence": confidence
        }

    # =====================================================
    # BUSINESS LOGIC
    # =====================================================
    def robot_logic(self, color):
        mapping = {
            "red": "red_bin",
            "green": "green_bin",
            "blue": "blue_bin"
        }
        return mapping.get(color, "reject_bin")

    def build_payload(self, detection):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

        if self.fail_mode:
            status = "ERROR"
            action_result = "fail"
        elif not detection["found"]:
            status = "WAIT_OBJECT"
            action_result = "waiting"
        else:
            status = "SORTING"
            action_result = "success"

        detected_color = detection["color"] if detection["found"] else "unknown"
        target_bin = self.robot_logic(detected_color)
        confidence = detection["confidence"] if detection["found"] else 0.0

        return {
            "robot_id": ROBOT_ID,
            "timestamp": timestamp,
            "status": status,
            "object_color_detected": detected_color,
            "target_bin": target_bin,
            "action_result": action_result,
            "confidence": round(float(confidence), 2)
        }

    def format_udp_for_labview(self, payload):
        """
        Khớp với format string LabVIEW:
        %s %<%Y-%m-%d_%H:%M:%S>T %s %s %s %s %f
        """
        return (
            f'{payload["robot_id"]} '
            f'{payload["timestamp"]} '
            f'{payload["status"]} '
            f'{payload["object_color_detected"]} '
            f'{payload["target_bin"]} '
            f'{payload["action_result"]} '
            f'{payload["confidence"]:.2f}'
        )

    # =====================================================
    # NETWORK
    # =====================================================
    def send_udp_packet(self, packet_text):
        try:
            ip = self.udp_ip_var.get().strip()
            port = int(self.udp_port_var.get().strip())
            self.udp_sock.sendto(packet_text.encode("utf-8"), (ip, port))
            return True, "UDP OK"
        except Exception as e:
            return False, f"UDP ERR: {e}"

    def send_tcp_json(self, payload):
        try:
            ip = self.db_ip_var.get().strip()
            port = int(self.db_port_var.get().strip())
            msg = json.dumps(payload, ensure_ascii=False) + "\n"

            with socket.create_connection((ip, port), timeout=0.25) as s:
                s.sendall(msg.encode("utf-8"))

            return True, "TCP OK"
        except Exception as e:
            return False, f"TCP ERR: {e}"

    def append_history(self, line):
        self.history_box.configure(state="normal")
        self.history_box.insert("end", line + "\n")
        self.history_box.see("end")
        self.history_box.configure(state="disabled")

    # =====================================================
    # DRAW
    # =====================================================
    def draw_overlay(self, frame, detection, payload):
        out = frame.copy()

        # Vẽ bounding box
        if detection["found"] and detection["bbox"] is not None:
            x, y, w, h = detection["bbox"]
            cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 2)

            color_bgr = {
                "red": (0, 0, 255),
                "green": (0, 180, 0),
                "blue": (255, 0, 0)
            }.get(detection["color"], (0, 0, 0))

            cv2.putText(
                out,
                detection["color"].upper(),
                (x, max(20, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color_bgr,
                2
            )

        status_color = (0, 0, 255) if self.fail_mode else (0, 140, 0)

        cv2.putText(
            out,
            f'Status: {payload["status"]}',
            (10, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            status_color,
            2
        )

        cv2.putText(
            out,
            f'Conf: {payload["confidence"]:.2f}',
            (10, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (30, 30, 30),
            2
        )

        return out

    # =====================================================
    # UI UPDATE
    # =====================================================
    def update_packet_box(self, payload):
        summary = f'Detected: {payload["object_color_detected"]} | Target bin: {payload["target_bin"]}'
        db_line = f'DB: {self.last_net_status}'

        self.packet_box.configure(state="normal")
        self.packet_box.delete("1.0", "end")
        self.packet_box.insert("1.0", summary + "\n")
        self.packet_box.insert("end", f"UDP: {self.last_udp_packet}\n")
        self.packet_box.insert("end", db_line)
        self.packet_box.configure(state="disabled")

    def update_status_label(self, text, ok=True):
        if ok:
            self.status_label.configure(bg="#dff0d8", fg="#1f5f1f")
        else:
            self.status_label.configure(bg="#ffd9d9", fg="#a10000")
        self.status_label.configure(text=text)

    # =====================================================
    # LOOP
    # =====================================================
    def update_loop(self):
        ret, frame = self.cap.read()

        if not ret:
            self.update_status_label("CAMERA ERROR", ok=False)
            self.root.after(80, self.update_loop)
            return

        detection = self.detect_object_and_color(frame)
        payload = self.build_payload(detection)

        udp_packet = self.format_udp_for_labview(payload)
        json_packet = json.dumps(payload, ensure_ascii=False)

        current_time = time.time()
        if current_time - self.last_send_time >= SEND_INTERVAL:
            udp_ok, udp_info = self.send_udp_packet(udp_packet)
            tcp_ok, tcp_info = self.send_tcp_json(payload)

            self.last_send_time = current_time
            self.last_udp_packet = udp_packet
            self.last_json_packet = json_packet
            self.last_net_status = f"{udp_info} | {tcp_info}"

            hist = (
                f'{payload["timestamp"]} | '
                f'{payload["status"]} | '
                f'{payload["object_color_detected"]} | '
                f'{payload["target_bin"]} | '
                f'{payload["confidence"]:.2f}'
            )
            self.append_history(hist)

            self.update_status_label(self.last_net_status, ok=(udp_ok and tcp_ok))

        # Draw and show frame
        frame = self.draw_overlay(frame, detection, payload)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = cv2.resize(frame_rgb, (376, 204))

        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        self.camera_label.imgtk = imgtk
        self.camera_label.configure(image=imgtk)

        self.update_packet_box(payload)
        self.root.after(40, self.update_loop)

    # =====================================================
    # CLOSE
    # =====================================================
    def on_close(self):
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass

        try:
            self.udp_sock.close()
        except Exception:
            pass

        self.root.destroy()


if __name__ == "__main__":
    SortingSimulatorApp()