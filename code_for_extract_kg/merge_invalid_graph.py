import json
import sys
import io
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

# --- Cấu hình (Constants) ---
BASE_DIR = Path(__file__).parent

# File chứa tất cả dữ liệu (File đích duy nhất)
FINAL_OUTPUT_FILE = BASE_DIR / "../exception_merged_graph.json"

# File input từ n8n/process trước đó (bị ghi đè liên tục)
INPUT_PATH = BASE_DIR / "../output_filtered.json" 

# --- Hàm tiện ích (Helpers) ---

def load_json_list_file(path: Path) -> Optional[List[Any]]:
    """Đọc file JSON (chỉ chấp nhận định dạng list)."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                 print(f"Cảnh báo: File {path} không phải là list. Coi như rỗng.")
                 return None
            return data
    except json.JSONDecodeError:
        # File có thể bị rỗng hoặc lỗi cú pháp
        return None
    except Exception as e:
        print(f"Lỗi không xác định khi đọc {path}: {e}")
        return None

def save_json_file(data: List[Any], path: Path):
    """Lưu danh sách dữ liệu ra file JSON, có backup file cũ."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup file cũ nếu tồn tại (để an toàn)
        if path.exists():
            backup_path = path.with_suffix(path.suffix + ".bak")
            shutil.copy(path, backup_path)
            
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi ghi file {path}: {e}")
        sys.exit(1)

def parse_node_labels(mapped_text: str) -> Dict[str, str]:
    """Chuyển đổi chuỗi mapped_text từ n8n thành dictionary."""
    nodes_label_map = {}
    if not mapped_text:
        return nodes_label_map
        
    for pair in mapped_text.split(","):
        if "-" in pair:
            parts = pair.split("-", 1)
            node = parts[0].strip().lower()
            label = parts[1].strip().lower()
            if label:
                nodes_label_map[node] = label
            else:
                nodes_label_map[node] = "unknown"
    return nodes_label_map

# --- Hàm Main ---

def main():
    # 1. Cấu hình UTF-8 cho console
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    
    # 2. Lấy mapped_text từ tham số dòng lệnh (n8n truyền vào)
    if len(sys.argv) < 2:
        # Nếu không có tham số, coi như không có mapping, vẫn chạy tiếp
        print("Cảnh báo: Không có mapped_text. Các node sẽ là 'unknown' hoặc giữ nguyên.")
        mapped_text = ""
    else:
        mapped_text = sys.argv[1]

    # 3. Parse node labels
    nodes_label_map = parse_node_labels(mapped_text)
    print(f"Đã parse {len(nodes_label_map)} node-label map.")

    # 4. Đọc file input mới (dữ liệu vừa xử lý xong)
    new_captions_list = load_json_list_file(INPUT_PATH)
    if not new_captions_list:
        print(f"Không có caption mới trong {INPUT_PATH} hoặc file lỗi/trống. Kết thúc.")
        sys.exit(0)
    
    print(f"Đã đọc {len(new_captions_list)} caption mới từ {INPUT_PATH}.")

    # 5. Đọc file tổng hiện tại (Master File)
    # Nếu file chưa có thì khởi tạo list rỗng
    master_data = load_json_list_file(FINAL_OUTPUT_FILE)
    if master_data is None:
        master_data = []
        print(f"File tổng chưa tồn tại. Sẽ tạo mới tại: {FINAL_OUTPUT_FILE}")
    else:
        print(f"Đã load file tổng hiện tại: {len(master_data)} records.")

    # 6. Xử lý dữ liệu mới (Map label vào node)
    processed_count = 0
    for item in new_captions_list:
        if not isinstance(item, dict) or "node" not in item:
            continue
            
        # --- Xử lý item (Thêm label vào node) ---
        original_node_names = item.get("node", [])
        new_node_list_with_labels = []
        
        # Nếu node là list strings ["cat", "dog"] -> convert sang object
        # Nếu node đã là object rồi (chạy lại script) -> giữ nguyên hoặc update
        for node_entry in original_node_names:
            if isinstance(node_entry, str):
                node_name = node_entry
                node_name_norm = node_name.strip().lower()
                label = nodes_label_map.get(node_name_norm, "unknown")
                new_node_list_with_labels.append({
                    "id": node_name, 
                    "label": label
                })
            elif isinstance(node_entry, dict):
                # Trường hợp data input đã có dạng object, ta update label nếu cần
                node_name = node_entry.get("id", "")
                node_name_norm = node_name.strip().lower()
                # Ưu tiên label mới từ map, nếu không giữ label cũ
                new_label = nodes_label_map.get(node_name_norm, node_entry.get("label", "unknown"))
                node_entry["label"] = new_label
                new_node_list_with_labels.append(node_entry)

        item["node"] = new_node_list_with_labels
        
        # Thêm vào danh sách tổng
        master_data.append(item)
        processed_count += 1

    # 7. Lưu file tổng
    save_json_file(master_data, FINAL_OUTPUT_FILE)
    
    print("------------------------------------------------")
    print(f"✅ HOÀN TẤT!")
    print(f"Đã thêm: {processed_count} caption mới.")
    print(f"Tổng số caption trong file merged: {len(master_data)}")
    print(f"Đường dẫn file: {FINAL_OUTPUT_FILE}")
    print("------------------------------------------------")

if __name__ == "__main__":
    main()