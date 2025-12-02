#Đọc index để truyền lên n8n
import json

file_path = "E:/final_project/index.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print(data["index"])
