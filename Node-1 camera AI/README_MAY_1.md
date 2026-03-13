# README - MÁY 1 (Python + Camera + AI nhẹ)

## 1. Chức năng
MÁY 1 có nhiệm vụ:
- Thu nhận hình ảnh từ camera.
- Xử lý ảnh và phân loại trạng thái.
- Tạo gói dữ liệu gửi sang MÁY 2 bằng UDP.
- Gửi JSON sang MÁY 3 bằng TCP để lưu cơ sở dữ liệu.

## 2. File sử dụng
- `camera.py`
- `requirements.txt`

## 3. Phần mềm cần cài
- Windows 10/11
- Python 3.10.x
- Camera USB hoặc webcam tích hợp

## 4. Thư viện Python
Tạo file `requirements.txt` với nội dung:

```txt
opencv-python
numpy
pillow
flask
```

Ghi chú:
- `tkinter` là thư viện đi kèm Python trên Windows, không cần cài bằng pip.
- Máy 1 chủ yếu dùng `opencv-python`, `numpy`, `pillow`.

## 5. Cài môi trường ảo
Mở Command Prompt hoặc PowerShell tại thư mục chứa file `camera.py`, sau đó chạy:

```bash
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 6. Cấu hình trước khi chạy
Trong giao diện chương trình hoặc trong phần cấu hình, cần kiểm tra:
- IP MÁY 2: địa chỉ máy chạy LabVIEW
- UDP Port MÁY 2: `9000`
- IP MÁY 3: địa chỉ máy chạy server SQLite
- TCP Port MÁY 3: `9100`

Theo code hiện tại:
- UDP mặc định: `0.0.0.0:9000`
- DB mặc định: `0.0.0.0:9100`

Khi chạy thực tế qua mạng LAN, nên đổi `0.0.0.0` thành IP thật của MÁY 2 và MÁY 3.

Ví dụ:
- MÁY 2: `192.168.1.20:9000`
- MÁY 3: `192.168.1.30:9100`

## 7. Chạy chương trình
```bash
python camera.py
```

## 8. Cách vận hành
1. Mở camera trong giao diện MÁY 1.
2. Kiểm tra vùng nhập IP/Port bên phải giao diện.
3. Đưa vật thể màu vào camera hoặc dùng dữ liệu giả lập.
4. Quan sát:
   - Gói UDP gửi sang MÁY 2
   - Gói JSON gửi sang MÁY 3
   - Lịch sử gửi dữ liệu

## 9. Dữ liệu gửi đi
### 9.1. Chuỗi gửi sang LabVIEW (UDP)
Dữ liệu có dạng chuỗi text để LabVIEW parse theo format string.

Ví dụ:
```text
R01 2026-03-07_21:15:12 SORTING red red_bin success 0.94
```

### 9.2. JSON gửi sang MÁY 3 (TCP)
Ví dụ:
```json
{
  "robot_id": "R01",
  "timestamp": "2026-03-07_21:15:12",
  "status": "SORTING",
  "object_color_detected": "red",
  "target_bin": "red_bin",
  "action_result": "success",
  "confidence": 0.94
}
```

## 10. Kiểm tra nhanh
- Nếu camera hiển thị hình ảnh: camera hoạt động.
- Nếu ô lịch sử có log gửi dữ liệu: chương trình đang chạy đúng.
- Nếu MÁY 2 nhận được chuỗi UDP: kết nối MÁY 1 -> MÁY 2 thành công.
- Nếu MÁY 3 ghi được SQLite: kết nối MÁY 1 -> MÁY 3 thành công.

## 11. Lỗi thường gặp
### Không mở được camera
- Kiểm tra webcam có đang bị phần mềm khác chiếm dụng không.
- Thử đổi `CAMERA_INDEX` trong `camera.py` từ `0` sang `1`.

### Gửi được nhưng MÁY 2 không nhận
- Kiểm tra đúng IP MÁY 2 chưa.
- Kiểm tra port UDP là `9000`.
- Tắt firewall hoặc mở port UDP tương ứng.

### Gửi được nhưng MÁY 3 không lưu DB
- Kiểm tra MÁY 3 đã chạy `SQlite-listen.py` chưa.
- Kiểm tra IP và port TCP `9100`.

## 12. Trình tự chạy đề xuất
1. Chạy MÁY 3 trước.
2. Chạy MÁY 2 tiếp theo.
3. Cuối cùng chạy MÁY 1 để phát dữ liệu.
