# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Từ Hoàng Giang — 2A202602363
**Nhóm:** DDGPT
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần nhau, cho thấy hai đoạn văn có nội dung hoặc ý nghĩa ngữ nghĩa gần nhau. Hai câu vẫn có thể đạt similarity cao dù sử dụng từ ngữ khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: “What time does the library open on weekdays?”
- Câu B: “When are the library's regular Monday-to-Friday opening hours?”
- Tại sao tương đồng: Cả hai đều hỏi về giờ mở cửa thư viện trong các ngày làm việc dù cách diễn đạt khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: “Where should I return a borrowed laptop?”
- Câu B: “What is the weather forecast for tomorrow?”
- Tại sao khác: Hai câu thuộc hai chủ đề và mục đích hoàn toàn khác nhau: trả thiết bị thư viện và dự báo thời tiết.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity so sánh hướng của các vector và ít bị ảnh hưởng bởi độ lớn của vector, nên phù hợp để đo mức độ gần nhau về ngữ nghĩa. Khoảng cách Euclid phụ thuộc nhiều hơn vào độ lớn và có thể coi hai vector cùng hướng là xa nhau chỉ vì chúng có chuẩn khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Phép tính:* `ceil((10.000 - 50) / (500 - 50)) = ceil(9.950 / 450) = ceil(22,11) = 23`.
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, số chunk là `ceil((10.000 - 100) / (500 - 100)) = ceil(9.900 / 400) = 25`, tăng từ 23 lên 25. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới chunk và tăng cơ hội truy xuất đủ ý, nhưng làm tăng số vector, dung lượng lưu trữ và nội dung trùng lặp.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi đã triển khai bằng regex dựa trên dấu kết thúc câu, chẳng hạn `(?<=[.!?])(?:\s+|\n+)`, để tách câu nhưng vẫn giữ dấu câu trong nội dung. Các câu được gom theo `max_sentences_per_chunk`; chuỗi rỗng trả về danh sách rỗng, khoảng trắng thừa được loại bỏ, còn văn bản không có dấu kết thúc câu được giữ thành một câu duy nhất.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Tôi đã triển khai thuật toán thử các separator theo thứ tự `\n\n`, `\n`, `. `, khoảng trắng và cuối cùng là ký tự, nhằm ưu tiên ranh giới tự nhiên lớn trước. Nếu một phần vẫn dài hơn `chunk_size`, `_split` tiếp tục xử lý bằng separator kế tiếp; các phần nhỏ liền kề được ghép lại đến gần giới hạn. Base case là văn bản rỗng, văn bản đã không vượt giới hạn, hết separator hoặc không thể tách tiếp; khi đó thuật toán cắt cứng theo `chunk_size` nếu cần.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` tạo embedding cho từng chunk và lưu nội dung, bản sao metadata, `doc_id` cùng vector trong bộ nhớ. `search` embedding câu hỏi bằng cùng một hàm, tính tích vô hướng với từng vector tài liệu, sắp xếp giảm dần theo score và trả về `top_k` kết quả mà không làm lộ vector trong output.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc các record khớp toàn bộ cặp key-value trong metadata trước, sau đó mới tính similarity và lấy top-k để các kết quả sai metadata không chiếm vị trí. `delete_document` xóa tất cả chunk có `metadata["doc_id"]` trùng với tài liệu cần xóa và trả về `True` nếu có ít nhất một record bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer` truy xuất top-k chunk liên quan, đánh số từng đoạn ngữ cảnh và ghép chúng vào prompt cùng câu hỏi. Prompt yêu cầu mô hình chỉ trả lời dựa trên context đã truy xuất và nói rõ không đủ thông tin nếu context không chứa đáp án, nhờ đó giảm câu trả lời không có căn cứ.

### Chiến lược truy xuất cá nhân — Parent-child

