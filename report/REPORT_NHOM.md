# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [DDGPT]
**Thành viên:** Trần Nguyễn Thái Duy — 2A202602991; Đinh Mạnh Dũng — 2A202602975; Nguyễn Hồng Phi — 2A202602750; Phạm Thành Trung — 2A202602949; Từ Hoàng Giang — 2A202602363
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ và Quy định thư viện

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề này vì các dịch vụ và quy định thư viện có tính thiết thực, gần gũi với nhu cầu học tập và nghiên cứu của sinh viên. Nguồn dữ liệu được công bố chính thức, có nội dung rõ ràng về giờ hoạt động, quy định mượn trả, tài liệu học tập và các dịch vụ hỗ trợ, nhờ đó thuận lợi cho việc xây dựng câu hỏi kiểm chứng và đánh giá chất lượng truy xuất. Ngoài ra, sự đa dạng về loại dịch vụ, đối tượng người dùng và danh mục tài liệu phù hợp để so sánh các chiến lược chunking cũng như khả năng lọc bằng metadata.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Services for persons with disabilities | https://utsc.library.utoronto.ca/services-persons-disabilities | 19/09/2026 / `not-stated` | 4.142 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`, `department`, `category`, `language` |
| 2 | Ask a Librarian chat service | https://utsc.library.utoronto.ca/ask-librarian-chat | 19/09/2026 / `not-stated` | 1.023 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`, `department`, `category`, `language` |
| 3 | UTSC Library borrowing policy | https://utsc.library.utoronto.ca/borrowing | 19/09/2026 / `2025-12-17` | 8.771 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`, `department`, `category`, `language` |
| 4 | Course reserves and short-term loans | https://utsc.library.utoronto.ca/course-reserves-short-term-loan | 19/09/2026 / `not-stated` | 2.023 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`, `department`, `category`, `language` |
| 5 | UTSC Library hours | https://utsc.library.utoronto.ca/hours | 19/09/2026 / `2026-09-08` | 1.008 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`, `department`, `category`, `language` |
| 6 | Library spaces and services | https://utsc.library.utoronto.ca/library-spaces | 19/09/2026 / `not-stated` | 2.660 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`, `department`, `category`, `language` |
| 7 | Research and publishing services for faculty | https://utsc.library.utoronto.ca/research-publishing | 19/09/2026 / `not-stated` | 6.487 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`, `department`, `category`, `language` |
| 8 | Technology loans | https://utsc.library.utoronto.ca/technology-loans | 19/09/2026 / `not-stated` | 18.672 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`, `department`, `category`, `language` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | Chuỗi | `utsc-course-reserves` | Định danh duy nhất và giúp truy vết chunk về tài liệu gốc. |
| `title` | Chuỗi | `Course reserves and short-term loans` | Cung cấp ngữ cảnh chủ đề và hỗ trợ hiển thị kết quả dễ hiểu. |
| `source_url` | URL | `https://utsc.library.utoronto.ca/course-reserves-short-term-loan` | Cho phép kiểm chứng nội dung từ nguồn chính thức. |
| `retrieved_at` | Ngày | `2026-09-19` | Cho biết thời điểm thu thập để đánh giá độ cập nhật của dữ liệu. |
| `document_version` | Chuỗi/ngày | `2026-09-08` | Hỗ trợ ưu tiên hoặc lọc theo phiên bản tài liệu. |
| `audience` | Chuỗi phân loại | `student` | Lọc kết quả theo đối tượng sử dụng như sinh viên, giảng viên hoặc tất cả người dùng. |
| `department` | Chuỗi phân loại | `utsc-library` | Giới hạn truy xuất theo đơn vị cung cấp thông tin. |
| `category` | Chuỗi phân loại | `course-reserves` | Thu hẹp kết quả theo nhóm dịch vụ hoặc loại quy định. |
| `language` | Mã ngôn ngữ | `en` | Hỗ trợ lọc tài liệu theo ngôn ngữ truy vấn. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Nhóm chọn 3 tài liệu sau để chạy `ChunkingStrategyComparator().compare()`:

