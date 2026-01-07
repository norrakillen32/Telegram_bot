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
    """Улучшенный классификатор намерений пользователя с контекстным анализом"""
    
    def __init__(self):
        # Детальные паттерны намерений с весами и контекстом
        self.intent_patterns = {
            'payment_to_supplier': {
                'primary': ['оплат[иь]т?ь?', 'платеж', 'перечисл[еи]т?ь?', 'списан[ие]', 'выплат[и]т?ь?'],
                'secondary': ['поставщик[уа]?', 'контрагенту', 'поставку', 'за товар[ы]?', 'за услугу'],
                'negative': ['оприход', 'поступл', 'получ[еи]', 'принят', 'товар[ы]? от'],
                'weight': 2.0,
                'threshold': 1.5
            },
            'goods_receipt': {
                'primary': ['оприход[ао]в[а]т?ь?', 'поступл[еи]', 'получ[еи]л?', 'принят[ь]', 'приемк[ау]'],
                'secondary': ['товар[ы]?', 'материал[ы]?', 'тмц', 'от поставщик', 'купил', 'закупил'],
                'negative': ['оплат', 'платеж', 'перечисл', 'деньг', 'списан'],
                'weight': 2.0,
                'threshold': 1.5
            },
            'invoice_creation': {
                'primary': ['накладн[аую]', 'счет[- ]?фактур[уа]?', 'упд', 'торг[- ]?12'],
                'secondary': ['созда[ть]', 'выписат[ь]', 'оформит[ь]', 'провести'],
                'negative': ['оплат', 'получ[еи]л?', 'принял'],
                'weight': 1.8,
                'threshold': 1.3
            },
            'bank_statement': {
                'primary': ['выписк[ау]', 'банковск[аую]', 'загруз[и]т?ь?', 'импорт[и]'],
                'secondary': ['банк[аеу]?', 'счет[ауе]?', 'операци[ий]', 'платеж[еи]'],
                'negative': ['касс', 'наличн'],
                'weight': 1.5,
                'threshold': 1.2
            },
            'cash_operations': {
                'primary': ['касс[ауеы]', 'наличн[ые]', 'пко', 'рко', 'ордер[ау]'],
                'secondary': ['приходн[ой]', 'расходн[ой]', 'выдат[ь]', 'получ[и]т?ь?'],
                'negative': ['безнал', 'банк', 'перечисл'],
                'weight': 1.5,
                'threshold': 1.2
            },
            'report_generation': {
                'primary': ['отчет[ау]?', 'ведомост[ьи]', 'анализ[ау]?', 'статистик[ау]'],
                'secondary': ['сформир[оа]в[а]т?ь?', 'посмотр[е]т?ь?', 'получит[ь]', 'построит[ь]'],
                'negative': ['документ', 'провести', 'создат[ь]'],
                'weight': 1.3,
                'threshold': 1.0
            },
            'debt_analysis': {
                'primary': ['задолженност[ьи]', 'дебиторск[аую]', 'кредиторск[аую]', 'долг[иа]'],
                'secondary': ['посмотр[е]т?ь?', 'проверит[ь]', 'проанализ[и]', 'контрагент'],
                'negative': ['оплат', 'перечисл', 'провести'],
                'weight': 1.4,
                'threshold': 1.1
            },
            'advance_report': {
                'primary': ['авансов[ый]', 'подотчет[н]', 'отчет сотрудник'],
                'secondary': ['созда[ть]', 'заполни[ть]', 'провести', 'сда[ть]'],
                'negative': ['выдат[ь]', 'получ[и]т?ь?', 'деньг[и] под'],
                'weight': 1.4,
                'threshold': 1.1
            },
            'goods_balance': {
                'primary': ['остатк[иау]', 'налич[ие]', 'склад[аеу]', 'запас[ыа]'],
                'secondary': ['товар[ы]?', 'посмотр[е]т?ь?', 'проверит[ь]', 'сколько есть'],
                'negative': ['продаж', 'отгрузк', 'реализац'],
                'weight': 1.3,
                'threshold': 1.0
            },
            'sales_period': {
                'primary': ['продаж[и] по', 'динамик[ау]', 'период[ауы]?', 'месяц[ауы]?'],
                'secondary': ['график', 'тенденц', 'сравнен[ие]'],
                'negative': ['оприход', 'поступл', 'закупк'],
                'weight': 1.3,
                'threshold': 1.0
            },
            'greeting': {
                'primary': ['привет', 'здравствуй', 'добр[ыйое]', 'hello', 'hi', 'здрасте'],
                'secondary': [],
                'negative': [],
                'weight': 3.0,
                'threshold': 0.5
            },
            'farewell': {
                'primary': ['пока', 'до свидан[ия]', 'выход', 'законч[и]т?ь?', 'спасибо'],
                'secondary': [],
                'negative': [],
                'weight': 3.0,
                'threshold': 0.5
            },
            'help_request': {
                'primary': ['помощ[ьи]', 'помог[и]', 'подскаж[и]', 'посовету[йи]'],
                'secondary': ['что ты умееш[ь]', 'команд[ы]', 'инструкц[ия]'],
                'negative': [],
                'weight': 2.5,
                'threshold': 0.8
            },
            'button_click': {
                'primary': ['button:', 'menu:', 'кнопк[ауи]', 'клик[ау]'],
                'secondary': ['нажат[ь]', 'нажм[и]', 'выбрат[ь]', 'нажы', 'кликн[уть]'],
                'negative': [],
                'weight': 2.0,
                'threshold': 0.7
            },
            'unknown': {
                'primary': [],
                'secondary': [],
                'negative': [],
                'weight': 0.0,
                'threshold': 0.0
            }
        }
    
    def classify(self, text: str) -> List[str]:
        """Определение намерений в тексте с учетом контекста"""
        text_lower = text.lower()
        detected_intents = []
        
        # Используем базовый классификатор для совместимости
        for intent_type in ['greeting', 'farewell', 'help_request', 'button_click']:
            if intent_type == 'button_click':
                if 'button:' in text_lower or 'menu:' in text_lower:
                    detected_intents.append('button_click')
            else:
                for pattern in self.intent_patterns[intent_type]['primary']:
                    if re.search(pattern, text_lower):
                        detected_intents.append(intent_type)
                        break
        
        # Если не нашли базовых интентов, используем контекстный анализ
        if not detected_intents:
            main_intent = self._classify_with_context(text_lower)
            detected_intents.append(main_intent)
        
        return detected_intents if detected_intents else ['unknown']
    
    def _classify_with_context(self, text: str) -> str:
        """Контекстная классификация с учетом весов и отрицательных слов"""
        scores = {}
        
        for intent_name, patterns in self.intent_patterns.items():
            if intent_name in ['greeting', 'farewell', 'help_request', 'button_click', 'unknown']:
                continue
                
            score = 0.0
            
            # Проверяем первичные паттерны
            for pattern in patterns['primary']:
                if re.search(pattern, text):
                    score += patterns['weight'] * 2.0
            
            # Проверяем вторичные паттерны
            for pattern in patterns['secondary']:
                if re.search(pattern, text):
                    score += patterns['weight'] * 1.0
            
            # Штрафуем за отрицательные слова
            for pattern in patterns['negative']:
                if re.search(pattern, text):
                    score -= patterns['weight'] * 3.0  # Сильный штраф
            
            scores[intent_name] = max(score, 0.0)
        
        # Находим интент с максимальным счетом
        if scores:
            best_intent = max(scores, key=scores.get)
            if scores[best_intent] >= self.intent_patterns[best_intent]['threshold']:
                return best_intent
        
        return 'unknown'
    
    def classify_with_context(self, text: str) -> Tuple[str, float]:
        """Расширенная классификация с возвратом уверенности"""
        text_lower = text.lower()
        
        # Сначала проверяем базовые интенты
        if 'button:' in text_lower or 'menu:' in text_lower:
            return 'button_click', 1.0
        
        # Контекстный анализ
        scores = {}
        for intent_name, patterns in self.intent_patterns.items():
            if intent_name in ['greeting', 'farewell', 'help_request', 'button_click', 'unknown']:
                continue
                
            score = 0.0
            primary_matches = 0
            secondary_matches = 0
            negative_matches = 0
            
            # Проверяем первичные паттерны
            for pattern in patterns['primary']:
                if re.search(pattern, text_lower):
                    score += patterns['weight'] * 2.0
                    primary_matches += 1
            
            # Проверяем вторичные паттерны
            for pattern in patterns['secondary']:
                if re.search(pattern, text_lower):
                    score += patterns['weight'] * 1.0
                    secondary_matches += 1
            
            # Штрафуем за отрицательные слова
            for pattern in patterns['negative']:
                if re.search(pattern, text_lower):
                    score -= patterns['weight'] * 3.0
                    negative_matches += 1
            
            # Учитываем соотношение совпадений
            total_matches = primary_matches + secondary_matches
            if total_matches > 0:
                match_ratio = primary_matches / total_matches
                score *= (0.5 + match_ratio * 0.5)
            
            scores[intent_name] = max(score, 0.0)
        
        if not scores:
            return 'unknown', 0.0
        
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        threshold = self.intent_patterns[best_intent]['threshold']
        
        # Нормализуем уверенность
        confidence = min(best_score / (threshold * 2), 1.0) if threshold > 0 else 0.5
        
        if best_score >= threshold:
            return best_intent, confidence
        
        return 'unknown', confidence
    
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
    
    def get_intent_description(self, intent_name: str) -> str:
        """Получение описания интента"""
        descriptions = {
            'payment_to_supplier': 'Оплата поставщику',
            'goods_receipt': 'Оприходование товара от поставщика',
            'invoice_creation': 'Создание накладной или счета-фактуры',
            'bank_statement': 'Работа с банковскими выписками',
            'cash_operations': 'Кассовые операции',
            'report_generation': 'Формирование отчетов',
            'debt_analysis': 'Анализ задолженности',
            'advance_report': 'Авансовые отчеты',
            'goods_balance': 'Остатки товаров',
            'sales_period': 'Продажи по периодам',
            'greeting': 'Приветствие',
            'farewell': 'Прощание',
            'help_request': 'Запрос помощи',
            'button_click': 'Нажатие кнопки',
            'unknown': 'Неизвестный запрос'
        }
        return descriptions.get(intent_name, 'Неизвестный интент')

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
    """Основной NLP-движок с улучшенной логикой классификации"""
    
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.intent_classifier = IntentClassifier()  # Используем новый классификатор
        self.kb_searcher = KnowledgeBaseSearcher()
        self.button_handler = ButtonHandler(self.kb_searcher)
    
    def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Полная обработка сообщения пользователя с улучшенной классификацией
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
        
        # Обычная текстовая обработка
        normalized = self.preprocessor.normalize_text(user_message)
        
        # Используем расширенную классификацию с контекстом
        main_intent, intent_confidence = self.intent_classifier.classify_with_context(normalized)
        intent_description = self.intent_classifier.get_intent_description(main_intent)
        
        # Извлечение ключевых слов
        keywords = self.preprocessor.extract_keywords(normalized)
        
        # Поиск в базе знаний с учетом опечаток
        kb_item, kb_confidence = self.kb_searcher.find_best_match(
            user_message, 
            threshold=0.35
        )
        
        # Проверяем, был ли это fuzzy match
        is_fuzzy_match = False
        if kb_item and kb_confidence < 0.7:
            original_question = kb_item.get('question', '')
            if original_question.lower() != normalized:
                is_fuzzy_match = True
        
        # Подготовка результата
        result = {
            'original_message': user_message,
            'normalized_message': normalized,
            'main_intent': main_intent,
            'intent_description': intent_description,
            'intent_confidence': intent_confidence,
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
    
    # Если нашли в базе знаний
    if analysis['has_kb_answer']:
        confidence = analysis['kb_confidence']
        
        # Если уверенность низкая (< 65%), предлагаем уточнить
        if confidence < 0.65:
            return self.get_clarification_response(analysis)
        
        # Если уверенность высокая, показываем обычный ответ
        return self._format_standard_response(analysis)
    
    # Если ничего не нашли
    return self._get_search_suggestions(user_message)
    
    def _get_search_suggestions(self, query: str) -> str:
        """Получение предложений по поиску"""
        normalized = self.preprocessor.normalize_text(query)
        keywords = self.preprocessor.extract_keywords(normalized)
        
        # Определяем основной интент для более точных предложений
        main_intent, _ = self.intent_classifier.classify_with_context(normalized)
        intent_desc = self.intent_classifier.get_intent_description(main_intent)
        
        # Ищем похожие вопросы в базе
        similar_questions = []
        
        for item in self.kb_searcher.kb_data[:15]:  # Проверяем первые 15
            item_question = self.preprocessor.normalize_text(item.get('question', ''))
            
            # Проверяем совпадение ключевых слов
            item_keywords = self.preprocessor.extract_keywords(item_question)
            common = set(keywords) & set(item_keywords)
            
            if len(common) >= 1 and item_question not in similar_questions:
                similar_questions.append(item.get('question', ''))
            
            if len(similar_questions) >= 3:
                break
        
        suggestions = "Попробуйте:\n"
        suggestions += "1. Использовать кнопки меню\n"
        suggestions += f"2. Уточнить вопрос по теме: {intent_desc}\n"
        
        if similar_questions:
            suggestions += "3. Возможно, вам нужен один из этих разделов:\n"
            for i, q in enumerate(similar_questions, 1):
                suggestions += f"   • {q}\n"
        
        suggestions += "4. Обратиться к администратору"
        
        return suggestions
        
    def get_clarification_response(self, analysis: Dict) -> str:
        """Универсальная генерация уточняющего ответа"""
        kb_item = analysis.get('kb_item')
        original_q = kb_item.get('question', '') if kb_item else ''
        
        # Получаем категории из тегов вопроса
        item_tags = kb_item.get('tags', []) if kb_item else []
        
        # Ищем вопросы в тех же категориях
        category_questions = self._get_questions_by_categories(
            item_tags, 
            exclude_id=kb_item.get('id') if kb_item else None
        )
        
        # Формируем интерактивное сообщение
        return self._create_interactive_clarification(
            original_q,
            category_questions,
            analysis.get('intent_description', '')
        )
    
    def _get_questions_by_categories(
        self, 
        categories: List[str], 
        exclude_id: Optional[int] = None,
        limit: int = 4
    ) -> List[Dict]:
        """Получение вопросов по категориям (тегам)"""
        if not categories:
            return []
        
        categorized_items = []
        
        for item in self.kb_searcher.kb_data:
            if exclude_id and item.get('id') == exclude_id:
                continue
                
            item_tags = item.get('tags', [])
            common_tags = set(categories) & set(item_tags)
            
            if common_tags:
                # Вычисляем степень релевантности
                relevance_score = len(common_tags) / len(categories)
                
                categorized_items.append({
                    'item': item,
                    'relevance': relevance_score,
                    'question': item.get('question', ''),
                    'tags': item_tags
                })
        
        # Сортируем по релевантности
        categorized_items.sort(key=lambda x: x['relevance'], reverse=True)
        
        return categorized_items[:limit]
    
    def _create_interactive_clarification(
        self, 
        original_question: str,
        alternative_questions: List[Dict],
        intent_description: str
    ) -> str:
        """Создание интерактивного уточняющего сообщения"""
        
        if not alternative_questions:
            # Базовый вариант, если нет альтернатив
            return (
                "🤔 **Мне нужно уточнение.**\n\n"
                f"Я думаю, вы имеете в виду: **«{original_question}»**\n\n"
                "*Если это не так, пожалуйста, переформулируйте вопрос.*"
            )
        
        # Формируем список альтернатив с эмодзи
        alternatives_text = []
        for i, alt in enumerate(alternative_questions, 1):
            question = alt['question']
            tags_preview = ", ".join(alt.get('tags', [])[:2]) if alt.get('tags') else ""
            
            if tags_preview:
                alternatives_text.append(f"{i}. 🔹 **{question}** *({tags_preview})*")
            else:
                alternatives_text.append(f"{i}. 🔹 **{question}**")
        
        # Определяем общую категорию
        if intent_description and intent_description != 'Неизвестный запрос':
            category_info = f"**Категория:** {intent_description}\n"
        else:
            category_info = ""
        
        # Собираем финальное сообщение
        message = (
            f"🔍 **Нужно уточнение**\n\n"
            f"{category_info}"
            f"Я нашел несколько вариантов, которые могут подходить:\n\n"
            f"{chr(10).join(alternatives_text)}\n\n"
            f"**Какой вариант вам нужен?**\n"
            f"• Напишите номер (1-{len(alternative_questions)})\n"
            f"• Или опишите задачу другими словами\n"
            f"• Используйте кнопки меню для точного выбора\n\n"
            f"*Самый похожий вопрос: «{original_question}»*"
        )
        
        return message        
# Создаем глобальный экземпляр NLP-движка
nlp_engine = NLPEngine()
