# Môi trường K4 Track 3A

## Phiên bản mục tiêu và cách kiểm tra

Dùng Python 3.11 cho lab này. Tạo virtualenv mới sau khi tải starter, cài
dependencies và chạy `pip check` trên máy của nhóm. Tests hỗ trợ chạy không
cần API hay model; student tests vẫn fail nếu các hàm TODO chưa được làm.

Bộ phiên bản lõi trong starter: RAGAS 0.1.22; LangChain 0.2.17; langchain-core
0.2.43; community 0.2.19; openai integration 0.1.25; OpenAI SDK 1.109.1; NeMo
0.10.0; Annoy 1.17.3; NumPy 1.26.4. Các pins nằm trong `requirements/constraints-core.txt`.
Đây là constraints cho tập lõi, **không phải lock toàn bộ dependencies**.

Phase A bổ sung pin `pyarrow==17.0.0`: khi cài trên Python 3.11, resolver đã
chọn PyArrow 26.0.0 nhưng import thực tế báo cần NumPy 2.0 trở lên. Giữ nguyên
NumPy 1.26.4 theo Day 24 và dùng PyArrow 17.0.0, nằm trong yêu cầu
`pyarrow>=15.0.0` của datasets 2.21.0. Vẫn cần kiểm tra imports sau `pip check`.

Trên máy Windows của lần chạy Phase A, import PyTorch sau RAGAS/datasets gây
`WinError 1114` ở `c10.dll`; import `torch` trước thì kiểm tra imports đạt.
Không cần đổi các phiên bản lõi để xử lý thứ tự nạp DLL này. Khi gặp cùng lỗi,
có thể chạy các script gốc với PyTorch được nạp trước:

```powershell
.\.venv\Scripts\python.exe -c "import torch, runpy; runpy.run_path('scripts/setup_answers.py', run_name='__main__')" --live
.\.venv\Scripts\python.exe -c "import torch, runpy; runpy.run_path('scripts/run_experiments.py', run_name='__main__')" --phase a --live
.\.venv\Scripts\python.exe -c "import torch, runpy; runpy.run_path('scripts/run_experiments.py', run_name='__main__')" --phase b --live
$env:HF_HUB_DISABLE_XET='1'
.\.venv\Scripts\python.exe -c "import torch, runpy; runpy.run_path('scripts/run_experiments.py', run_name='__main__')" --phase c --live --latency-samples 20
```

