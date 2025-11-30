import json
from pathlib import Path
from collections import defaultdict
import itertools

BASE_DIR = Path(__file__).parent
MERGED_FILE = BASE_DIR / "../merged_all_captions.json"
OUTPUT_MATRIX = BASE_DIR / "../co_occurrence_matrix.json"

def load_json(path: Path):
    if not path.exists():
        print("Không tìm thấy file merged_all_captions.json")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    data = load_json(MERGED_FILE)

    co_matrix = defaultdict(lambda: defaultdict(int))
    all_nodes = set()

    for item in data:
        if "node" not in item:
            continue

        nodes = []
        for n in item["node"]:
            if isinstance(n, dict) and "id" in n:
                nodes.append(n["id"])

        nodes = list(set(nodes))
        all_nodes.update(nodes)

        for a, b in itertools.combinations(nodes, 2):
            co_matrix[a][b] += 1
            co_matrix[b][a] += 1

    # Convert to JSON-serializable structure
    out = {}
    for a in sorted(all_nodes):
        out[a] = {}
        for b in sorted(all_nodes):
            out[a][b] = co_matrix[a][b]

    with open(OUTPUT_MATRIX, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=4)

    print(f"Đã tạo ma trận đồng xuất hiện: {OUTPUT_MATRIX}")

if __name__ == "__main__":
    main()
