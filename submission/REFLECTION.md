# Reflection - Day 20 Model Serving

**Họ Tên:** _(Người nộp tự bổ sung)_

**MSSV:** _(Người nộp tự bổ sung)_

**Cohort:** _(Người nộp tự bổ sung)_

**Ngày hoàn thiện kỹ thuật:** 2026-10-06

## 1. Hardware & runtime

- **OS:** Windows 10 AMD64
- **CPU:** 11th Gen Intel Core i7-11800H @ 2.30 GHz
- **Cores:** 8 physical / 16 logical
- **CPU extensions:** AVX2, AVX-512
- **RAM:** 31.7 GB
- **Accelerator:** NVIDIA RTX A2000 Laptop GPU, 4,096 MiB; Vulkan
- **llama.cpp asset:** `llama-b10488-bin-win-vulkan-x64.zip`
- **Model:** Qwen3.5 0.8B (`LAB_MODEL=qwen35-0.8b`)
- **Quantization:** Q4_K_M + UD-Q2_K_XL
- **Chạy ở đâu:** laptop local

**Setup story:** Máy không có Python trên PATH và PowerShell 5.1 dùng console
encoding cũ, nên script được sửa để tìm Python do `uv` quản lý và xuất UTF-8.
Hardware probe cũng cần Windows fallbacks vì WMI bị từ chối. Hai GGUF được kiểm
tra SHA-256 trước khi chạy; runtime Vulkan b10488 nhận cả iGPU Intel và RTX A2000.

## 2. Đo lường

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|---|--:|--:|--:|--:|--:|--:|
| Q4_K_M | 0.50 | 17,638 | 300 / 361 | 13.3 / 14.3 | 1,090 / 1,249 / 1,249 | 74.9 |
| UD-Q2_K_XL | 0.39 | 25,002 | 247 / 309 | 13.7 / 14.7 | 1,110 / 1,200 / 1,200 | 73.2 |

**Quan sát:** Q2 nhỏ hơn 22% nhưng decode chậm hơn khoảng 2.3% và cold start
chậm hơn 7.4 giây, nên không đáng đổi trong giới hạn RAM này. Quality gate C5 cho
cả hai chỉ đạt 2/5; Q2 còn thất bại ở bản dịch mà Q4 trả lời đúng. Tôi chọn Q4 và
dùng validator cho tác vụ có định dạng chặt.

## 3. Serving under load

| Users | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|--:|--:|--:|--:|--:|--:|--:|
| 10 | 0.14 | 29,000 | 29,000 | 29,000 | 3.9 | 0.0% |
| 50 | 0.00 | 0 | 0 | 0 | 0.0 | 0.0% |

- **Offered load tăng 5x, throughput hoàn tất tăng:** 0.00x
- **P95 tăng:** không xác định; không request nào hoàn tất trong cửa sổ 60 giây
- **Effective concurrency ở 50 users:** số 0 bị censored, không phản ánh request đang chạy
- **Peak `llamacpp:n_busy_slots_per_decode`:** 2.09 / 4 slots; `requests_processing` đạt 4

**Saturation reading:** Ở 10 users, Little's Law đã cho 3.9 request đồng thời,
gần bằng bốn slot. Ở 50 users, Prometheus vẫn thấy bốn request đang xử lý nhưng
Locust không nhận được completion trước khi hết 60 giây. Vì vậy hàng số 0 là dữ
liệu bị kiểm duyệt bởi thời lượng test, không phải headroom. Tôi sẽ giảm output
cap/SLO budget hoặc scale replica trước khi tăng `--parallel`, vì thêm slot sẽ chia
nhỏ hơn bandwidth vốn đã bão hòa.

## 4. Integration

| Day | Piece | Real hay stub? |
|---|---|---|
| N16 Cloud/IaC | local process | stub |
| N17 Data pipeline | in-process fixture corpus | stub |
| N18 Lakehouse | no external storage/table engine | stub |
| N19 Vector + features | keyword-overlap retrieval | stub |
| N20 Serving | `llama-server` HTTP | real |

**Latency split** (mean 3 query):

- embed: 0.0 ms
- retrieve: 0.2 ms
- llm: 14,351.6 ms
- **stage chiếm nhiều nhất:** llm (xấp xỉ 100% total)

