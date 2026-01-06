from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class SemanticEngine:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        # Загружаем русскоязычную модель
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        # Векторизуем все вопросы из базы
        self.question_embeddings = self.model.encode(
            [item["question"] for item in self.kb],
            convert_to_numpy=True
        )

    def find_best_match(self, user_query, threshold=0.6):
        """
        Поиск наиболее релевантного ответа по семантической близости
        :param user_query: текст запроса пользователя
        :param threshold: порог сходства (0.0–1.0)
        :return: текст ответа или None
        """
        # Векторизуем запрос
        query_embedding = self.model.encode([user_query], convert_to_numpy=True)

        # Вычисляем косинусное сходство
        similarities = cosine_similarity(query_embedding, self.question_embeddings).flatten()
        best_score = np.max(similarities)
        best_idx = np.argmax(similarities)

        if best_score >= threshold:
            return self.kb[best_idx]["answer"]
        return None
