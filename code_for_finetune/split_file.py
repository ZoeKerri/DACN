import os
import shutil
import json
from tqdm import tqdm

INPUT_IMG_DIR = 'flickr30k_images/flickr30k_images'
OUTPUT_DIR = 'flickr30k_split'
JSON_PATH = 'dataset_flickr30k.json'

with open(JSON_PATH, 'r') as f:
    data = json.load(f)

for split in ['train', 'val', 'test']:
    os.makedirs(os.path.join(OUTPUT_DIR, split), exist_ok=True)

print(f"Sao chép hình ảnh tới {OUTPUT_DIR}...")

for img in tqdm(data['images']):
    filename = img['filename']
    split_type = img['split']
    src = os.path.join(INPUT_IMG_DIR, filename)
    dst = os.path.join(OUTPUT_DIR, split_type, filename)
    if os.path.exists(src):
        shutil.copy(src, dst)

print("Xong!")
