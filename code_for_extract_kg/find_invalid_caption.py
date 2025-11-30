import pandas as pd
import json

# Do lỗi trong quá trình gộp file, ta có thể có các dòng thừa, nên ta cần làm sạch lại.
# input_file = 'merged_all_captions_kg.json' 
# output_file = 'clean_merge_final.json'

#Tiếp đó, sau khi xử lý các caption bị thiếu, khoảng 547 hình bị thiếu caption thì còn lại 33 ảnh bị thiếu caption <5
#Những caption này lý do thiếu là do tên caption trùng nhau chứ không phải là do quá trình xử lý nữa, nên ta chỉ cần gộp lại
input_file = 'merged_unique.json' 
output_file = 'clean_merge_final_3.json'

print(f"Đang đọc file {input_file}...")
try:
    df = pd.read_json(input_file)
except ValueError:
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data)

print(f"Tổng số dòng ban đầu: {len(df)}")

# Xóa dòng trùng lặp hoàn toàn (cả filename và caption giống hệt nhau)
df = df.drop_duplicates(subset=['filename', 'caption'])
print(f"Số dòng sau khi xóa trùng lặp nội dung: {len(df)}")

df_clean = df.groupby('filename').head(5).reset_index(drop=True)

check_counts = df_clean.groupby('filename').size()
over_5 = check_counts[check_counts > 5]
under_5 = check_counts[check_counts < 5]

print("-" * 40)
print("KẾT QUẢ SAU KHI LỌC:")
print(f"- Tổng số ảnh: {len(check_counts)}")
print(f"- Số dòng dữ liệu cuối cùng: {len(df_clean)}")

if len(over_5) == 0:
    print("Không còn ảnh nào bị dư caption (>5).")
else:
    print(f"Vẫn còn {len(over_5)} ảnh bị dư (vô lý - cần kiểm tra lại logic).")

if len(under_5) > 0:
    print(f"Có {len(under_5)} ảnh bị thiếu caption (<5).")

df_clean.to_json(output_file, orient='records', indent=4, force_ascii=False)
print(f"\nĐã lưu file sạch tại: {output_file}")

list_thieu = under_5.index.tolist()

print("\n" + "="*40)
print(f"CHI TIẾT {len(list_thieu)} ẢNH BỊ THIẾU CAPTION (<5):")
print("="*40)

print(list_thieu[:20])
if len(list_thieu) > 20:
    print(f"... và {len(list_thieu) - 20} ảnh khác.")
    
#Cái này là dùng  cho xem caption thiếu ở graph ban đầu
# with open('invalid_caption_files.txt', 'w', encoding='utf-8') as f:
#     f.write('\n'.join(list_thieu))
 
#Cái này là dùng cho xem caption thiếu ở graph sau khi đã xử lý lại   
with open('invalid_caption_files_2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(list_thieu))

print(f"\n-> Đã lưu danh sách đầy đủ vào file: 'invalid_caption_files.txt'")

if len(list_thieu) > 0:
    sample_img = list_thieu[0] 
    print(f"\n[Ví dụ] Soi nội dung ảnh '{sample_img}':")
    rows = df_clean[df_clean['filename'] == sample_img]
    for idx, row in rows.iterrows():
        print(f"- {row['caption']}")
    print(f"-> Tổng cộng chỉ còn: {len(rows)} caption.")