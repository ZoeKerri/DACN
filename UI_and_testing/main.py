import pygame
import torch
from PIL import Image
import pandas as pd
import os
import sys
import gc
import spacy
import nltk
import tkinter as tk
from tkinter import filedialog
from transformers import (
    BlipProcessor,
    BlipForConditionalGeneration,
    AutoTokenizer,
    AutoModelForSeq2SeqLM
)
from peft import PeftModel

# Đường dẫn file CSV Knowledge Graph trên máy tính
LOCAL_KG_CSV_PATH = "UI_and_testing/kg_pmi_ranked.csv" 

# Đường dẫn thư mục chứa model LoRA đã train
LOCAL_LORA_MODEL_PATH = "UI_and_testing/t5_lora_finetune"

# Thiết bị
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

print(">> Đang khởi tạo ứng dụng và load model...")

try:
    nltk.data.find('corpora/wordnet.zip')
except LookupError:
    nltk.download('wordnet')
    nltk.download('omw-1.4')

try:
    nlp = spacy.load("en_core_web_sm")
except:
    print("Đang tải spacy model...")
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Load Knowledge Graph
kg_lookup = {}
if os.path.exists(LOCAL_KG_CSV_PATH):
    try:
        df_kg = pd.read_csv(LOCAL_KG_CSV_PATH)
        print(f"Đã tải KG ({len(df_kg)} dòng).")
        kg_lookup = df_kg.groupby('head').apply(
            lambda x: x[['relation', 'tail', 'pmi_score']].to_dict('records')
        ).to_dict()
    except Exception as e:
        print(f"Lỗi tải KG CSV: {e}")
else:
    print(f"Cảnh báo: Không tìm thấy file KG tại {LOCAL_KG_CSV_PATH}")

# Load BLIP
print("Đang tải BLIP...")
try:
    blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    blip_model = BlipForConditionalGeneration.from_pretrained(
        "Salesforce/blip-image-captioning-base", torch_dtype=DTYPE
    ).to(DEVICE)
except Exception as e:
    print(f"Lỗi tải BLIP: {e}")
    sys.exit()

# Load T5 + LoRA
print("Đang tải T5 + LoRA...")
t5_model = None
t5_tokenizer = None
try:
    t5_tokenizer = AutoTokenizer.from_pretrained("t5-base")
    t5_base = AutoModelForSeq2SeqLM.from_pretrained("t5-base", torch_dtype=DTYPE)
    t5_model = PeftModel.from_pretrained(t5_base, LOCAL_LORA_MODEL_PATH).to(DEVICE)
    t5_model.eval()
    print("Đã tải T5 thành công.")
except Exception as e:
    print(f"Lỗi tải T5 LoRA: {e}. Kiểm tra lại đường dẫn LOCAL_LORA_MODEL_PATH")

def extract_entities(caption):
    doc = nlp(caption.lower())
    entities = []
    for chunk in doc.noun_chunks:
        text = chunk.text.replace("a ", "").replace("an ", "").replace("the ", "")
        if len(text) > 2:
            entities.append(text.strip())
    for token in doc:
        if token.pos_ == "NOUN" and len(token.text) > 2:
            is_in_chunk = any(token.text in e for e in entities)
            if not is_in_chunk:
                entities.append(token.text)
    return list(set(entities))

def get_knowledge_triplets(entities, kg_lookup_dict, top_k=2):
    if not entities: return ""
    found_triplets = []
    for head in entities:
        if head in kg_lookup_dict:
            candidates = kg_lookup_dict[head]
            candidates.sort(key=lambda x: x['pmi_score'], reverse=True)
            for item in candidates:
                tail = item['tail']
                if tail in entities and tail != head:
                    found_triplets.append(f"{head} {item['relation']} {tail}")
    unique_triplets = list(set(found_triplets))
    return ", ".join(unique_triplets[:top_k])

def run_inference(image_path):
    """Hàm chạy toàn bộ pipeline và trả về caption cuối cùng"""
    try:
        raw_img = Image.open(image_path).convert('RGB')
        
        # 1. BLIP
        inputs = blip_processor(raw_img, return_tensors="pt").to(DEVICE)
        if DTYPE == torch.float16:
            inputs = {k: v.to(DTYPE) if v.dtype == torch.float else v for k, v in inputs.items()}
            
        with torch.no_grad():
            out = blip_model.generate(**inputs)
        blip_cap = blip_processor.decode(out[0], skip_special_tokens=True)
        
        # 2. KG Extraction
        entities = extract_entities(blip_cap)
        kg_str = get_knowledge_triplets(entities, kg_lookup, top_k=1)
        
        # 3. T5 Refinement
        input_text = f"refine caption: {blip_cap} <sep> graph: {kg_str}"
        
        if t5_model:
            inputs_t5 = t5_tokenizer(input_text, return_tensors="pt").to(DEVICE)
            with torch.no_grad():
                outputs_t5 = t5_model.generate(
                    **inputs_t5, max_length=100, num_beams=4, 
                    repetition_penalty=2.5, early_stopping=True
                )
            final_cap = t5_tokenizer.decode(outputs_t5[0], skip_special_tokens=True)
        else:
            final_cap = "Error: T5 Model not loaded."
            
        return final_cap, blip_cap, kg_str
        
    except Exception as e:
        return f"Error: {str(e)}", "", ""