- **Vai trò trong nhóm:** Thành viên 3 — Từ Hoàng Giang.
- **Loại chiến lược:** Custom Parent-child.
- **Bộ benchmark:** sử dụng đúng 5 query và gold answer thống nhất trong `REPORT_NHOM.md`, với `top_k=3`.
- **Embedding backend:** Gemini API với model `gemini-embedding-001`, được dùng thống nhất để embedding cả chunk con và câu hỏi truy xuất. Smoke test thành công trên Python 3.13.1: model trả về vector 3.072 chiều và toàn bộ giá trị đều hữu hạn.
- **Cấu hình đã sử dụng:** chunk con khoảng 200–300 ký tự để tìm kiếm; section cha khoảng 500–800 ký tự để đưa vào ngữ cảnh trả lời.
- **Cách tổ chức:** mỗi chunk con lưu thêm `parent_id`, `section`, `doc_id` và các metadata gốc. Khi tìm kiếm, hệ thống xếp hạng chunk con; sau đó lấy các section cha tương ứng, loại trùng và đưa chúng vào prompt của agent.
- **Lý do chọn:** Chunk con nhỏ hướng tới retrieval precision cao, còn chunk cha giữ đủ nội dung của mục dịch vụ hoặc quy định. Thử nghiệm này kiểm tra liệu mở rộng sang parent có khắc phục trường hợp hệ thống tìm đúng chi tiết nhưng agent thiếu ngữ cảnh xung quanh hay không.
- **Giả thuyết và kết quả:** Parent-child phù hợp với các mục gồm nhiều câu liên quan như quy định mượn tài liệu và Technology Loans, nhưng cần quản lý quan hệ cha–con và có thể đưa thêm nội dung không cần thiết vào prompt. Kết quả 5 benchmark query cho thấy cả 5 câu đều có parent liên quan trong top-3; điểm agent là 9/10. Hạn chế quan sát được là câu trả lời giờ mở cửa đã bỏ sót ngoại lệ ngày 12/10.
- **Code triển khai:** `benchmark_parent_child.py`; smoke test trên corpus đã đồng bộ tạo 54 parent và 118 child, parent tối đa 790 ký tự, child tối đa 250 ký tự. Kết quả child được ánh xạ về parent trước khi đưa vào agent.
- **Lệnh đánh giá:** `python bench_gemini.py --data-dir data/utsc-library-services --output benchmark_results_gemini.json`.

Đoạn code cốt lõi của chiến lược:

```python
corpus = build_parent_child_corpus(
    DATA_DIR, max_parent_chars=800, child_chars=250, child_overlap=25
)
retriever = ParentChildRetriever(corpus, embedding_fn=embedder)
results = retriever.search_with_filter(
    query, top_k=3, metadata_filter={"audience": "student"}
)

# Tìm trên child, sau đó mở rộng kết quả về parent đầy đủ cho agent.
for item in results:
    print(item["metadata"]["parent_id"], item["content"])
```

Đoạn triển khai này tạo child để embedding/search, giữ `parent_id` trong metadata, rồi deduplicate và trả về section parent tương ứng.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.13.1, pytest-9.1.1
collected 42 items

tests/test_solution.py ..........................................       [100%]

======================== 42 passed, 1 warning in 0.23s ========================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

