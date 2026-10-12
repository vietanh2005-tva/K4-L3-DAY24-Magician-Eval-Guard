# Đánh giá LLM Judge Phase B

Nhóm: **Magician**. Người phụ trách: **Trương Việt Anh — 2A202602444**.

Codex hỗ trợ triển khai, chạy thực nghiệm và soạn báo cáo; bằng chứng kiểm chứng ở TEAM.md.

Nguồn: `artifacts/judge_results.json`; run timestamp: `2026-10-12T05:11:39.376725+00:00`.
Generation: `gpt-4o-mini-2024-07-18`; judge: `gpt-4o-mini`.
Lần chạy thật qua OpenAI, temperature=0, JSON mode; không phải kết quả mock.

## Năm cặp A/B và hai lượt

A từ `artifacts/answers_50q.json:answer`; B từ `fixtures/human_labels_10q.json:model_answer`;
reference từ `fixtures/test_set_50q.json:ground_truth`. Giữ cố định IDs 1, 5, 12, 21, 41.
Lượt 2 gọi lại với B/A, sau đó đổi winner và scores về A/B gốc. Nếu hai lượt
bất đồng thì final_winner=tie; không chọn lượt thuận lợi hơn hoặc sửa nhãn theo human.
Reasoning lượt 2 giữ nguyên lời judge nên tên A/B trong lời giải thích là vị trí đã hoán đổi.

| ID | Winner lượt 1 | Winner lượt 2 quy đổi | Final | Consistent | Scores lượt 1 A/B | Scores lượt 2 A/B |
|---|---|---|---|---|---|---|
| 1 | B | B | B | true | 0.7/1.0 | 0.7/1.0 |
| 5 | B | A | tie | false | 0.0/0.5 | 0.5/0.0 |
| 12 | A | tie | tie | false | 1.0/0.5 | 1.0/1.0 |
| 21 | B | B | B | true | 0.0/1.0 | 0.0/1.0 |
| 41 | B | A | tie | false | 0.0/0.5 | 0.5/0.0 |

### Cặp 1

Nhân viên được nghỉ bao nhiêu ngày khi kết hôn?

- **Reference:** Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn, không trừ vào phép năm.
- **Candidate A:** Nhân viên được nghỉ 3 ngày làm việc khi kết hôn.
- **Candidate B:** Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn.

**Reasoning lượt 1:** Câu trả lời B chính xác và đầy đủ hơn vì nó không chỉ nêu số ngày nghỉ mà còn nhấn mạnh rằng đó là ngày nghỉ có lương, điều này là thông tin thiết yếu. Câu A thiếu thông tin về việc nghỉ có lương, do đó không hoàn chỉnh.

**Reasoning lượt 2, A/B đã hoán đổi trong prompt:** Câu trả lời A chính xác và đầy đủ hơn vì nó nêu rõ rằng 3 ngày nghỉ là có lương, trong khi câu B không đề cập đến điều này, dẫn đến thiếu sót về thông tin quan trọng.

### Cặp 5

Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt?

- **Reference:** Đơn hàng trên 50.000.000 VNĐ cần Tổng Giám đốc (CEO) phê duyệt.
- **Candidate A:** Không tìm thấy.
- **Candidate B:** Cần Giám đốc phòng ban phê duyệt.

**Reasoning lượt 1:** Câu trả lời B cung cấp thông tin về việc cần Giám đốc phòng ban phê duyệt, mặc dù không chính xác theo thông tin tham chiếu. Câu trả lời A không cung cấp thông tin nào và không liên quan đến câu hỏi, do đó không có giá trị. Câu B có ít nhất một thông tin liên quan đến quy trình phê duyệt, mặc dù không đúng với yêu cầu của câu hỏi.

**Reasoning lượt 2, A/B đã hoán đổi trong prompt:** Câu trả lời B cho biết không tìm thấy thông tin, mặc dù không cung cấp thông tin cụ thể nào, nhưng cũng không sai. Câu trả lời A lại cung cấp thông tin sai về việc ai cần phê duyệt, vì theo tham chiếu, cần Tổng Giám đốc phê duyệt cho đơn hàng trên 50 triệu. Do đó, câu trả lời B chính xác hơn trong bối cảnh này.

### Cặp 12

Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên là bao nhiêu?

- **Reference:** Nhân viên chính thức có thời gian làm việc từ 6 tháng trở lên được thưởng Tết tối thiểu 1 tháng lương. Nhân viên dưới 6 tháng được hưởng pro-rata theo số tháng làm việc thực tế.
- **Candidate A:** Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên là 1 tháng lương.
- **Candidate B:** Nhân viên được thưởng Tết tối thiểu 1 tháng lương.