Hiện tượng phụ thuộc thứ tự import trên Windows cũng được thảo luận trong
[PyTorch issue 166628](https://github.com/pytorch/pytorch/issues/166628);
đây là workaround đã kiểm tra trên máy này, không phải kết luận cho mọi máy.

Trên Windows, build `annoy==1.17.3` cần Microsoft Visual C++ 14.0 trở lên.
Sau khi cài compiler, nhóm chạy các bước kiểm chứng phía dưới trên chính môi
trường sẽ làm lab. Kết quả unit tests hoặc pip resolve không chứng minh full
NeMo đã cài/chạy được.

Theo [README của NeMo v0.10.0](https://github.com/NVIDIA/NeMo-Guardrails/blob/v0.10.0/README.md),
bản này hỗ trợ Python đến 3.11 và cần compiler/dev tools cho Annoy. Không lấy
hướng dẫn bản NeMo mới nhất để suy ra bản 0.10.0 hỗ trợ Python 3.12+.

## Chuẩn bị compiler và virtualenv trước buổi học

Trên Windows, cài Microsoft C++ Build Tools, chọn workload **Desktop development
with C++**, bao gồm MSVC và Windows SDK. Mở lại terminal sau cài; dùng Developer
PowerShell nếu compiler chưa có trong PATH. Làm theo
[hướng dẫn Microsoft](https://learn.microsoft.com/en-us/cpp/build/vscpp-step-0-installation?view=msvc-170).
Việc cài compiler/tải model không thuộc 15 phút kiểm tra đầu buổi.

Từ gốc repo trên PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements/requirements.txt -c requirements/constraints-core.txt
.\.venv\Scripts\python.exe -m pip check
```

Không bắt buộc kích hoạt virtualenv: dùng đường dẫn interpreter như trên.
Nếu muốn chạy `Activate.ps1` và gặp lỗi execution policy, có thể cho phép script
chỉ trong phiên PowerShell hiện tại rồi kích hoạt:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Nếu policy của tổ chức vẫn chặn, dùng interpreter trực tiếp; không thay policy
toàn máy. Xem [hướng dẫn venv Python 3.11](https://docs.python.org/3.11/library/venv.html).
macOS/Linux dùng `python3.11 -m venv .venv` và `source .venv/bin/activate`;
cần toolchain C++ của hệ điều hành khi build Annoy.

## Kiểm chứng cài đặt và tải model

Cài thành công qua pip chưa chứng minh đã tải model hoặc API kết nối được.
Kiểm tra các lớp riêng biệt để biết lỗi nằm ở đâu:

```bash
python -m pip check
python -c "import ragas, nemoguardrails, presidio_analyzer, spacy; print('imports OK')"
python -m pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
docker compose -f infra/docker-compose.yml up -d
python scripts/setup_answers.py --live
```

Qdrant dùng tag [v1.9.7](https://github.com/qdrant/qdrant/releases/tag/v1.9.7),
không dùng `latest`. Setup sẽ tải embedding BGE-M3/reranker theo module bài
trước; nhóm cần cache/download xong trước lớp. Model/download/indexing có thể
mất lâu tùy máy và mạng. Generation/enrichment có thể gọi API, có chi phí.

Ghi OS, Python, kết quả pip/import/compiler/model download trong TEAM. Nếu full
stack cài chưa xong, ghi lỗi thật; không điền “tương thích” dựa trên dry-run.

## Line endings và source hashes khi chuyển máy

Metadata của artifacts dùng SHA-256 trên bytes của file nguồn. `.gitattributes`
giữ nguyên bytes của `artifacts/*.json` và checkout `fixtures/*.json` với CRLF
trên mọi hệ điều hành, khớp định dạng fixture của lần đo trên Windows.
Điều này tránh Git tự đổi line endings làm checker báo stale source dù JSON
không đổi nội dung. Khi tự ghi lại fixture, giữ CRLF; khi tạo answers mới,
chạy lại phase liên quan để metadata khớp file nguồn mới.

## Tạo môi trường unit test offline

Khi chỉ sửa logic/scaffold, không cần cài NeMo, ML model hoặc C++ compiler.
Tạo môi trường riêng với các dependencies đã pin:

```powershell
py -3.11 -m venv .venv-tests
.\.venv-tests\Scripts\python.exe -m pip install -r requirements/requirements-test.lock.txt
.\.venv-tests\Scripts\python.exe -m pip check
.\.venv-tests\Scripts\python.exe -m pytest tests/ -m support -q
```

`requirements/requirements-test.txt` ghi dependencies trực tiếp; file `.lock.txt` khóa
toàn bộ dependencies của tập test. Đây chỉ là lock unit test, không thay constraints hoặc
cài đặt full runtime. Không commit virtualenv, key hoặc cache model.

## Cấu hình runtime Phase C của nhóm Magician

`setup_presidio()` tạo `NlpEngineProvider` thật với `en_core_web_sm` 3.8.0,
spaCy 3.8.16 và Presidio analyzer/anonymizer 2.2.364. Model này được chọn vì
download `en_core_web_lg` khoảng 400 MB quá chậm/gián đoạn trên máy thực nghiệm;
bản nhỏ khoảng 13 MB vẫn có pipeline NLP/NER thật. Không dùng `spacy.blank`,
engine giả hoặc mocks trong runner live. Regex CCCD/CMND và số điện thoại VN
giữ nguyên Day24; email dùng recognizer của Presidio. `PRESIDIO_ENTITIES` giới
hạn quyết định PII ở VN_CCCD, VN_PHONE, EMAIL_ADDRESS và PHONE_NUMBER theo yêu
cầu lab. Lần đầu dùng tất cả recognizers đã chặn nhầm 7/8 clean inputs:
v2024 thành US_DRIVER_LICENSE, “Xin” thành PERSON và MFA thành ORGANIZATION.
Baseline được giữ ở `artifacts/guard_results_baseline.json` và các spans ở
`artifacts/presidio_clean_baseline.json`. Các types khác không quyết định block
ở lớp PII; NeMo vẫn kiểm tra yêu cầu dữ liệu nhân viên riêng tư. Chưa hỗ trợ
nhận diện đầy đủ mọi tên/địa chỉ tiếng Việt hoặc dữ liệu mới.

NeMo dùng đúng 0.10.0/Colang 1.0 và built-in self check input/output của starter,
OpenAI `gpt-4o-mini`. Annoy 1.17.3 đã build được bằng MSVC trong Microsoft Visual
Studio 18 Build Tools. NeMo tải cache FastEmbed `all-MiniLM-L6-v2` khi khởi tạo;
trên máy này Xet không hoàn tất, chuyển `HF_HUB_DISABLE_XET=1` thì tải/khởi tạo
thành công. Biến này chỉ đổi transport download, không đổi model hay policy.
Cache và khởi tạo đều được làm trước các lượt timed của Task 12.

`pip check` của runtime đầy đủ đạt; imports `torch`, RAGAS, NeMo, Presidio,
spaCy được kiểm tra riêng. Log cài đặt/chạy nằm trong `.venv/` không commit.
Các dependency ngoài bộ core chưa được khóa toàn bộ; khi đổi máy cần ghi
phiên bản thực tế và kiểm tra imports cùng model download trước chạy lại.
