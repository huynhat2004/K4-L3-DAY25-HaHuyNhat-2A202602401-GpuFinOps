# Bài phân tích — GPU FinOps cho NimbusAI

## 1. Chi phí ban đầu và kết quả tối ưu

Chi phí ban đầu là **$27,133/tháng**, sau tối ưu còn **$14,627/tháng**. NimbusAI tiết kiệm **$12,506/tháng (46.1%)**. Riêng suy luận, chi phí giảm từ **$48.87 xuống $8.51/ngày**; đơn giá chuẩn hóa giảm từ **$6.488 xuống $1.129/1M-token (82.6%)**. $/1M-token là KPI phù hợp hơn $/GPU-giờ vì phản ánh lượng sản phẩm thực sự phục vụ.

## 2. Phân tích các đòn bẩy

Đòn bẩy lớn nhất là **Mua tài nguyên (spot/reserved)**, tiết kiệm **$10,040/tháng**. Spot phù hợp với tác vụ có thể gián đoạn và checkpoint; reserved phù hợp khối lượng công việc ổn định vượt điểm hòa vốn 55%. Cascade đưa yêu cầu đơn giản sang mô hình nhỏ, cache giảm chi phí đầu vào lặp lại và batch giảm 50% cho lưu lượng không nhạy độ trễ. Điều chỉnh GPU hiệu suất thấp và tắt GPU nhàn rỗi lần lượt tiết kiệm **$655** và **$600/tháng**.

## 3. GPU-Util lie

Các GPU bị gắn cờ là **gpu-h100-4, gpu-a10g-1**. Đặc biệt `gpu-h100-4` báo GPU-Util xấp xỉ 98% nhưng MFU chỉ khoảng 20%. GPU-Util chỉ cho biết GPU có bận trong cửa sổ lấy mẫu; memory stall, truyền dữ liệu hoặc kernel overhead vẫn có thể làm FLOPs hữu ích thấp. Nếu chỉ nhìn `nvidia-smi`, công ty có thể tiếp tục trả tiền H100 dù workload phù hợp GPU nhỏ hơn. Cơ hội right-size ước tính **$655/tháng**; idle waste là **$600/tháng**.

## 4. Các phần mở rộng đã thực hiện

**Hiệu quả kinh tế của cache:** hệ thống tính số lần đọc hòa vốn trước khi áp dụng cache và cộng cả chi phí khởi tạo cache. Có **16/16** nhóm tiền tố đạt ngưỡng. Tầng mô hình `small` cần **1.67** lần đọc, tầng `large` cần **1.39** lần. Kết luận: cache không mặc nhiên tiết kiệm; số lần tái sử dụng phải đủ bù chi phí ghi.

**Ngân sách reasoning:** reasoning chỉ chiếm **8.4% số yêu cầu** nhưng chiếm **16.5% chi phí** và **94.0% năng lượng**. Mô phỏng giới hạn 5% hạ 81 yêu cầu đơn giản xuống chế độ thường, tiết kiệm **$0.194/ngày** và **7.65 kWh/ngày**. Quy tắc đề xuất là chỉ bật reasoning khi bộ phân loại đánh giá tác vụ khó hoặc mô hình nhỏ có độ tin cậy thấp.

**Lập lịch có xét đến carbon:** khối lượng công việc có thể gián đoạn tiêu thụ **1,789.0 kWh**. Chuyển từ `us-east-1` sang `europe-north1` giảm **626.1 kgCO2e (92.1%)**. `us-east-wa` rẻ nhất, `europe-north1` sạch nhất, còn `us-east-wa` là lựa chọn cân bằng theo trọng số 50/50. Cần kiểm tra độ trễ và yêu cầu lưu trú dữ liệu trước khi di chuyển lưu lượng trực tuyến.

## 5. Ba hành động ưu tiên

1. Áp dụng spot + checkpoint cho job interruptible và reserved cho workload ổn định; theo dõi savings thực tế hàng tháng.
2. Đưa cascade, cache gate và batch vào gateway inference, dùng $/1M-token làm KPI theo team/project.
3. Điều tra GPU có MFU thấp, tắt tài nguyên idle, đồng thời áp reasoning budget và lịch carbon-aware cho batch/training.

Số liệu giá và carbon là ảnh chụp tại thời điểm tháng 6/2026; cần thiết lập lại baseline trước khi ra quyết định sản xuất.
