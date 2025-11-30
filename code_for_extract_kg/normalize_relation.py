import json
import os
import sys

BASE_DIR = os.path.dirname(__file__)

if len(sys.argv) < 2:
    print(json.dumps({"error": "Thiếu relation truyền vào"}))
    sys.exit(1)

normalize_input = sys.argv[1].strip('"')

relation_map = {}
for pair in normalize_input.split(","):
    if " - " in pair:
        left, right = pair.split(" - ")
        relation_map[right.strip()] = left.strip()

input_path = os.path.join(BASE_DIR, "../output_original.json")
output_path = os.path.join(BASE_DIR, "../output_mapped.json")

with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for item in data:
    new_triplets = []
    new_edges = []

    for t in item.get("triplets", []):
        rel = t["relation"].strip()
        if rel in relation_map:
            t["relation"] = relation_map[rel]
            new_triplets.append(t)
            new_edges.append(relation_map[rel])

    item["triplets"] = new_triplets
    item["edge"] = list(dict.fromkeys(new_edges))

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(json.dumps(data, ensure_ascii=False))
