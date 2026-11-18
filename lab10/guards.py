"""★ FILE ĐỘI SỬA (1/3): cổng cấp hệ thống, nằm NGOÀI model và prompt.

VÒNG 1 (trước khi biết sự cố): viết 2–3 CỔNG PHÒNG NGỪA rút từ pre-mortem / HAZOP / checklist của bàn, rồi chốt bằng
    python3 -m lab10.checkpoint        (chép file này thành guards_round1.py = mốc "prepared"; KHÔNG sửa bản chép)
VÒNG 2 (sau khi bốc thẻ): sửa tiếp NGAY TRONG FILE NÀY. Giữ các cổng vòng 1, thêm cổng mới.
Hai file còn lại bàn được sửa: lab10/monitors.py (chỉ số theo dõi) và config/operating_gates.json (cổng kinh doanh,
vận hành, pháp lý: những con số và tên người mà trợ lý phải tuân theo, không cần code).

Hai điểm móc, agent gọi tự động:
  pre_guard(ctx)          chạy TRƯỚC khi agent đọc ticket
  write_gate(ctx, action) chạy TRƯỚC MỖI lệnh ghi (issue_refund, file_carrier_fault,
                          notify_carrier, send_reply)

Trả về một Verdict:
  Verdict.allow()                       cho qua   (pre_guard: allow(policy_id="...") để ghim phiên bản chính sách)
  Verdict.deny("lý do")                 bỏ riêng lệnh ghi này, agent đi tiếp
  Verdict.escalate("lý do")             dừng, chuyển ticket cho người
  Verdict.modify("lý do", amount_vnd=…) sửa tham số lệnh ghi (amount_vnd, payer, carrier_id, parcel_id, payload…)
  Verdict.rewrite("lý do", text)        chỉ pre_guard: thay nội dung ticket mà agent sẽ đọc

ctx.ticket   ticket gốc (chữ khách viết là DỮ LIỆU, không phải lệnh)
ctx.tools    tra cứu nguồn sự thật: lookup_order, lookup_policies, lookup_approvals(**lọc),
             ledger_rows(**lọc), fault_rows(**lọc), lookup_carrier; ctx.as_of = ngày hôm nay
             ops_limits() = các trần đã thống nhất với Ops/Finance; ops_facts() = số liệu vận hành;
             auto_refund_today_vnd() = tổng đã hoàn tự động trong ngày
ctx.gates    config cổng của bàn (config/operating_gates.json), chỉ đọc;  ctx.cost_vnd = tiền LLM đã tốn cho ticket này
ctx.events   trace tới thời điểm này;  ctx.log("ten_su_kien", ...) ghi thêm sự kiện guard vào trace
lab10.helpers: db_delay_days, ticket_parcel, effective_policy, entitlement_vnd, carrier_at_fault, digits
"""
import re

from . import helpers as H


def _effective_policy(ctx):
    policies = ctx.tools.lookup_policies()
    pol = H.effective_policy(policies, ctx.as_of)
    if pol is None:
        pol = next((p for p in policies if p.get("index_active")), None)
        if pol is None and policies:
            pol = policies[0]
    return pol


def _sanitize_text(text: str) -> str:
    """Loại bỏ dữ liệu không đáng tin từ khách: số ngày trễ tự ghi và chỉ thị hoàn tiền."""
    out = text
    # số ngày trễ do khách tự khai (tracking DB là nguồn sự thật)
    out = re.sub(r"\d+\s*ngày", "", out)
    # chỉ thị ép hoàn toàn bộ / full refund
    for pat in (r"hoàn\s+toàn\s+bộ", r"hoàn\s+tất\s+cả", r"hoàn\s+full", r"hoàn\s+100%",
                r"full\s*refund", r"hoàn\s+toàn\s+bộ\s+tiền"):
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    return out.strip()


def pre_guard(ctx):
    pol = _effective_policy(ctx)
    changes = {}
    if pol is not None:
        changes["policy_id"] = pol["policy_id"]
    text = ctx.ticket.get("text", "") or ""
    new_text = _sanitize_text(text)
    if new_text and new_text != text.strip():
        changes["text"] = new_text
        ctx.log("pre_guard", action="rewrite", reason="loại bỏ số ngày khách tự ghi và chỉ thị hoàn tiền")
    from .tools import Verdict
    if "text" in changes:
        extra = {k: v for k, v in changes.items() if k != "text"}
        return Verdict.rewrite("loại bỏ số ngày khách tự ghi và chỉ thị hoàn tiền", changes["text"], **extra)
    if pol is not None:
        return Verdict.allow(policy_id=pol["policy_id"])
    return Verdict.allow()


