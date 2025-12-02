# Image Captioning System using Knowledge Graph & Deep Learning

Dự án này phát triển hệ thống sinh chú thích ảnh (Image Captioning) tích hợp Đồ thị tri thức (Knowledge Graph - KG) và Deep Learning (T5 Model). Hệ thống sử dụng quy trình trích xuất Triplet từ ảnh (thông qua n8n), xây dựng KG toàn cục, tính toán PMI để hỗ trợ sinh caption chính xác hơn trong thực tế.

## 📂 Cấu trúc Dự án & Mô tả File Code

### 1. Module `code_for_extract_kg`
**Mục đích:** Xử lý hậu kỳ cho dữ liệu Triplet được trích xuất từ n8n. Quy trình bao gồm: đọc dữ liệu thô, chuẩn hóa quan hệ, gộp file (merge), và lọc trùng lặp/nhiễu.

* **Quản lý Index & Đọc dữ liệu thô:**
    * `read_caption.py`: Đọc file text caption, sử dụng Regex để tách các node và edge (triplets) từ định dạng output của n8n.
    * `read_invalid_caption.py`: Tương tự `read_caption.py` nhưng xử lý các file nằm trong danh sách ngoại lệ (`invalid_caption_files.txt`).
    * `read_index.py`: Đọc giá trị index hiện tại từ file `index.json` để đồng bộ quy trình xử lý.
    * `update_index.py`: Cập nhật tăng giá trị index trong `index.json` sau khi xử lý xong một batch.

* **Xử lý Quan hệ (Relation Processing):**
    * `normalize_relation.py`: Chuẩn hóa các quan hệ đồng nghĩa (ví dụ: mapping nhiều cách viết về một relation chuẩn) dựa trên input từ n8n.
    * `filter_relation.py`: Lọc bỏ các triplet có quan hệ không mong muốn hoặc không nằm trong danh sách hợp lệ.

* **Gộp & Kiểm tra dữ liệu (Merge & Cleaning):**
    * `merge_graph.py`: Gộp danh sách các file JSON con (`all_captions_kg_*.json`) thành một file tổng hợp.
    * `merge_invalid_graph.py`: Gộp các graph xử lý lại (từ các file lỗi/ngoại lệ) vào file dữ liệu chính (`exception_merged_graph.json`), có hỗ trợ map nhãn node.
    * `merge_all.py`: Script gộp cuối cùng, kết hợp các file dữ liệu đã làm sạch (`clean_merge_final.json`...) thành file `merged_unique.json`.
    * `find_invalid_caption.py`: Kiểm tra tính toàn vẹn của dataset (đủ 5 caption/ảnh hay không), tìm các ảnh bị lỗi và loại bỏ các dòng dữ liệu trùng lặp (deduplicate).

---

### 2. Module `code_for_finetune`
**Mục đích:** Xây dựng Knowledge Graph tổng quát từ dữ liệu đã làm sạch, tính toán thống kê (Co-occurrence, PMI) và chuẩn bị dữ liệu input cho mô hình T5.

* **Xây dựng Knowledge Graph & PMI:**
    * `create_co_occurrence_matrix.py`: Tạo ma trận đồng xuất hiện (Co-occurrence Matrix) từ file JSON tổng, tính tần suất xuất hiện cùng nhau của các cặp node.
    * `cal_PMI.py`: Tính điểm **PMI (Pointwise Mutual Information)** từ ma trận đồng xuất hiện. Kết quả lưu ra `kg_pmi_ranked.csv`, dùng để xếp hạng và truy xuất triplet quan trọng nhất khi test thực tế.

* **Làm sạch & Gán nhãn (Labeling):**
    * `find_unknown.py`: Quét và tìm tất cả các node đang bị gán nhãn là "unknown" để xử lý.
    * `replace_unknown_label.py`: Sử dụng thư viện **SpaCy** để tự động dự đoán và thay thế nhãn "unknown" bằng nhãn hợp lý (dựa trên entity type hoặc noun chunk).
    * `find_index.py`: Đối chiếu caption trong file KG với file CSV gốc (`results.csv`) để tìm và cập nhật lại filename chính xác cho từng mục dữ liệu.

* **Chuẩn bị Dữ liệu Train/Test:**
    * `create_input_for_t5.py`: Tạo file dataset huấn luyện (`t5_finetune.csv`) bằng cách ghép caption gốc (từ BLIP) với chuỗi Triplet từ KG theo định dạng: `refine caption: ... <sep> graph: ...`.
    * `split_file.py`: Copy và chia file ảnh vào các thư mục `train`, `val`, `test` dựa trên file cấu hình JSON.
    * `split_train_valid_test.py`: Chia file CSV dữ liệu (`t5_finetune.csv`) thành 3 file riêng biệt (`train.csv`, `val.csv`, `test.csv`) để đưa vào model.

---

### 3. Notebook Thực nghiệm (`Untitled0 (1).ipynb`)
File Jupyter Notebook chứa toàn bộ quy trình Huấn luyện và Kiểm thử mô hình Deep Learning.

* **Training:**
    * Model: **T5-base**.
    * Kỹ thuật: **LoRA** (Low-Rank Adaptation) để fine-tune hiệu quả.
    * Input: Dữ liệu từ `code_for_finetune`.
* **Testing (Thực tế):**
    * Quy trình: Ảnh -> BLIP Caption -> Extract Entities -> **Tra cứu bảng PMI (`kg_pmi_ranked.csv`)** -> Lấy Triplet -> T5 Refinement -> Final Caption.
    * Đánh giá: BLEU, METEOR, ROUGE.

## 🚀 Hướng dẫn thực hiện

1.  **Giai đoạn 1: Trích xuất (Extract)**
    * Chạy các script trong `code_for_extract_kg` để xử lý output từ n8n.
    * Dùng `find_invalid_caption.py` để lọc lỗi và `merge_all.py` để tạo file JSON sạch nhất.

2.  **Giai đoạn 2: Xây dựng KG (Finetune Prep)**
    * Chạy `replace_unknown_label.py` để sửa nhãn lỗi.
    * Chạy `create_co_occurrence_matrix.py` -> `cal_PMI.py` để tạo bảng điểm quan hệ (dùng cho Test).
    * Chạy `create_input_for_t5.py` -> `split_train_valid_test.py` để tạo dữ liệu Train.

3.  **Giai đoạn 3: Train & Test**
    * Mở notebook `Untitled0 (1).ipynb`.
    * Chạy phần Training để fine-tune T5 với dữ liệu đã chuẩn bị.
    * Chạy phần Inference để sinh caption cho ảnh mới sử dụng bảng PMI đã tính toán.