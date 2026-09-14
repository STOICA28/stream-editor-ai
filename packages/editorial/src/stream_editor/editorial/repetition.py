import math
import re
from collections import Counter


class RepetitionDetector:
    @staticmethod
    def score(candidate_text: str, other_texts: list[str]) -> float:
        if not candidate_text.strip() or not other_texts:
            return 0.0
            
        def tokenize(text: str) -> list[str]:
            return [w.lower() for w in re.findall(r'\w+', text)]
            
        all_texts = [candidate_text] + other_texts
        documents = [tokenize(t) for t in all_texts]
        
        # Calculate DF
        df = Counter()
        for doc in documents:
            df.update(set(doc))
            
        N = len(documents)
        
        # Calculate TF-IDF vectors
        def get_vector(doc: list[str]) -> dict[str, float]:
            tf = Counter(doc)
            vec = {}
            for word, count in tf.items():
                idf = math.log((N + 1) / (df[word] + 1)) + 1  # smooth idf
                vec[word] = count * idf
            return vec
            
        def cosine_sim(v1: dict[str, float], v2: dict[str, float]) -> float:
            dot = sum(v1.get(w, 0) * v2.get(w, 0) for w in set(v1) | set(v2))
            mag1 = math.sqrt(sum(val**2 for val in v1.values()))
            mag2 = math.sqrt(sum(val**2 for val in v2.values()))
            if mag1 == 0 or mag2 == 0:
                return 0.0
            return dot / (mag1 * mag2)
            
        cand_vec = get_vector(documents[0])
        
        max_sim = 0.0
        for i in range(1, len(documents)):
            other_vec = get_vector(documents[i])
            sim = cosine_sim(cand_vec, other_vec)
            if sim > max_sim:
                max_sim = sim
                
        return max_sim