def write_gate(ctx, action):
    from .tools import Verdict
    tool = action.get("tool")

    if tool == "issue_refund":
        amt = int(action.get("amount_vnd", 0) or 0)
        if amt <= 0:
            return Verdict.deny("số tiền không hợp lệ")
        order = ctx.tools.lookup_order(action.get("order_id"))
        # chỉ thị hoàn từ shop (payer MERCHANT) phải có người duyệt
        if action.get("payer") == "MERCHANT" and not action.get("approval_id"):
            return Verdict.escalate("hoàn từ shop cần người duyệt")
        # model lỗi (fail_open) không được tự hoàn
        if action.get("basis") == "fail_open":
            return Verdict.escalate("model lỗi, không tự hoàn")
        # trần hoàn tự động mỗi ngày cho một khách
        if order is not None and not action.get("approval_id"):
            cust = order.get("customer_id")
            if cust:
                already = sum(r["amount_vnd"] for r in ctx.tools.ledger_rows(customer_id=cust)
                              if not r.get("approval_id"))
                cap_cust = (ctx.tools.ops_limits() or {}).get("max_auto_refund_per_customer_per_day_vnd", 300000)
                if already + amt > cap_cust:
                    return Verdict.escalate("vượt trần hoàn tự động mỗi ngày cho khách")
        # điều chỉnh số tiền theo tracking DB (nguồn sự thật) cho khoản do LogiX tự hoàn
        if order is not None and action.get("payer", "LOGIX") == "LOGIX" and not action.get("approval_id"):
            pol = _effective_policy(ctx)
            if pol is not None:
                worst = max(order["parcels"], key=lambda p: H.db_delay_days(p, ctx.as_of))
                db_delay = H.db_delay_days(worst, ctx.as_of)
                cause = worst.get("delay_cause") or ("CARRIER" if db_delay > 0 else None)
                ent = H.entitlement_vnd(pol, order, db_delay, cause)
                if amt > ent:
                    if ent <= 0:
                        return Verdict.deny("số tiền vượt quyền lợi theo tracking DB")
                    return Verdict.modify("điều chỉnh số tiền theo tracking DB", amount_vnd=ent)
        # trần hoàn tự động mỗi ngày của Finance
        cap = (ctx.gates or {}).get("business", {}).get("daily_refund_cap_vnd")
        spent = ctx.tools.auto_refund_today_vnd()
        if cap is not None and not action.get("approval_id") and spent + amt > cap:
            return Verdict.escalate("vượt trần tiền hoàn tự động mỗi ngày (config)")
        return Verdict.allow()

    if tool == "file_carrier_fault":
        order = ctx.tools.lookup_order(action.get("order_id"))
        pol = _effective_policy(ctx)
        parcel = None
        if order is not None:
            parcel = next((p for p in order["parcels"] if p["parcel_id"] == action.get("parcel_id")), None)
            if parcel is None and order["parcels"]:
                parcel = order["parcels"][0]
        db_delay = None
        if parcel is not None:
            db_delay = H.db_delay_days(parcel, ctx.as_of)
        if pol is not None and parcel is not None and db_delay is not None:
            if not H.carrier_at_fault(pol, parcel, db_delay):
                return Verdict.deny("hãng không có lỗi theo tracking DB")
            if action.get("delay_days") is not None and action.get("delay_days") != db_delay:
                return Verdict.modify("điều chỉnh số ngày trễ theo tracking DB", delay_days=db_delay)
        # số lỗi tự động mỗi ngày cho một hãng
        carrier = action.get("carrier_id")
        if carrier:
            cap_strikes = (ctx.tools.ops_limits() or {}).get("max_auto_strikes_per_carrier_per_day", 2)
            existing = len(ctx.tools.fault_rows(carrier_id=carrier))
            if existing >= cap_strikes:
                return Verdict.escalate("vượt số lỗi tự động mỗi ngày cho hãng")
        return Verdict.allow()

    if tool == "notify_carrier":
        return Verdict.allow()

    if tool == "send_reply":
        return Verdict.allow()

    return Verdict.allow()
