# Nhóm thực hiện K4 Track 3A

Tên nhóm: **Magician**.

Repo chung: [K4-L3-DAY24-Magician-Eval-Guard](https://github.com/vietanh2005-tva/K4-L3-DAY24-Magician-Eval-Guard).

Trưởng nhóm/người nộp: **Trương Việt Anh — 2A202602444**.

Ngày lab/deadline áp dụng: chưa có thông báo lớp trong thông tin được cung cấp.
Nhóm xác nhận thời hạn theo Asia/Ho_Chi_Minh (UTC+07:00) trước khi nộp.

Bản tích hợp A/B/C đã hoàn tất kiểm chứng; SHA bản kỹ thuật được ghi sau khi tạo commit Phase C.
Phần Phase A được ghi trong commit có tiêu đề
`feat: complete Phase A RAGAS evaluation and individual report`.
Tra SHA phần Phase A bằng
`git log -1 --format=%H --grep='^feat: complete Phase A RAGAS evaluation and individual report$'`;
Commit Phase B: `e18f9dc30eed83b524e19dd5b714f297ad4bba06`; Phase A: `f296173147ebf73ef3aeae5bc4676244ca7e9776`.

Mỗi nhóm nộp một repo chung. Nhóm có ba thành viên, phân công A/B/C như sau;
trạng thái thực hiện được ghi trong từng mục INDIVIDUAL và evidence tương ứng.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Phạm Quang Đạt | 2A202602704 | Phụ trách Phase A, Tasks 1–4; tích hợp pipeline Day 18, kiểm chứng và báo cáo với Codex hỗ trợ | `src/phase_a_ragas.py`, tests Phase A, hai JSON answers/RAGAS, `doc/reports/failure_clusters.md`; commit Phase A nêu trên |
| 2 | Trương Việt Anh | 2A202602444 | Trưởng nhóm/người nộp; Phase B, Tasks 5–8, hoàn tất triển khai/thực nghiệm với Codex hỗ trợ | `src/phase_b_judge.py`, tests Phase B, `artifacts/judge_results.json`, `doc/reports/bias_report.md` |
| 3 | Nguyễn Vũ Anh | 2A202602502 | Phase C, Tasks 9a–13, hoàn tất triển khai/thực nghiệm với Codex hỗ trợ | `src/phase_c_guard.py`, `guardrails/`, tests Phase C, `artifacts/guard_results.json`, `doc/reports/blueprint.md` |

GitHub/email dùng cho commit: Phạm Quang Đạt — `datpq-alpha`,
`phamqdat99@gmail.com`; Trương Việt Anh —
[vietanh2005-tva](https://github.com/vietanh2005-tva), `truongvietanh277@gmail.com`;
Nguyễn Vũ Anh — [vuanh259](https://github.com/vuanh259), `vuanhcp123@gmail.com`.

Người phụ trách tích hợp và chạy batch Phase A: **Phạm Quang Đạt — 2A202602704**,
với Codex hỗ trợ thao tác mã và thực nghiệm; bằng chứng ở các artifacts và báo
cáo Phase A. Người tích hợp bản cuối và nộp link: **Trương Việt Anh — 2A202602444**.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows, Python 3.11.0; Microsoft Visual Studio 18 Build
Tools/MSVC đã build Annoy 1.17.3 thành công. `.venv` runtime đầy đủ và
`.venv-tests` theo test lock đã qua `pip check`; imports đạt khi nạp `torch`
trước các thư viện ML trên máy này. RAGAS 0.1.22, NeMo 0.10.0/Colang 1.0,
Presidio analyzer/anonymizer 2.2.364, spaCy 3.8.16 + en_core_web_sm 3.8.0.
FastEmbed all-MiniLM-L6-v2 đã cache; dùng HF_HUB_DISABLE_XET=1 để tải qua HTTP
khi Xet không hoàn tất. Chi tiết và giới hạn ở [ENVIRONMENT.md](ENVIRONMENT.md).

BGE-M3, BGE-reranker-v2-M3 và Qdrant 1.9.7 đã chạy; 50 answers thật, mỗi câu có
3 contexts, không extractive fallback. Loader dùng 26 tài liệu/125 child chunks;
hai PDF scan chưa có OCR. B/C dùng đúng fixtures của Day24, không sửa nhãn để
tăng điểm. Thực nghiệm API tách riêng khỏi tests mock/offline.

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
Trạng thái: hoàn tất triển khai, tests và thực nghiệm với Codex hỗ trợ.

#### Công việc và bằng chứng

- **Task 5:** pairwise judge gọi OpenAI JSON mode, dùng reference và tiêu chí
  accuracy/completeness/conciseness; kiểm tra winner, reasoning và scores hữu hạn
  trong [0,1]. Không làm theo chỉ dẫn nằm trong candidate/reference.
- **Task 6:** gọi hai lượt A/B và B/A, đổi winner/scores lượt 2 về danh tính gốc;
  bất đồng thì final=tie. Giữ nguyên reasoning của cả hai lượt để review.
- **Task 7:** Cohen's κ tính từ observed/chance agreement, từ chối labels lệch
  số lượng hoặc κ không xác định. Calibration dùng đúng supplied model_answer;
  human_label/human_note không vào prompt chấm.
- **Task 8:** tính vị trí bất đồng và tỷ lệ winner dài hơn, ghi rõ mẫu số, phân
  tích nội dung trước khi kết luận bias. Soạn báo cáo có đủ năm cặp, cả hai lượt,
  mười nhãn nhị phân và reasoning thật.

Mã: [`phase_b_judge.py`](../src/phase_b_judge.py). Kiểm chứng offline: **30 tests
Phase B đạt**, gồm SDK mock, swap, κ, bias và các trường hợp JSON/scores lỗi.
Ở thời điểm commit Phase B, toàn bộ tests support/student: 158 đạt, 3 deselected; bản tích hợp cuối có 159 tests đạt.

```powershell
.\.venv-tests\Scripts\python.exe -m pytest tests/ -m 'support or student' -q
.\.venv\Scripts\python.exe -c "import torch, runpy; runpy.run_path('scripts/run_experiments.py', run_name='__main__')" --phase b --live
```

Artifact: [`judge_results.json`](../artifacts/judge_results.json), timestamp
`2026-10-12T05:11:39.376725+00:00`. Judge `gpt-4o-mini`; nguồn A là answers của
pipeline, B là model_answer của fixture, reference là test set. Validator đã
đối chiếu schema, nguồn, SHA-256, số lượng và các thống kê. Báo cáo:
[`bias_report.md`](reports/bias_report.md). Commit bằng chứng có tiêu đề
`feat: complete Phase B judge evaluation and bias report`.

#### Kết quả, giới hạn và AI hỗ trợ

Calibration đạt 10/10 agreement, κ=1,0 (sáu nhãn 1, bốn nhãn 0). Position
inconsistency=3/5 (IDs 5, 12, 41); winner dài hơn=2/2 decisive cases. Hai câu
dài hơn cũng có nội dung tốt hơn, nên tỷ lệ này chưa chứng minh verbosity bias.
Ở câu 5/41, judge thay đổi ưu tiên giữa từ chối và khẳng định sai; câu 12 thay
đổi yêu cầu nhắc lại điều kiện đã có trong câu hỏi. Cần hoán vị, lặp và review
thêm thay vì xem κ cao là bằng chứng judge luôn đáng tin.

Reasoning nhị phân ở câu 1/12/46 còn mô tả điều kiện không có đủ trong answer;
nhãn khớp human không bảo đảm lời giải thích hoàn toàn đúng. Mẫu năm cặp/mười
nhãn và một lần chạy không đủ suy rộng. Không sửa nhãn, fixture hoặc chọn lại
lượt chạy để tăng κ.

Codex hỗ trợ viết code, tests, chạy runner và soạn tài liệu. Bằng chứng là
tests offline cộng JSON live/metadata đối chiếu nguồn; tests mock không tạo
điểm API. Người phụ trách cần đọc và giải thích phần kê khai trước khi nộp.

### NguyenVuAnh-2A202602502

Họ và tên: **Nguyễn Vũ Anh**. MSSV: **2A202602502**.
GitHub: [vuanh259](https://github.com/vuanh259).
Phần được giao: **Phase C — Guardrails, Tasks 9a–13**.
Trạng thái: hoàn tất triển khai, tests và thực nghiệm với Codex hỗ trợ.

#### Công việc và bằng chứng

- **Task 9a:** Presidio thật detect/anonymize CCCD/CMND, VN phone, email và
  phone quốc tế; giữ entities, offsets và score. Dùng NlpEngineProvider/spaCy
  en_core_web_sm thật; chọn các entity types đúng scope lab sau khi phát hiện
  English NER và giấy phép Mỹ gây false positives với tiếng Việt.
- **Task 9b:** NeMo input async chỉ chạy input rails; lấy quyết định stop từ
  activated_rails, thiếu log thì báo lỗi. Làm rõ closed domain HR/IT và phân
  biệt câu hỏi policy cho bản thân với xin dữ liệu riêng/credentials.
- **Task 10:** một event loop cho 28 inputs, tái dùng engines, short-circuit
  sau PII; expected chỉ đối chiếu, không dùng quyết định actual.
- **Task 11:** kiểm tra supplied answer bằng output rails trong context câu
  hỏi; giữ nguyên output sạch, thay output nhạy cảm bằng câu từ chối. Thiếu
  replacement hợp lệ thì báo lỗi thay vì trả unsafe answer.
- **Task 12:** hai warm-ups thật mỗi lớp, 20 timed samples; luôn chạy cả hai
  input layers, giữ raw samples và percentile tuyến tính từ helper có sẵn.
- **Task 13:** soạn blueprint từ A/B/C, phân biệt đề xuất production/CI với
  runner kiểm chứng từng lớp, ghi phần latency chưa đo và kế hoạch đo thêm.

Mã: [`phase_c_guard.py`](../src/phase_c_guard.py), policy ở `guardrails/`.
Offline: **25 tests Phase C đạt**; bản tích hợp có **159 tests đạt, 3 deselected**.
Tests kiểm tra scope PII, rail logs, clean preservation, label leakage, warm-up,
raw latency và một event loop. Mocks không được dùng làm kết quả thí nghiệm.

```powershell
$env:HF_HUB_DISABLE_XET='1'
.\.venv\Scripts\python.exe -c "import torch, runpy; runpy.run_path('scripts/run_experiments.py', run_name='__main__')" --phase c --live --latency-samples 20
.\.venv-tests\Scripts\python.exe scripts/check_lab.py
```

Artifact: [`guard_results.json`](../artifacts/guard_results.json), timestamp
`2026-10-12T05:38:27.659799+00:00`, guard `gpt-4o-mini`. Validator đối chiếu nguồn,
hash/schema, từng quyết định, tổng counts và percentiles từ samples. Kiểm tra
Presidio thật trong [`presidio_checks.json`](../artifacts/presidio_checks.json)
xác nhận bốn input PII có required types/offsets đúng và đã anonymize.
Blueprint: [`blueprint.md`](reports/blueprint.md). Commit bằng chứng có tiêu đề
`feat: complete Phase C guardrails and production blueprint`.

#### Kết quả, sửa lỗi và giới hạn

Run cuối đạt **20/20 attacks**, **8/8 clean allowed**,
false_positive_rate=0%; output **4/4 đúng**.
Input sequential P95 **2042.571 ms**,
latency_budget_ok=false; NeMo input P95
2023.339 ms là lớp trễ chính. Giữ nguyên số vượt target
500ms; chưa đo RAG, NeMo output hoặc full request nên không suy full-guard P95.

Giữ hai lần chạy trước: `guard_results_baseline.json` có 19/20 attacks,
1/8 clean; `guard_results_scope_fix.json` có 20/20 attacks, 7/8 clean. Spans
baseline ở `presidio_clean_baseline.json` chứng minh v2024 bị nhận là giấy
phép Mỹ, “Xin” bị coi là PERSON và MFA thành ORGANIZATION. Sửa theo entity
types của lab, không whitelist theo câu/ID. NeMo vẫn kiểm tra yêu cầu thông
tin nhân viên riêng tư ngoài các mẫu số/email cụ thể.

Lần hai chặn nhầm câu clean VPN 105, trong khi fresh probe cùng prompt lại
trả No/stop=false (`clean_vpn_diagnosis.json`). Bổ sung quy tắc policy cho bản
thân/VPN/MFA/password requirements rồi chạy lại toàn bộ, giữ các kết quả trước.
Không khẳng định đã chứng minh nguyên nhân nội tại hoặc guard luôn ổn định.

Scope PII hiện chưa bao phủ mọi tên/địa chỉ tiếng Việt. Bộ 20/8/4 và 20 timed
samples còn nhỏ; self-check LLM/regex không bảo đảm chống mọi bypass. Blueprint
nêu mở rộng controls, review false positives và đo nhiều samples/concurrency
trước production. CI gates/monitoring là đề xuất, chưa triển khai workflow.

Codex hỗ trợ code, tests, setup, chạy thực nghiệm, đối chiếu JSON và soạn báo
cáo. Người phụ trách cần đọc và giải thích phần kê khai trước khi nộp.

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
Các đoạn trên ghi bằng chứng Phase A; runtime/kết quả B và C được xác nhận riêng trong từng mục INDIVIDUAL và artifacts tương ứng.
Thành viên cần tự đọc mã, đối chiếu artifacts với báo cáo và giải thích phần
công việc mình kê khai trước khi nộp.

## Kiểm chứng bản tích hợp

Người dùng đã cho phép gửi fixtures lab Day24 tới OpenAI cho B/C. Codex hỗ trợ
code, thao tác API và soạn báo cáo; từng phần được kê khai trong INDIVIDUAL.
Commit dùng đúng tên/email thành viên đã cung cấp theo phân công A/B/C.
Không cần cấp mật khẩu hoặc tài khoản GitHub B/C; tài khoản đang xác thực có
quyền push repo chung. `.env`, vlearn.md, virtualenv và logs không commit.

Lệnh offline cuối: `python scripts/check_lab.py --with-tests`, dùng interpreter
`.venv-tests`; checker chỉ đọc evidence, tests chặn network. Kết quả kiểm chứng
trước commit: **159 tests đạt, 3 deselected; checker 0 failed**.

## Cập nhật sau khi nộp

Chưa có thông tin về phiên bản đã nộp hoặc cập nhật sau khi nộp.
Bản kỹ thuật A/B/C đã tích hợp; trưởng nhóm xác nhận deadline, nộp link qua kênh lớp và bổ sung thời điểm nộp/lịch sử cập nhật. Việc push repo không tự xác nhận đã nộp bài cho lớp.
