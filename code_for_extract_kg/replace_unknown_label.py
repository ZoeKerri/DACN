#Đổi label "unknown" trong merged_all_captions.json thành các label dự đoán được bằng SpaCy
import os
import json
import spacy

print("Đang tải model SpaCy...")
nlp = spacy.load("en_core_web_sm")

def predict_label(text_id):
    text = text_id.strip()
    doc = nlp(text)

    if doc.ents:
        label = doc.ents[0].label_
        if label == "PERSON": return "person"
        if label in ("GPE", "LOC"): return "location"
        if label == "ORG": return "organization"
        if label in ("DATE", "TIME"): return "time"

    for chunk in doc.noun_chunks:
        return chunk.root.lemma_.lower()

    tokens = text.replace("-", " ").split()
    if tokens:
        return tokens[-1].lower()

    return "unknown"

def main():
    file_path = "merged_all_captions.json"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        print("Không thể đọc file")
        return

    total_fixed = 0
    file_changed = False

    for entry in data:
        nodes = entry.get("node", [])
        for node in nodes:
            if node.get("label") == "unknown":
                new_label = predict_label(node.get("id", ""))
                if new_label and new_label != "unknown":
                    node["label"] = new_label
                    total_fixed += 1
                    file_changed = True

    if file_changed:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Đã sửa {total_fixed} node.")

if __name__ == "__main__":
    main()
