"""Report assembly — the lab's deliverable: baseline vs optimized + savings chart."""
from __future__ import annotations


def build_report(baseline_usd: float, optimized_usd: float, levers: dict,
                 sustainability: dict | None = None, period: str = "monthly",
                 analysis: dict | None = None) -> str:
    """Tạo báo cáo tối ưu chi phí ở định dạng Markdown."""
    savings = baseline_usd - optimized_usd
    pct = (savings / baseline_usd * 100.0) if baseline_usd > 0 else 0.0
    lines = [
        "# NimbusAI — Báo cáo tối ưu chi phí GPU",
        "",
        f"**Kỳ báo cáo:** {'hàng tháng' if period == 'monthly' else period}",
        f"**Chi phí ban đầu:** ${baseline_usd:,.0f}",
        f"**Chi phí sau tối ưu:** ${optimized_usd:,.0f}",
        f"**Tiết kiệm dự kiến (Projected savings):** ${savings:,.0f}  (**{pct:.0f}%**)",
        "",
        "## Tiết kiệm theo từng đòn bẩy",
        "",
        "| Đòn bẩy | Tiết kiệm (USD) |",
        "|---|---|",
    ]
    for name, amount in levers.items():
        lines.append(f"| {name} | ${amount:,.0f} |")
    if analysis:
        unit = analysis.get("unit_economics", {})
        lines += [
            "",
            "## Hiệu quả kinh tế theo đơn vị",
            "",
            "| Chỉ số | Ban đầu | Sau tối ưu | Thay đổi |",
            "|---|---:|---:|---:|",
            f"| Chi phí suy luận/ngày | ${unit.get('baseline_daily', 0):,.2f} | "
            f"${unit.get('optimized_daily', 0):,.2f} | tiết kiệm {unit.get('savings_pct', 0):.1f}% |",
            f"| $/1M-token | ${unit.get('baseline_per_m', 0):,.3f} | "
            f"${unit.get('optimized_per_m', 0):,.3f} | tiết kiệm {unit.get('savings_pct', 0):.1f}% |",
            "",
            "Chỉ số chuẩn hóa $/1M-token phản ánh sản lượng thực tế; nếu chỉ nhìn $/GPU-giờ, "
            "GPU có thể trông rẻ nhưng hiệu suất thấp vẫn làm mỗi token hữu ích trở nên đắt đỏ.",
        ]

        efficiency = analysis.get("efficiency", {})
        lines += [
            "",
            "## Kiểm toán hiệu suất",
            "",
            f"- GPU có GPU-Util gây hiểu nhầm: {', '.join(efficiency.get('lie_ids', [])) or 'không có'}.",
            f"- Lãng phí do nhàn rỗi: ${efficiency.get('idle_daily', 0):,.2f}/ngày "
            f"(${efficiency.get('idle_monthly', 0):,.0f}/tháng).",
            f"- Cơ hội tiết kiệm khi điều chỉnh cấu hình: "
            f"${efficiency.get('rightsize_monthly', 0):,.0f}/tháng.",
            "",
            "GPU-Util cao chỉ cho biết bộ máy thực thi bận trong khoảng lấy mẫu, không đo lượng "
            "FLOPs hữu ích của mô hình. Nghẽn bộ nhớ, di chuyển dữ liệu và chi phí khởi chạy kernel "
            "có thể khiến GPU-Util cao nhưng MFU vẫn thấp.",
        ]

        allocation = analysis.get("allocation", {})
        lines += [
            "",
            "## Phân bổ chi phí",
            "",
            f"Độ phủ thẻ là {allocation.get('tag_coverage', 0):.1%}; "
            f"sẵn sàng chargeback: **{'Có' if allocation.get('chargeback_ready', False) else 'Không'}**.",
            "",
            "| Nhóm | Chi phí suy luận sau tối ưu/ngày |",
            "|---|---:|",
        ]
        for team, amount in sorted(allocation.get("by_team", {}).items(), key=lambda item: -item[1]):
            lines.append(f"| {team} | ${amount:,.2f} |")

        cache = analysis.get("cache", {})
        reasoning = analysis.get("reasoning", {})
        carbon = analysis.get("carbon", {})
        lines += [
            "",
            "## Các phần mở rộng đã thực hiện",
            "",
            "### Phần mở rộng 3 — Điều kiện kinh tế cho cache",
            "",
            f"Cache đạt điều kiện kinh tế ở **{cache.get('qualified_groups', 0)}/"
            f"{cache.get('total_groups', 0)}** nhóm tiền tố đã quan sát. Chi phí khởi tạo cache là "
            f"${cache.get('write_cost_daily', 0):,.4f}/ngày và đã được tính vào chi phí sau tối ưu.",
            "",
            "| Tầng mô hình | Chi phí ghi cache $/1M | Số lần đọc hòa vốn |",
            "|---|---:|---:|",
        ]
        for tier, row in cache.get("by_tier", {}).items():
            lines.append(
                f"| {tier} | ${row['write_price_per_m']:.2f} | {row['break_even_reads']:.2f} |"
            )
        lines += [
            "",
            "### Phần mở rộng 4 — Ngân sách reasoning",
            "",
            f"Reasoning chiếm **{reasoning.get('request_share_pct', 0):.1f}%** số yêu cầu và "
            f"{reasoning.get('token_share_pct', 0):.1f}% số token, nhưng tạo ra "
            f"**{reasoning.get('cost_share_pct', 0):.1f}%** chi phí suy luận sau tối ưu và "
            f"**{reasoning.get('energy_share_pct', 0):.1f}%** năng lượng phục vụ.",
            f"Giới hạn reasoning ở {reasoning.get('cap_pct', 0):.0f}% lưu lượng sẽ hạ "
            f"{reasoning.get('downgraded_requests', 0)} yêu cầu đơn giản xuống chế độ thường, tiết kiệm "
            f"${reasoning.get('cap_savings_daily', 0):,.3f}/ngày và "
            f"{reasoning.get('cap_energy_savings_wh_daily', 0)/1000:,.2f} kWh/ngày.",
            "",
            "Chính sách đề xuất: chỉ cho phép reasoning khi bộ phân loại đánh giá tác vụ đủ phức tạp "
            "hoặc mô hình nhỏ có độ tin cậy dưới ngưỡng; ghi lại mọi lần ghi đè chính sách.",
            "",
            "### Phần mở rộng 5 — Lập lịch có xét đến carbon",
            "",
            f"Nhóm khối lượng công việc có thể gián đoạn tiêu thụ {carbon.get('energy_kwh', 0):,.1f} kWh. "
            f"Di chuyển từ {carbon.get('baseline_region', 'không có')} sang "
            f"{carbon.get('cleanest_region', 'không có')} giúp giảm "
            f"{carbon.get('carbon_saved_kg', 0):,.1f} kgCO2e "
            f"({carbon.get('carbon_reduction_pct', 0):.1f}%).",
            "",
            "| Khu vực | $/kWh | gCO2/kWh | Chi phí điện | Phát thải |",
            "|---|---:|---:|---:|---:|",
        ]
        for row in carbon.get("regions", []):
            lines.append(
                f"| {row['region']} | ${row['price_per_kwh']:.3f} | "
                f"{row['carbon_g_per_kwh']:.0f} | ${row['electricity_cost_usd']:,.2f} | "
                f"{row['carbon_kg']:,.1f} kg |"
            )
        lines += [
            "",
            f"Rẻ nhất: **{carbon.get('cheapest_region', 'không có')}**; sạch nhất: "
            f"**{carbon.get('cleanest_region', 'không có')}**; lựa chọn cân bằng với trọng số 50/50: "
            f"**{carbon.get('balanced_region', 'không có')}**. Chỉ nên di chuyển khối lượng công việc có thể "
            "gián đoạn; suy luận phục vụ người dùng vẫn cần đánh giá độ trễ và yêu cầu lưu trú dữ liệu.",
            "",
            "## Hành động ưu tiên",
            "",
            "1. Áp dụng spot kèm checkpoint và reserved cho các khối lượng công việc phù hợp; đây là đòn bẩy "
            "tiết kiệm tiền lớn nhất đã đo được.",
            "2. Áp dụng điều kiện cache, định tuyến cascade và tiêu chí batch; giám sát bằng $/1M-token.",
            "3. Xử lý GPU có GPU-Util gây hiểu nhầm hoặc nhàn rỗi; quản trị reasoning và lập lịch có xét carbon.",
        ]
    if sustainability:
        lines += [
            "",
            "## Tính bền vững",
            "",
            f"- Năng lượng mỗi truy vấn: {sustainability.get('wh_per_query', 0):.2f} Wh",
            f"- Phát thải mỗi truy vấn: {sustainability.get('carbon_g', 0):.3f} gCO2e",
            f"- Khu vực rẻ nhất: {sustainability.get('cheapest_region', 'không có')}",
            f"- Khu vực sạch nhất: {sustainability.get('cleanest_region', 'không có')}",
            f"- Khu vực cân bằng: {sustainability.get('balanced_region', 'không có')}",
        ]
    lines += ["", "_Số liệu là ảnh chụp tại thời điểm tháng 6/2026; cần thiết lập lại baseline trước khi áp dụng._"]
    return "\n".join(lines)


