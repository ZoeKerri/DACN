import pandas as pd
import numpy as np

df = pd.read_csv('node_relation_co_occurrence_tensor.csv')

N = df['Frequency'].sum()
subject_counts = df.groupby('Subject')['Frequency'].sum().to_dict()
object_counts = df.groupby('Object')['Frequency'].sum().to_dict()

def calculate_ppmi(row):
    s, o, freq = row['Subject'], row['Object'], row['Frequency']
    c_s = subject_counts.get(s, 0)
    c_o = object_counts.get(o, 0)
    if c_s == 0 or c_o == 0:
        return 0
    ratio = (N * freq) / (c_s * c_o)
    if ratio <= 0:
        return 0
    pmi = np.log(ratio)
    return max(pmi, 0)

df_filtered = df[df['Frequency'] >= 1].copy()
df_filtered['ppmi'] = df_filtered.apply(calculate_ppmi, axis=1)

df_filtered = df_filtered.drop(columns=['Frequency'])

check_word = "man"
results = df_filtered[df_filtered['Subject'] == check_word] \
            .sort_values(by='ppmi', ascending=False).head(10)

print(results[['Subject', 'Relation', 'Object', 'ppmi']])

df_filtered.to_csv('kg_ppmi_ranked.csv', index=False)
