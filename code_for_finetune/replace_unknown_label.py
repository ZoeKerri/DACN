import os
import json
import glob
import spacy

# Load model ngôn ngữ tiếng Anh
print("Đang tải model SpaCy...")
nlp = spacy.load("en_core_web_sm")

def predict_label(text_id):
    """
    Hàm đoán nhãn dựa trên văn bản (text_id)
    """
    text = text_id.strip()
    doc = nlp(text)

    # 1. Ưu tiên Nhận diện thực thể (Named Entity Recognition)
    # Nếu SpaCy nhận ra đây là Người, Địa điểm, Tổ chức...
    if doc.ents:
        label = doc.ents[0].label_
        if label == "PERSON": return "person"
        if label == "GPE" or label == "LOC": return "location"
        if label == "ORG": return "organization"
        if label == "DATE" or label == "TIME": return "time"
    
    # 2. Quy tắc "Danh từ chính" (Root Noun)
    # Ví dụ: "red-hair" -> root là "hair"
    # Ví dụ: "a heavy metal table" -> root là "table"
    # SpaCy phân tích cú pháp rất giỏi việc này.
    for chunk in doc.noun_chunks:
        # Trả về danh từ gốc của cụm danh từ (thường là từ quan trọng nhất)
        return chunk.root.lemma_.lower()
    
    # 3. Fallback: Nếu không tìm thấy cụm danh từ, lấy từ cuối cùng (thường là danh từ trong tiếng Anh)
    # Ví dụ: "red-hair" (nếu bước 2 fail) -> lấy "hair"
    # Tách bằng khoảng trắng hoặc gạch ngang
    tokens = text.replace("-", " ").split()
    if tokens:
        return tokens[-1].lower()

    return "unknown" # Bó tay thì giữ nguyên

def main():
    kg_folder = 'knowledge_graph_outputs'
    search_pattern = os.path.join(kg_folder, 'all_captions_kg_*.json')
    json_files = glob.glob(search_pattern)

    print(f"Tìm thấy {len(json_files)} file. Bắt đầu xử lý...")

    total_fixed = 0
    
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_changed = False
            
            for entry in data:
                nodes = entry.get('node', [])
                for node in nodes:
                    # Chỉ xử lý nếu label đang là 'unknown'
                    if node.get('label') == 'unknown':
                        original_id = node.get('id', '')
                        
                        # Dự đoán nhãn mới
                        new_label = predict_label(original_id)
                        
                        # Nếu nhãn mới khác 'unknown' và khác chuỗi rỗng
                        if new_label and new_label != 'unknown':
                            node['label'] = new_label
                            file_changed = True
                            total_fixed += 1
                            # print(f"Fixed: '{original_id}' -> '{new_label}'") # Uncomment nếu muốn xem log chi tiết

            # Nếu có thay đổi thì ghi đè lại file
            if file_changed:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"Lỗi file {filepath}: {e}")

    print("-" * 30)
    print(f"Đã tự động sửa nhãn cho {total_fixed} node 'unknown'.")

if __name__ == "__main__":
    main()