# --- Pygame UI ---
pygame.init()
WIDTH, HEIGHT = 900, 700
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Image Captioning - KG Enhanced")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (70, 130, 180)
DARK_BLUE = (25, 25, 112)

font_path = "UI_and_testing/arial.ttf"

if not os.path.exists(font_path):
    print("Không tìm thấy font Arial, đang dùng font mặc định (có thể lỗi tiếng Việt).")
    font_path = None 

FONT_BTN = pygame.font.Font(font_path, 20)
FONT_TEXT = pygame.font.Font(font_path, 18)
FONT_CAPTION = pygame.font.Font(font_path, 22)

FONT_BTN.set_bold(True)
FONT_CAPTION.set_bold(True)

current_image = None
current_image_path = None
generated_caption = "Chưa có ảnh nào được chọn."
blip_result = ""
kg_result = ""
is_processing = False

def open_file_dialog():
    root = tk.Tk()
    root.withdraw() 
    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")]
    )
    root.destroy()
    return file_path

def draw_text_multiline(surface, text, pos, font, color, max_width):
    words = [word.split(' ') for word in text.splitlines()]  
    space = font.size(' ')[0] 
    x, y = pos
    for line in words:
        for word in line:
            word_surface = font.render(word, True, color)
            word_width, word_height = word_surface.get_size()
            if x + word_width >= max_width + pos[0]:
                x = pos[0] 
                y += word_height 
            surface.blit(word_surface, (x, y))
            x += word_width + space
        x = pos[0]  
        y += word_height 

def main():
    global current_image, current_image_path, generated_caption, blip_result, kg_result, is_processing
    
    clock = pygame.time.Clock()
    running = True

    btn_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT - 80, 200, 50)

    while running:
        SCREEN.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_rect.collidepoint(event.pos) and not is_processing:

                    path = open_file_dialog()
                    if path:
                        current_image_path = path
                        
                        img = pygame.image.load(path)
                        img_w, img_h = img.get_size()
                        target_h = 400
                        scale_factor = target_h / img_h
                        new_w = int(img_w * scale_factor)
                        current_image = pygame.transform.scale(img, (new_w, target_h))
                        
                        is_processing = True
                        generated_caption = "Đang xử lý (Generating)... Vui lòng đợi."
                        blip_result = ""
                        kg_result = ""

        if current_image:
            x_pos = (WIDTH - current_image.get_width()) // 2
            SCREEN.blit(current_image, (x_pos, 20))
        else:
            text_surf = FONT_TEXT.render("Chưa chọn ảnh", True, GRAY)
            SCREEN.blit(text_surf, (WIDTH//2 - 50, 200))

        pygame.draw.rect(SCREEN, BLUE if not is_processing else GRAY, btn_rect, border_radius=10)
        btn_text = FONT_BTN.render("Chọn Ảnh (Input)", True, WHITE)
        text_rect = btn_text.get_rect(center=btn_rect.center)
        SCREEN.blit(btn_text, text_rect)

        pygame.draw.line(SCREEN, GRAY, (50, 440), (WIDTH-50, 440), 2)
        
        caption_label = FONT_CAPTION.render("Final Caption:", True, DARK_BLUE)
        SCREEN.blit(caption_label, (50, 460))
        draw_text_multiline(SCREEN, generated_caption, (50, 490), FONT_TEXT, BLACK, WIDTH - 100)
        
        if blip_result:
            blip_label = FONT_TEXT.render("BLIP Base:", True, (100, 100, 100))
            SCREEN.blit(blip_label, (50, 550))
            draw_text_multiline(SCREEN, blip_result, (150, 550), FONT_TEXT, (100, 100, 100), WIDTH - 200)
            
            kg_label = FONT_TEXT.render("KG Info:", True, (100, 100, 100))
            SCREEN.blit(kg_label, (50, 580))
            draw_text_multiline(SCREEN, kg_result, (150, 580), FONT_TEXT, (100, 100, 100), WIDTH - 200)

        pygame.display.flip()

        if is_processing and current_image_path:
            final, base, kg = run_inference(current_image_path)
            
            generated_caption = final
            blip_result = base
            kg_result = kg if kg else "(None)"
            is_processing = False
            
            torch.cuda.empty_cache()
            gc.collect()

        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()