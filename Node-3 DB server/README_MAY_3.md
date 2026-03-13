# README - MÁY 3 (Python Server + SQLite + Flask Dashboard)

## 1. Chức năng
MÁY 3 có nhiệm vụ:
- Nhận dữ liệu JSON từ MÁY 1 qua TCP.
- Lưu dữ liệu vào cơ sở dữ liệu SQLite.
- Hiển thị dữ liệu trên Dashboard web.
- Hỗ trợ tra cứu và xuất dữ liệu.

## 2. File sử dụng
- `SQlite-listen.py`  : TCP server nhận JSON và ghi SQLite
- `app.py`            : Flask dashboard
- `index.html`        : giao diện dashboard
- `query.html`        : giao diện truy vấn dữ liệu
- `robot_sorting.db`  : file cơ sở dữ liệu SQLite
- `requirements.txt`

## 3. Phần mềm cần cài
- Windows 10/11
- Python 3.10.x

## 4. Thư viện Python
Tạo file `requirements.txt` với nội dung:

```txt
flask
opencv-python
numpy
pillow
```

Ghi chú:
- MÁY 3 thực tế chỉ cần `flask` là đủ để chạy dashboard.
- Có thể dùng chung `requirements.txt` với MÁY 1 để tiện triển khai toàn hệ thống.

## 5. Cài môi trường ảo
Mở Command Prompt hoặc PowerShell tại thư mục chứa file `SQlite-listen.py` và `app.py`, sau đó chạy:

```bash
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 6. Cấu hình server
### TCP JSON Server
Theo code hiện tại:
- Host: `127.0.0.1`
- Port: `9100`

Nếu chạy liên máy qua mạng LAN, cần sửa trong file `SQlite-listen.py`:

```python
HOST = "0.0.0.0"
PORT = 9100
```

Giải thích:
- `127.0.0.1` chỉ nhận kết nối nội bộ trên chính MÁY 3.
- `0.0.0.0` cho phép MÁY 1 kết nối từ máy khác trong mạng LAN.

### Flask Dashboard
Theo code hiện tại:
- Host: `0.0.0.0`
- Port: `9123`

Sau khi chạy, có thể mở bằng trình duyệt tại:
- Trên chính MÁY 3: `http://127.0.0.1:9123`
- Từ máy khác trong LAN: `http://IP_MAY_3:9123`

Ví dụ:
- `http://192.168.1.30:9123`

## 7. Chạy hệ thống trên MÁY 3
### Bước 1 - Chạy TCP server ghi SQLite
```bash
python SQlite-listen.py
```

Nếu chạy thành công, màn hình sẽ hiển thị tương tự:
```text
[SYS] TCP JSON server listening on 0.0.0.0:9100
[SYS] SQLite DB: robot_sorting.db
```

### Bước 2 - Mở cửa sổ lệnh thứ hai và chạy Flask
```bash
python app.py
```

### Bước 3 - Mở trình duyệt
Truy cập:
```text
http://127.0.0.1:9123
```

## 8. Kiểm tra hoạt động
- Khi MÁY 1 gửi dữ liệu, cửa sổ `SQlite-listen.py` sẽ hiện log kết nối TCP.
- File `robot_sorting.db` sẽ được tạo tự động nếu chưa có.
- Dashboard sẽ hiển thị:
  - trạng thái mới nhất
  - tổng số sự kiện
  - thống kê màu
  - lịch sử sự kiện gần nhất
- Trang query cho phép lọc và xuất CSV.

## 9. Dữ liệu JSON nhận vào
Ví dụ JSON hợp lệ:

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

## 10. Lỗi thường gặp
### MÁY 1 không gửi được sang MÁY 3
- Kiểm tra `SQlite-listen.py` đã chạy chưa.
- Kiểm tra port `9100`.
- Nếu chạy khác máy, sửa `HOST = "0.0.0.0"`.
- Kiểm tra firewall Windows.

### Dashboard mở không lên
- Kiểm tra `app.py` đã chạy chưa.
- Kiểm tra port `9123` có bị ứng dụng khác chiếm không.
- Thử mở `http://127.0.0.1:9123` trước.

### Có dữ liệu DB nhưng dashboard không cập nhật
- Kiểm tra file `robot_sorting.db` có nằm cùng thư mục với `app.py` không.
- Kiểm tra cả `SQlite-listen.py` và `app.py` đang dùng cùng một file DB.

## 11. Trình tự chạy đề xuất
1. Chạy `SQlite-listen.py`.
2. Chạy `app.py`.
3. Mở dashboard trên trình duyệt.
4. Chạy MÁY 2.
5. Chạy MÁY 1 để bắt đầu gửi dữ liệu.
