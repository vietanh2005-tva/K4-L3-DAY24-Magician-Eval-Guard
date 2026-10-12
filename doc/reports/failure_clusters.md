# Phân tích lỗi Phase A

Nhóm: **Magician**. Người phụ trách Phase A: **Phạm Quang Đạt — 2A202602704**.
Repo chung: [K4-L3-DAY24-Magician-Eval-Guard](https://github.com/vietanh2005-tva/K4-L3-DAY24-Magician-Eval-Guard).

Nguồn: [`artifacts/ragas_50q.json`](../../artifacts/ragas_50q.json), [`artifacts/answers_50q.json`](../../artifacts/answers_50q.json) và [`fixtures/test_set_50q.json`](../../fixtures/test_set_50q.json).

Run timestamp (metadata, UTC): `2026-10-12T04:38:15.332202+00:00`; Asia/Ho_Chi_Minh: `2026-10-12T11:38:15.332202+07:00`. Run kind: `live`.

## Điều kiện chạy và nguồn kết quả

Đã chấm thực tế đủ 50 câu, 4 metric/câu (200 giá trị hữu hạn trong [0,1]). Bộ đề, ground truth, answers và contexts được giữ nguyên. Generation có 50/50 câu dùng LLM, không có extractive fallback; mỗi câu có 3 contexts từ search/rerank.

Model generation ghi từ response: `gpt-4o-mini-2024-07-18`. Evaluator IDs do m4 đọc từ chính client dùng chấm: `gpt-4o-mini, text-embedding-3-small`. Judge và guard không tham gia lần chạy Phase A. Evaluator LLM dùng alias `gpt-4o-mini`; metadata không khẳng định snapshot cụ thể của alias này.

Python 3.11.0 trên Windows; RAGAS 0.1.22, NumPy 1.26.4, PyArrow 17.0.0. Setup trước đó dùng Qdrant 1.9.7, BGE-M3 để embedding truy xuất và BGE-reranker-v2-M3 để rerank. Embedding chấm answer_relevancy là `text-embedding-3-small`, tách biệt với embedding truy xuất.

Corpus có 26 tài liệu đọc được và 125 child chunks. Loader bỏ qua `BCTC.pdf` và `Nghi_dinh_so_13-2023_ve_bao_ve_du_lieu_ca_nhan_508ee.pdf` vì là scan không có lớp văn bản; chưa thực hiện OCR. Contexts có phần enrichment từ M5 bên cạnh đoạn nguồn, nên faithfulness đo theo toàn bộ contexts đã lưu, không thay thế việc kiểm tra tài liệu gốc.

Có 13/50 answers đúng chuỗi “Không tìm thấy.” (factual 2, multi_hop 7, adversarial 4). Đây là phản hồi LLM, không phải extractive fallback.

RAGAS 0.1 được dùng với sentence segmenter bổ sung dấu chấm cuối các đoạn trong bản nhìn phục vụ faithfulness; answer lưu và input sources không bị sửa. Cách này giúp metric xét cả câu trả lời dạng mảnh câu, không thêm khẳng định mới.

## Điểm theo distribution

Số hiển thị làm tròn 4 chữ số; JSON giữ nguyên giá trị đo.

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---:|---:|---:|
| faithfulness | 0.8750 | 0.2700 | 0.6000 |
| answer_relevancy | 0.6558 | 0.4200 | 0.4990 |
| context_precision | 0.9583 | 0.9667 | 0.9167 |
| context_recall | 0.9000 | 0.7625 | 0.6833 |
| avg_score | 0.8473 | 0.6048 | 0.6748 |

## Bottom 10 và chẩn đoán từ Task 3

Đúng 10 dòng do `bottom_10()` trả về; diagnosis và suggested_fix dưới đây được giữ nguyên từ JSON. Chẩn đoán tự động là giả thuyết cần đối chiếu evidence; phần phân tích sau kiểm tra các trường hợp cụ thể.

| Rank | ID | Distribution | avg_score | worst_metric |
|---:|---:|---|---:|---|
| 1 | 39 | multi_hop | 0.0833 | faithfulness |
| 2 | 5 | factual | 0.2083 | faithfulness |
| 3 | 7 | factual | 0.2500 | faithfulness |
| 4 | 21 | multi_hop | 0.3750 | faithfulness |
| 5 | 30 | multi_hop | 0.3750 | faithfulness |
| 6 | 33 | multi_hop | 0.3750 | faithfulness |
| 7 | 44 | adversarial | 0.3958 | faithfulness |
| 8 | 50 | adversarial | 0.4167 | faithfulness |
| 9 | 22 | multi_hop | 0.4167 | faithfulness |
| 10 | 41 | adversarial | 0.4167 | faithfulness |

### Rank 1 — câu 39

Question: So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA.

Diagnosis: faithfulness=0.000; Cần đối chiếu từng khẳng định của answer với bằng chứng trong contexts. Question: «So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA.». Answer: «Không tìm thấy.». Reference: «v1.0 (đã hết hiệu lực): tối thiểu 8 ký tự, đổi mỗi 90 ngày, không yêu cầu MFA. v2.0 (hiện hành): tối thiểu 12 ký tự, đổi mỗi 120 ngày, MFA bắt buộc cho tất cả: email, VPN và hệ thố…». Context để đối chiếu (3 đoạn): «Đoạn trích đề cập đến việc thay thế chính sách mật khẩu cũ bằng phiên bản mới và thông báo cho người dùng về sự thay đổi này. Tóm tắt: Chính sách mật khẩu v1.0 đã được thay thế bởi…». Contexts có các mốc/phiên bản 2022, 2024, v1.0, v2.0; cần kiểm tra hiệu lực.

Suggested fix: Kiểm tra các khẳng định chưa được context hỗ trợ; yêu cầu generation dẫn căn cứ hoặc từ chối khi thiếu dữ liệu; đối chiếu đủ bằng chứng cho từng vế và phép tính trong câu hỏi multi-hop. Chạy lại cùng câu «So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA.» và so sánh đủ bốn metric sau khi đọc evidence.

### Rank 2 — câu 5

Question: Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt?

Diagnosis: faithfulness=0.000; Cần đối chiếu từng khẳng định của answer với bằng chứng trong contexts. Question: «Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt?». Answer: «Không tìm thấy.». Reference: «Đơn hàng trên 50.000.000 VNĐ cần Tổng Giám đốc (CEO) phê duyệt.». Context để đối chiếu (3 đoạn): «Đoạn trích nằm trong phần quy định về thẩm quyền phê duyệt đơn hàng trong tài liệu mua sắm. Tóm tắt: Đoạn trích quy định thẩm quyền phê duyệt đơn hàng dựa trên giá trị của đơn hàng…».

Suggested fix: Kiểm tra các khẳng định chưa được context hỗ trợ; yêu cầu generation dẫn căn cứ hoặc từ chối khi thiếu dữ liệu. Chạy lại cùng câu «Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt?» và so sánh đủ bốn metric sau khi đọc evidence.

### Rank 3 — câu 7

Question: Nghỉ phép không lương 20 ngày cần ai phê duyệt?

Diagnosis: faithfulness=0.000; Cần đối chiếu từng khẳng định của answer với bằng chứng trong contexts. Question: «Nghỉ phép không lương 20 ngày cần ai phê duyệt?». Answer: «Không tìm thấy.». Reference: «Nghỉ từ 16-30 ngày không lương cần phê duyệt của Giám đốc điều hành (CEO). Lưu ý: nghỉ trên 14 ngày không lương, nhân viên phải tự đóng phần bảo hiểm của mình.». Context để đối chiếu (3 đoạn): «Đoạn trích đề cập đến quy định về việc xin nghỉ phép trong tổ chức, cụ thể là thời gian nghỉ từ 16-30 ngày. Tóm tắt: Nghỉ từ 16-30 ngày cần có sự phê duyệt của Giám đốc điều hành.…».

Suggested fix: Kiểm tra các khẳng định chưa được context hỗ trợ; yêu cầu generation dẫn căn cứ hoặc từ chối khi thiếu dữ liệu. Chạy lại cùng câu «Nghỉ phép không lương 20 ngày cần ai phê duyệt?» và so sánh đủ bốn metric sau khi đọc evidence.

### Rank 4 — câu 21

Question: Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào?

Diagnosis: faithfulness=0.000; Cần đối chiếu từng khẳng định của answer với bằng chứng trong contexts. Question: «Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào?». Answer: «Không tìm thấy.». Reference: «Theo chính sách v2024: 15 ngày cơ bản + 3 ngày thâm niên (9÷3=3) = 18 ngày phép. Lương Senior (P3-P4): 20-35 triệu VNĐ/tháng.». Context để đối chiếu (3 đoạn): «Đoạn trích đề cập đến quy định về thâm niên công tác và cách tính ngày phép cho nhân viên trong tài liệu về nghỉ phép năm. Tóm tắt: Nhân viên có thâm niên từ 3 năm trở lên sẽ được…».

Suggested fix: Kiểm tra các khẳng định chưa được context hỗ trợ; yêu cầu generation dẫn căn cứ hoặc từ chối khi thiếu dữ liệu; đối chiếu đủ bằng chứng cho từng vế và phép tính trong câu hỏi multi-hop. Chạy lại cùng câu «Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào?» và so sánh đủ bốn metric sau khi đọc evidence.

### Rank 5 — câu 30

Question: So sánh quyền lợi bảo hiểm giữa nhân viên thử việc và nhân viên chính thức.

Diagnosis: faithfulness=0.000; Cần đối chiếu từng khẳng định của answer với bằng chứng trong contexts. Question: «So sánh quyền lợi bảo hiểm giữa nhân viên thử việc và nhân viên chính thức.». Answer: «Không tìm thấy.». Reference: «Nhân viên thử việc: chỉ được tham gia BHXH bắt buộc, KHÔNG được hưởng gói bảo hiểm sức khỏe PVI. Nhân viên chính thức: được hưởng BHXH + gói PVI hạn mức 200 triệu/năm (nội trú, ngo…». Context để đối chiếu (3 đoạn): «Đoạn trích đề cập đến quyền lợi bảo hiểm của nhân viên thử việc trong một chính sách liên quan đến bảo hiểm xã hội và sức khỏe. Tóm tắt: Nhân viên thử việc có quyền tham gia bảo hi…».

Suggested fix: Kiểm tra các khẳng định chưa được context hỗ trợ; yêu cầu generation dẫn căn cứ hoặc từ chối khi thiếu dữ liệu; đối chiếu đủ bằng chứng cho từng vế và phép tính trong câu hỏi multi-hop. Chạy lại cùng câu «So sánh quyền lợi bảo hiểm giữa nhân viên thử việc và nhân viên chính thức.» và so sánh đủ bốn metric sau khi đọc evidence.

### Rank 6 — câu 33

Question: Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm theo v2024 là bao nhiêu?

Diagnosis: faithfulness=0.000; Cần đối chiếu từng khẳng định của answer với bằng chứng trong contexts. Question: «Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm theo v2024 là bao nhiêu?». Answer: «Không tìm thấy.». Reference: «Phụ cấp tháng: ăn trưa 1.000.000 + điện thoại Manager 500.000 = 1.500.000 VNĐ. Phép năm v2024: 15 ngày cơ bản + 4 ngày thâm niên (12÷3=4) = 19 ngày phép.». Context để đối chiếu (3 đoạn): «Đoạn trích đề cập đến số ngày phép năm của nhân viên chính thức và sự thay đổi trong chính sách từ năm 2023. Tóm tắt: Nhân viên chính thức được hưởng 15 ngày phép năm có lương, tăn…».

Suggested fix: Kiểm tra các khẳng định chưa được context hỗ trợ; yêu cầu generation dẫn căn cứ hoặc từ chối khi thiếu dữ liệu; đối chiếu đủ bằng chứng cho từng vế và phép tính trong câu hỏi multi-hop. Chạy lại cùng câu «Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm theo v2024 là bao…» và so sánh đủ bốn metric sau khi đọc evidence.

### Rank 7 — câu 44

Question: Bao lâu phải đổi mật khẩu một lần?

Diagnosis: faithfulness=0.000; Cần đối chiếu từng khẳng định của answer với bằng chứng trong contexts. Question: «Bao lâu phải đổi mật khẩu một lần?». Answer: «Không tìm thấy.». Reference: «Theo v2.0 HIỆN HÀNH: mỗi 120 ngày. Chính sách v1.0 (đã hết hiệu lực) là 90 ngày. Câu trả lời đúng là 120 ngày.». Context để đối chiếu (3 đoạn): «Đoạn trích đề cập đến việc thay thế chính sách mật khẩu cũ bằng phiên bản mới và thông báo cho người dùng về sự thay đổi này. Tóm tắt: Chính sách mật khẩu v1.0 đã được thay thế bởi…». Contexts có các mốc/phiên bản 2024, v1.0, v2.0; cần kiểm tra hiệu lực.

Suggested fix: Kiểm tra các khẳng định chưa được context hỗ trợ; yêu cầu generation dẫn căn cứ hoặc từ chối khi thiếu dữ liệu; đối chiếu phiên bản hiệu lực, phủ định và điều kiện trong question/reference. Chạy lại cùng câu «Bao lâu phải đổi mật khẩu một lần?» và so sánh đủ bốn metric sau khi đọc evidence.

### Rank 8 — câu 50

Question: Nhân viên Manager có thể dùng VPN cá nhân (như NordVPN) khi WFH để tăng bảo mật thêm không?

Diagnosis: faithfulness=0.000; Cần đối chiếu từng khẳng định của answer với bằng chứng trong contexts. Question: «Nhân viên Manager có thể dùng VPN cá nhân (như NordVPN) khi WFH để tăng bảo mật thêm không?». Answer: «Không tìm thấy.». Reference: «KHÔNG. Chính sách VPN v1.3 cấm sử dụng VPN cá nhân (NordVPN, ExpressVPN) trong mạng công ty. Bắt buộc dùng VPN WireGuard của công ty. Đây là policy contradiction trap — câu hỏi ngh…». Context để đối chiếu (3 đoạn): «Đoạn trích nằm trong phần quy định sử dụng VPN, hướng dẫn người dùng về cách thức và quy tắc khi sử dụng dịch vụ VPN trong công ty. Tóm tắt: Đoạn trích nêu rõ các quy định sử dụng…».

Suggested fix: Kiểm tra các khẳng định chưa được context hỗ trợ; yêu cầu generation dẫn căn cứ hoặc từ chối khi thiếu dữ liệu; đối chiếu phiên bản hiệu lực, phủ định và điều kiện trong question/reference. Chạy lại cùng câu «Nhân viên Manager có thể dùng VPN cá nhân (như NordVPN) khi WFH để tăng bảo mật thêm không?» và so sánh đủ bốn metric sau khi đọc evidence.

### Rank 9 — câu 22

Question: Nếu cần mua một chiếc laptop 30 triệu cho nhân viên mới, ai phê duyệt và cần gì từ phòng CNTT?

Diagnosis: faithfulness=0.000; Cần đối chiếu từng khẳng định của answer với bằng chứng trong contexts. Question: «Nếu cần mua một chiếc laptop 30 triệu cho nhân viên mới, ai phê duyệt và cần gì từ phòng CNTT?». Answer: «Không tìm thấy.». Reference: «Laptop 30 triệu nằm trong khoảng 5-50 triệu nên cần Giám đốc phòng ban (Director) phê duyệt. Cần đính kèm ít nhất 3 báo giá (trên 10 triệu). Mua sắm thiết bị CNTT cần xác nhận cấu…». Context để đối chiếu (3 đoạn): «Đoạn trích đề cập đến quy định mua sắm thiết bị CNTT và các yêu cầu liên quan trong tài liệu. Tóm tắt: Mua sắm thiết bị CNTT cần có xác nhận của phòng CNTT về cấu hình kỹ thuật. Đơ…».

Suggested fix: Kiểm tra các khẳng định chưa được context hỗ trợ; yêu cầu generation dẫn căn cứ hoặc từ chối khi thiếu dữ liệu; đối chiếu đủ bằng chứng cho từng vế và phép tính trong câu hỏi multi-hop. Chạy lại cùng câu «Nếu cần mua một chiếc laptop 30 triệu cho nhân viên mới, ai phê duyệt và cần gì từ phòng CNTT?» và so sánh đủ bốn metric sau khi đọc evidence.

### Rank 10 — câu 41

Question: Nhân viên được nghỉ bao nhiêu ngày phép năm?

Diagnosis: faithfulness=0.000; Cần đối chiếu từng khẳng định của answer với bằng chứng trong contexts. Question: «Nhân viên được nghỉ bao nhiêu ngày phép năm?». Answer: «Không tìm thấy.». Reference: «Theo chính sách v2024 HIỆN HÀNH: 15 ngày cơ bản (+1 ngày/3 năm thâm niên). Chính sách v2023 (đã bị thay thế) là 12 ngày. RAG có thể retrieve cả 2 tài liệu — câu trả lời đúng phải ư…». Context để đối chiếu (3 đoạn): «Đoạn trích đề cập đến số ngày phép năm của nhân viên chính thức và sự thay đổi trong chính sách từ năm 2023. Tóm tắt: Nhân viên chính thức được hưởng 15 ngày phép năm có lương, tăn…».

Suggested fix: Kiểm tra các khẳng định chưa được context hỗ trợ; yêu cầu generation dẫn căn cứ hoặc từ chối khi thiếu dữ liệu; đối chiếu phiên bản hiệu lực, phủ định và điều kiện trong question/reference. Chạy lại cùng câu «Nhân viên được nghỉ bao nhiêu ngày phép năm?» và so sánh đủ bốn metric sau khi đọc evidence.

## Matrix và nhóm yếu nhất

| Worst metric | factual | multi_hop | adversarial | Tổng |
|---|---:|---:|---:|---:|
| faithfulness | 3 | 18 | 4 | 25 |
| answer_relevancy | 14 | 2 | 1 | 17 |
| context_precision | 2 | 0 | 1 | 3 |
| context_recall | 1 | 0 | 4 | 5 |
| Tổng | 20 | 20 | 10 | 50 |

Nhóm yếu nhất theo mean: **multi_hop**, avg_score = **0.6048**. Metric là worst_metric nhiều nhất: **faithfulness**, **25/50** câu.

factual: mean=0.8473, n=20; multi_hop: mean=0.6048, n=20; adversarial: mean=0.6748, n=10. Nhóm multi_hop có avg_score trung bình thấp nhất (0.6048). faithfulness là worst_metric của 25/50 câu. Matrix thống kê mọi câu, kể cả câu điểm cao; số đếm không phải số failures. Đọc question/answer/contexts/reference của bottom 10 để kiểm chứng nguyên nhân trước khi chọn cách sửa.

Có 12/50 câu đồng hạng ở điểm thấp nhất và 1/50 câu đạt xấp xỉ 1 ở cả bốn metric (sai số không quá 10^-9). Khi hòa, property `worst_metric` chọn metric xuất hiện trước theo thứ tự faithfulness, answer_relevancy, context_precision, context_recall. Vì vậy matrix đếm mọi câu và chịu ảnh hưởng quy tắc hòa; không diễn giải nó như số lỗi đã được xác nhận.

## Đối chiếu evidence và nguyên nhân

Cả 10 câu cuối bảng đều trả lời “Không tìm thấy.” Tuy nhiên, không thể quy
chúng về một nguyên nhân chung chỉ vì cùng có worst_metric là faithfulness.
Các quan sát dưới đây dựa trên toàn bộ contexts và reference của từng câu;
số thứ tự context tính từ 1 theo `per_question` trong JSON.

| Câu | Bằng chứng trong answers/contexts/reference | Diễn giải và cách sửa cần thử |
|---:|---|---|
| 39 | Cả 3 contexts nói về thay thế v1.0 bằng v2.0 hoặc tiêu đề phiên bản; không có các trị số 8/12 ký tự, 90/120 ngày hay quy định MFA cần so sánh. context_recall = 0, context_precision = 0,3333. | Retrieval lấy thông tin phiên bản thay cho các điều khoản cần trả lời. Tách truy vấn theo độ dài, chu kỳ và MFA của từng phiên bản; ghép bằng chứng trước generation. |
| 5 | Context 1 kết thúc ở hàng “Trên 50.000.000 VNĐ” nhưng thiếu ô người phê duyệt. Dòng đầy đủ trong `data/mua_sam.md` có “Tổng Giám đốc (CEO)”. context_recall = 0. | Corpus có đáp án nhưng context cuối cùng bị cắt giữa hàng bảng. Giữ nguyên hàng bảng hoặc mở rộng parent/sibling chunk, rồi kiểm tra ô CEO có đến generation. |
| 7 | Context 2 nêu rõ nghỉ 16–30 ngày cần CEO phê duyệt, nhưng answer vẫn từ chối. Reference còn có điều kiện bảo hiểm trên 14 ngày, chưa xuất hiện trong các contexts. | Có bằng chứng trực tiếp cho ý chính đã hỏi; cần kiểm tra generation dùng đoạn CEO và tách phần đủ căn cứ với phần còn thiếu. Không giải thích toàn bộ từ chối bằng thiếu retrieval. |
| 21 | Context 1 có ví dụ 9 năm = 18 ngày; contexts 2–3 lại là quy định cũ 12 ngày và thêm 1 ngày/5 năm. Không context nào có dải lương Senior 20–35 triệu. context_recall = 0,5. | Multi-hop thiếu một nhánh bằng chứng và trộn phiên bản. Tách truy vấn phép năm và lương, ưu tiên bản hiệu lực; trả lời phần đã có căn cứ thay vì từ chối toàn bộ. |
| 30 | Context 1 nêu thử việc được BHXH, chưa được PVI; hai contexts còn lại về nghỉ phép/lương thử việc, thiếu gói PVI 200 triệu của nhân viên chính thức. context_recall = 0,5. | Thiếu nhánh so sánh nhân viên chính thức. Bổ sung truy vấn quyền lợi bảo hiểm chính thức và kiểm tra đủ hai đối tượng trước khi sinh answer. |
| 33 | Contexts có 12 ngày cũ, 15 ngày mới và quy tắc thâm niên 5 năm cũ; không có phụ cấp ăn trưa/điện thoại và không có quy tắc 3 năm của v2024. context_recall = 0,5. | Không đủ điều kiện để tính 1,5 triệu phụ cấp và 19 ngày phép như reference. Tách truy vấn phụ cấp và phép năm, giữ phiên bản/thời điểm hiệu lực khi ghép. |
| 44 | Context 1 có chu kỳ 90 ngày, context 2 có 120 ngày, context 3 nói v1.0 đã được thay thế bởi v2.0; answer vẫn từ chối. | Version conflict trong bottom 10. Có cả hai giá trị nhưng thiếu liên kết nguồn/phiên bản trên từng điều khoản; cần truyền metadata hiệu lực và chọn rõ bản hiện hành. Không coi từ chối là đã giải được bẫy. |
| 50 | Context 1 cấm VPN cá nhân NordVPN/ExpressVPN; context 2 bắt buộc WireGuard cho kết nối từ xa, nhưng answer từ chối. | Có bằng chứng trực tiếp để trả lời phủ định. Kiểm tra prompt dùng lệnh cấm/điều kiện thay vì coi lời gợi ý “tăng bảo mật” trong question là căn cứ. |
| 22 | Context 1 có xác nhận cấu hình CNTT, context 2 có Director phê duyệt 5–50 triệu; context 3 lại về tài trợ đào tạo. Không có quy tắc ba báo giá cho đơn trên 10 triệu. context_recall = 0,6667. | Retrieval thiếu một điều kiện, nhưng hai ý chính của question đã có căn cứ. Kết hợp truy vấn mua sắm/báo giá, và yêu cầu generation trả lời các ý đã chứng minh được. |
| 41 | Contexts có 12 ngày cũ, 15 ngày mới kèm câu thay thế chính sách 2023, và thâm niên 5 năm cũ; answer từ chối. | Version conflict trong bottom 10. Cần giữ nguồn và hiệu lực cho từng chunk, dùng điều khoản 15 ngày hiện hành, tránh ghép quy tắc thâm niên cũ. |

### Vì sao multi-hop yếu nhất trong lần chạy này

Multi-hop có mean 0,6048, thấp hơn factual 0,8473 và adversarial 0,6748.
Faithfulness trung bình chỉ 0,2700 và answer_relevancy 0,4200; context_precision
vẫn 0,9667. Có 7/20 câu multi-hop từ chối, so với 2/20 factual. Các câu
21, 30, 33 cho thấy top 3 có thể tập trung vào một nhánh hỏi, bỏ mất nhánh còn
lại. Precision cao không đồng nghĩa đã đủ bằng chứng cho mọi ý trong câu hỏi.

Ngoài bottom 10, câu 24 trả lời phí phạt 300.000 VNĐ cho “20 ngày quá hạn”,
trong khi contexts có hạn thanh toán 15 ngày và mức 2%/tháng. Reference dùng
5 ngày quá hạn và pro-rata 5/30, được 50.000 VNĐ. Faithfulness đo được là 0,
context_recall là 1. Cần kiểm tra lập luận thời gian và đơn vị; bản contexts
không nêu tường minh mẫu số 30 ngày nên không khẳng định mọi quy tắc tính
đều đã được retrieval cung cấp. Câu 27 cũng lấy ví dụ 9 năm = 18 ngày áp cho
thâm niên 7 năm, trả lời còn 14 ngày thay vì 13 như reference: cần kiểm tra
phép chia lấy phần nguyên và không sao chép ví dụ thành kết quả của đề.

### Cách sửa và đánh giá lại

Ưu tiên ba thay đổi để thử riêng: giữ trọn bảng/mở rộng parent cho câu 5;
tách truy vấn và kiểm tra đủ các nhánh cho câu 21, 30, 33; truyền nguồn và
phiên bản hiệu lực cho câu 41, 44. Với generation, yêu cầu trả lời từng ý có
bằng chứng, nêu phần chưa đủ dữ liệu, và kiểm tra phủ định hoặc phép tính.

Các sửa trên là đề xuất sau phân tích, chưa được triển khai/chạy lại trong
lần đo này. Khi thử, lưu riêng baseline JSON/answers hiện tại, sinh bộ answers
mới trên đúng 50 câu không sửa ground truth, rồi chấm bằng cùng evaluator và
tham số. So sánh bốn metric và mean theo nhóm, số từ chối, tỷ lệ đủ bằng chứng
từng nhánh; đọc lại các câu đã nêu để xác nhận CEO, 18 ngày + dải lương Senior,
PVI của hai đối tượng, 19 ngày + phụ cấp Manager, chu kỳ 120 ngày và lệnh cấm
VPN cá nhân. Không chọn cải tiến chỉ vì một metric tăng khi câu trả lời vẫn sai.

## Bẫy adversarial và giới hạn đánh giá

Adversarial mean 0,6748 thấp hơn factual 0,8473 khoảng 0,1725; kết quả đáp ứng
điều kiện số đo cho bonus Phase A và có phân tích bẫy, nhưng không tự chứng
minh pipeline đã xử lý tốt version conflict. Trong bottom 10, câu 41/44 chứa
hai phiên bản và bị từ chối; câu 50 có lệnh cấm rõ nhưng vẫn từ chối.

Ngoài bottom 10, câu 43 chọn mật khẩu 8 ký tự dù context 1 nêu 12 và context
2 nêu 8; reference yêu cầu bản v2.0 hiện hành với 12 ký tự. Các đoạn yêu cầu
này không chứa tiêu đề phiên bản trong text đưa tới generation. Ngược lại,
câu 46 trả lời đúng phủ định “KHÔNG được nghỉ phép năm”, với faithfulness = 1
và answer_relevancy = 1. Câu 48 vẫn từ chối dù context nêu rõ thử việc chưa
được hưởng PVI; answer_relevancy = 0 nhưng faithfulness = 1. Chỉ số grounding
của một câu từ chối không đủ phản ánh câu đó đã trả lời đúng hay chưa.

RAGAS cũng có trường hợp cần đọc thủ công: câu 31 trả lời 2,4 triệu theo
1,2 triệu/đêm × 2 đêm, câu 38 trả lời 600 USD theo 200 USD/đêm × 3 đêm; cả hai
khớp kết quả reference và mức trong contexts nhưng faithfulness đều bằng 0.
Đây là bất đồng giữa số đo và đối chiếu phép tính. Chưa lưu reasoning chi tiết
của evaluator nên chưa thể xác định chắc nguyên nhân là suy diễn số học,
trích xuất statements hay phán xét LLM. Giữ nguyên điểm đo, không sửa thành 1.
Vì vậy không diễn giải 18/20 multi-hop có worst_metric faithfulness là 18 lỗi
generation đã được con người xác nhận.

Các giới hạn khác: chỉ 50 câu và 10 adversarial, một lần chấm với một alias
LLM, không có khoảng tin cậy hay đo độ ổn định giữa nhiều lần chạy; một số
reference còn nêu thông tin bổ sung ngoài ý hỏi trực tiếp. Hai PDF scan chưa
OCR và enrichment M5 cũng ảnh hưởng phạm vi bằng chứng. Mean bốn metric là
thống kê tổng hợp của lab, không thay thế đánh giá đúng/sai nghiệp vụ. Chưa
đánh giá được hiệu quả của các sửa đề xuất nếu chưa có thực nghiệm đối chứng.

## Kiểm chứng và cách tái lập

104 tests offline đạt, 3 tests deselect, bằng môi trường `requirements/requirements-test.lock.txt`. Live artifact đã qua `validate_answers`, `validate_phase_a` và `validate_metadata`: schema, đúng nguồn từng dòng, đủ 20/20/10 câu, bốn điểm hữu hạn, bottom 10, means, matrix và source hashes. Unit tests là bằng chứng logic; JSON live là bằng chứng số đo API.

Chạy từ gốc repo, chỉ khi đã cho phép dùng API:

```powershell
.\.venv\Scripts\python.exe -c "import torch, runpy; runpy.run_path('scripts/run_experiments.py', run_name='__main__')" --phase a --live
```

Các source SHA-256 để kiểm tra lần chạy:

```json
{
  "answers_50q.json": "db86b4a26a3945913822349c0293e879c7629e77bb4296b1d305463e2a0820e5",
  "test_set_50q.json": "0e87f26e020a32c62ea0864940720618f39600b9d3378193704cf2f86e88446d"
}
```

Nguồn mã Day 18 và các điều chỉnh được ghi trong [PIPELINE_INTERFACE.md](../PIPELINE_INTERFACE.md); đóng góp cá nhân của Phạm Quang Đạt và phạm vi AI hỗ trợ được kê khai trong [TEAM.md](../TEAM.md#phamquangdat-2a202602704). Nhóm Magician phân công Trương Việt Anh phụ trách Phase B và Nguyễn Vũ Anh phụ trách Phase C; phiên bản nộp cuối được chốt sau khi tích hợp cả ba phase.
