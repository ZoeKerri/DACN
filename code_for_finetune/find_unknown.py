import os
import json
import glob

def main():
    # CẤU HÌNH
    input_folder = 'knowledge_graph_outputs'    # Thư mục chứa file KG gốc
    output_file = 'unknown_items_to_fix.json'   # File kết quả chứa các mục cần sửa

    # Tìm tất cả file json trong thư mục
    search_pattern = os.path.join(input_folder, 'all_captions_kg_*.json')
    json_files = glob.glob(search_pattern)

    if not json_files:
        print(f"Không tìm thấy file nào trong thư mục {input_folder}")
        return

    extracted_data = []
    total_unknown_entries = 0

    print(f"Đang quét {len(json_files)} file...")

    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Duyệt qua từng mục (graph) trong file
            for entry in data:
                nodes = entry.get('node', [])
                
                # Kiểm tra xem có node nào là unknown không
                has_unknown = False
                for node in nodes:
                    # Kiểm tra label là 'unknown' (có thể thêm .lower() nếu cần)
                    if node.get('label') == 'unknown':
                        has_unknown = True
                        break # Tìm thấy 1 cái là đủ để lôi ra rồi
                
                if has_unknown:
                    # Thêm thông tin file gốc để bạn biết nó nằm ở đâu
                    # Dùng os.path.basename để lấy tên file (vd: all_captions_kg_0.json)
                    entry['_source_file'] = os.path.basename(filepath)
                    
                    extracted_data.append(entry)
                    total_unknown_entries += 1

        except Exception as e:
            print(f"Lỗi khi đọc file {filepath}: {e}")

    # Lưu kết quả ra file mới
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=4, ensure_ascii=False)

    print("-" * 30)
    print(f"HOÀN TẤT!")
    print(f"Đã tìm thấy {total_unknown_entries} mục có node 'unknown'.")
    print(f"Kết quả đã được lưu vào file: {output_file}")

if __name__ == "__main__":
    main()