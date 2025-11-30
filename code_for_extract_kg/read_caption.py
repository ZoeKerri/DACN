import os
import sys
import json
import re

BASE_DIR = "E:/final_project/Sentences"
CAPTIONS_PER_FILE = 5

def get_sorted_files(base_dir):
    files = [f.replace(".txt", "") for f in os.listdir(base_dir) if f.endswith(".txt")]
    return sorted(files, key=lambda x: int(x))

def get_captions_by_file_index(file_index):
    files = get_sorted_files(BASE_DIR)
    
    if file_index < 0 or file_index >= len(files):
        return None

    filename = files[file_index]
    filepath = os.path.join(BASE_DIR, f"{filename}.txt")

    # Đọc file caption
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        return {
            "file": filename,
            "captions": ["" for _ in range(CAPTIONS_PER_FILE)]
        }

    # Đảm bảo luôn có đúng 5 phần tử (nếu thiếu thì thêm "")
    captions = lines[:CAPTIONS_PER_FILE]
    while len(captions) < CAPTIONS_PER_FILE:
        captions.append("")

    return {
        "file": filename,
        "captions": captions
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Thiếu index"}))
        sys.exit(1)

    file_index = int(sys.argv[1])
    result = get_captions_by_file_index(file_index)

    # Nếu index vượt phạm vi → trả về rỗng
    if not result:
        result = {"file": "", "captions": [""] * CAPTIONS_PER_FILE}
    
    data = result

    # --- Regex để bắt phần trong ngoặc vuông ---
    regex = re.compile(r'\[\/EN#[^/]+\/[^\s]+ ([^\]]+)\]')

    all_results = []

    for caption in data["captions"]:
        # Lấy tất cả inside (nội dung trong ngoặc)
        insides = [m.replace(",", "").strip() for m in regex.findall(caption)]

        # Thay tất cả inside bằng placeholder để tách các đoạn ngoài (bao gồm trước và sau)
        temp = regex.sub("|||", caption)

        # Tách bằng placeholder -> ta có parts = [before_first_inside, between_0_1, between_1_2, ..., after_last_inside]
        parts = [p.strip() for p in temp.split("|||")]

        # Các outside giữa hai inside sẽ là parts[1] ... parts[-2] (nếu tồn tại)
        if len(parts) >= 3:
            outsides_between = parts[1:-1]
        else:
            outsides_between = []

        # Lọc bỏ các phần không có chữ (dấu câu, rỗng)
        outsides_between = [p for p in outsides_between if re.search(r'[A-Za-z0-9]', p)]

        # Sinh tổ hợp theo yêu cầu:
        triplets = []
        n = len(insides)
        for i in range(n - 1):
            for j in range(i, n - 1):
                # bảo đảm outsides_between có index j
                if j < len(outsides_between):
                    subj = insides[i]
                    rel = outsides_between[j]
                    obj = insides[j + 1]
                    triplets.append({
                        "from": subj,
                        "relation": rel,
                        "to": obj
                    })

        all_results.append({
            "caption": caption,
            "node": insides,
            "edge": outsides_between,
            "triplets": triplets
        })

    all_edges = []
    for item in all_results:
        all_edges.extend(item["edge"])
    
    all_nodes = []
    for item in all_results:
        all_nodes.extend(item["node"])
        
    output_data = {
    "filename": data["file"],
    "nodes": all_nodes,
    "edges": all_edges
    }

    print(json.dumps(output_data, ensure_ascii=False))
    output_path = f"E:/final_project/output_original.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)