- **UTSC Library borrowing policy:** chứa các nhóm đối tượng, hạn mức mượn và ngoại lệ; phù hợp để kiểm tra chunk có giữ được liên kết giữa đối tượng và quy định tương ứng khi bảng được chuyển thành văn bản hay không.
- **Technology loans:** tài liệu dài nhất trong bộ dữ liệu, gồm nhiều mục thiết bị có cấu trúc lặp lại; phù hợp để kiểm tra việc giữ tên thiết bị cùng thông số và thời hạn mượn, tránh trộn thông tin giữa các mục.
- **Course reserves and short-term loans:** tài liệu ngắn, được tổ chức theo câu hỏi và đoạn giải thích; phù hợp để so sánh khả năng giữ trọn câu trả lời và liên kết với tiêu đề câu hỏi.

Ba tài liệu đại diện cho những khác biệt về độ dài và cấu trúc trong corpus. Baseline chưa được chạy; các ô kết quả dưới đây sẽ được bổ sung sau thực nghiệm.

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| UTSC Library borrowing policy | FixedSizeChunker (`fixed_size`) | | | |
| UTSC Library borrowing policy | SentenceChunker (`by_sentences`) | | | |
| UTSC Library borrowing policy | RecursiveChunker (`recursive`) | | | |
| Technology loans | FixedSizeChunker (`fixed_size`) | | | |
| Technology loans | SentenceChunker (`by_sentences`) | | | |
| Technology loans | RecursiveChunker (`recursive`) | | | |
| Course reserves and short-term loans | FixedSizeChunker (`fixed_size`) | | | |
| Course reserves and short-term loans | SentenceChunker (`by_sentences`) | | | |
| Course reserves and short-term loans | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

Các cấu hình dưới đây đã được chạy trên cùng bộ benchmark bằng Gemini embedding `gemini-embedding-001` và Gemini chat `gemini-3.6-flash`.

**Thành viên 1 — Trần Nguyễn Thái Duy**
- **Loại chiến lược:** Fixed-size
- **Cấu hình dự kiến:** `chunk_size=500`, `overlap=50` (overlap 10%).
- **Mô tả & lý do chọn:** Đây là đường cơ sở đơn giản, tạo các chunk có kích thước đồng đều và dễ kiểm soát chi phí. Overlap 10% được dùng để giảm nguy cơ mất ngữ cảnh ở ranh giới chunk, đúng với khoảng 10–15% được gợi ý trong bài giảng.

**Thành viên 2 — Đinh Mạnh Dũng**
- **Loại chiến lược:** Recursive
- **Cấu hình dự kiến:** `chunk_size=500`, dùng thứ tự separator mặc định `\n\n`, `\n`, `. `, khoảng trắng và ký tự.
- **Mô tả & lý do chọn:** Chiến lược ưu tiên tách theo đoạn và dòng trước khi dùng ranh giới nhỏ hơn, nên giữ cấu trúc tự nhiên tốt hơn Fixed-size. Cấu hình này phù hợp với corpus Markdown có đoạn văn, danh sách và nhiều mục thông tin với độ dài khác nhau.

**Thành viên 3 — Nguyễn Hồng Phi**
- **Loại chiến lược:** Custom Heading/structural
- **Cấu hình dự kiến:** tách theo các heading Markdown `#`, `##`, `###`; nếu một section vượt 500 ký tự thì tiếp tục chia bằng Recursive.
- **Mô tả & lý do chọn:** Các tài liệu đều có tiêu đề và các mục dịch vụ rõ ràng, vì vậy tách theo heading giúp mỗi chunk giữ trọn một chủ đề và có thể gắn metadata về section. Theo cây quyết định trong bài giảng, đây là chiến lược nên thử đầu tiên với tài liệu Markdown có cấu trúc tốt.
- **Code snippet (custom):** sẽ bổ sung sau khi triển khai và kiểm thử.

**Thành viên 4 — Phạm Thành Trung**
- **Loại chiến lược:** Custom Sentence-window
- **Cấu hình dự kiến:** index từng câu; khi truy xuất, mở rộng thêm 1 câu trước và 1 câu sau làm ngữ cảnh.
- **Mô tả & lý do chọn:** Cách này hướng tới độ chính xác cao khi tìm các quy định hoặc con số cụ thể, đồng thời vẫn cung cấp đủ ngữ cảnh cho agent. Chiến lược đặc biệt hữu ích khi câu trả lời nằm trong một câu ngắn nhưng cần câu lân cận để xác định dịch vụ hoặc đối tượng áp dụng.
- **Code snippet (custom):** sẽ bổ sung sau khi triển khai và kiểm thử.

