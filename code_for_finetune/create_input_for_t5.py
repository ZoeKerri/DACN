import json
import pandas as pd

# === CẤU HÌNH ===
kg_file_path = 'merged_unique.json'
blip_file_path = 'blip_captions_from_kaggle.json'
output_csv = 't5_finetune.csv'

def normalize_key(x):
    if x is None:
        return None
    x = str(x).strip()
    return x.replace(".jpg", "")

def format_triplets(triplets_list):
    if not triplets_list:
        return "empty"
    valid = [
        f"{t['from']} {t['relation']} {t['to']}"
        for t in triplets_list
        if 'from' in t and 'relation' in t and 'to' in t
    ]
    return ", ".join(valid) if valid else "empty"

def create_dataset_final():

    print("Đang tải JSON...")
    with open(kg_file_path, 'r', encoding='utf-8') as f:
        kg_data = json.load(f)
    with open(blip_file_path, 'r', encoding='utf-8') as f:
        blip_data = json.load(f)

    # === BLIP lookup chuẩn hóa key ===
    blip_lookup = {}

    if isinstance(blip_data, dict):
        for k, v in blip_data.items():
            blip_lookup[normalize_key(k)] = v
    else:
        for item in blip_data:
            key_raw = item.get("filename") or item.get("image_id")
            if key_raw:
                blip_lookup[normalize_key(key_raw)] = item.get("caption")

    print("Tổng BLIP unique key:", len(blip_lookup))

    final_rows = []
    seen_pairs = set()

    for item in kg_data:

        filename_raw = item.get("filename") or item.get("image_id")
        if not filename_raw:
            continue

        # === Giữ filename gốc để xuất ra dataset (có .jpg) ===
        output_filename = str(filename_raw).strip()

        # === nhưng dùng key không .jpg để lookup BLIP ===
        lookup_key = normalize_key(filename_raw)

        blip_caption = blip_lookup.get(lookup_key)
        if not blip_caption:
            continue

        target = item.get("caption", "")
        triplet_str = format_triplets(item.get("triplets", []))

        input_text = f"refine caption: {blip_caption} <sep> graph: {triplet_str}"

        # === CHỐNG TRÙNG TUYỆT ĐỐI ===
        pair_key = (output_filename, blip_caption, target)
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        final_rows.append({
            "image_id": output_filename,    
            "input_text": input_text,
            "target_text": target
        })

    df = pd.DataFrame(final_rows)

    print("Tổng dòng:", len(df))
    df.to_csv(output_csv, index=False)
    print(f"Đã lưu dataset sạch: {output_csv}")


if __name__ == "__main__":
    create_dataset_final()