**Reflection:** LLM là bottleneck đúng như kỳ vọng với retriever in-memory, dù
query đầu còn chịu residual work sau load test. Muốn giảm 2x, tôi sẽ tối ưu hoặc
tách replica serving, áp dụng cấu hình bốn thread đã tune và giảm output budget.
Tối ưu retrieve dưới 1 ms không thể thay đổi đáng kể tổng latency.

## 5. The single change that mattered most

**Change:** giảm `-t` từ default theo 8 physical cores xuống 4 thread.

```text
before:  85.2 tok/s (8 threads, tg128)
after:   96.3 tok/s (4 threads, tg128)
speedup: 1.13x
```

Phần lớn graph đã offload qua Vulkan, nên CPU không còn đủ công việc độc lập để
tám thread mang lại lợi ích. Bốn thread là điểm gối: chúng cung cấp đủ scheduling
và phần CPU còn lại, trong khi tám thread tăng synchronization và tranh chấp
cache/memory bandwidth. Dữ liệu cũng cho thấy đường cong không đơn điệu: 16 và 32
thread hồi phục một phần nhưng vẫn không vượt bốn thread, phù hợp với overhead và
OS scheduling hơn là thiếu FLOPs.

## 6. Bonus

**Đã làm:** B1 native source build + compare; B2 context-length sweep; B3
before/after dưới đây; B4 challenge C5 smallest useful quant; B5 C8 semantic-cache
offline threshold sweep.

```text
before:  32.7 tok/s (prebuilt, CPU ngl=0)
after:   32.5 tok/s (source GGML_NATIVE=ON, CPU ngl=0)
speedup: 0.99x (không có cải thiện có ý nghĩa)
```

Native build dùng đúng source revision b10488 và Zig/Clang 21.1 vì máy thiếu
Windows SDK. Cả hai phía được khóa `ngl=0`; do đó kết quả không trộn compiler với
Vulkan. Prebuilt đã runtime-dispatch kernel phù hợp AVX2/AVX-512 và decode bị giới
hạn bởi bandwidth, nên native build không thắng là kết quả hợp lý.

Context sweep tăng từ 71.0 ms ở 256 token lên 1,081.1 ms ở 4,096 token, nhưng chỉ
bằng 0.95x dự đoán tuyến tính; quadratic bend chưa xuất hiện trong dải này. C5 cho
thấy cả hai quant cần guardrail, còn Q2 có failure dịch thuật quan sát được. C8
offline đạt 3/8 hit ở mọi threshold 0.70-0.95, chứng minh bag-of-words tạo đường
cong phẳng và không đủ để chọn threshold production; cache phải được salt/isolate
theo tenant để tránh leakage qua timing.

## 7. Điều làm tôi ngạc nhiên nhất

Quant 2-bit vừa nhỏ hơn nhưng không nhanh hơn, và source build native cũng không
thắng prebuilt. Hai kết quả nhắc rằng tối ưu chỉ có giá trị khi đúng bottleneck:
giảm bytes hoặc bật ISA không tự động tạo speedup nếu dequantization, scheduling
hay memory bandwidth mới là giới hạn.

## 8. Self-check

- [x] `hardware.json` và `models/active.json`
- [x] benchmark hai quant và tuning report
- [x] smoke test, load 10/50, metrics trùng load 50, saturation report
- [x] integration report
- [x] báo cáo bonus B1/B2/B4/B5 và mọi phần phân tích bắt buộc
- [ ] thông tin cá nhân (được loại khỏi phạm vi theo yêu cầu)
- [ ] screenshots (được loại khỏi phạm vi theo yêu cầu)
- [ ] commit/push/public repo (chưa thực hiện tự động)

## 9. Khai báo sử dụng AI

Đã dùng OpenAI Codex để đọc yêu cầu, sửa tính tương thích Windows, điều phối các
phép đo, kiểm tra checksum, và biên soạn báo cáo. Toàn bộ con số benchmark trong
bài được sinh từ các lệnh chạy thật trên máy này; không dùng số liệu giả lập cho
các kết quả base. Báo cáo C8 ghi rõ riêng phần offline synthetic.
