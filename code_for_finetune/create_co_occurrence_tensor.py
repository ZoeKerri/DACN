import json
import spacy
import pandas as pd
from pathlib import Path
from collections import defaultdict

# Cấu hình đường dẫn
BASE_DIR = Path(__file__).parent
INPUT_FILE = BASE_DIR / "../merged_unique.json" 
OUTPUT_CSV = BASE_DIR / "../node_relation_co_occurrence_tensor.csv"

# Load model SpaCy
print("Đang load model SpaCy...")
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Lỗi: Chưa cài model. Chạy lệnh: python -m spacy download en_core_web_sm")
    exit()

def normalize_text(text):
    """
    Chuẩn hóa text:
    - Chuyển về chữ thường & dạng gốc (Lemma).
    - CHỈ GIỮ LẠI: Danh từ (NOUN) và Danh từ riêng (PROPN).
    """
    if not text:
        return ""
    
    doc = nlp(str(text).lower())
    
    # Lọc token dựa trên Part-of-Speech (POS) tag
    clean_tokens = [
        token.lemma_ 
        for token in doc 
        if token.pos_ in ["NOUN", "PROPN"]  # Chỉ lấy danh từ
    ]
    
    if not clean_tokens:
        return ""
        
    return " ".join(clean_tokens)

def load_json(path: Path):
    if not path.exists():
        print(f"Không tìm thấy file {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    print(f"Đang đọc file: {INPUT_FILE}")
    data = load_json(INPUT_FILE)

    tensor_counter = defaultdict(int)
    total_items = len(data)
    print(f"Bắt đầu xử lý {total_items} mục dữ liệu...")

    for index, item in enumerate(data):
        if "triplets" not in item:
            continue

        for triplet in item["triplets"]:
            raw_source = triplet.get("from")
            raw_relation = triplet.get("relation")
            raw_target = triplet.get("to")

            if not raw_source or not raw_relation or not raw_target:
                continue

            # 1. Chuẩn hóa: Chỉ lấy danh từ cho Source/Target
            norm_source = normalize_text(raw_source)
            norm_target = normalize_text(raw_target)

            # Nếu sau khi lọc danh từ mà rỗng thì bỏ qua triplet này
            if not norm_source or not norm_target:
                continue

            # 2. Quan hệ giữ nguyên (chỉ lowercase)
            norm_relation = raw_relation.lower().strip()

            # 3. Đếm tần suất xuất hiện của bộ ba
            key = (norm_source, norm_relation, norm_target)
            tensor_counter[key] += 1

        if (index + 1) % 100 == 0:
            print(f"Đã xử lý {index + 1}/{total_items} caption...")

    # Xuất ra CSV
    print("Đang tạo file CSV...")
    records = []
    for (src, rel, tgt), count in tensor_counter.items():
        records.append({
            "Subject": src,
            "Relation": rel,
            "Object": tgt,
            "Frequency": count
        })

    df = pd.DataFrame(records)
    
    # Sắp xếp theo độ phổ biến giảm dần
    df = df.sort_values(by="Frequency", ascending=False)

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    
    print(f"Hoàn tất! File đã được lưu tại: {OUTPUT_CSV}")
    print("-" * 30)
    print("Top 5 quan hệ xuất hiện nhiều nhất:")
    print(df.head(5))

if __name__ == "__main__":
    main()