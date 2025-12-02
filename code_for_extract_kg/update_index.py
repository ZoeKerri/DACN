#Cập nhật index trong file index.json
import json

# Đường dẫn file
file_path = "E:/final_project/index.json"

# Đọc file
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Tăng giá trị index
data["index"] += 1

# Ghi lại file
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(data['index'])
