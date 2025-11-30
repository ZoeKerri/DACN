import os
import json
import pandas as pd
import glob

def main():
    # CẤU HÌNH ĐƯỜNG DẪN
    csv_path = 'flickr30k_images/results.csv'                    
    kg_folder = 'knowledge_graph_outputs'       
    output_folder = 'knowledge_graph_outputs'    

    # 1. Đọc dữ liệu mapping từ CSV
    print(f"Dang doc du lieu tu {csv_path}...")
    try:
        # Đọc file CSV với dấu phân cách '|'
        df = pd.read_csv(csv_path, sep='|', engine='python')
        
        # Chuẩn hóa tên cột (xóa khoảng trắng thừa)
        df.columns = [c.strip() for c in df.columns]
        
        # Cần đảm bảo cột chứa caption tên là 'comment' và ảnh là 'image_name'
        if 'comment' not in df.columns or 'image_name' not in df.columns:
            print("Loi: Khong tim thay cot 'comment' hoac 'image_name' trong CSV.")
            return

        # Tạo từ điển mapping: Caption -> Filename
        caption_map = dict(zip(df['comment'].str.strip(), df['image_name'].str.strip()))
        print(f"Da tao index cho {len(caption_map)} captions.")

    except Exception as e:
        print(f"Loi khi doc CSV: {e}")
        return

    # 2. Tìm tất cả các file all_captions_kg_*.json trong thư mục
    search_pattern = os.path.join(kg_folder, 'all_captions_kg_*.json')
    json_files = glob.glob(search_pattern)
    
    if not json_files:
        print(f"Khong tim thay file .json nao trong thu muc: {kg_folder}")
        return

    print(f"Tim thay {len(json_files)} file JSON. Bat dau xu ly...")

    # 3. Duyệt qua từng file và cập nhật
    count_processed = 0
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            is_updated = False
            for entry in data:
                # Lấy caption trong JSON
                caption = entry.get('caption', '').strip()
                
                # Tìm tên file ảnh tương ứng
                if caption in caption_map:
                    entry['filename'] = caption_map[caption]
                    is_updated = True
                else:
                    # Nếu không tìm thấy, có thể để trống hoặc ghi chú
                    # entry['filename'] = None 
                    pass

            # Ghi đè lại file cũ (hoặc lưu file mới tùy bạn)
            if is_updated:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                count_processed += 1
                
                # In tiến độ mỗi 100 file
                if count_processed % 100 == 0:
                    print(f"Da xu ly xong {count_processed} file...")

        except Exception as e:
            print(f"Loi khi xu ly file {filepath}: {e}")

    print(f"HOAN TAT! Da cap nhat {count_processed} file.")

if __name__ == "__main__":
    main()