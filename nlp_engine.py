import json
import re
from typing import Tuple, Optional, Dict, List, Any
import difflib
from enum import Enum

class TextPreprocessor:
    """Предобработка текста пользователя с учетом опечаток"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Нормализация текста: нижний регистр, удаление лишних символов"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)  # Удаляем пунктуацию
        text = re.sub(r'\s+', ' ', text)      # Убираем лишние пробелы
        return text
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """Извлечение ключевых слов из текста"""
        stop_words = {
            'как', 'где', 'что', 'кто', 'когда', 'почему', 'зачем',
            'мне', 'мной', 'меня', 'тебе', 'тобой', 'тебя',
            'свой', 'своя', 'своё', 'свои',
            'это', 'этот', 'эта', 'эти', 'этот',
            'вот', 'тут', 'там', 'здесь', 'туда',
            'очень', 'просто', 'вообще', 'совсем',
            'можно', 'нужно', 'надо', 'хочу', 'хотел'
        }
        
        words = text.split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords
    
    @staticmethod
    def get_word_variations(word: str) -> List[str]:
        """Генерация вариаций слова для учета опечаток"""
        variations = [word]
        
        # Распространенные опечатки в русском языке
        common_typos = {
            'а': ['о'], 'о': ['а'], 'е': ['э'], 'и': ['й', 'ы'],
            'т': ['тт', 'д'], 'п': ['пп', 'б'], 'к': ['кк', 'г'],
            'с': ['сс', 'з'], 'в': ['вв', 'ф']
        }
        
        # Добавляем варианты с заменой похожих букв
        for i, char in enumerate(word):
            if char in common_typos:
                for replacement in common_typos[char]:
                    variation = word[:i] + replacement + word[i+1:]
                    variations.append(variation)
        
        # Добавляем варианты с пропущенными/лишними буквами (для коротких слов)
        if len(word) > 3:
            # Пропуск одной буквы
            for i in range(len(word)):
                variations.append(word[:i] + word[i+1:])
            
            # Добавление лишней буквы (повтор)
            for i in range(len(word)-1):
                if word[i] == word[i+1]:
                    variations.append(word[:i] + word[i+1:])
        
        return list(set(variations))  # Убираем дубли

class FuzzySearcher:
    """Нечеткий поиск с учетом опечаток"""
    
    @staticmethod
    def fuzzy_ratio(text1: str, text2: str) -> float:
        """Расчет схожести текстов с учетом опечаток"""
        # Базовое сравнение
        base_ratio = difflib.SequenceMatcher(None, text1, text2).ratio()
        
        # Дополнительные метрики
        words1 = text1.split()
        words2 = text2.split()
        
        # Сравнение по словам
        word_overlap = len(set(words1) & set(words2)) / max(len(set(words1)), 1)
        
        # Сравнение начальных букв
        first_letter_score = 0
        if words1 and words2:
            if words1[0][0] == words2[0][0]:
                first_letter_score = 0.2
        
        # Комбинированный score
        fuzzy_score = (base_ratio * 0.6) + (word_overlap * 0.3) + (first_letter_score * 0.1)
        
        return fuzzy_score
    
    @staticmethod
    def find_best_fuzzy_match(query: str, candidates: List[str], threshold: float = 0.5) -> Tuple[Optional[str], float]:
        """Поиск лучшего нечеткого совпадения"""
        if not candidates:
            return None, 0.0
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            score = FuzzySearcher.fuzzy_ratio(query, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate
        
        if best_score >= threshold:
            return best_match, best_score
        
        return None, 0.0
    
    @staticmethod
    def soundex_rus(word: str) -> str:
        """Упрощенный Soundex для русского языка"""
        if not word:
            return ""
        
        # Кодирование первой буквы
        first_char = word[0].upper()
        
        # Коды для остальных букв
        codes = {
            'а': '0', 'б': '1', 'в': '2', 'г': '3', 'д': '4', 'е': '0', 'ё': '0',
            'ж': '1', 'з': '2', 'и': '0', 'й': '0', 'к': '3', 'л': '4', 'м': '5',
            'н': '6', 'о': '0', 'п': '1', 'р': '2', 'с': '3', 'т': '4', 'у': '0',
            'ф': '1', 'х': '2', 'ц': '3', 'ч': '4', 'ш': '5', 'щ': '6', 'ъ': '0',
            'ы': '0', 'ь': '0', 'э': '0', 'ю': '0', 'я': '0'
        }
        
        # Кодируем слово
        encoded = first_char
        
        for char in word[1:].lower():
            code = codes.get(char, '0')
            if code != '0' and (not encoded or encoded[-1] != code):
                encoded += code
        
        # Дополняем до 4 символов
        encoded = (encoded + '000')[:4]
        
        return encoded
    
    @staticmethod
    def soundex_match(query: str, target: str) -> bool:
        """Проверка совпадения по Soundex"""
        query_soundex = FuzzySearcher.soundex_rus(query)
        target_soundex = FuzzySearcher.soundex_rus(target)
        
        return query_soundex == target_soundex

class KnowledgeBaseSearcher:
    """Поиск в локальной базе знаний с учетом опечаток"""
    
    def __init__(self, file_path: str = "knowledge_base.json"):
        self.file_path = file_path
        self.kb_data = self._load_knowledge_base()
        self.preprocessor = TextPreprocessor()
        self.fuzzy_searcher = FuzzySearcher()
        
        # Создаем индекс для быстрого поиска
        self.question_index = self._build_index()
    
    def _load_knowledge_base(self) -> List[Dict]:
        """Загрузка базы знаний"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ Загружено {len(data)} записей из базы знаний")
                return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Ошибка загрузки базы знаний: {e}")
            return []
    
    def _build_index(self) -> Dict[str, List[Dict]]:
        """Построение индекса для быстрого поиска"""
        index = {}
        
        for item in self.kb_data:
            question = item.get('question', '')
            normalized = self.preprocessor.normalize_text(question)
            
            # Индексируем по ключевым словам
            keywords = self.preprocessor.extract_keywords(normalized)
            for keyword in keywords:
                if keyword not in index:
                    index[keyword] = []
                index[keyword].append(item)
            
            # Индексируем по Soundex
            soundex = self.fuzzy_searcher.soundex_rus(question)
            if soundex not in index:
                index[soundex] = []
            index[soundex].append(item)
        
        return index
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Расчет схожести текстов с учетом опечаток"""
        return self.fuzzy_searcher.fuzzy_ratio(text1, text2)
    
    def find_best_match(
        self, 
        user_question: str, 
        source_type: Optional[str] = None,
        threshold: float = 0.4  # Более низкий порог для учета опечаток
    ) -> Tuple[Optional[Dict], float]:
        """
        Поиск лучшего совпадения в базе знаний с учетом опечаток
        """
        if not self.kb_data:
            return None, 0.0
        
        normalized_question = self.preprocessor.normalize_text(user_question)
        keywords = self.preprocessor.extract_keywords(normalized_question)
        
        best_item = None
        best_confidence = 0.0
        
        # Поиск через индекс (быстрый)
        candidate_items = set()
        
        for keyword in keywords:
            if keyword in self.question_index:
                candidate_items.update(self.question_index[keyword])
        
        # Если не нашли через индекс, ищем во всей базе
        if not candidate_items:
            candidate_items = self.kb_data
        
        # Генерируем вариации запроса для учета опечаток
        query_variations = []
        for keyword in keywords[:3]:  # Берем только первые 3 ключевых слова
            variations = self.preprocessor.get_word_variations(keyword)
            query_variations.extend(variations)
        
        for item in candidate_items:
            item_question = item.get('question', '')
            item_source = item.get('source', 'manual')
            
            # Фильтрация по типу источника, если указан
            if source_type and item_source != source_type:
                continue
            
            # Нормализуем вопрос из базы
            normalized_item = self.preprocessor.normalize_text(item_question)
            
            # Рассчитываем схожесть через нечеткий поиск
            similarity = self._calculate_similarity(normalized_question, normalized_item)
            
            # Проверяем совпадение по Soundex
            soundex_match = self.fuzzy_searcher.soundex_match(
                normalized_question[:10],  # Берем начало для скорости
                normalized_item[:10]
            )
            
            if soundex_match:
                similarity = max(similarity, 0.6)  # Повышаем score при совпадении по Soundex
            
            # Проверяем вариации
            for variation in query_variations[:5]:  # Ограничиваем количество проверок
                if variation in normalized_item:
                    similarity = max(similarity, 0.55)  # Небольшой бонус
                    break
            
            # Дополнительный бонус за ключевые слова
            item_keywords = self.preprocessor.extract_keywords(normalized_item)
            common_keywords = set(keywords) & set(item_keywords)
            keyword_overlap = len(common_keywords) / max(len(keywords), 1)
            
            # Итоговая уверенность с учетом всех факторов
            confidence = (similarity * 0.6) + (keyword_overlap * 0.4)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_item = item
        
        # Проверяем порог уверенности (ниже для учета опечаток)
        if best_confidence >= threshold:
            return best_item, best_confidence
        
        # Дополнительная проверка: поиск по частям вопроса
        if len(keywords) > 1:
            # Пробуем найти по комбинации ключевых слов
            for item in self.kb_data:
                if source_type and item.get('source') != source_type:
                    continue
                    
                item_text = self.preprocessor.normalize_text(item.get('question', ''))
                matches = sum(1 for kw in keywords if kw in item_text)
                
                if matches >= 2:  # Если есть хотя бы 2 совпадения
                    confidence = matches / len(keywords)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_item = item
        
        if best_confidence >= threshold * 0.8:  # Еще более низкий порог
            return best_item, best_confidence
        
        return None, 0.0
    
    def find_by_exact_question(
        self, 
        question: str, 
        source_type: Optional[str] = None
    ) -> Optional[Dict]:
        """Поиск точного совпадения по вопросу"""
        normalized_question = self.preprocessor.normalize_text(question)
        
        for item in self.kb_data:
            item_question = self.preprocessor.normalize_text(item.get('question', ''))
            item_source = item.get('source', 'manual')
            
            if source_type and item_source != source_type:
                continue
            
            if item_question == normalized_question:
                return item
        
        return None

class IntentClassifier:
    """Классификатор намерений пользователя"""
    
    def __init__(self):
        self.intents = {
            'greeting': ['привет', 'здравствуй', 'добрый', 'hello', 'hi', 'начать', 'прив'],
            'farewell': ['пока', 'до свидания', 'выход', 'закончить', 'спасибо', 'пок', 'всего'],
            'help': ['помощь', 'помоги', 'что ты умеешь', 'команды', 'подскажи', 'посоветуй'],
            'question_1c': ['как', 'где', 'почему', 'зачем', 'можно ли', 'какой', 'чем'],
            'document': ['накладная', 'счет', 'акт', 'договор', 'ордер', 'отчет', 'документ'],
            'operation': ['создать', 'удалить', 'изменить', 'провести', 'отменить', 'сделать', 'написать'],
            'search': ['найти', 'поиск', 'искать', 'где найти', 'как найти', 'найди'],
            'button_click': ['button:', 'menu:', 'нажать кнопку', 'клик по', 'кнопка']
        }
    
    def classify(self, text: str) -> List[str]:
        """Определение намерений в тексте"""
        text_lower = text.lower()
        detected_intents = []
        
        for intent, keywords in self.intents.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected_intents.append(intent)
                    break
        
        return detected_intents if detected_intents else ['unknown']
    
    def is_button_click(self, text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Определение, является ли запрос нажатием кнопки"""
        text_lower = text.lower()
        
        # Проверяем форматы: "button:накладные" или "menu:отчеты"
        for prefix in ['button:', 'menu:']:
            if text_lower.startswith(prefix):
                parts = text_lower.split(':', 1)
                if len(parts) == 2:
                    return True, prefix.rstrip(':'), parts[1].strip()
        
        # Проверяем текстовое описание (с учетом опечаток)
        button_patterns = [
            (['нажать кнопку', 'нажми кнопку', 'нажы кнопку', 'нажатькнопку'], 'button'),
            (['клик по кнопке', 'кликнуть кнопку', 'клик по', 'кликнуть'], 'button'),
            (['в меню', 'меню', 'в разедел', 'разедел'], 'menu'),
            (['раздел', 'раздил', 'радел'], 'menu')
        ]
        
        for patterns, source_type in button_patterns:
            for pattern in patterns:
                if pattern in text_lower:
                    # Извлекаем текст после паттерна
                    start_idx = text_lower.find(pattern) + len(pattern)
                    button_text = text_lower[start_idx:].strip()
                    if button_text:
                        return True, source_type, button_text
        
        return False, None, None

