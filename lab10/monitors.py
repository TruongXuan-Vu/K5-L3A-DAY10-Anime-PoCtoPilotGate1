"""★ FILE ĐỘI SỬA (2/3): chỉ số theo dõi (monitor). Thêm ÍT NHẤT MỘT chỉ số bắt được sự cố của bàn.

Mỗi monitor nhận danh sách trial (KHÔNG có nhãn đúng/sai, giống production) và trả về một số.
Một trial = {"ticket_id", "seed", "day", "status", "amount_vnd", "ticket", "events", "ledger", "faults", "outbound",
             "arrive_min", "warehouse", "cost_vnd", "review_kind", "queue_wait_min", "queue_stuck"}
  "day"            một ngày vận hành giả lập: các ticket cùng "day" và cùng "seed" chạy nối nhau trên cùng một sổ cái
  "arrive_min"     phút ticket tới trong ca (0..480)          "warehouse"   kho của đơn
  "cost_vnd"       tiền LLM + nền tảng đã tốn cho ticket      "review_kind" None / "escalated" (trợ lý chuyển người) /
  "queue_wait_min" số phút chờ người duyệt (None nếu không vào hàng chờ)     "recheck" (nhân viên tự kiểm lại)
Chỉ số có thể là kỹ thuật (tỉ lệ model đè số trong ticket lên DB), vận hành (số ca cần người trong giờ đông nhất),
hay kinh doanh (tỉ lệ ticket trợ lý đọc xong vẫn phải chuyển người).

lab10.grade kiểm: monitor chạy không lỗi, và giá trị trên gói sự cố khác giá trị trên bộ nền,
tức là monitor "sáng đèn" khi sự cố xảy ra.
"""


def escalation_rate(trials):
    return sum(t["status"] == "escalated" for t in trials) / max(1, len(trials))


def claim_mismatch_rate(trials):
    """Tỉ lệ trial mà số ngày trễ do khách tự ghi khác tracking DB (model_override)."""
    bad = 0
    total = 0
    for t in trials:
        for e in (t.get("events") or []):
            if e.get("type") == "model_override":
                total += 1
                if e.get("db") != e.get("ticket"):
                    bad += 1
            if e.get("type") == "tracking":
                total = total or 1
    # mẫu số = số trial có sự kiện proposal (đã qua bước tracking)
    denom = sum(1 for t in trials if any(e.get("type") == "proposal" for e in (t.get("events") or [])))
    if denom == 0:
        return 0.0
    # đếm trial có ít nhất một model_override khác db
    bad_trials = 0
    for t in trials:
        mm = False
        for e in (t.get("events") or []):
            if e.get("type") == "model_override" and e.get("db") != e.get("ticket"):
                mm = True
        if mm:
            bad_trials += 1
    return bad_trials / denom


def pii_leak_rate(trials):
    """Tỉ lệ trial có thông tin người nhận bị gửi cho hãng (payload chứa recipient_contact)."""
    bad = 0
    for t in trials:
        for e in (t.get("events") or []):
            if e.get("type") == "tool" and e.get("tool") == "notify_carrier":
                payload = e.get("payload") or {}
                if "recipient_contact" in payload:
                    bad += 1
                    break
    return bad / max(1, len(trials))


def cost_per_ticket(trials):
    return sum(t.get("cost_vnd", 0) for t in trials) / max(1, len(trials))


MONITORS = {
    "escalation_rate": escalation_rate,     # có sẵn; KHÔNG tính là metric mới của đội
    "claim_mismatch_rate": claim_mismatch_rate,
    "pii_leak_rate": pii_leak_rate,
    "cost_per_ticket": cost_per_ticket,
}
STARTER_MONITORS = ("escalation_rate",)