def build_writeup(baseline_usd: float, optimized_usd: float, levers: dict,
                  analysis: dict) -> str:
    """Build the required concise Vietnamese submission write-up."""
    savings = baseline_usd - optimized_usd
    savings_pct = savings / baseline_usd * 100 if baseline_usd else 0.0
    unit = analysis["unit_economics"]
    efficiency = analysis["efficiency"]
    cache = analysis["cache"]
    reasoning = analysis["reasoning"]
    carbon = analysis["carbon"]
    largest_name, largest_value = max(levers.items(), key=lambda item: item[1])
    return f"""# Bài phân tích — GPU FinOps cho NimbusAI

## 1. Chi phí ban đầu và kết quả tối ưu

Chi phí ban đầu là **${baseline_usd:,.0f}/tháng**, sau tối ưu còn **${optimized_usd:,.0f}/tháng**. NimbusAI tiết kiệm **${savings:,.0f}/tháng ({savings_pct:.1f}%)**. Riêng suy luận, chi phí giảm từ **${unit['baseline_daily']:.2f} xuống ${unit['optimized_daily']:.2f}/ngày**; đơn giá chuẩn hóa giảm từ **${unit['baseline_per_m']:.3f} xuống ${unit['optimized_per_m']:.3f}/1M-token ({unit['savings_pct']:.1f}%)**. $/1M-token là KPI phù hợp hơn $/GPU-giờ vì phản ánh lượng sản phẩm thực sự phục vụ.

## 2. Phân tích các đòn bẩy

Đòn bẩy lớn nhất là **{largest_name}**, tiết kiệm **${largest_value:,.0f}/tháng**. Spot phù hợp với tác vụ có thể gián đoạn và checkpoint; reserved phù hợp khối lượng công việc ổn định vượt điểm hòa vốn 55%. Cascade đưa yêu cầu đơn giản sang mô hình nhỏ, cache giảm chi phí đầu vào lặp lại và batch giảm 50% cho lưu lượng không nhạy độ trễ. Điều chỉnh GPU hiệu suất thấp và tắt GPU nhàn rỗi lần lượt tiết kiệm **${levers['Điều chỉnh GPU hiệu suất thấp']:,.0f}** và **${levers['Tắt GPU nhàn rỗi']:,.0f}/tháng**.

## 3. GPU-Util lie

Các GPU bị gắn cờ là **{', '.join(efficiency['lie_ids'])}**. Đặc biệt `gpu-h100-4` báo GPU-Util xấp xỉ 98% nhưng MFU chỉ khoảng 20%. GPU-Util chỉ cho biết GPU có bận trong cửa sổ lấy mẫu; memory stall, truyền dữ liệu hoặc kernel overhead vẫn có thể làm FLOPs hữu ích thấp. Nếu chỉ nhìn `nvidia-smi`, công ty có thể tiếp tục trả tiền H100 dù workload phù hợp GPU nhỏ hơn. Cơ hội right-size ước tính **${efficiency['rightsize_monthly']:,.0f}/tháng**; idle waste là **${efficiency['idle_monthly']:,.0f}/tháng**.

## 4. Các phần mở rộng đã thực hiện

**Hiệu quả kinh tế của cache:** hệ thống tính số lần đọc hòa vốn trước khi áp dụng cache và cộng cả chi phí khởi tạo cache. Có **{cache['qualified_groups']}/{cache['total_groups']}** nhóm tiền tố đạt ngưỡng. Tầng mô hình `small` cần **{cache['by_tier']['small']['break_even_reads']:.2f}** lần đọc, tầng `large` cần **{cache['by_tier']['large']['break_even_reads']:.2f}** lần. Kết luận: cache không mặc nhiên tiết kiệm; số lần tái sử dụng phải đủ bù chi phí ghi.

**Ngân sách reasoning:** reasoning chỉ chiếm **{reasoning['request_share_pct']:.1f}% số yêu cầu** nhưng chiếm **{reasoning['cost_share_pct']:.1f}% chi phí** và **{reasoning['energy_share_pct']:.1f}% năng lượng**. Mô phỏng giới hạn {reasoning['cap_pct']:.0f}% hạ {reasoning['downgraded_requests']} yêu cầu đơn giản xuống chế độ thường, tiết kiệm **${reasoning['cap_savings_daily']:.3f}/ngày** và **{reasoning['cap_energy_savings_wh_daily']/1000:.2f} kWh/ngày**. Quy tắc đề xuất là chỉ bật reasoning khi bộ phân loại đánh giá tác vụ khó hoặc mô hình nhỏ có độ tin cậy thấp.

**Lập lịch có xét đến carbon:** khối lượng công việc có thể gián đoạn tiêu thụ **{carbon['energy_kwh']:,.1f} kWh**. Chuyển từ `{carbon['baseline_region']}` sang `{carbon['cleanest_region']}` giảm **{carbon['carbon_saved_kg']:,.1f} kgCO2e ({carbon['carbon_reduction_pct']:.1f}%)**. `{carbon['cheapest_region']}` rẻ nhất, `{carbon['cleanest_region']}` sạch nhất, còn `{carbon['balanced_region']}` là lựa chọn cân bằng theo trọng số 50/50. Cần kiểm tra độ trễ và yêu cầu lưu trú dữ liệu trước khi di chuyển lưu lượng trực tuyến.

## 5. Ba hành động ưu tiên

1. Áp dụng spot + checkpoint cho job interruptible và reserved cho workload ổn định; theo dõi savings thực tế hàng tháng.
2. Đưa cascade, cache gate và batch vào gateway inference, dùng $/1M-token làm KPI theo team/project.
3. Điều tra GPU có MFU thấp, tắt tài nguyên idle, đồng thời áp reasoning budget và lịch carbon-aware cho batch/training.

Số liệu giá và carbon là ảnh chụp tại thời điểm tháng 6/2026; cần thiết lập lại baseline trước khi ra quyết định sản xuất.
"""