class ButtonHandler:
    """Обработчик нажатий кнопок с учетом опечаток"""
    
    def __init__(self, kb_searcher: KnowledgeBaseSearcher):
        self.kb_searcher = kb_searcher
        self.preprocessor = TextPreprocessor()
    
    def handle_button_click(
        self, 
        source_type: str, 
        button_text: str
    ) -> Optional[Dict]:
        """Обработка нажатия кнопки с учетом опечаток"""
        print(f"🔘 Обработка кнопки: source={source_type}, text='{button_text}'")
        
        normalized_button = self.preprocessor.normalize_text(button_text)
        
        # 1. Сначала ищем точное совпадение
        exact_match = self.kb_searcher.find_by_exact_question(
            normalized_button, 
            source_type=source_type
        )
        
        if exact_match:
            print(f"✅ Найдено точное совпадение для кнопки '{button_text}'")
            return exact_match
        
        # 2. Ищем с учетом опечаток (низкий порог)
        fuzzy_match, confidence = self.kb_searcher.find_best_match(
            normalized_button,
            source_type=source_type,
            threshold=0.3  # Очень низкий порог для кнопок
        )
        
        if fuzzy_match and confidence >= 0.3:
            print(f"✅ Найдено нечеткое совпадение (уверенность: {confidence:.2f})")
            return fuzzy_match
        
        # 3. Если не нашли в указанном source, ищем в любом source
        any_match, confidence = self.kb_searcher.find_best_match(
            normalized_button,
            threshold=0.35
        )
        
        if any_match:
            print(f"⚠️ Найдено совпадение в другом источнике (уверенность: {confidence:.2f})")
            return any_match
        
        print(f"❌ Не найдено совпадений для кнопки '{button_text}'")
        return None

