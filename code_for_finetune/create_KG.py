#Dùng cho việc khởi tạo KG từ file CSV và lưu vào JSON để sau này tạo code Cypher sau
import pandas as pd
import json

def csv_to_json_kg(input_file, output_file):
    df = pd.read_csv(input_file)

    knowledge_graph_data = []

    for index, row in df.iterrows():
        node = {
            "from": row['Subject'],
            "relation": row['Relation'],
            "to": row['Object'],
            "properties": {
                "ppmi": row['ppmi']
            }
        }
        knowledge_graph_data.append(node)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge_graph_data, f, indent=4, ensure_ascii=False)
    
    print(f"Đã tạo file {output_file} thành công với {len(knowledge_graph_data)} quan hệ.")

csv_to_json_kg('kg_ppmi_ranked.csv', 'knowledge_graph_for_neo4j.json')