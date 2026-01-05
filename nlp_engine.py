from sentence_transformers import SentenceTransformer
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class NLPEngine:
    def __init__(self, intents_file: str, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        # Загрузка модели для векторизации
        self.model = SentenceTransformer(model_name)

        # Загрузка базы знаний
        self.intents = self._load_intents(intents_file)

        # Векторизация всех шаблонов из базы знаний
        self.pattern_vectors = self._vectorize_patterns()

    def _load_intents(self, file_path: str) -> list:
        """Загрузка базы знаний из JSON"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)["intents"]

    def _vectorize_patterns(self) -> np.ndarray:
        """Преобразование всех шаблонов в векторы"""
        all_patterns = []
        for intent in self.intents:
            all_patterns.extend(intent["patterns"])

        return self.model.encode(all_patterns)

    def _get_intent_by_similarity(self, user_vector: np.ndarray, threshold: float = 0.6) -> tuple:
        """
        Поиск наиболее похожего шаблона по косинусному сходству.
        Возвращает (intent, response) или (None, None), если сходство ниже threshold.
        """
        # Вычисление косинусного сходства
        similarities = cosine_similarity([user_vector], self.pattern_vectors)[0]

        max_similarity = np.max(similarities)

        if max_similarity < threshold:
            return None, None

        # Находим индекс наиболее похожего шаблона
        best_idx = np.argmax(similarities)

        # Определяем, к какому intent относится шаблон
        pattern_counter = 0
        for intent in self.intents:
            if best_idx < pattern_counter + len(intent["patterns"]):
                return intent["intent"], intent["response"]
            pattern_counter += len(intent["patterns"])

        return None, None

    def classify_intent(self, text: str) -> tuple:
        """Классификация намерения через векторное сравнение"""
        # Векторизуем пользовательский запрос
        user_vector = self.model.encode([text])

        # Ищем наиболее похожее намерение
        intent, response = self._get_intent_by_similarity(user_vector[0])

        if intent is not None:
            return intent, response

        return None, (
            "Извините, не удалось понять ваш запрос. "
            "Попробуйте уточнить или сформулируйте иначе."
        )

