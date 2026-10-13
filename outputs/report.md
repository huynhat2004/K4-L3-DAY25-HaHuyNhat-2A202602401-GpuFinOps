# NimbusAI — Báo cáo tối ưu chi phí GPU

**Kỳ báo cáo:** hàng tháng
**Chi phí ban đầu:** $27,133
**Chi phí sau tối ưu:** $14,627
**Tiết kiệm dự kiến (Projected savings):** $12,506  (**46%**)

## Tiết kiệm theo từng đòn bẩy

| Đòn bẩy | Tiết kiệm (USD) |
|---|---|
| Suy luận (cascade/cache/batch) | $1,211 |
| Mua tài nguyên (spot/reserved) | $10,040 |
| Điều chỉnh GPU hiệu suất thấp | $655 |
| Tắt GPU nhàn rỗi | $600 |

## Hiệu quả kinh tế theo đơn vị

| Chỉ số | Ban đầu | Sau tối ưu | Thay đổi |
|---|---:|---:|---:|
| Chi phí suy luận/ngày | $48.87 | $8.51 | tiết kiệm 82.6% |
| $/1M-token | $6.488 | $1.129 | tiết kiệm 82.6% |

Chỉ số chuẩn hóa $/1M-token phản ánh sản lượng thực tế; nếu chỉ nhìn $/GPU-giờ, GPU có thể trông rẻ nhưng hiệu suất thấp vẫn làm mỗi token hữu ích trở nên đắt đỏ.

## Kiểm toán hiệu suất

- GPU có GPU-Util gây hiểu nhầm: gpu-h100-4, gpu-a10g-1.
- Lãng phí do nhàn rỗi: $20.00/ngày ($600/tháng).
- Cơ hội tiết kiệm khi điều chỉnh cấu hình: $655/tháng.

GPU-Util cao chỉ cho biết bộ máy thực thi bận trong khoảng lấy mẫu, không đo lượng FLOPs hữu ích của mô hình. Nghẽn bộ nhớ, di chuyển dữ liệu và chi phí khởi chạy kernel có thể khiến GPU-Util cao nhưng MFU vẫn thấp.

## Phân bổ chi phí

Độ phủ thẻ là 91.8%; sẵn sàng chargeback: **Có**.

| Nhóm | Chi phí suy luận sau tối ưu/ngày |
|---|---:|
| assistant | $2.59 |
| search | $2.49 |
| eval | $1.79 |
| rag | $1.60 |

## Các phần mở rộng đã thực hiện

### Phần mở rộng 3 — Điều kiện kinh tế cho cache

Cache đạt điều kiện kinh tế ở **16/16** nhóm tiền tố đã quan sát. Chi phí khởi tạo cache là $0.0213/ngày và đã được tính vào chi phí sau tối ưu.

| Tầng mô hình | Chi phí ghi cache $/1M | Số lần đọc hòa vốn |
|---|---:|---:|
| small | $0.30 | 1.67 |
| large | $3.75 | 1.39 |

### Phần mở rộng 4 — Ngân sách reasoning

Reasoning chiếm **8.4%** số yêu cầu và 16.5% số token, nhưng tạo ra **16.5%** chi phí suy luận sau tối ưu và **94.0%** năng lượng phục vụ.
Giới hạn reasoning ở 5% lưu lượng sẽ hạ 81 yêu cầu đơn giản xuống chế độ thường, tiết kiệm $0.194/ngày và 7.65 kWh/ngày.

Chính sách đề xuất: chỉ cho phép reasoning khi bộ phân loại đánh giá tác vụ đủ phức tạp hoặc mô hình nhỏ có độ tin cậy dưới ngưỡng; ghi lại mọi lần ghi đè chính sách.

### Phần mở rộng 5 — Lập lịch có xét đến carbon

Nhóm khối lượng công việc có thể gián đoạn tiêu thụ 1,789.0 kWh. Di chuyển từ us-east-1 sang europe-north1 giúp giảm 626.1 kgCO2e (92.1%).

| Khu vực | $/kWh | gCO2/kWh | Chi phí điện | Phát thải |
|---|---:|---:|---:|---:|
| europe-central2 | $0.180 | 660 | $322.02 | 1,180.7 kg |
| europe-north1 | $0.090 | 30 | $161.01 | 53.7 kg |
| us-east-1 | $0.120 | 380 | $214.68 | 679.8 kg |
| us-east-wa | $0.055 | 90 | $98.39 | 161.0 kg |
| us-west-2 | $0.070 | 120 | $125.23 | 214.7 kg |

Rẻ nhất: **us-east-wa**; sạch nhất: **europe-north1**; lựa chọn cân bằng với trọng số 50/50: **us-east-wa**. Chỉ nên di chuyển khối lượng công việc có thể gián đoạn; suy luận phục vụ người dùng vẫn cần đánh giá độ trễ và yêu cầu lưu trú dữ liệu.

## Hành động ưu tiên

1. Áp dụng spot kèm checkpoint và reserved cho các khối lượng công việc phù hợp; đây là đòn bẩy tiết kiệm tiền lớn nhất đã đo được.
2. Áp dụng điều kiện cache, định tuyến cascade và tiêu chí batch; giám sát bằng $/1M-token.
3. Xử lý GPU có GPU-Util gây hiểu nhầm hoặc nhàn rỗi; quản trị reasoning và lập lịch có xét carbon.

## Tính bền vững

- Năng lượng mỗi truy vấn: 0.24 Wh
- Phát thải mỗi truy vấn: 0.091 gCO2e
- Khu vực rẻ nhất: us-east-wa
- Khu vực sạch nhất: europe-north1
- Khu vực cân bằng: us-east-wa

_Số liệu là ảnh chụp tại thời điểm tháng 6/2026; cần thiết lập lại baseline trước khi áp dụng._