**Thành viên 5 — Từ Hoàng Giang**
- **Loại chiến lược:** Custom Parent-child
- **Cấu hình dự kiến:** dùng chunk con khoảng 200–300 ký tự để tìm kiếm và section cha khoảng 500–800 ký tự để đưa vào ngữ cảnh trả lời.
- **Mô tả & lý do chọn:** Chunk con nhỏ giúp tăng độ chính xác truy xuất, còn chunk cha giữ đủ nội dung của mục dịch vụ hoặc quy định. Cấu hình này dùng để kiểm tra liệu việc mở rộng ngữ cảnh có khắc phục trường hợp retrieval tìm đúng chi tiết nhưng agent thiếu thông tin xung quanh hay không.
- **Code snippet (custom):**

```python
corpus = build_parent_child_corpus(
    DATA_DIR, max_parent_chars=800, child_chars=250, child_overlap=25
)
retriever = ParentChildRetriever(corpus, embedding_fn=embedder)
results = retriever.search_with_filter(
    query, top_k=3, metadata_filter={"audience": "student"}
)
```

Child được dùng để embedding và tìm kiếm; `parent_id` ánh xạ kết quả về section cha đầy đủ trước khi đưa vào agent.

**Chiến lược được ưu tiên theo bài giảng:** Heading/structural. Corpus được lưu dưới dạng Markdown và có heading rõ ràng, nên chiến lược này phù hợp với cây quyết định trong bài giảng và có khả năng giữ nguyên từng mục dịch vụ tốt hơn cách cắt thuần theo số ký tự. Kết luận cuối cùng vẫn phải dựa trên kết quả của 5 benchmark query.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | What are the UTSC Library's regular opening hours from Monday to Friday between September 8 and December 22, 2026? | The library's regular weekday hours are 8:00 AM to 10:00 PM. It is closed on October 12, 2026. | `utsc-library-hours` — “Library Hours” |
| 2 | As an undergraduate student, how long can I borrow regular library items, and what is my item limit? | Undergraduate students have a regular loan period of 14 days and an item limit of 50. | `utsc-borrowing-policy` — “Loan privileges by patron type at most University of Toronto Libraries” |
| 3 | Where should a user return a borrowed laptop from the Technology Loans collection? | A borrowed laptop should be returned directly to the Info Desk. | `utsc-technology-loans` — đoạn mở đầu “Technology Loans”, hướng dẫn trả thiết bị |
| 4 | A student needs to find a physical course reading placed on reserve. Where is it located? | Physical course reserves are located 20 steps to the left of the InfoDesk at the UTSC Library. | `utsc-course-reserves` — “Where are physical course reserves located?” |
| 5 | Which service provides a free and secure University of Toronto repository for disseminating and preserving faculty and graduate-student research? | TSpace – University of Toronto Research Repository. | `utsc-research-publishing` — “TSpace - University of Toronto Research Repository” |

**Thiết kế A/B test bằng metadata:** Câu 4 được chạy hai lần với cùng chiến lược chunking, embedding và `top_k=3`: lần A không dùng bộ lọc; lần B dùng `metadata_filter={"audience": "student"}`. Nhóm sẽ so sánh thứ hạng của chunk đúng, số chunk liên quan trong top-3 và độ chính xác của câu trả lời trước khi kết luận bộ lọc có giúp ích hay không.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Giờ mở cửa ngày thường | Parent-child | Có (top-2; top-3) | Score 1/2; đúng giờ nhưng thiếu ngoại lệ 12/10 trong câu trả lời. |
| 2 | Mượn tài liệu và giới hạn sinh viên đại học | Parent-child | Có (top-1) | Score 2/2; nêu đúng 14 ngày và 50 món. |
| 3 | Nơi trả laptop | Parent-child | Có (top-1) | Score 2/2; nêu đúng Info Desk. |
| 4 | Vị trí course reserve vật lý | Parent-child | Có (top-1) | Score 2/2; nêu đúng 20 bước bên trái InfoDesk. |
| 5 | Kho lưu trữ nghiên cứu | Parent-child | Có (top-1) | Score 1/2; nhận diện đúng TSpace nhưng diễn đạt rút gọn. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Cả 5/5 câu đều có parent liên quan trong top-3. Parent-child đạt 8/10 theo thang điểm agent; các lỗi còn lại là thiếu một ngoại lệ thời gian hoặc rút gọn tên đầy đủ, không phải lỗi truy xuất. A/B query 4 cho kết quả giống nhau ở hai điều kiện, nên metadata filter chưa tạo khác biệt trên mẫu này.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
