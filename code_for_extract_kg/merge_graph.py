import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "../knowledge_graph_outputs"
MERGED_FILE = BASE_DIR / "../merged_all_captions.json"

def load_json_list(path: Path):
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except:
        return []

def main():
    merged = []

    for file in OUTPUT_DIR.glob("all_captions_kg_*.json"):
        lst = load_json_list(file)
        merged.extend(lst)

    with open(MERGED_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=4)

    print(f"Đã merge xong {len(merged)} caption vào {MERGED_FILE}")

if __name__ == "__main__":
    main()
