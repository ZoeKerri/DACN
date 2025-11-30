#Tương tự với read_caption.py nhưng file này đọc các caption bị thiếu caption từ danh sách trong invalid_caption_files.txt
#Trong thư mục có invalid_caption_files_2.txt là danh sách caption bị thiếu sau khi trích xuất lại, file đó cũng không phải là thiếu mà là do các caption trong cụm 5 caption bị trùng lặp
import os
import sys
import json
import re

BASE_DIR = "E:/final_project/Sentences"
LOOKUP_FILE = "E:/final_project/invalid_caption_files.txt"
CAPTIONS_PER_FILE = 5

def get_captions_via_lookup(index):
    try:
        with open(LOOKUP_FILE, "r", encoding="utf-8") as f:
            file_list = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        return None

    if index < 0 or index >= len(file_list):
        return None

    raw_filename = file_list[index]
    base_name = os.path.splitext(raw_filename)[0]
    filename = f"{base_name}.txt"
    filepath = os.path.join(BASE_DIR, filename)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        return {"file": filename, "captions": ["" for _ in range(CAPTIONS_PER_FILE)]}

    captions = lines[:CAPTIONS_PER_FILE]
    while len(captions) < CAPTIONS_PER_FILE:
        captions.append("")

    return {"file": filename, "captions": captions}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Thiếu index"}))
        sys.exit(1)

    file_index = int(sys.argv[1])
    result = get_captions_via_lookup(file_index)

    if not result:
        result = {"file": "", "captions": [""] * CAPTIONS_PER_FILE}

    data = result

    regex = re.compile(r'\[\/EN#[^/]+\/[^\s]+ ([^\]]+)\]')

    all_results = []

    for caption in data["captions"]:
        insides = [m.replace(",", "").strip() for m in regex.findall(caption)]
        temp = regex.sub("|||", caption)
        parts = [p.strip() for p in temp.split("|||")]

        if len(parts) >= 3:
            outsides_between = parts[1:-1]
        else:
            outsides_between = []

        outsides_between = [p for p in outsides_between if re.search(r'[A-Za-z0-9]', p)]

        triplets = []
        n = len(insides)
        for i in range(n - 1):
            for j in range(i, n - 1):
                if j < len(outsides_between):
                    triplets.append({
                        "from": insides[i],
                        "relation": outsides_between[j],
                        "to": insides[j + 1]
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

    output_path = "E:/final_project/output_original.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
