import json
import pandas as pd
from collections import Counter
import os
import glob 

# 1. Cấu hình đường dẫn
kg_folder = 'knowledge_graph_outputs'
# Tạo đường dẫn tìm kiếm: knowledge_graph_outputs/all_captions_kg_*.json
search_pattern = os.path.join(kg_folder, 'all_captions_kg_*.json')

# Tự động lấy danh sách file khớp với mẫu
input_files = glob.glob(search_pattern)

print(f"Đang tìm kiếm trong thư mục: {kg_folder}")
print(f"Tìm thấy {len(input_files)} file dữ liệu: {input_files}")

merged_data = []

# 2. Đọc và gộp dữ liệu
if not input_files:
    print("LỖI: Không tìm thấy file nào khớp với mẫu yêu cầu!")
else:
    print("Đang đọc và gộp các file...")
    for file_name in input_files:
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
                merged_data.extend(data)
        except Exception as e:
            print(f"Lỗi khi đọc file {file_name}: {e}")

    # Lưu file gộp (Optional - để kiểm tra nếu cần)
    output_merged_file = 'merged_all_captions_kg.json'
    with open(output_merged_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=4, ensure_ascii=False)
    print(f"Đã lưu file gộp tạm thời tại: {output_merged_file}")

    # 3. Xử lý để tạo Ma trận đồng xuất hiện (Co-occurrence Matrix)
    triplet_counter = Counter()

    print("Đang tính toán ma trận đồng xuất hiện...")
    for entry in merged_data:
        # Tạo từ điển ánh xạ ID sang Label cho caption hiện tại
        # Ví dụ: "A pilot" -> "worker"
        id_to_label = {}
        if 'node' in entry:
            for node in entry['node']:
                # Chuẩn hóa: đưa về chữ thường và bỏ khoảng trắng thừa
                # Thêm kiểm tra an toàn nếu id hoặc label bị thiếu
                if 'id' in node:
                    node_id = node['id'].strip()
                    # Nếu không có label thì dùng luôn id làm label (fallback)
                    node_label = node.get('label', node_id).strip().lower()
                    id_to_label[node_id] = node_label

        # Duyệt qua các triplets
        if 'triplets' in entry:
            for triplet in entry['triplets']:
                if 'from' in triplet and 'to' in triplet and 'relation' in triplet:
                    subj_id = triplet['from'].strip()
                    relation = triplet['relation'].strip().lower()
                    obj_id = triplet['to'].strip()

                    # Ánh xạ ID sang Label. 
                    # Nếu không tìm thấy label (do lỗi dữ liệu node), dùng chính ID đó
                    subj_label = id_to_label.get(subj_id, subj_id.lower())
                    obj_label = id_to_label.get(obj_id, obj_id.lower())

                    # Tạo key cho triplet (Head - Relation - Tail)
                    triplet_key = (subj_label, relation, obj_label)
                    
                    # Đếm số lần xuất hiện
                    triplet_counter[triplet_key] += 1

    # 4. Chuyển đổi sang DataFrame và xuất ra CSV
    matrix_data = []
    for (subj, rel, obj), count in triplet_counter.items():
        matrix_data.append({
            'head': subj,
            'relation': rel,
            'tail': obj,
            'weight': count
        })

    if matrix_data:
        # Sắp xếp theo số lượng xuất hiện giảm dần
        df_matrix = pd.DataFrame(matrix_data)
        df_matrix = df_matrix.sort_values(by='weight', ascending=False)

        output_matrix_file = 'kg_co_occurrence_matrix.csv'
        df_matrix.to_csv(output_matrix_file, index=False)

        print(f"Đã xuất thành công ma trận đồng xuất hiện tại: {output_matrix_file}")
        print("-" * 30)
        print("Top 10 quan hệ xuất hiện nhiều nhất:")
        print(df_matrix.head(10))
    else:
        print("Không tạo được ma trận do không có dữ liệu hợp lệ.")