class NLPEngine:
    """Основной NLP-движок с учетом опечаток"""
    
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.intent_classifier = IntentClassifier()
        self.kb_searcher = KnowledgeBaseSearcher()
        self.button_handler = ButtonHandler(self.kb_searcher)
    
    def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Полная обработка сообщения пользователя с учетом опечаток
        """
        print(f"\n📨 Получено сообщение: '{user_message}'")
        
        # Проверяем, является ли это нажатием кнопки
        is_button_click, source_type, button_text = self.intent_classifier.is_button_click(
            user_message
        )
        
        if is_button_click and source_type and button_text:
            print(f"🎯 Определено как нажатие кнопки: {source_type} -> '{button_text}'")
            
            # Обрабатываем как кнопку
            kb_item = self.button_handler.handle_button_click(source_type, button_text)
            
            if kb_item:
                return {
                    'original_message': user_message,
                    'normalized_message': button_text,
                    'intents': ['button_click'],
                    'source_type': source_type,
                    'kb_answer': kb_item.get('answer'),
                    'kb_item': kb_item,
                    'kb_confidence': 1.0,
                    'has_kb_answer': True,
                    'is_button_click': True,
                    'is_fuzzy_match': False
                }
        
        # Обычная текстовая обработка с учетом опечаток
        normalized = self.preprocessor.normalize_text(user_message)
        
        # Классификация намерений
        intents = self.intent_classifier.classify(normalized)
        
        # Извлечение ключевых слов
        keywords = self.preprocessor.extract_keywords(normalized)
        
        # Поиск в базе знаний с учетом опечаток
        kb_item, kb_confidence = self.kb_searcher.find_best_match(
            user_message, 
            threshold=0.35  # Низкий порог для текстовых запросов
        )
        
        # Проверяем, был ли это fuzzy match
        is_fuzzy_match = False
        if kb_item and kb_confidence < 0.7:
            # Если уверенность невысокая, проверяем оригинальный вопрос
            original_question = kb_item.get('question', '')
            if original_question.lower() != normalized:
                is_fuzzy_match = True
        
        # Подготовка результата
        result = {
            'original_message': user_message,
            'normalized_message': normalized,
            'intents': intents,
            'keywords': keywords,
            'kb_answer': kb_item.get('answer') if kb_item else None,
            'kb_item': kb_item,
            'kb_confidence': kb_confidence,
            'has_kb_answer': kb_item is not None,
            'is_button_click': False,
            'is_fuzzy_match': is_fuzzy_match
        }
        
        return result
    
    def get_final_answer(self, user_message: str) -> str:
        """Получение финального ответа для пользователя"""
        analysis = self.process_message(user_message)
        
        # Если нашли в базе знаний
        if analysis['has_kb_answer']:
            kb_item = analysis['kb_item']
            answer = kb_item.get('answer', '')
            
            # Для кнопок добавляем специальное оформление
            if analysis.get('is_button_click'):
                source = kb_item.get('source', '')
                button_text = kb_item.get('metadata', {}).get('button_text', '')
                
                if button_text and source in ['menu', 'button']:
                    header = f"🔘 **{button_text}**\n\n"
                    return header + answer
            
            # Для fuzzy match добавляем пояснение
            confidence_percent = int(analysis['kb_confidence'] * 100)
            
            if analysis.get('is_fuzzy_match'):
                original_question = kb_item.get('question', '')
                return f"✅ {answer}\n\n<i>(Возможно, вы имели в виду: '{original_question}'. Найдено с уверенностью {confidence_percent}%)</i>"
            else:
                return f"✅ {answer}\n\n<i>(Найдено в базе знаний с уверенностью {confidence_percent}%)</i>"
        
        # Если ничего не нашли
        suggestions = self._get_search_suggestions(user_message)
        return f"🤔 <b>К сожалению, я не смог найти ответ на ваш вопрос.</b>\n\n{suggestions}"
    
    def _get_search_suggestions(self, query: str) -> str:
        """Получение предложений по поиску"""
        normalized = self.preprocessor.normalize_text(query)
        keywords = self.preprocessor.extract_keywords(normalized)
        
        # Ищем похожие вопросы в базе
        similar_questions = []
        
        for item in self.kb_searcher.kb_data[:10]:  # Проверяем первые 10
            item_question = self.preprocessor.normalize_text(item.get('question', ''))
            
            # Простая проверка совпадения ключевых слов
            item_keywords = self.preprocessor.extract_keywords(item_question)
            common = set(keywords) & set(item_keywords)
            
            if len(common) >= 1 and item_question not in similar_questions:
                similar_questions.append(item_question)
            
            if len(similar_questions) >= 3:
                break
        
        suggestions = "Попробуйте:\n"
        suggestions += "1. Использовать кнопки меню\n"
        suggestions += "2. Переформулировать вопрос\n"
        
        if similar_questions:
            suggestions += "3. Возможно, вам нужен один из этих разделов:\n"
            for i, q in enumerate(similar_questions, 1):
                suggestions += f"   • {q}\n"
        
        suggestions += "4. Обратиться к администратору"
        
        return suggestions

# Создаем глобальный экземпляр NLP-движка
nlp_engine = NLPEngine()