> Ghi chú: Bộ test được chạy bằng Python 3.13.1 do máy hiện tại chưa có Python 3.11 trong Python Launcher. Cảnh báo duy nhất liên quan đến quyền tạo thư mục `.pytest_cache`, không ảnh hưởng đến kết quả kiểm thử.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | What time does the library open on weekdays? | When are the library's regular Monday-to-Friday opening hours? | Cao | 0.8712 | Đúng |
| 2 | Where can a student find physical course reserves? | Where are course readings placed on reserve located? | Cao | 0.8830 | Đúng |
| 3 | Where should I return a borrowed laptop? | Large electronic devices must be returned to the Info Desk. | Cao | 0.7316 | Đúng |
| 4 | What is the item limit for undergraduate students? | Which repository preserves University of Toronto research? | Thấp | 0.5076 | Đúng |
| 5 | What are the library's borrowing rules? | What is the weather forecast for tomorrow? | Thấp | 0.4864 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cả 5 kết quả đều đúng với dự đoán. Cặp 1 và 2 có điểm số rất cao (>0.87) dù sử dụng từ vựng khác nhau (ví dụ: "open on weekdays" vs "Monday-to-Friday opening hours"), cho thấy embedding model bắt được ý nghĩa ngữ nghĩa (semantic meaning) thay vì chỉ so khớp từ khóa. Tuy nhiên, ở cặp 3, điểm số có sự chênh lệch thấp hơn một chút (0.7316), do hai câu sử dụng những từ có nghĩa rộng và không hoàn toàn đồng nghĩa trực tiếp ("laptop" vs "large electronic devices"). Điều này chứng minh embeddings biểu diễn ý nghĩa thông qua khoảng cách vector trong không gian ngữ nghĩa, không chỉ là trùng khớp từ vựng.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | What are the UTSC Library's regular opening hours from Monday to Friday between September 8 and December 22, 2026? | `utsc-library-hours#parent-0` — Library Hours | 0.850 | Có, trong top-3 | Agent trả lời đúng 8:00 AM–10:00 PM nhưng bỏ sót ngoại lệ đóng cửa ngày 12/10. |
| 2 | As an undergraduate student, how long can I borrow regular library items, and what is my item limit? | `utsc-borrowing-policy#parent-1` — Loan privileges by patron type | 0.781 | Có, top-1 | Trả lời đúng 14 ngày và tối đa 50 món. |
| 3 | Where should a user return a borrowed laptop from the Technology Loans collection? | `utsc-technology-loans#parent-2` — Technology Loans | 0.812 | Có, top-1 | Trả trực tiếp tại Info Desk. |
| 4 | Which form should be completed to designate another borrower when the patron cannot visit the library because of a disability? | `utsc-borrowing-policy#parent-6` — Designate a Proxy Borrower | 0.823 | Có, top-1 sau khi lọc | Agent chỉ trả đúng “proxy application form”. |
| 5 | Which service is a free institutional open-access repository for preserving and disseminating papers produced by faculty and graduate researchers? | `utsc-research-publishing#parent-2` — TSpace | 0.731 | Có, top-1 | Agent nhận diện đúng TSpace Research Repository và trả lời có căn cứ. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5/5. Điểm agent theo thang 0–2 là 1, 2, 2, 2, 2; tổng 9/10. Câu 1 chỉ đạt 1/2 vì trả lời đúng giờ thường lệ nhưng bỏ sót ngoại lệ đóng cửa ngày 12/10.

**Kết quả A/B test cho câu 4:** Không lọc, `utsc-accessibility-services#parent-7` đứng top-1 với score 0.8234 và agent trộn hai biểu mẫu “Pickup Authorization Form” và “proxy application form”, nên đạt 1/2. Khi lọc bằng `metadata_filter={"audience": "student"}`, `utsc-borrowing-policy#parent-6` lên top-1 với score 0.8227; agent chỉ trả đúng “proxy application form” và đạt 2/2. Bộ lọc vì vậy cải thiện trực tiếp độ chính xác theo đối tượng.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Bài học rút ra từ demo là không có một kích thước chunk tối ưu cho mọi loại tài liệu. Heading/structural có lợi thế với Markdown có cấu trúc rõ, còn Parent-child có thể hữu ích khi chunk nhỏ truy xuất đúng nhưng chưa đủ ngữ cảnh để agent tạo câu trả lời hoàn chỉnh.

> **Ghi chú đồng bộ:** Sau khi thay corpus theo `REPORT_NHOM.md`, smoke test Parent-child và `benchmark_results_gemini.json` đều ghi nhận 54 parent và 118 child. Kết quả benchmark hiện tại là `[1, 2, 2, 2, 2]`, tổng 9/10.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |
