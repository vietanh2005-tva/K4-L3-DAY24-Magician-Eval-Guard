# Nhóm thực hiện K4 Track 3A

Tên nhóm: **Magician**.

Repo chung: [K4-L3-DAY24-Magician-Eval-Guard](https://github.com/vietanh2005-tva/K4-L3-DAY24-Magician-Eval-Guard).

Trưởng nhóm/người nộp: **Trương Việt Anh — 2A202602444**.

Ngày lab/deadline áp dụng: chưa có thông báo lớp trong thông tin được cung cấp.
Nhóm xác nhận thời hạn theo Asia/Ho_Chi_Minh (UTC+07:00) trước khi nộp.

Commit dùng để chấm bài nhóm: chưa chốt phiên bản tích hợp cả ba phase.
Phần Phase A được ghi trong commit có tiêu đề
`feat: complete Phase A RAGAS evaluation and individual report`.
Tra SHA phần Phase A bằng
`git log -1 --format=%H --grep='^feat: complete Phase A RAGAS evaluation and individual report$'`;
trưởng nhóm ghi SHA của bản nộp cuối sau khi tích hợp Phase B/C.

Mỗi nhóm nộp một repo chung. Nhóm có ba thành viên, phân công A/B/C như sau;
trạng thái thực hiện được ghi trong từng mục INDIVIDUAL và evidence tương ứng.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Phạm Quang Đạt | 2A202602704 | Phụ trách Phase A, Tasks 1–4; tích hợp pipeline Day 18, kiểm chứng và báo cáo với Codex hỗ trợ | `src/phase_a_ragas.py`, tests Phase A, hai JSON answers/RAGAS, `doc/reports/failure_clusters.md`; commit Phase A nêu trên |
| 2 | Trương Việt Anh | 2A202602444 | Trưởng nhóm/người nộp; phụ trách Phase B, Tasks 5–8, với Codex hỗ trợ; đang triển khai | `src/phase_b_judge.py`; bổ sung artifact/report và kết quả kiểm chứng khi hoàn tất |
| 3 | Nguyễn Vũ Anh | 2A202602502 | Phụ trách Phase C, Tasks 9a–13, với Codex hỗ trợ; đang triển khai | `src/phase_c_guard.py`, `guardrails/`; bổ sung artifact/blueprint và kết quả kiểm chứng khi hoàn tất |

GitHub/email dùng cho commit: Phạm Quang Đạt — `datpq-alpha`,
`phamqdat99@gmail.com`; Trương Việt Anh —
[vietanh2005-tva](https://github.com/vietanh2005-tva), `truongvietanh277@gmail.com`;
Nguyễn Vũ Anh — [vuanh259](https://github.com/vuanh259), `vuanhcp123@gmail.com`.

Người phụ trách tích hợp và chạy batch Phase A: **Phạm Quang Đạt — 2A202602704**,
với Codex hỗ trợ thao tác mã và thực nghiệm; bằng chứng ở các artifacts và báo
cáo Phase A. Người tích hợp bản cuối và nộp link: **Trương Việt Anh — 2A202602444**.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows, Python 3.11.0 cho Phase A; compiler phục vụ
Annoy/Phase C chưa được kiểm chứng trong phần việc này.
Virtualenv/dependencies/imports: `.venv` cho Phase A và `.venv-tests` theo
test lock; cả hai đã qua `pip check`. Imports Phase A đạt khi nạp `torch`
trước RAGAS/datasets; chi tiết workaround ở `doc/ENVIRONMENT.md`.
Models/Qdrant/50 answers đã chuẩn bị: BGE-M3, BGE-reranker-v2-M3 đã chạy,
Qdrant 1.9.7; 50 answers thật, mỗi câu có 3 contexts, không extractive fallback.
Loader dùng 26 tài liệu/125 child chunks; hai PDF scan chưa có OCR.
Runtime NeMo/Annoy/Presidio cho Phase C chưa được kiểm chứng trong phần việc
Phase A; các kết quả dưới đây không xác nhận full stack của cả ba phase.

## INDIVIDUAL

### PhamQuangDat-2A202602704

Họ và tên: **Phạm Quang Đạt**. MSSV: **2A202602704**.
Phần được giao: **Phase A — đánh giá RAG bằng RAGAS, Tasks 1–4**.
Phần triển khai và kiểm chứng dưới đây có Codex hỗ trợ, được kê khai ở mục
AI hỗ trợ Phase A; không nhận phần Phase B/C là đóng góp đã hoàn thành.

#### Công việc và mục đích

- **Task 1 — `group_by_distribution()`:** chia bộ đề thành factual,
  multi_hop và adversarial, giữ nguyên dữ liệu/thứ tự, từ chối distribution
  lạ; kiểm tra bộ đề có đúng 20/20/10 câu.
- **Task 2 — `run_ragas_50q()`:** truyền question, answer, contexts và
  ground_truth tới m4 theo cùng thứ tự, ghép lại ID/distribution của nguồn.
  Kiểm tra số dòng, điểm hữu hạn trong [0,1], trạng thái chấm và model
  evaluator thực tế từ m4; không thay điểm thiếu bằng 0 hoặc đoán model judge.
- **Task 3 — `bottom_10()`:** xếp tăng dần theo trung bình bốn metric, xuất
  đúng 10 câu với rank, ID, distribution, diagnosis và suggested_fix. Chẩn
  đoán có evidence trích từ từng câu; exporter giữ nguyên các dòng Task 3.
- **Task 4 — `cluster_analysis()`:** tạo matrix worst_metric × distribution,
  chọn nhóm yếu bằng avg_score trung bình thấp nhất, kèm insight. Matrix
  đếm mọi câu; kích thước nhóm 20/20/10 không dùng để kết luận chất lượng.
- **Tích hợp và thực nghiệm:** đưa m1–m5 và helpers từ repo Day 18 vào Day 24,
  ưu tiên cấu hình Day 24; dùng Qdrant API tương thích client 1.9, bổ sung
  metadata model evaluator, chuẩn bị môi trường Python 3.11 và chạy script
  setup/runner gốc. Viết phân tích lỗi từ JSON thực tế, gồm retrieval,
  generation, phiên bản hiệu lực và giới hạn của evaluator.

#### Bằng chứng

Mã chính: [`src/phase_a_ragas.py`](../src/phase_a_ragas.py),
[`src/m2_search.py`](../src/m2_search.py),
[`src/m4_eval.py`](../src/m4_eval.py).
Tests: [`tests/test_phase_a_validation.py`](../tests/test_phase_a_validation.py),
[`tests/test_day18_integration.py`](../tests/test_day18_integration.py) cùng
tests Phase A/support có sẵn của starter.

Kết quả thực tế: [`answers_50q.json`](../artifacts/answers_50q.json),
[`ragas_50q.json`](../artifacts/ragas_50q.json) và
[`failure_clusters.md`](reports/failure_clusters.md).
Run RAGAS có timestamp `2026-10-12T04:38:15.332202+00:00`
(11:38:15 ngày 12/10/2026, UTC+07:00); source SHA-256 trong metadata đối chiếu
với đúng answers và test set. Bằng chứng Git là commit Phase A nêu đầu tài liệu.

#### Cách kiểm tra và kết quả

Kiểm tra offline, không gọi API:

```powershell
.\.venv-tests\Scripts\python.exe -m pytest tests/ -m 'support or student' --ignore=tests/test_phase_b.py --ignore=tests/test_phase_c.py -q
```

Kết quả: **104 tests đạt, 3 tests bị deselect**. Mocks kiểm tra adapter,
khả năng từ chối kết quả lỗi và tính toán thống kê; không dùng tests mock
để khẳng định đã chấm RAGAS thực tế.

Các lệnh thực nghiệm đã chạy trên máy Windows, dùng `.env` riêng để xác thực:

```powershell
.\.venv\Scripts\python.exe -c "import torch, runpy; runpy.run_path('scripts/setup_answers.py', run_name='__main__')" --live
.\.venv\Scripts\python.exe -c "import torch, runpy; runpy.run_path('scripts/run_experiments.py', run_name='__main__')" --phase a --live
```

Setup lưu **50 answers bằng LLM**, mỗi câu có 3 contexts, không extractive
fallback. Chấm live có **200/200 giá trị hợp lệ** cho bốn metric.
`validate_answers`, `validate_phase_a` và `validate_metadata` đã kiểm tra
schema, nguồn từng dòng, model roles, source hashes, bottom 10, means và
matrix; diagnosis/fix trong báo cáo khớp nguyên văn JSON Task 3.

| Distribution | Số câu | Mean avg_score |
|---|---:|---:|
| factual | 20 | 0,8473 |
| multi_hop | 20 | 0,6048 |
| adversarial | 10 | 0,6748 |

Multi-hop là nhóm yếu nhất theo mean. Faithfulness là worst_metric của
25/50 câu; số này không có nghĩa 25 lỗi đã được con người xác nhận.
Adversarial mean thấp hơn factual, kèm phân tích bẫy trong báo cáo.

#### Điều rút ra từ kết quả

Đánh giá cần truy ngược được question/answer/contexts/reference, giữ nguyên
ID và nguồn để tránh ghép nhầm điểm. Context precision cao chưa đảm bảo đủ
mọi nhánh bằng chứng cho câu multi-hop: câu 21 thiếu dải lương Senior, câu 30
thiếu quyền lợi bảo hiểm của nhân viên chính thức. Câu 5 cho thấy cắt bảng
giữa chunk có thể làm mất ô CEO dù corpus có đáp án. Câu 41/44 cho thấy cần
giữ phiên bản và hiệu lực của từng điều khoản khi các contexts mâu thuẫn.

Điểm evaluator cũng cần đọc cùng evidence: câu 31/38 có phép tính khớp
reference nhưng faithfulness bằng 0; câu 48 từ chối trả lời nhưng faithfulness
bằng 1 và answer_relevancy bằng 0. Vì vậy không sửa điểm để hợp nhận định
cá nhân, và không dùng một metric thay cho đánh giá đúng/sai của câu trả lời.

#### Giới hạn và hướng xử lý

Hai PDF dạng scan chưa OCR nên loader bỏ qua; báo cáo ghi rõ giới hạn corpus.
Trên Windows, import PyTorch sau RAGAS/datasets gây lỗi DLL, được xử lý bằng
cách nạp `torch` trước; PyArrow được pin 17.0.0 để giữ NumPy 1.26.4 của Day 24.
Cách tái lập ở [`ENVIRONMENT.md`](ENVIRONMENT.md).
Thêm `.gitattributes` để bảo toàn bytes của JSON kết quả và checkout fixture
với CRLF trên mọi máy; SHA-256 trong metadata vì vậy vẫn khớp sau khi clone.

Lần đo chỉ có 50 câu và một lần chấm bằng alias evaluator, chưa đo độ ổn định
hay hiệu quả của cải tiến. Giữ trọn bảng, mở rộng parent, tách truy vấn
multi-hop và truyền metadata phiên bản là đề xuất sau phân tích; chưa khai
các đề xuất này là thay đổi đã triển khai/chạy lại.

#### Nguồn và AI hỗ trợ

Mã pipeline từ bài Day 18 của Phạm Quang Đạt, repo
[`K4-Track3A-DAY18-PhamQuangDat-2A202602704-ProductionRAG`](https://github.com/datpq-alpha/K4-Track3A-DAY18-PhamQuangDat-2A202602704-ProductionRAG),
commit `f9acd87`; các điều chỉnh cho Day 24 được ghi trong
[`PIPELINE_INTERFACE.md`](PIPELINE_INTERFACE.md).
Codex hỗ trợ viết/sửa mã, tests, cấu hình, thao tác thực nghiệm, đối chiếu
evidence và soạn tài liệu. Cách kiểm chứng phần hỗ trợ là tests offline,
script live gốc, các validators và đối chiếu từng case với artifacts đã lưu;
không tự điền số đo hoặc nhận kết quả mock làm kết quả API.
Người phụ trách cần hiểu và giải thích được các nội dung kê khai khi nộp bài.

### TruongVietAnh-2A202602444

Họ và tên: **Trương Việt Anh**. MSSV: **2A202602444**.
GitHub: [vietanh2005-tva](https://github.com/vietanh2005-tva).
Phần được giao: **Phase B — LLM Judge, Tasks 5–8**; trưởng nhóm/người nộp.
Trạng thái: đang triển khai với Codex hỗ trợ; chưa kê khai thực nghiệm B đã đạt.

Phạm vi: pairwise judge dựa trên reference, hai lượt hoán đổi A/B và quy đổi
winner/scores, Cohen's kappa trên đúng mười supplied model_answer, position và
verbosity analysis. Evidence dự kiến ở `src/phase_b_judge.py`, tests Phase B,
`artifacts/judge_results.json` và `doc/reports/bias_report.md`.
Khi hoàn tất, ghi kết quả thật, các trường hợp bất đồng và giới hạn số mẫu;
không dùng human_label/human_note trong prompt chấm.

### NguyenVuAnh-2A202602502

Họ và tên: **Nguyễn Vũ Anh**. MSSV: **2A202602502**.
GitHub: [vuanh259](https://github.com/vuanh259).
Phần được giao: **Phase C — Guardrails, Tasks 9a–13**.
Trạng thái: đang triển khai với Codex hỗ trợ; chưa kê khai thực nghiệm C đã đạt.

Phạm vi: Presidio PII recognizers, NeMo input/output rails, 20 attacks và 8
clean controls, 4 output cases, latency hai tầng input và blueprint.
Evidence dự kiến ở `src/phase_c_guard.py`, `guardrails/`, tests Phase C,
`artifacts/guard_results.json` và `doc/reports/blueprint.md`.
Khi hoàn tất, ghi số đo thật, false positives, warm-up/raw latency và giới hạn;
không dùng expected để quyết định actual hoặc giả lập runtime NeMo.

## AI hỗ trợ Phase A

Codex hỗ trợ tích hợp các module m1–m5 từ repo Day 18
`datpq-alpha/K4-Track3A-DAY18-PhamQuangDat-2A202602704-ProductionRAG`,
commit nguồn `f9acd87`, triển khai Tasks 1–4 trong `src/phase_a_ragas.py`,
kiểm tra tương thích với cấu hình Day 24 và chuẩn bị môi trường chạy thực tế.
Các thay đổi khi tích hợp được ghi trong `doc/PIPELINE_INTERFACE.md`.

Kiểm chứng offline bằng môi trường `requirements/requirements-test.lock.txt`:
104 tests đạt, 3 tests ngoài phạm vi bị deselect, với lệnh:

```powershell
.\.venv-tests\Scripts\python.exe -m pytest tests/ -m 'support or student' --ignore=tests/test_phase_b.py --ignore=tests/test_phase_c.py -q
```

Chuẩn bị answers đã chạy script setup gốc trên corpus và bộ 50 câu của Day 24:
50/50 câu dùng LLM, model được ghi là `gpt-4o-mini-2024-07-18`, không có
extractive fallback. API key lưu riêng trong `.env`.
Người dùng đã cho phép gửi dữ liệu lab Day24 tới OpenAI để chấm RAGAS và
hoàn tất Phase A. Runner gốc đã chấm đủ 50 câu × 4 metric, lưu
`artifacts/ragas_50q.json` với metadata nguồn/model/timestamp, kiểm tra bằng
`validate_answers`, `validate_phase_a`, `validate_metadata` và đối chiếu
evidence để viết `doc/reports/failure_clusters.md`.
Mean factual/multi_hop/adversarial lần lượt 0,8473 / 0,6048 / 0,6748;
evaluator client dùng `gpt-4o-mini` và `text-embedding-3-small`.
Unit tests sử dụng mocks không phải bằng chứng cho điểm RAGAS.
Môi trường Phase A dùng Windows, Python 3.11.0, Qdrant 1.9.7, RAGAS 0.1.22;
cách khởi chạy trên máy này ở `doc/ENVIRONMENT.md`.
Phần kê khai này không xác nhận runtime NeMo/Phase B/Phase C đã chạy.
Thành viên cần tự đọc mã, đối chiếu artifacts với báo cáo và giải thích phần
công việc mình kê khai trước khi nộp.

## Cập nhật sau khi nộp

Chưa có thông tin về phiên bản đã nộp hoặc cập nhật sau khi nộp.
Commit hiện tại ghi phần Phase A của Phạm Quang Đạt; chưa xác nhận là bản
nộp cuối của cả nhóm. Trưởng nhóm bổ sung SHA, thời điểm nộp và lịch sử
cập nhật theo thông báo lớp khi hoàn tất tích hợp.