def savings_waterfall(levers: dict, path: str) -> str:
    """Write a four-lever descending savings waterfall chart."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return ""
    names = list(levers.keys())
    vals = [float(levers[n]) for n in names]
    remaining = sum(vals)
    bottoms = []
    for value in vals:
        remaining -= value
        bottoms.append(remaining)

    fig, ax = plt.subplots(figsize=(9, 5))
    x = list(range(len(names)))
    colors = ["#2e548a", "#238b45", "#756bb1", "#d95f0e"]
    bars = ax.bar(x, vals, bottom=bottoms, color=colors[:len(vals)], width=0.72)
    for index in range(len(vals) - 1):
        ax.plot(
            [index + 0.36, index + 1 - 0.36],
            [bottoms[index], bottoms[index]],
            color="#666666", linewidth=1, linestyle="--",
        )
    for bar, value in zip(bars, vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_y() + bar.get_height() / 2,
            f"-${value:,.0f}", ha="center", va="center", color="white", fontweight="bold",
        )
    ax.set_xticks(x, names)
    ax.set_ylabel("Tiết kiệm (USD/tháng)")
    ax.set_title(f"Biểu đồ thác nước tiết kiệm chi phí GPU — tổng ${sum(vals):,.0f}/tháng")
    ax.grid(axis="y", alpha=0.2)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
