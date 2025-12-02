import json
import pandas as pd
import spacy
from collections import defaultdict
import os
import nltk
from nltk.corpus import wordnet as wn

tensor_file_path = 'node_relation_co_occurrence_tensor.csv'
kg_file_path = 'knowledge_graph_enriched.json'
results_file_path = 'flickr30k_images/results.csv'
output_csv = 't5_finetune_final.csv'
blip_caption_path = 'blip_captions_from_kaggle.json'

try:
    nltk.data.find('corpora/wordnet.zip')
except LookupError:
    nltk.download('wordnet')
    nltk.download('omw-1.4')

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

#Dùng cho việc lấy hypernym từ WordNet nếu không tìm thấy trong KG lẫn tensor
def get_wordnet_hypernym(noun):
    try:
        synsets = wn.synsets(noun, pos=wn.NOUN)
        if not synsets: return None
        hypernyms = synsets[0].hypernyms()
        if not hypernyms: return None
        return hypernyms[0].lemmas()[0].name().replace('_', ' ')
    except:
        return None

def load_blip_captions():
    blip_dict = {}
    if os.path.exists(blip_caption_path):
        with open(blip_caption_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                blip_dict = data
            elif isinstance(data, list):
                for item in data:
                    key = item.get("filename") or item.get("image_id") or item.get("id")
                    val = item.get("caption") or item.get("text")
                    if key and val:
                        blip_dict[str(key).strip()] = str(val).strip()
    return blip_dict

def load_data_lookup():
    tensor_lookup = defaultdict(list)
    kg_lookup = defaultdict(list)

    # 1. Load Tensor
    if os.path.exists(tensor_file_path):
        df_tensor = pd.read_csv(tensor_file_path)
        for _, row in df_tensor.iterrows():
            triplet = f"{row['Subject']} {row['Relation']} {row['Object']}"
            key = str(row['Subject']).lower().strip()
            tensor_lookup[key].append(triplet)

    # 2. Load Knowledge Graph
    allowed_relations = ['is a', 'is found at', 'can', 'is used for']
    
    if os.path.exists(kg_file_path):
        with open(kg_file_path, 'r', encoding='utf-8') as f: 
            kg_data = json.load(f)
            for item in kg_data:
                # Chỉ lấy quan hệ tăng cường
                if item.get('relation') in allowed_relations:
                    triplet = f"{item['from']} {item['relation']} {item['to']}"
                    
                    node_name = str(item['from']).lower().strip()
                    
                    kg_lookup[node_name].append(triplet)
    else:
        print(f"Không tìm thấy file {kg_file_path}")

    return tensor_lookup, kg_lookup

def get_nouns_from_caption(caption):
    if not caption: return []
    doc = nlp(str(caption).lower())
    nouns = [token.lemma_ for token in doc if token.pos_ in ['NOUN', 'PROPN']]
    return list(set(nouns))

def create_t5_dataset():
    blip_data_dict = load_blip_captions()
    tensor_lookup, kg_lookup = load_data_lookup()

    # Load Results
    if not os.path.exists(results_file_path):
        print("Lỗi: Không tìm thấy file results.csv")
        return
    df_results = pd.read_csv(results_file_path, delimiter='|')
    df_results.columns = [c.strip() for c in df_results.columns]
    
    results_lookup = defaultdict(list)
    for _, row in df_results.iterrows():
        if 'image_name' in row and 'comment' in row:
            results_lookup[str(row['image_name']).strip()].append(str(row['comment']).strip())

    final_rows = []
    print(f"--- Đang xử lý {len(blip_data_dict)} ảnh từ BLIP ---")

    for filename, blip_caption in blip_data_dict.items():
        filename = filename.strip()
        nouns = get_nouns_from_caption(blip_caption)
        
        caption_triplets = set()

        for noun in nouns:
            noun_specific_triplets = []
            
            # 1. Tìm trong Tensor
            if noun in tensor_lookup:
                noun_specific_triplets.extend(tensor_lookup[noun][:5]) 
            
            # 2. Tìm trong Knowledge Graph
            if noun in kg_lookup:
                noun_specific_triplets.extend(kg_lookup[noun][:5])
            
            # 3. FALLBACK: WordNet (nếu không tìm thấy quan hệ nào)
            if not noun_specific_triplets:
                hypernym = get_wordnet_hypernym(noun)
                if hypernym:
                    fallback_triplet = f"{noun} is a {hypernym}"
                    noun_specific_triplets.append(fallback_triplet)
            
            caption_triplets.update(noun_specific_triplets)

        graph_str = ", ".join(caption_triplets) if caption_triplets else "empty"
        input_text = f"refine caption: {blip_caption} <sep> graph: {graph_str}"

        target_captions = results_lookup.get(filename, [])
        if not target_captions: continue

        for target in target_captions:
            final_rows.append({
                "image_id": filename,
                "input_text": input_text,
                "target_text": target
            })

    if final_rows:
        df_final = pd.DataFrame(final_rows)
        df_final.to_csv(output_csv, index=False)
        print(f"--- Hoàn tất! File đã lưu tại: {output_csv} ---")
    else:
        print("Không tạo được dữ liệu.")

if __name__ == "__main__":
    create_t5_dataset()