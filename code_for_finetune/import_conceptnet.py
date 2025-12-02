import csv
from neo4j import GraphDatabase
from tqdm import tqdm

NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"
CSV_FILE_PATH = "assertions.csv"

VALID_RELATIONS = {
    '/r/RelatedTo', '/r/IsA', '/r/PartOf', '/r/HasA', '/r/UsedFor',
    '/r/CapableOf', '/r/AtLocation', '/r/Causes', '/r/HasProperty',
    '/r/MotivatedByGoal', '/r/Desires', '/r/CreatedBy'
}

class ConceptNetImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # Tạo Constraint (Index) cho property name của Concept
    def create_constraints(self):
        with self.driver.session() as session:
            query = "CREATE CONSTRAINT concept_name_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE"
            try:
                session.run(query)
            except Exception as e:
                print(f"[WARNING] Không thể tạo constraint: {e}")

    def import_batch(self, batch_dict):
        with self.driver.session() as session:
            for rel_type, rows in batch_dict.items():
                if not rows: continue
                query = f"""
                UNWIND $rows AS row
                MERGE (source:Concept {{name: row.start}})
                MERGE (target:Concept {{name: row.end}})
                MERGE (source)-[r:{rel_type}]->(target)
                SET r.weight = row.weight
                """
                try:
                    session.run(query, rows=rows)
                except Exception as e:
                    print(f"Lỗi khi import batch {rel_type}: {e}")

def run_import():
    importer = ConceptNetImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    # Tạo Index trước khi import dữ liệu
    importer.create_constraints()
    
    batch_dict = {r.split('/')[-1]: [] for r in VALID_RELATIONS}
    BATCH_SIZE = 5000
    current_count = 0
    
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            
            for row in tqdm(reader, desc="Importing"):
                if len(row) < 4: continue
                
                rel, start, end = row[1], row[2], row[3]
                if not (start.startswith('/c/en/') and end.startswith('/c/en/')): continue
                if rel not in VALID_RELATIONS: continue
                
                def clean_term(term):
                    parts = term.split('/')
                    if len(parts) >= 4:
                        return parts[3].replace('_', ' ').lower()
                    return None

                s_clean = clean_term(start)
                e_clean = clean_term(end)
                
                if s_clean and e_clean and s_clean != e_clean:
                    rel_key = rel.split('/')[-1]
                    if rel_key in batch_dict:
                        batch_dict[rel_key].append({'start': s_clean, 'end': e_clean, 'weight': 1.0})
                        current_count += 1
                
                if current_count >= BATCH_SIZE:
                    importer.import_batch(batch_dict)
                    batch_dict = {r.split('/')[-1]: [] for r in VALID_RELATIONS}
                    current_count = 0
            
            if current_count > 0:
                importer.import_batch(batch_dict)
                
    except FileNotFoundError:
        print(f"[ERROR] Không tìm thấy file {CSV_FILE_PATH}.")
    except Exception as e:
        print(f"[ERROR] Lỗi không mong muốn: {e}")
    finally:
        importer.close()
        print("[SUCCESS] Quá trình import hoàn tất.")

if __name__ == "__main__":
    run_import()
