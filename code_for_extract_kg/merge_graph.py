import json
import sys
import io
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "../knowledge_graph_outputs"
INPUT_PATH = BASE_DIR / "../output_filtered.json"
USER_INDEX_PATH = Path("E:/final_project/index.json")

def load_json_list_file(path: Path) -> Optional[List[Any]]:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                 print(f"Cảnh báo: File {path} không phải list.")
                 return None
            return data
    except json.JSONDecodeError:
        print(f"Lỗi JSON ở {path}.")
        return None
    except Exception as e:
        print(f"Lỗi khi đọc {path}: {e}")
        return None

def save_json_file(data: List[Any], path: Path):
    try:
        path.parent.mkdir(exist_ok=True)
        if path.exists():
            backup_path = path.with_suffix(path.suffix + ".bak")
            shutil.copy(path, backup_path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi khi ghi {path}: {e}")
        sys.exit(1)

def parse_node_labels(mapped_text: str) -> Dict[str, str]:
    nodes = {}
    for pair in mapped_text.split(","):
        if "-" in pair:
            node, label = pair.split("-", 1)
            nodes[node.strip().lower()] = label.strip().lower() or "unknown"
    return nodes

def load_user_index(path: Path) -> int:
    if not path.exists():
        print(f"Không tìm thấy file index: {path}")
        sys.exit(1)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data.get("index"), int):
                return data["index"]
            else:
                print(f"File index {path} không có key 'index' hợp lệ.")
                sys.exit(1)
    except Exception as e:
        print(f"Lỗi đọc file index {path}: {e}")
        sys.exit(1)

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    OUTPUT_DIR.mkdir(exist_ok=True)

    if len(sys.argv) < 2:
        print("Thiếu mapped_text.")
        sys.exit(1)

    mapped_text = sys.argv[1]
    nodes_label_map = parse_node_labels(mapped_text)
    print(f"Đã parse {len(nodes_label_map)} node-label.")

    new_captions_list = load_json_list_file(INPUT_PATH)
    if not new_captions_list:
        print("Không có caption mới.")
        sys.exit(0)

    print(f"Đọc {len(new_captions_list)} caption mới.")

    current_index = load_user_index(USER_INDEX_PATH)
    print(f"Index hiện tại: {current_index}")

    file_batches = defaultdict(list)
    caption_counter = current_index

    for item in new_captions_list:
        if not isinstance(item, dict) or "node" not in item:
            continue

        caption_counter += 1

        new_nodes = []
        for node_name in item.get("node", []):
            key = node_name.strip().lower()
            label = nodes_label_map.get(key, "unknown")
            new_nodes.append({"id": node_name, "label": label})

        item["node"] = new_nodes

        group_index = ((caption_counter - 1) // 100) * 100
        target_path = OUTPUT_DIR / f"all_captions_kg_{group_index}.json"
        file_batches[target_path].append(item)

    if not file_batches:
        print("Không có caption hợp lệ.")
        sys.exit(0)

    print(f"Sẽ ghi vào {len(file_batches)} file.")

    for target_path, captions in file_batches.items():
        old_data = load_json_list_file(target_path) or []
        save_json_file(old_data + captions, target_path)
        print(f"  -> {target_path.name}: +{len(captions)} caption. Tổng {len(old_data) + len(captions)}")

    print(f"Hoàn tất! Xử lý {current_index + 1} → {caption_counter}.")
    print("Không cập nhật file index.")

if __name__ == "__main__":
    main()
