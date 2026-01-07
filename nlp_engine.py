import json
import re
from typing import Tuple, Optional, Dict, List, Any
import difflib

class TextPreprocessor:
    """Предобработка текста пользователя с учетом опечаток"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Нормализация текста: нижний регистр, удаление лишних символов"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
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

class FuzzySearcher:
    """Нечеткий поиск с учетом опечаток"""
    
    @staticmethod
    def fuzzy_ratio(text1: str, text2: str) -> float:
        """Расчет схожести текстов с учетом опечаток"""
        base_ratio = difflib.SequenceMatcher(None, text1, text2).ratio()
        words1 = text1.split()
        words2 = text2.split()
        word_overlap = len(set(words1) & set(words2)) / max(len(set(words1)), 1)
        first_letter_score = 0
        if words1 and words2:
            if words1[0][0] == words2[0][0]:
                first_letter_score = 0.2
        fuzzy_score = (base_ratio * 0.6) + (word_overlap * 0.3) + (first_letter_score * 0.1)
        return fuzzy_score

class KnowledgeBaseSearcher:
    """Поиск в локальной базе знаний с учетом опечаток"""
    
    def __init__(self, file_path: str = "knowledge_base.json"):
        self.file_path = file_path
        self.kb_data = self._load_knowledge_base()
        self.preprocessor = TextPreprocessor()
        self.fuzzy_searcher = FuzzySearcher()
        self.question_index = self._build_index()
    
    def _load_knowledge_base(self) -> List[Dict]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ База знаний загружена: {len(data)} записей")
                return data
        except FileNotFoundError:
            print(f"⚠️ Файл {self.file_path} не найден")
            return []
        except json.JSONDecodeError as e:
            print(f"⚠️ Ошибка чтения JSON: {e}")
            return []
        except Exception as e:
            print(f"⚠️ Ошибка загрузки базы знаний: {e}")
            return []
    
    def _build_index(self) -> Dict[str, List[Dict]]:
        index = {}
        for item in self.kb_data:
            question = item.get('question', '')
            normalized = self.preprocessor.normalize_text(question)
            keywords = self.preprocessor.extract_keywords(normalized)
            for keyword in keywords:
                if keyword not in index:
                    index[keyword] = []
                index[keyword].append(item)
        return index
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        return self.fuzzy_searcher.fuzzy_ratio(text1, text2)
    
    def find_best_match(
        self, 
        user_question: str, 
        source_type: Optional[str] = None,
        threshold: float = 0.4
    ) -> Tuple[Optional[Dict], float]:
        if not self.kb_data:
            return None, 0.0
        
        normalized_question = self.preprocessor.normalize_text(user_question)
        keywords = self.preprocessor.extract_keywords(normalized_question)
        
        best_item = None
        best_confidence = 0.0
        
        candidate_items = set()
        for keyword in keywords:
            if keyword in self.question_index:
                candidate_items.update(self.question_index[keyword])
        
        if not candidate_items:
            candidate_items = self.kb_data
        
        for item in candidate_items:
            item_question = item.get('question', '')
            item_source = item.get('source', 'manual')
            
            if source_type and item_source != source_type:
                continue
            
            normalized_item = self.preprocessor.normalize_text(item_question)
            similarity = self._calculate_similarity(normalized_question, normalized_item)
            
            item_keywords = self.preprocessor.extract_keywords(normalized_item)
            common_keywords = set(keywords) & set(item_keywords)
            keyword_overlap = len(common_keywords) / max(len(keywords), 1)
            
            confidence = (similarity * 0.6) + (keyword_overlap * 0.4)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_item = item
        
        if best_confidence >= threshold:
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
        text_lower = text.lower()
        detected_intents = []
        for intent, keywords in self.intents.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected_intents.append(intent)
                    break
        return detected_intents if detected_intents else ['unknown']
    
    def is_button_click(self, text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        text_lower = text.lower()
        
        for prefix in ['button:', 'menu:']:
            if text_lower.startswith(prefix):
                parts = text_lower.split(':', 1)
                if len(parts) == 2:
                    return True, prefix.rstrip(':'), parts[1].strip()
        
        button_patterns = [
            (['нажать кнопку', 'нажми кнопку', 'нажы кнопку', 'нажатькнопку'], 'button'),
            (['клик по кнопке', 'кликнуть кнопку', 'клик по', 'кликнуть'], 'button'),
            (['в меню', 'меню', 'в разедел', 'разедел'], 'menu'),
            (['раздел', 'раздил', 'радел'], 'menu')
        ]
        
        for patterns, source_type in button_patterns:
            for pattern in patterns:
                if pattern in text_lower:
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
        normalized_button = self.preprocessor.normalize_text(button_text)
        
        exact_match = self.kb_searcher.find_by_exact_question(
            normalized_button, 
            source_type=source_type
        )
        
        if exact_match:
            return exact_match
        
        fuzzy_match, confidence = self.kb_searcher.find_best_match(
            normalized_button,
            source_type=source_type,
            threshold=0.3
        )
        
        if fuzzy_match and confidence >= 0.3:
            return fuzzy_match
        
        any_match, confidence = self.kb_searcher.find_best_match(
            normalized_button,
            threshold=0.35
        )
        
        if any_match:
            return any_match
        
        return None

class NLPEngine:
    """Основной NLP-движок"""
    
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.intent_classifier = IntentClassifier()
        self.kb_searcher = KnowledgeBaseSearcher()
        self.button_handler = ButtonHandler(self.kb_searcher)
        self._current_options = {}
    
    def process_message(self, user_message: str) -> Dict[str, Any]:
        print(f"\n📨 Получено сообщение: '{user_message}'")
        
        is_button_click, source_type, button_text = self.intent_classifier.is_button_click(user_message)
        
        if is_button_click and source_type and button_text:
            print(f"🎯 Определено как нажатие кнопки: {source_type} -> '{button_text}'")
            
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
        
        normalized = self.preprocessor.normalize_text(user_message)
        intents = self.intent_classifier.classify(normalized)
        keywords = self.preprocessor.extract_keywords(normalized)
        
        kb_item, kb_confidence = self.kb_searcher.find_best_match(
            user_message, 
            threshold=0.35
        )
        
        is_fuzzy_match = False
        if kb_item and kb_confidence < 0.7:
            original_question = kb_item.get('question', '')
            if original_question.lower() != normalized:
                is_fuzzy_match = True
        
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
        analysis = self.process_message(user_message)
        
        if analysis['has_kb_answer']:
            kb_item = analysis['kb_item']
            answer = kb_item.get('answer', '')
            confidence = analysis['kb_confidence']
            
            # Если уверенность низкая (< 65%), предлагаем уточнить
            if confidence < 0.65:
                clarification_response = self.get_clarification_response(analysis)
                return clarification_response
            
            # Для кнопок добавляем специальное оформление
            if analysis.get('is_button_click'):
                source = kb_item.get('source', '')
                button_text = kb_item.get('metadata', {}).get('button_text', '')
                
                if button_text and source in ['menu', 'button']:
                    header = f"🔘 **{button_text}**\n\n"
                    return header + answer
            
            # Для fuzzy match добавляем пояснение
            confidence_percent = int(confidence * 100)
            
            if analysis.get('is_fuzzy_match'):
                original_question = kb_item.get('question', '')
                return f"✅ {answer}\n\n<i>(Возможно, вы имели в виду: '{original_question}'. Найдено с уверенностью {confidence_percent}%)</i>"
            else:
                return f"✅ {answer}\n\n<i>(Найдено в базе знаний с уверенностью {confidence_percent}%)</i>"
        
        suggestions = self._get_search_suggestions(user_message)
        return f"🤔 <b>К сожалению, я не смог найти ответ на ваш вопрос.</b>\n\n{suggestions}"
    
    def get_clarification_response(self, analysis: Dict) -> str:
        kb_item = analysis.get('kb_item')
        if not kb_item:
            return "Извините, произошла ошибка при обработке вашего запроса."
        
        original_q = kb_item.get('question', '')
        item_tags = kb_item.get('tags', [])
        item_id = kb_item.get('id')
        
        # Ищем вопросы в тех же категориях
        category_questions = self._get_questions_by_categories(
            item_tags, 
            exclude_id=item_id,
            min_relevance=0.2
        )
        
        # Формируем интерактивное сообщение
        return self._create_interactive_clarification(
            original_q,
            category_questions,
            "Неизвестный запрос",
            user_query=analysis.get('original_message', '')
        )
    
    def _get_questions_by_categories(
        self, 
        categories: List[str], 
        exclude_id: Optional[int] = None,
        limit: int = 4,
        min_relevance: float = 0.1
    ) -> List[Dict]:
        if not categories:
            return []
        
        categorized_items = []
        
        for item in self.kb_searcher.kb_data:
            if exclude_id and item.get('id') == exclude_id:
                continue
                
            item_tags = item.get('tags', [])
            common_tags = set(categories) & set(item_tags)
            
            if common_tags:
                relevance_score = len(common_tags) / len(categories)
                
                if relevance_score >= min_relevance:
                    categorized_items.append({
                        'item': item,
                        'relevance': relevance_score,
                        'question': item.get('question', ''),
                        'tags': item_tags
                    })
        
        categorized_items.sort(key=lambda x: x['relevance'], reverse=True)
        return categorized_items[:limit]
    
    def _create_interactive_clarification(
        self, 
        original_question: str,
        alternative_questions: List[Dict],
        intent_description: str,
        user_query: str = ""
    ) -> str:
        if not alternative_questions:
            return (
                "🤔 **Мне нужно уточнение.**\n\n"
                f"По вашему запросу **«{user_query[:50]}...»** я нашел:\n"
                f"**«{original_question}»**\n\n"
                "*Если это не то, что вам нужно, попробуйте:*\n"
                "• Использовать другие ключевые слова\n"
                "• Обратиться к разделам меню\n"
                "• Сформулировать вопрос более конкретно"
            )
        
        alternatives_text = []
        option_counter = 1
        option_map = {}
        
        for alt in alternative_questions[:3]:
            question = alt['question']
            tags_preview = ", ".join(alt.get('tags', [])[:2]) if alt.get('tags') else ""
            
            option_map[option_counter] = alt
            if tags_preview:
                alternatives_text.append(f"{option_counter}. 🔹 **{question}** *({tags_preview})*")
            else:
                alternatives_text.append(f"{option_counter}. 🔹 **{question}**")
            option_counter += 1
        
        self._current_options = option_map
        
        message = (
            f"🔍 **Нужно уточнение**\n\n"
            f"По вашему запросу я нашел несколько вариантов:\n\n"
            f"{chr(10).join(alternatives_text)}\n\n"
            f"**Какой вариант вам нужен?**\n"
            f"• Ответьте номером (1-{option_counter-1}) для быстрого выбора\n"
            f"• Или переформулируйте запрос более конкретно\n"
            f"• Используйте кнопки меню для точного выбора\n\n"
            f"*Текущий запрос: «{user_query}»*"
        )
        
        return message
    
    def _get_search_suggestions(self, query: str) -> str:
        normalized = self.preprocessor.normalize_text(query)
        keywords = self.preprocessor.extract_keywords(normalized)
        
        similar_questions = []
        
        for item in self.kb_searcher.kb_data[:10]:
            item_question = self.preprocessor.normalize_text(item.get('question', ''))
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
    
    def get_option_selection(self, option_number: int) -> Optional[str]:
        """Обработка выбора опции пользователем"""
        if option_number in self._current_options:
            selected = self._current_options[option_number]
            item = selected['item']
            answer = item.get('answer', '')
            source = item.get('source', '')
            
            if source in ['button', 'menu']:
                button_text = item.get('metadata', {}).get('button_text', '')
                return f"🔘 **{button_text}**\n\n{answer}"
            else:
                return answer
        
        return None   
# Создаем глобальный экземпляр NLP-движка
nlp_engine = NLPEngine()
