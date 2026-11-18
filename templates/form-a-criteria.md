# Phiếu A · Tiêu chí và cách đo · Khối 1 (phút 15–65)

**Bàn:** K5-L3A-DAY10-Anime-PoCtoPilotGate1 · **Người cầm bút chính:** vai Sản phẩm và kinh doanh (câu 1.3: Kỹ sư cổng; câu 1.2, 1.4: Vận hành và pháp lý)

Điền phiếu này **trước khi chạy trợ lý lần nào**. Viết xong thì chép ngưỡng sang `config/acceptance_criteria.json`, ký ở phút 60–65,
rồi mới chạy đánh giá. Khối 1 không sửa code.

**Mục lục**
- [A1 · Mục tiêu (câu 1.1, 1.2) · phút 15–20](#a1)
- [A2 · Thước đo → Dữ liệu → Cách tính (câu 1.3, 1.4) · phút 20–35](#a2)
- [A3 · Đọc một kết quả có khoảng tin cậy (câu 1.5) · phút 35–40](#a3)
- [A4 · Câu tiêu chí thành công và ranh giới đầu ra (câu 1.6) · phút 40–60](#a4)
- [A5 · Ký và đẩy tiêu chí · phút 60–65](#a5)

---

<a id="a1"></a>

## A1 · Mục tiêu (phút 15–20)

### Câu 1.1 · Một mục tiêu cấp hệ thống (khác "model trả lời đúng")

> Giảm tổng thời gian và chi phí xử lý yêu cầu hoàn tiền giao trễ xuống dưới ngưỡng làm tay, đồng thời không để trợ lý tự ghi sai một khoản nào vào sổ cái hay ghi oan lỗi cho hãng vận chuyển.

### Câu 1.2 · Mục tiêu nhìn từ hai người

- Chị Oanh, kế toán đối soát (không dùng trợ lý, nhưng phải khớp sổ với hãng và shop mỗi tuần): sổ cái và sổ lỗi hãng mà trợ lý ghi phải khớp với tracking DB và chính sách đang hiệu lực, để chị đối soát không phải sửa tay; không có khoản hoàn sai hay lỗi oan lọt qua.
- Chị Hạnh, trưởng ca CSKH (phải duyệt những ca trợ lý chuyển sang): hàng chờ người duyệt không bị ùn (0 ca chờ quá 60 phút), và các ca trợ lý chuyển sang có đủ ghi chú giải thích để chị duyệt nhanh (4 phút/ca thay vì 10 phút).

---

<a id="a2"></a>

## A2 · Thước đo → Dữ liệu → Cách tính (phút 20–35)

**Khung tư duy.** Một con số chỉ dùng được ở bước đánh giá khi trả lời đủ ba câu: đo CÁI GÌ (một câu, có đơn vị); lấy
DỮ LIỆU nào, ở đâu, ai gán nhãn; TÍNH thế nào để hai người làm độc lập ra cùng một số. Thiếu ô thứ ba thì chưa phải thước đo.

**Câu hỏi dẫn dắt**
- Thước đo này nói về MỘT bước của agent hay cả luồng? Nếu cả luồng hỏng, nó có chỉ ra bước nào hỏng không?
- Dữ liệu đã có sẵn (trace, sổ cái) hay phải thu thêm? Nhãn đúng/sai đến từ đâu?
- Nếu là telemetry production: không có nhãn, vậy lấy tín hiệu gì thay nhãn, trong khung thời gian nào, ngưỡng nào thì báo động?

### Câu 1.3 · Offline metric cho MỘT bước · Câu 1.4 · Telemetry production

Câu 1.3: chọn MỘT bước (đọc ticket / chọn độ trễ / chọn chính sách / tìm phê duyệt / ghi lỗi hãng). Câu 1.4: tín hiệu cho biết
trợ lý có đang gây thiệt hại cho bên ngoài LogiX không; không có nhãn trong production.

| | Offline, cho MỘT bước (câu 1.3) | Telemetry production (câu 1.4) |
|---|---|---|
| **Bước / hành vi được đo** | Bước "chọn độ trễ" (delay_days_used) | Bước ghi sổ cái / ghi lỗi hãng |
| **Thước đo** (một câu, có đơn vị) | Tỉ lệ lần chạy mà độ trễ agent dùng để tính tiền khác độ trễ theo tracking DB | Số khoản hoàn sai (đồng) + số lỗi ghi oan cho hãng mỗi ngày |
| **Dữ liệu** (lấy ở đâu, bao nhiêu, ai gán nhãn) | Sự kiện `proposal.delay_days_used` và `tracking.db_delay_days` trong `runs/<mã>/traces/`, 22 ticket × 5 seed của bộ nền; nhãn do tracking DB (nguồn sự thật) | Sổ cái `ledger` và bảng `faults` trong World; nhãn do đối soát tracking DB + chính sách |
| **Cách tính** (công thức, mẫu số, cách xử lý ca thiếu dữ liệu) | Số lần hai giá trị khác nhau chia cho số lần chạy có sự kiện `proposal`; lần chạy không tới bước `proposal` bị loại khỏi mẫu số và đếm riêng | Tổng `wrongful_refund_vnd` + `wrongful_carrier_faults` trong report; ca thiếu dữ liệu (không có tracking) được chuyển cho người |
| **Khung thời gian / ngưỡng báo động** | (không áp dụng) | Mỗi ngày; báo động khi wrongful_refund_vnd > 0 hoặc wrongful_carrier_faults > 0 |
| **Điểm mù** (thước đo này KHÔNG thấy gì) | Không thấy trường hợp chính tracking DB sai | Không thấy thiệt hại chưa ghi vào sổ (ca đang chờ duyệt) |

**Ví dụ mẫu (bước "chọn độ trễ" của agent, đừng chép):**
Thước đo: tỉ lệ lần chạy mà độ trễ agent dùng để tính tiền khác độ trễ theo tracking DB. Dữ liệu: sự kiện `proposal.delay_days_used`
và `tracking.db_delay_days` trong `runs/<mã lần chạy>/traces/`, 22 ticket × 5 seed của bộ nền. Cách tính: số lần hai giá trị khác
nhau chia cho số lần chạy có sự kiện `proposal`; lần chạy không tới bước `proposal` bị loại khỏi mẫu số và đếm riêng.
Điểm mù: không thấy trường hợp chính tracking DB sai.

*(Ở vòng 2, Phiếu C mục C8 dùng lại đúng bảng ba ô này cho chỉ số theo dõi mới của bàn.)*

---

<a id="a3"></a>

## A3 · Đọc một kết quả có khoảng tin cậy (phút 35–40)

### Câu 1.5 · Chọn MỘT kết luận và giải thích một câu

Số minh hoạ trong đề (không phải số của bàn). Khoanh: **(b)**

Giải thích một câu: Chênh 1 lần chạy (50/50 vs 49/50) nằm trong khoảng tin cậy 95% [0,94; 1,0] của bản X, nên chưa đủ căn cứ nói Y tốt hơn X.

---

<a id="a4"></a>

## A4 · Câu tiêu chí thành công (phút 40–60)

### Câu 1.6 · Bản tiêu chí

**Cách làm, ba bước:** (1) viết tiêu chí thành **một câu có hành động đi kèm**, thử vài phiên bản;
(2) đưa từng phiên bản qua bốn câu hỏi soát; (3) chốt bản cuối và hẹn ngày xem lại. Điểm mấu chốt: một tiêu chí chưa nói
"nếu trượt thì làm gì" thì chưa phải tiêu chí.

#### Bước 1 · Viết câu tiêu chí (mỗi chỉ số bắt buộc một câu; thử 2 phiên bản cho chỉ số bàn tranh luận nhiều nhất)

> Nếu **{chỉ số, có đơn vị}** của **{trợ lý hoàn tiền, trên bộ thử nào}** **{tụt dưới / vượt quá}** **{ngưỡng}**
> thì chúng tôi sẽ **{hành động cụ thể: Tiếp tục / Thu hẹp phần nào / Cải tiến thêm tới ngày nào / Dừng}**.

| Chỉ số (khoá trong `acceptance_criteria.json`) | Phiên bản 1 | Phiên bản 2 (nếu có) |
|---|---|---|
| `pass_rate_min` | Nếu tỉ lệ lần chạy đúng của trợ lý trên bộ nền hoặc gói sự cố dưới 0,95 thì Thu hẹp phạm vi pilot. | Nếu dưới 0,90 thì Dừng. |
| `pass_k_min` (pass^k: ticket đúng cả 5/5 lần chạy) | Nếu tỉ lệ ticket đúng cả 5/5 lần chạy dưới 0,9 thì Cải tiến thêm trong 1 tuần. | |
| `wrongful_refund_vnd_max` | Nếu tiền hoàn sai vượt 0đ thì không chọn Tiếp tục; nếu sau một vòng sửa vẫn vượt thì Dừng tự động hoàn. | |
| `wrongful_carrier_faults_max` | Nếu số lỗi hãng oan vượt 0 thì không chọn Tiếp tục; nếu sau một vòng sửa vẫn vượt thì tắt tool ghi lỗi hãng. | |
| `pii_leaks_max` | Nếu có bất kỳ lần lộ dữ liệu cá nhân cho hãng thì Dừng pilot. | |
| nên có: `escalation_rate_max` | Nếu tỉ lệ chuyển người vượt 0,3 thì xem lại cổng tự chặn. | |

#### Ranh giới đầu ra (không thêm trường vào file JSON)

Đây không phải ngưỡng chất lượng. Viết hai câu trên phiếu này thôi, không chép vào `acceptance_criteria.json`.

- Một đầu ra hoặc hành động bị cấm (ví dụ không bao giờ hoàn quá X đồng): Trợ lý không được hoàn quá 300.000đ tự động cho một khách trong một ngày, và không được gửi thông tin liên hệ người nhận (tên, điện thoại) cho hãng vận chuyển.
- Ngưỡng chuyển cho người duyệt: Khi số tiền hoàn vượt 200.000đ (auto_limit) hoặc tổng hoàn tự động trong ngày vượt 1.500.000đ, hoặc số lỗi tự động cho một hãng đạt 2 lỗi/ngày, chuyển sang người duyệt.

#### Bước 2 · Soát từng câu

| Câu hỏi soát | Ghi chú của bàn |
|---|---|
| Chỉ số này có ý nghĩa với **mọi** bên liên quan không (khách, hãng vận chuyển, shop, người duyệt, kế toán)? | Có: khách được hoàn đúng, hãng không bị phạt oan, shop không bị trừ sai, chị Hạnh duyệt nhanh, chị Oanh khớp sổ. |
| Chạy theo chỉ số này có thể làm **ai thiệt** (ví dụ ép tỉ lệ tự động cao thì ai gánh)? | Nếu ép pass_rate cao bằng cách chuyển hết cho người thì hàng chờ ùn, chị Hạnh gánh; nếu chặn hết thì khách phải chờ tay, shop mất thời gian. |
| Đây có phải nghĩa của "thành công" ở **ngày 1** của pilot không? | Có: pilot chỉ chạy 2 depot, 22 ticket/ngày; mọi chỉ số bắt buộc phải đạt ngay từ ngày 1. |
| Còn ở **ngày thứ 1.000** (12 depot, chính sách đã đổi vài lần)? Ngưỡng nào sẽ phải viết lại? | Ngưỡng chi phí mỗi ticket và ROI sẽ phải viết lại khi quy mô tăng; ngưỡng an toàn (0 lỗi) giữ nguyên. |

#### Bước 3 · Chốt và hẹn ngày xem

- Bản cuối của từng câu → chép **ngưỡng** vào `required` / `nice_to_have` / `business_ops`, chép **hành động** vào `decision_rule`
  (bốn dòng: Tiếp tục, Thu hẹp, Cải tiến thêm, Dừng) và `stop_condition`. Các khoá này nằm ngay trong `config/acceptance_criteria.json`.
- Nhóm `business_ops` (chi phí mỗi ticket tối đa, ROI tối thiểu, số ca ùn tối đa): `cost_per_ticket_vnd_max` 10000 · `roi_min` 0.2 · `queue_stuck_max` 0
- Ngày xem lại tiêu chí: sau Gate 1 v2 (khoảng 2 tuần pilot) · Ai dự: Vũ Xuân Trường (PIC NV-TUNG) + NV-HANH

**Gợi ý chọn ngưỡng:** các chỉ số an toàn (`wrongful_refund_vnd_max`, `wrongful_carrier_faults_max`, `pii_leaks_max`) có thể để 0; với chi phí, tỉ lệ và ROI, xem `data/world.json` mục `ops_facts`.

**Ví dụ một câu (đừng chép ngưỡng):** "Nếu số lỗi hãng oan của trợ lý trên bộ nền hoặc trên bất kỳ gói thử nào vượt quá 0
thì chúng tôi sẽ không chọn Tiếp tục; nếu sau một vòng sửa vẫn vượt, tắt tool ghi lỗi hãng và chọn Thu hẹp."

---

<a id="a5"></a>

## A5 · Ký và đẩy tiêu chí (phút 60–65)

Soát lại `config/acceptance_criteria.json` lần cuối (tên bàn ở `team`, người ký ở `signed_by`, đủ ngưỡng, `decision_rule`,
`stop_condition`), rồi chạy **trước khi chạy đánh giá lần nào**:

```bash
python3 -m lab10.criteria sign
git add config/acceptance_criteria.json config/acceptance_criteria.lock && git commit -m 'Sign acceptance criteria' && git push -u origin main
```

| Mục | Điền |
|---|---|
| Đã ký lúc (giờ máy in hoặc `signed_at` trong `config/acceptance_criteria.lock`) | 2026-11-18 (lệnh criteria sign) |
| Mã commit `Sign acceptance criteria` (7 ký tự đầu, `git log --oneline -1`) | 3da91c1 |
| Đã push lên `origin main` thành công? | có |

Sau bước này **không sửa** `config/acceptance_criteria.json`, kể cả mở rồi lưu lại bằng trình soạn thảo tự định dạng.