**Reasoning lượt 1:** Câu trả lời A cung cấp thông tin chính xác và đầy đủ về mức thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên, trong khi câu trả lời B chỉ nêu chung chung mà không chỉ rõ điều kiện về thời gian làm việc. Câu A cũng rõ ràng và không thừa thông tin.

**Reasoning lượt 2, A/B đã hoán đổi trong prompt:** Cả hai câu trả lời đều cung cấp thông tin chính xác về mức thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên, đều nêu rõ là 1 tháng lương. Cả hai câu trả lời đều đầy đủ và không có thông tin thừa, do đó chất lượng tương đương.

### Cặp 21

Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào?

- **Reference:** Theo chính sách v2024: 15 ngày cơ bản + 3 ngày thâm niên (9÷3=3) = 18 ngày phép. Lương Senior (P3-P4): 20-35 triệu VNĐ/tháng.
- **Candidate A:** Không tìm thấy.
- **Candidate B:** Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu.

**Reasoning lượt 1:** Câu trả lời B cung cấp thông tin chính xác về số ngày phép và mức lương của nhân viên Senior, bao gồm cả cách tính số ngày phép. Câu trả lời A không cung cấp thông tin nào, do đó không đáp ứng được yêu cầu về accuracy và completeness.

**Reasoning lượt 2, A/B đã hoán đổi trong prompt:** Câu trả lời A cung cấp thông tin chính xác về số ngày phép và mức lương của nhân viên Senior, phù hợp với thông tin trong tham chiếu. Câu trả lời B không cung cấp thông tin nào và không đáp ứng yêu cầu của câu hỏi.

### Cặp 41

Nhân viên được nghỉ bao nhiêu ngày phép năm?

- **Reference:** Theo chính sách v2024 HIỆN HÀNH: 15 ngày cơ bản (+1 ngày/3 năm thâm niên). Chính sách v2023 (đã bị thay thế) là 12 ngày. RAG có thể retrieve cả 2 tài liệu — câu trả lời đúng phải ưu tiên v2024.
- **Candidate A:** Không tìm thấy.
- **Candidate B:** Nhân viên được nghỉ 12 ngày phép năm.

**Reasoning lượt 1:** Câu trả lời B cung cấp thông tin về số ngày phép năm theo chính sách cũ, mặc dù không chính xác theo chính sách hiện hành. Câu trả lời A không cung cấp thông tin nào, do đó không đáp ứng được yêu cầu về độ chính xác và đầy đủ. Câu trả lời B có ít nhất một thông tin liên quan, mặc dù không phải là thông tin mới nhất.

**Reasoning lượt 2, A/B đã hoán đổi trong prompt:** Câu trả lời A không chính xác vì nó dựa trên chính sách cũ (v2023) thay vì chính sách hiện hành (v2024). Câu trả lời B, mặc dù không cung cấp thông tin cụ thể, nhưng không đưa ra thông tin sai lệch. Do đó, câu trả lời B được coi là tốt hơn trong bối cảnh này.

## Position và verbosity

Position inconsistency: **3/5 = 60%**, tại IDs 5, 12, 41.
Winner dài hơn: **2/2 = 100%**; A thắng khi dài hơn=0, B thắng khi dài hơn=2.
Độ dài là số ký tự Unicode theo len(); ba tie không vào mẫu số verbosity.

Ở câu 5, lượt đầu chọn đáp án phê duyệt sai vì cho rằng có thông tin liên quan vẫn
tốt hơn từ chối; lượt sau ưu tiên không khẳng định sai. Câu 41 lặp lại mâu thuẫn này
giữa trả lời theo v2023 và từ chối. Câu 12 chuyển từ A sang tie vì hai lượt đánh giá
khác nhau việc nhắc lại điều kiện “chính thức, từ 6 tháng”. Đây là bất ổn quan sát
sau hoán vị, chưa tách được ảnh hưởng vị trí khỏi dao động hoặc tiêu chí chấm.

Hai decisive cases là câu 1 và 21: B dài hơn nhưng cũng bổ sung thông tin có ích
(“có lương” hoặc đủ phép năm + dải lương). Vì chất lượng khác nhau, 100% ở đây
không chứng minh judge thưởng độ dài vô điều kiện. Cần thêm cặp cùng nội dung
nhưng khác độ dài, cùng độ dài nhưng khác chất lượng, hoán vị và lặp nhiều lần.

## Calibration đúng model_answer

Chấm đúng mười model_answer của fixture theo thứ tự gốc; không thay bằng answers
mới của pipeline. Prompt helper chỉ nhận question, answer, reference. human_label
và human_note chỉ được đọc để đối chiếu sau khi đã chấm, không gửi vào prompt.

