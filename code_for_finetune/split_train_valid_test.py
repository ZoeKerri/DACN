# Code để chia tệp CSV thành train, val, test dựa trên tệp JSON cung cấp thông tin chia tệp
import json
import pandas as pd
import os

csv_path = 't5_finetune.csv'        
json_path = 'dataset_flickr30k.json' 
output_dir = 't5_data_split'        

os.makedirs(output_dir, exist_ok=True)

print("Đang đọc dữ liệu...")
df = pd.read_csv(csv_path)

# Cắt khoảng trắng thừa
df['image_id'] = df['image_id'].astype(str).str.strip()

with open(json_path, 'r') as f:
    data = json.load(f)

# Tạo mapping filename → split
img_to_split = {img['filename']: img['split'] for img in data['images']}

# Gán split cho CSV
df['split_group'] = df['image_id'].map(img_to_split)

# Những dòng không tìm thấy trong JSON → tự động cho vào train
missing_mask = df['split_group'].isna()
missing_rows = df[missing_mask]

if len(missing_rows) > 0:
    print(f"\nCó {len(missing_rows)} dòng không tìm thấy trong JSON → chuyển vào TRAIN.")

    # Gán train cho tất cả dòng bị thiếu
    df.loc[missing_mask, 'split_group'] = 'train'

# --- TIẾP TỤC CHIA FILE ---
for split_name in ['train', 'val', 'test']:
    subset_df = df[df['split_group'] == split_name].copy()
    subset_df.drop(columns=['split_group'], inplace=True)

    save_path = os.path.join(output_dir, f'{split_name}.csv')
    subset_df.to_csv(save_path, index=False)

    print(f"Đã lưu '{split_name}': {len(subset_df)} dòng "
          f"(tương ứng {subset_df['image_id'].nunique()} ảnh)")

print("\nHoàn tất! Kiểm tra thư mục:", output_dir)
