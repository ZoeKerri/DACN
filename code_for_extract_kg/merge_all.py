import json

# Đọc 2 file
with open('clean_merge_final.json', 'r', encoding='utf-8') as f1:
    data1 = json.load(f1)

with open('clean_merge_final_2.json', 'r', encoding='utf-8') as f2:
    data2 = json.load(f2)

all_data = data1 + data2

seen = set()
unique_data = []

for item in all_data:
    key = (item["filename"], item["caption"])  

    if key not in seen:
        seen.add(key)
        unique_data.append(item)

with open('merged_unique.json', 'w', encoding='utf-8') as f:
    json.dump(unique_data, f, ensure_ascii=False, indent=4)
