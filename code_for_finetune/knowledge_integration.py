import spacy
import nltk
from nltk.corpus import wordnet as wn
from neo4j import GraphDatabase, basic_auth
import logging
from typing import List, Dict, Set, Any
from collections import defaultdict

# Tự động tải dữ liệu WordNet nếu chưa có
try:
    nltk.data.find('corpora/wordnet.zip')
except LookupError:
    logging.info("Đang tải dữ liệu WordNet...")
    nltk.download('wordnet')
    nltk.download('omw-1.4')

#Class dùng để tích hợp tri thức từ WordNet và ConceptNet
class KnowledgeIntegrationModule:

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_pass: str):
        # 1. Khởi tạo Spacy để Lemmatization (Đưa từ về nguyên mẫu)
        # Cần thiết để khớp chính xác từ trong ảnh với từ điển tri thức
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logging.warning("Không tìm thấy model Spacy. Đang tải 'en_core_web_sm'...")
            from spacy.cli import download
            download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

        # 2. Kết nối Neo4j Driver cho ConceptNet
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(
                neo4j_uri, 
                auth=basic_auth(neo4j_user, neo4j_pass)
            )
            # Kiểm tra kết nối
            self.driver.verify_connectivity()
            logging.info("Kết nối thành công đến Neo4j Database.")
        except Exception as e:
            logging.error(f"Lỗi kết nối Neo4j: {e}")
            raise

    def close(self):
        if self.driver:
            self.driver.close()

    def lemmatize(self, text: str) -> str:
        doc = self.nlp(text)
        if not doc:
            return text
        # Lấy lemma của token cuối cùng (thường là danh từ chính trong cụm danh từ)
        return doc[-1].lemma_.lower()

    # --- PHẦN 1: WORDNET (NLTK) ---
    def get_hypernyms(self, concept: str, depth: int = 1) -> List[str]:
        lemma = self.lemmatize(concept)
        synsets = wn.synsets(lemma)
        
        if not synsets:
            return []

        # Heuristic: Chọn synset danh từ (noun) phổ biến nhất
        noun_synsets = [s for s in synsets if s.pos() == 'n']
        if noun_synsets:
            primary_synset = noun_synsets[0]
        else:
            primary_synset = synsets[0]
        
        if not primary_synset:
            return []

        hypernyms = set()
        current_level = [primary_synset]
        
        # Duyệt cây phân cấp lên trên theo độ sâu yêu cầu
        for _ in range(depth):
            next_level = []
            for s in current_level:
                for hyper in s.hypernyms():
                    # Lấy tên lemma đầu tiên của hypernym, thay '_' bằng khoảng trắng
                    lemmas_list = hyper.lemmas()
                    name = lemmas_list[0].name().replace('_', ' ')
                    hypernyms.add(name)
                    next_level.append(hyper)
            current_level = next_level

        return list(hypernyms)

    # --- PHẦN 2: CONCEPTNET (NEO4J CYPHER QUERY) ---
    def get_conceptnet_context(self, concept: str, limit: int = 2) -> Dict[str, List[str]]:
        lemma = self.lemmatize(concept)
        
        # Câu lệnh Cypher tối ưu:
        # - Chỉ match các node Concept có tên trùng khớp (cần Index trên property 'name')
        # - Lọc theo loại quan hệ (type(r))
        # - Lọc theo trọng số (weight > 1.0) để bỏ nhiễu
        # - Sắp xếp giảm dần theo trọng số để lấy tri thức phổ biến nhất
        cypher_query = """
        MATCH (start:Concept {name: $name})-[r]->(end:Concept)
        WHERE type(r) IN ['UsedFor', 'CapableOf', 'AtLocation']
        AND r.weight >= 1.0
        RETURN type(r) AS rel_type, end.name AS target_name
        ORDER BY r.weight DESC
        LIMIT $limit_per_type * 3 
        """
        
        knowledge = defaultdict(list)

        if not self.driver:
            logging.warning("Neo4j driver chưa được khởi tạo.")
            return dict(knowledge)
        
        try:
            with self.driver.session() as session:
                # Lấy nhiều hơn limit một chút để lọc sau
                result = session.run(cypher_query, name=lemma, limit_per_type=limit)
                
                for record in result:
                    rel = record["rel_type"]
                    target = record["target_name"]
                    
                    if target.startswith("/c/en/"):
                        parts = target.split("/")
                        if len(parts) > 3:
                            target = parts[1]
                        else:
                            target = parts[-1]
                    target = target.replace("_", " ")

                    if len(knowledge[rel]) < limit:
                        knowledge[rel].append(target)
                        
        except Exception as e:
            logging.warning(f"Lỗi truy vấn Neo4j cho '{concept}': {e}")
            
        return dict(knowledge)

    def enrich_entity(self, entity_raw: str) -> Dict[str, Any]:
        return {
            "entity": entity_raw,
            "wordnet": self.get_hypernyms(entity_raw),
            "conceptnet": self.get_conceptnet_context(entity_raw)
        }