# README - MÁY 2 (LabVIEW + PLC GX Works)

## 1. Chức năng
MÁY 2 có nhiệm vụ:
- Nhận dữ liệu từ MÁY 1 bằng UDP.
- Parse chuỗi dữ liệu trong LabVIEW.
- Hiển thị dữ liệu trên Front Panel.
- Gửi dữ liệu sang PLC mô phỏng thông qua MX Component.

## 2. File sử dụng
- File LabVIEW chính: `... .vi`
- Project PLC GX Works: `...`
- Cấu hình MX Component: theo PLC mô phỏng đang dùng

## 3. Phần mềm cần cài
- LabVIEW
- GX Works / GX Works2 hoặc GX Works3
- MX Component
- PLC Simulator tương ứng (nếu dùng mô phỏng)

## 4. Chuẩn bị trước khi chạy
Cần có sẵn:
- File VI LabVIEW nhận UDP
- Project PLC mô phỏng
- Ánh xạ biến giữa LabVIEW và PLC

Ví dụ các biến PLC:
- `STATUS`
- `ERROR_CODE`
- `OPERATE`
- `DECISION`
- `FIX_DONE`
- `ALARM`

## 5. Cấu hình mạng
- IP của MÁY 2: địa chỉ LAN của máy chạy LabVIEW
- Port UDP nhận dữ liệu: `9000`

MÁY 1 sẽ gửi chuỗi dữ liệu đến địa chỉ này.

Ví dụ:
- MÁY 2: `192.168.1.20`
- UDP Port: `9000`

## 6. Format dữ liệu nhận từ MÁY 1
Ví dụ chuỗi dữ liệu:

```text
R01 2026-03-07_21:15:12 SORTING red red_bin success 0.94
```

Format parse trong LabVIEW:

```text
%s %<%Y-%m-%d_%H:%M:%S>T %s %s %s %s %f
```

Thứ tự trường dữ liệu:
1. Robot ID
2. Timestamp
3. Status
4. Object Color
5. Target Bin
6. Action Result
7. Confidence

## 7. Trình tự chạy
### Bước 1 - Mở PLC mô phỏng
- Mở GX Works.
- Mở project PLC.
- Nạp hoặc chạy PLC Simulator.
- Kiểm tra PLC ở trạng thái RUN.

### Bước 2 - Kiểm tra MX Component
- Mở cấu hình kết nối trong MX Component.
- Chọn đúng loại PLC và cổng truyền thông.
- Kiểm tra kết nối từ máy tính đến PLC mô phỏng.

### Bước 3 - Mở VI LabVIEW
- Mở file VI chính.
- Kiểm tra các control/indicator trên Front Panel.
- Kiểm tra port UDP đang lắng nghe là `9000`.

### Bước 4 - Chạy UDP Listener
- Nhấn Run trên LabVIEW.
- Đảm bảo chương trình đang ở trạng thái lắng nghe.

### Bước 5 - Kiểm tra dữ liệu
- Chạy MÁY 1.
- Quan sát dữ liệu xuất hiện trong LabVIEW.
- Kiểm tra dữ liệu đã được ghi xuống vùng nhớ PLC.

## 8. Hướng dẫn kiểm tra tín hiệu PLC
Cần lập bảng ánh xạ địa chỉ PLC thực tế, ví dụ:

| Biến | Kiểu | Địa chỉ PLC | Ý nghĩa |
|---|---|---|---|
| STATUS | BOOL/WORD | ... | Trạng thái hệ thống |
| ERROR_CODE | WORD | ... | Mã lỗi |
| OPERATE | BOOL | ... | Cho phép chạy |
| DECISION | WORD | ... | Kết quả phân loại |
| FIX_DONE | BOOL | ... | Sửa lỗi xong |
| ALARM | BOOL | ... | Cảnh báo |

## 9. Lỗi thường gặp
### LabVIEW không nhận được UDP
- Kiểm tra port `9000` có đúng không.
- Kiểm tra firewall Windows.
- Kiểm tra đúng IP MÁY 2 trên MÁY 1.

### Parse sai dữ liệu
- Kiểm tra chuỗi gửi từ MÁY 1 có đúng thứ tự trường không.
- Kiểm tra format string trong LabVIEW.
- Kiểm tra timestamp có đúng định dạng `YYYY-MM-DD_HH:MM:SS` không.

### Gửi PLC không thành công
- Kiểm tra MX Component đã cấu hình đúng chưa.
- Kiểm tra PLC đang RUN chưa.
- Kiểm tra lại địa chỉ vùng nhớ PLC.

## 10. Trình tự chạy đề xuất
1. Mở GX Works và PLC mô phỏng.
2. Mở LabVIEW VI.
3. Run UDP Listener.
4. Chạy MÁY 3.
5. Chạy MÁY 1 để phát dữ liệu.
