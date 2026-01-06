import json
import re
import pickle
import numpy as np
from typing import Tuple, Optional, Dict, List
from collections import defaultdict
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
import os

class TextPreprocessor:
    """Предобработка текста с расширенными функциями"""
    
    def __init__(self):
        # Расширенный список стоп-слов для русского языка
        self.stop_words = set([
            'и', 'в', 'на', 'о', 'а', 'но', 'что', 'как', 'я', 'вы', 'мы', 
            'они', 'этот', 'тот', 'весь', 'все', 'из', 'по', 'для', 'без', 
            'над', 'под', 'про', 'при', 'до', 'после', 'через', 'у', 'с', 
            'со', 'к', 'ко', 'за', 'же', 'бы', 'ли', 'ну', 'вот', 'тут', 
            'там', 'здесь', 'туда', 'очень', 'просто', 'вообще', 'совсем',
            'может', 'можно', 'нужно', 'должен', 'стоит', 'еще', 'уже', 'опять'
        ])
    
    def normalize(self, text: str) -> str:
        """Нормализация текста"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """Токенизация с фильтрацией стоп-слов"""
        tokens = text.split()
        return [token for token in tokens if token not in self.stop_words and len(token) > 2]
    
    def get_ngrams(self, text: str, n: int = 2) -> List[str]:
        """Генерация n-грамм"""
        tokens = self.tokenize(text)
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngrams.append(' '.join(tokens[i:i+n]))
        return ngrams

class KnowledgeBaseManager:
    """Управление базой знаний с версионированием"""
    
    def __init__(self, file_path: str = "knowledge_base.json"):
        self.file_path = file_path
        self.data = []
        self.version = 1
        self.load()
    
    def load(self):
        """Загрузка базы знаний"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self.version += 1
            print(f"База знаний загружена. Записей: {len(self.data)}")
        except FileNotFoundError:
            print(f"Файл {self.file_path} не найден. Создана новая база.")
            self.data = []
        except json.JSONDecodeError as e:
            print(f"Ошибка чтения JSON: {e}")
            self.data = []
    
    def save(self):
        """Сохранение базы знаний"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"База знаний сохранена. Записей: {len(self.data)}")
    
    def add_entry(self, question: str, answer: str, tags: List[str] = None, 
                  source: str = "manual", metadata: Dict = None):
        """Добавление новой записи в базу"""
        entry = {
            'id': len(self.data) + 1,
            'question': question,
            'answer': answer,
            'tags': tags or [],
            'source': source,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat(),
            'version': self.version
        }
        self.data.append(entry)
        self.save()
        return entry
    
    def search_by_id(self, entry_id: int) -> Optional[Dict]:
        """Поиск записи по ID"""
        for entry in self.data:
            if entry['id'] == entry_id:
                return entry
        return None
    
    def update_entry(self, entry_id: int, **kwargs):
        """Обновление существующей записи"""
        for entry in self.data:
            if entry['id'] == entry_id:
                entry.update(kwargs)
                entry['updated_at'] = datetime.now().isoformat()
                self.save()
                return True
        return False
    
    def get_statistics(self) -> Dict:
        """Получение статистики по базе знаний"""
        return {
            'total_entries': len(self.data),
            'sources': defaultdict(int, {entry['source']: 
                       sum(1 for e in self.data if e['source'] == entry['source']) 
                       for entry in self.data}),
            'latest_version': self.version,
            'last_updated': max([entry.get('created_at', '') for entry in self.data], default='')
        }

class NLPTrainer:
    """Обучение и дообучение NLP-моделей"""
    
    def __init__(self, model_path: str = "nlp_model.pkl"):
        self.model_path = model_path
        self.preprocessor = TextPreprocessor()
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.9,
            stop_words=list(self.preprocessor.stop_words)
        )
        self.nn_model = NearestNeighbors(
            n_neighbors=5,
            metric='cosine',
            algorithm='auto'
        )
        self.is_trained = False
        self.training_data = []
        self.load_model()
    
    def prepare_training_data(self, knowledge_base: List[Dict]) -> Tuple[List[str], List[str]]:
        """Подготовка данных для обучения"""
        questions = []
        answers = []
        
        for entry in knowledge_base:
            # Основной вопрос
            questions.append(entry['question'])
            answers.append(entry['answer'])
            
            # Добавляем вариации вопросов
            if 'variations' in entry.get('metadata', {}):
                for variation in entry['metadata']['variations']:
                    questions.append(variation)
                    answers.append(entry['answer'])
            
            # Добавляем n-граммы
            ngrams = self.preprocessor.get_ngrams(entry['question'], n=2)
            for ngram in ngrams[:3]:  # Берем первые 3 n-граммы
                questions.append(ngram)
                answers.append(entry['answer'])
        
        return questions, answers
    
    def train(self, knowledge_base: List[Dict], incremental: bool = False):
        """Обучение модели"""
        print(f"Начало обучения. Записей: {len(knowledge_base)}")
        
        questions, answers = self.prepare_training_data(knowledge_base)
        
        if not questions:
            print("Нет данных для обучения")
            return False
        
        # Векторизация вопросов
        X = self.vectorizer.fit_transform(questions)
        
        # Обучение модели ближайших соседей
        self.nn_model.fit(X)
        
        # Сохранение данных
        self.training_data = list(zip(questions, answers))
        self.is_trained = True
        
        print(f"Модель обучена. Образцов: {len(questions)}")
        
        # Сохранение модели
        self.save_model()
        
        return True
    
    def incremental_train(self, new_entries: List[Dict]):
        """Инкрементальное обучение на новых данных"""
        if not self.is_trained:
            return self.train(new_entries)
        
        # Добавляем новые данные
        for entry in new_entries:
            self.training_data.append((entry['question'], entry['answer']))
        
        # Переобучение
        questions, answers = zip(*self.training_data) if self.training_data else ([], [])
        
        if questions:
            X = self.vectorizer.fit_transform(questions)
            self.nn_model.fit(X)
            self.save_model()
            print(f"Модель дообучена. Всего образцов: {len(questions)}")
    
    def predict(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """Поиск похожих вопросов"""
        if not self.is_trained:
            return []
        
        # Преобразование запроса
        query_vec = self.vectorizer.transform([query])
        
        # Поиск ближайших соседей
        distances, indices = self.nn_model.kneighbors(query_vec, n_neighbors=top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.training_data):
                question, answer = self.training_data[idx]
                confidence = 1.0 - dist  # Преобразование расстояния в уверенность
                results.append((answer, confidence))
        
        return results
    
    def save_model(self):
        """Сохранение модели в файл"""
        model_data = {
            'vectorizer': self.vectorizer,
            'nn_model': self.nn_model,
            'training_data': self.training_data,
            'is_trained': self.is_trained
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"Модель сохранена в {self.model_path}")
    
    def load_model(self):
        """Загрузка модели из файла"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.vectorizer = model_data['vectorizer']
                self.nn_model = model_data['nn_model']
                self.training_data = model_data['training_data']
                self.is_trained = model_data['is_trained']
                print(f"Модель загружена из {self.model_path}")
                return True
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
        
        return False
    
    def evaluate(self, test_questions: List[str], test_answers: List[str]) -> Dict:
        """Оценка качества модели"""
        if not self.is_trained:
            return {'error': 'Модель не обучена'}
        
        correct = 0
        confidences = []
        
        for query, expected_answer in zip(test_questions, test_answers):
            results = self.predict(query, top_k=1)
            if results:
                predicted_answer, confidence = results[0]
                if predicted_answer == expected_answer:
                    correct += 1
                confidences.append(confidence)
        
        accuracy = correct / len(test_questions) if test_questions else 0
        avg_confidence = np.mean(confidences) if confidences else 0
        
        return {
            'accuracy': accuracy,
            'avg_confidence': avg_confidence,
            'total_tests': len(test_questions),
            'correct': correct
        }

