import pandas as pd
import numpy as np

# 1. Đọc file của bạn
df = pd.read_csv('kg_co_occurrence_matrix.csv')

# 2. Tính toán các thống kê cơ bản
# Tổng trọng số toàn bộ graph
N = df['weight'].sum()

# Tính tổng số lần xuất hiện của từng Head và Tail
head_counts = df.groupby('head')['weight'].sum().to_dict()
tail_counts = df.groupby('tail')['weight'].sum().to_dict()

# 3. Hàm tính PMI
def calculate_pmi(row):
    h, t, w = row['head'], row['tail'], row['weight']
    c_h = head_counts.get(h, 0)
    c_t = tail_counts.get(t, 0)
    
    if c_h == 0 or c_t == 0: return 0
    
    # Công thức PMI: log( (N * w) / (count_head * count_tail) )
    val = (N * w) / (c_h * c_t)
    return np.log(val) if val > 0 else 0

# 4. Áp dụng tính PMI
# Mẹo: Lọc bỏ những cái xuất hiện quá ít (ví dụ < 2) để tránh nhiễu nếu muốn
df_filtered = df[df['weight'] >= 2].copy() 
df_filtered['pmi_score'] = df_filtered.apply(calculate_pmi, axis=1)

# 5. Xem kết quả thử với từ "man"
check_word = "man"
print(f"--- Top quan hệ thú vị nhất cho '{check_word}' ---")
results = df_filtered[df_filtered['head'] == check_word].sort_values(by='pmi_score', ascending=False).head(10)
print(results[['head', 'relation', 'tail', 'weight', 'pmi_score']])

# 6. Lưu lại file mới để dùng cho model
# Khi query, bạn sort theo 'pmi_score' thay vì 'weight'
df_filtered.to_csv('kg_pmi_ranked.csv', index=False)