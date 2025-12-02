#Tăng cường dữ liệu từ WordNet và ConceptNet vào KG.JSON trước khi đưa vào Neo4j
import json
from tqdm import tqdm
from knowledge_integration import KnowledgeIntegrationModule

def run_enrichment_process(input_file, output_file, knowledge_module):
    # Đọc file JSON gốc (KG từ PPMI)
    with open(input_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)

    # Trích tập thực thể cần tăng cường tri thức
    entities = set()
    for item in original_data:
        entities.add(item['from'])
        entities.add(item['to'])

    new_knowledge_entries = []

    for entity in tqdm(entities, desc="Đang tăng cường tri thức"):
        # GỌI MODULE TĂNG CƯỜNG TRI THỨC (WordNet + ConceptNet)
        enriched_data = knowledge_module.enrich_entity(entity)

        # --- WORDNET → ánh xạ về quan hệ "is a" (hypernym) ---
        for hypernym in enriched_data.get('wordnet', []):
            new_knowledge_entries.append({
                "from": entity,
                "relation": "is a",
                "to": hypernym,
                "properties": {"source": "wordnet", "type": "hypernym"}
            })

        # --- CONCEPTNET → ánh xạ về quan hệ tự nhiên ---
        cnet_data = enriched_data.get('conceptnet', {})
        relation_map = {
            'UsedFor': 'is used for',
            'CapableOf': 'can',
            'AtLocation': 'is found at'
        }

        for cnet_rel, target_list in cnet_data.items():
            if cnet_rel in relation_map:
                natural_relation = relation_map[cnet_rel]
                for target in target_list:
                    new_knowledge_entries.append({
                        "from": entity,
                        "relation": natural_relation,
                        "to": target,
                        "properties": {"source": "conceptnet", "type": cnet_rel}
                    })

    # Gộp KG cũ + tri thức được tăng cường
    final_data = original_data + new_knowledge_entries

    # Xuất ra file phục vụ Neo4j
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASS = "12345678"

    try:
        # Khởi tạo lớp tích hợp tri thức
        kim = KnowledgeIntegrationModule(URI, USER, PASS)

        # Chạy toàn bộ pipeline tăng cường tri thức
        run_enrichment_process(
            input_file='knowledge_graph_for_neo4j.json',
            output_file='knowledge_graph_enriched.json',
            knowledge_module=kim
        )

        kim.close()

    except Exception as e:
        print(f"Lỗi: {e}")