class QuestionAnalyzer:
    """Анализ вопросов пользователя"""
    
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        
        # Паттерны для извлечения сущностей
        self.patterns = {
            'document': re.compile(r'(накладн|счет|акт|договор|ордер|отчет)', re.IGNORECASE),
            'action': re.compile(r'(созда|удали|измени|проведи|отмени|найди)', re.IGNORECASE),
            'number': re.compile(r'\b(\d+)\b'),
            'date': re.compile(r'\b(\d{1,2}[./]\d{1,2}[./]\d{2,4})\b')
        }
        
        # Шаблоны вопросов
        self.question_templates = [
            (r'как (создать|сделать|оформить)', 'how_to_create'),
            (r'где (найти|посмотреть|взять)', 'where_to_find'),
            (r'почему (не|нет)', 'why_not'),
            (r'что (такое|значит)', 'what_is'),
            (r'когда (будет|можно)', 'when_will'),
        ]
    
    def analyze(self, question: str) -> Dict:
        """Полный анализ вопроса"""
        normalized = self.preprocessor.normalize(question)
        tokens = self.preprocessor.tokenize(question)
        
        # Извлечение сущностей
        entities = {}
        for entity_type, pattern in self.patterns.items():
            matches = pattern.findall(question)
            if matches:
                entities[entity_type] = matches
        
        # Определение типа вопроса
        question_type = 'general'
        for pattern, q_type in self.question_templates:
            if re.search(pattern, question, re.IGNORECASE):
                question_type = q_type
                break
        
        # Определение сложности
        complexity = 'simple'
        if len(tokens) > 8 or len(entities) > 2:
            complexity = 'complex'
        elif any(word in question for word in ['почему', 'зачем', 'каким образом']):
            complexity = 'complex'
        
        return {
            'original': question,
            'normalized': normalized,
            'tokens': tokens,
            'entities': entities,
            'question_type': question_type,
            'complexity': complexity,
            'token_count': len(tokens),
            'has_entities': bool(entities)
        }

