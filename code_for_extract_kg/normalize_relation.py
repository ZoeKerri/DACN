import json
import os
import sys

BASE_DIR = os.path.dirname(__file__)

# --- Kiểm tra tham số truyền vào ---
if len(sys.argv) < 2:
    print(json.dumps({"error": "Thiếu relation truyền vào"}))
    sys.exit(1)

# --- Lấy chuỗi normalize từ n8n ---
normalize_input = sys.argv[1]
# Nếu n8n truyền vào có dấu ngoặc kép (stringified JSON) → loại bỏ
normalize_input = normalize_input.strip('"')
# --- Chuyển thành mapping dictionary ---
relation_map = {}
for pair in normalize_input.split(","):
    if " - " in pair:
        left, right = pair.split(" - ")
        relation_map[right.strip()] = left.strip()

# --- Đọc file JSON ---
input_path = os.path.join(BASE_DIR, "../output_original.json")
output_path = os.path.join(BASE_DIR, "../output_mapped.json")

with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# --- Xử lý normalize ---
for item in data:
    new_triplets = []
    new_edges = []

    for t in item.get("triplets", []):
        rel = t["relation"].strip()
        if rel in relation_map:
            t["relation"] = relation_map[rel]
            new_triplets.append(t)
            new_edges.append(relation_map[rel])
        # nếu không có thì bỏ qua

    item["triplets"] = new_triplets
    item["edge"] = list(dict.fromkeys(new_edges))

# --- Ghi file kết quả ---
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# --- In kết quả cho n8n đọc ---
print(json.dumps(data, ensure_ascii=False))
