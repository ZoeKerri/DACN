import json
import os
import sys
import re

BASE_DIR = os.path.dirname(__file__)

# --- Đường dẫn file mapped JSON ---
file_name = sys.argv[2]
input_path = os.path.join(BASE_DIR, "../output_mapped.json")

# --- Danh sách triplet chuẩn hóa từ LLM hoặc n8n ---
correct_triplet_str = sys.argv[1]

# --- Chuyển thành Set để kiểm tra nhanh ---
valid_triplets = set([t.strip() for t in correct_triplet_str.split(";") if t.strip()])

# --- Đọc dữ liệu JSON ---
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# --- Lọc triplets và làm sạch caption ---
filtered_output = []
for item in data:
    # Lọc triplets
    new_triplets = []
    for t in item.get("triplets", []):
        triplet_text = f"from: {t['from']} - relation: {t['relation']} - to: {t['to']}"
        if triplet_text in valid_triplets:
            new_triplets.append(t)

    # Cập nhật edge từ các triplets còn lại
    new_edges = list(dict.fromkeys([t["relation"] for t in new_triplets]))

    # Làm sạch caption
    caption = item.get("caption", "")
    clean_caption = re.sub(r"\[/EN#[^/]+/[^ ]+ ([^\]]+)\]", r"\1", caption).strip()

    # Tạo item mới
    filtered_output.append({
        "caption": clean_caption,
        "node": item.get("node", []),
        "edge": new_edges,
        "triplets": new_triplets,
        "filename": file_name
    })

# --- Nếu muốn, vẫn có thể ghi ra file ---
output_path = os.path.join(BASE_DIR, "../output_filtered.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(filtered_output, f, ensure_ascii=False, indent=2)