class LearningFeedbackSystem:
    """Система обратной связи для улучшения модели"""
    
    def __init__(self, feedback_path: str = "feedback.json"):
        self.feedback_path = feedback_path
        self.feedback_data = self.load_feedback()
    
    def load_feedback(self):
        """Загрузка данных обратной связи"""
        try:
            with open(self.feedback_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'correct_responses': [],
                'incorrect_responses': [],
                'user_corrections': [],
                'confidence_stats': []
            }
    
    def save_feedback(self):
        """Сохранение обратной связи"""
        with open(self.feedback_path, 'w', encoding='utf-8') as f:
            json.dump(self.feedback_data, f, ensure_ascii=False, indent=2)
    
    def add_feedback(self, user_question: str, bot_answer: str, 
                    correct: bool, user_correction: str = None, 
                    confidence: float = None):
        """Добавление обратной связи"""
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'question': user_question,
            'answer': bot_answer,
            'correct': correct,
            'user_correction': user_correction,
            'confidence': confidence
        }
        
        if correct:
            self.feedback_data['correct_responses'].append(feedback_entry)
        else:
            self.feedback_data['incorrect_responses'].append(feedback_entry)
            
            if user_correction:
                self.feedback_data['user_corrections'].append({
                    **feedback_entry,
                    'correction': user_correction
                })
        
        if confidence is not None:
            self.feedback_data['confidence_stats'].append({
                'timestamp': datetime.now().isoformat(),
                'confidence': confidence,
                'correct': correct
            })
        
        # Ограничиваем размер данных
        for key in self.feedback_data:
            if isinstance(self.feedback_data[key], list):
                self.feedback_data[key] = self.feedback_data[key][-1000:]
        
        self.save_feedback()
        return feedback_entry
    
    def get_learning_suggestions(self) -> List[Dict]:
        """Получение предложений для обучения на основе обратной связи"""
        suggestions = []
        
        # Анализ неправильных ответов
        incorrect_entries = self.feedback_data['incorrect_responses'][-50:]  # Последние 50
        
        for entry in incorrect_entries:
            if entry.get('user_correction'):
                suggestion = {
                    'type': 'correction',
                    'question': entry['question'],
                    'current_answer': entry['answer'],
                    'correct_answer': entry['user_correction'],
                    'priority': 'high',
                    'reason': 'Пользователь исправил ответ'
                }
                suggestions.append(suggestion)
        
        # Анализ ответов с низкой уверенностью
        low_confidence = [e for e in self.feedback_data.get('confidence_stats', []) 
                         if e.get('confidence', 1) < 0.3]
        
        for entry in low_confidence[-20:]:  # Последние 20
            suggestion = {
                'type': 'low_confidence',
                'priority': 'medium',
                'reason': f'Низкая уверенность модели: {entry.get("confidence", 0):.2f}'
            }
            suggestions.append(suggestion)
        
        return suggestions