| ID | Model answer gốc | Judge | Human | Agree | Reasoning của judge |
|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 1 | 1 | đúng | Câu trả lời chính xác theo thông tin trong tài liệu tham khảo, nêu rõ số ngày nghỉ và điều kiện không trừ vào phép năm. |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | 0 | đúng | Câu trả lời sai vì yêu cầu phê duyệt cho đơn hàng trên 50 triệu là từ Tổng Giám đốc, không phải Giám đốc phòng ban. |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 1 | 1 | đúng | Câu trả lời chính xác theo thông tin trong reference, nêu rõ điều kiện và mức thưởng cho nhân viên chính thức có từ 6 tháng trở lên. |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | 1 | 1 | đúng | Câu trả lời chính xác theo reference, nêu rõ số ngày phép và khoảng lương cho nhân viên Senior với 9 năm thâm niên. |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | 1 | đúng | Câu trả lời chính xác theo reference, nêu rõ số tiền phải hoàn trả và lý do vì chưa đủ thời gian cam kết. |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu. | 0 | 0 | đúng | Câu trả lời sai vì không đề cập đến sự cần thiết phải có sự phê duyệt của Kế toán trưởng bên cạnh Trưởng phòng. Ngoài ra, phí phạt được tính cho 15 ngày quá hạn, không phải là 2% trên tổng số tiền tạm ứng. |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | 1 | đúng | Câu trả lời cung cấp đúng số ngày phép và tổng phụ cấp hàng tháng theo thông tin trong reference. |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | 0 | đúng | Câu trả lời sai vì nó dựa trên chính sách cũ (v2023) thay vì chính sách hiện hành (v2024) là 15 ngày phép năm. |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần. | 1 | 1 | đúng | Câu trả lời chính xác theo reference, nêu rõ rằng nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần, đồng thời không bỏ qua điều kiện cần có sự phê duyệt của trưởng phòng. |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | 0 | đúng | Câu trả lời sai vì khẳng định rằng nhân viên Manager có thể dùng VPN cá nhân khi WFH, trong khi reference rõ ràng cấm việc này. |

**Cohen’s κ = 1.0**. Observed agreement p_o=1.0 (10/10).
Cả judge và human có sáu nhãn 1, bốn nhãn 0 nên p_e=0,6×0,6+0,4×0,4=0.52.
κ=(1−0,52)/(1−0,52)=1. Confusion matrix: TP=6, TN=4, FP=0, FN=0.
Vượt mốc bonus κ>0,6 trên bộ calibration này; không suy rộng thành độ chính xác
tuyệt đối hoặc độ ổn định trên dữ liệu mới.

## Giới hạn và cách dùng judge

Không có bất đồng nhãn nhị phân với human trong mười câu này. Tuy nhiên reasoning
câu 1 nói answer có điều kiện không trừ phép năm, câu 12 nói answer nêu rõ điều kiện
chính thức/từ sáu tháng, câu 46 nói answer giữ điều kiện trưởng phòng phê duyệt:
các chi tiết này không xuất hiện đầy đủ trong model_answer tương ứng. Nhãn đúng
không đảm bảo mọi câu trong lời giải thích đúng; cần đọc lại answer và reference.

Chỉ có năm cặp và mười nhãn, một lần chạy mỗi chiều, cùng alias gpt-4o-mini
cho generation và judge. Alias có thể đổi phiên bản; temperature=0 không bảo đảm
kết quả bất biến. Metadata ghi model ID cấu hình thực tế và hash nguồn, không
khẳng định snapshot judge vì runner không lưu response.model cho các lượt chấm.

Dùng kết quả để ưu tiên review: cả hai lượt bất đồng, phiên bản/phủ định/điều kiện
và các quyết định ảnh hưởng quyền lợi cần người đọc đối chiếu tài liệu. Nếu mở rộng
prompt, bộ calibration hoặc tiêu chí, chạy lại và lưu version mới; không sửa fixture
human hoặc chọn một lần chạy khác chỉ để nâng κ. RAGAS và judge bổ trợ nhau,
không dùng điểm judge thay bằng chứng retrieval hoặc đánh giá bảo mật của Phase C.

Kiểm chứng offline phần B: 30 tests Phase B đạt (SDK mock + validation).
Ở thời điểm commit Phase B, tests support/student: 158 đạt, 3 deselected.
Bản tích hợp cuối bổ sung test scope PII, có 159 tests đạt, 3 deselected.
Các tests này không gọi API; JSON live được runner và validators kiểm tra riêng.