class AdvancedNLPSearch:
    """Расширенный поиск с обучением и анализом"""
    
    def __init__(self):
        self.kb_manager = KnowledgeBaseManager()
        self.nlp_trainer = NLPTrainer()
        self.question_analyzer = QuestionAnalyzer()
        self.feedback_system = LearningFeedbackSystem()
        
        # Инициализация или загрузка модели
        if not self.nlp_trainer.is_trained and self.kb_manager.data:
            print("Обучение модели на существующей базе знаний...")
            self.nlp_trainer.train(self.kb_manager.data)
    
    def search(self, user_question: str, threshold: float = 0.5) -> Dict:
        """Основной метод поиска с анализом"""
        # Анализ вопроса
        analysis = self.question_analyzer.analyze(user_question)
        
        # Поиск в базе знаний
        results = self.nlp_trainer.predict(user_question, top_k=3)
        
        best_answer = None
        best_confidence = 0.0
        
        if results:
            best_answer, best_confidence = results[0]
        
        # Проверка порога уверенности
        if best_confidence >= threshold:
            response_type = 'kb_match'
        else:
            response_type = 'fallback'
            best_answer = self._get_fallback_response(user_question, analysis)
        
        return {
            'answer': best_answer,
            'confidence': best_confidence,
            'response_type': response_type,
            'analysis': analysis,
            'suggestions': self._generate_suggestions(user_question, analysis)
        }
    
    def _get_fallback_response(self, question: str, analysis: Dict) -> str:
        """Запасной ответ, если не найдено в базе"""
        # Можно добавить более умные fallback-ответы
        templates = {
            'how_to_create': "Инструкция по созданию этого документа находится в разделе справки 1С.",
            'where_to_find': "Этот элемент интерфейса расположен в основном меню программы.",
            'why_not': "Проверьте настройки прав доступа и состояние документа.",
            'general': f"По запросу '{question}' я не нашел точного ответа в базе знаний."
        }
        
        return templates.get(analysis['question_type'], templates['general'])
    
    def _generate_suggestions(self, question: str, analysis: Dict) -> List[str]:
        """Генерация предложений для пользователя"""
        suggestions = []
        
        if analysis['complexity'] == 'complex':
            suggestions.append("Попробуйте разбить вопрос на несколько простых.")
        
        if not analysis['has_entities']:
            suggestions.append("Уточните, о каком документе или операции идет речь.")
        
        if analysis['token_count'] < 3:
            suggestions.append("Задайте более подробный вопрос.")
        
        return suggestions
    
    def learn_from_feedback(self, user_question: str, bot_answer: str, 
                           is_correct: bool, correct_answer: str = None):
        """Обучение на основе обратной связи"""
        # Сохраняем обратную связь
        confidence = 0.8  # Примерная уверенность
        
        feedback = self.feedback_system.add_feedback(
            user_question, bot_answer, is_correct, correct_answer, confidence
        )
        
        # Если ответ был неправильный и есть исправление
        if not is_correct and correct_answer:
            # Добавляем исправление в базу знаний
            self.kb_manager.add_entry(
                question=user_question,
                answer=correct_answer,
                tags=['corrected'],
                source='user_feedback',
                metadata={
                    'original_answer': bot_answer,
                    'correction_date': datetime.now().isoformat()
                }
            )
            
            # Дообучаем модель на новом примере
            new_entry = {
                'question': user_question,
                'answer': correct_answer
            }
            self.nlp_trainer.incremental_train([new_entry])
            
            return {
                'action': 'model_updated',
                'feedback_id': feedback['timestamp'],
                'new_entry_id': len(self.kb_manager.data)
            }
        
        return {'action': 'feedback_recorded', 'feedback_id': feedback['timestamp']}
    
    def add_knowledge(self, question: str, answer: str, tags: List[str] = None):
        """Добавление новых знаний в систему"""
        entry = self.kb_manager.add_entry(question, answer, tags)
        
        # Дообучаем модель
        self.nlp_trainer.incremental_train([{
            'question': question,
            'answer': answer
        }])
        
        return entry
    
    def get_system_stats(self) -> Dict:
        """Получение статистики системы"""
        kb_stats = self.kb_manager.get_statistics()
        feedback_stats = {
            'total_feedback': len(self.feedback_system.feedback_data['correct_responses']) +
                             len(self.feedback_system.feedback_data['incorrect_responses']),
            'accuracy_rate': None
        }
        
        total = feedback_stats['total_feedback']
        correct = len(self.feedback_system.feedback_data['correct_responses'])
        
        if total > 0:
            feedback_stats['accuracy_rate'] = correct / total
        
        return {
            'knowledge_base': kb_stats,
            'model': {
                'is_trained': self.nlp_trainer.is_trained,
                'training_samples': len(self.nlp_trainer.training_data),
                'last_trained': datetime.now().isoformat()
            },
            'feedback': feedback_stats,
            'learning_suggestions': len(self.feedback_system.get_learning_suggestions())
        }
    
    def export_training_data(self, file_path: str = "training_export.json"):
        """Экспорт данных для обучения"""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'knowledge_base': self.kb_manager.data,
            'training_samples': self.nlp_trainer.training_data,
            'feedback_summary': {
                'total_feedback': len(self.feedback_system.feedback_data['correct_responses']) +
                                 len(self.feedback_system.feedback_data['incorrect_responses']),
                'user_corrections': len(self.feedback_system.feedback_data['user_corrections'])
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return export_data

# Создаем глобальный экземпляр системы NLP
nlp_system = AdvancedNLPSearch()

# Функции для удобства использования
def search_answer(question: str, threshold: float = 0.5) -> str:
    """Поиск ответа на вопрос"""
    result = nlp_system.search(question, threshold)
    return result['answer']

def add_new_knowledge(question: str, answer: str, tags: List[str] = None) -> Dict:
    """Добавление новых знаний"""
    return nlp_system.add_knowledge(question, answer, tags)

def process_feedback(question: str, bot_answer: str, 
                    is_correct: bool, correct_answer: str = None) -> Dict:
    """Обработка обратной связи"""
    return nlp_system.learn_from_feedback(question, bot_answer, is_correct, correct_answer)

def get_system_status() -> Dict:
    """Получение статуса системы"""
    return nlp_system.get_system_stats()
