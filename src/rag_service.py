"""
RAG Service для Telegram бота
"""
import logging
import json
from typing import List, Dict, Any, Tuple
import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import SearchRequest, Filter, FieldCondition, MatchValue
import ollama

from config import Config

logger = logging.getLogger(__name__)


class RAGService:
    """Сервис для RAG (Retrieval-Augmented Generation)"""
    
    def __init__(self, config: Config):
        """
        Инициализация RAG сервиса
        
        Args:
            config: Конфигурация приложения
        """
        self.config = config
        self.qdrant_client = QdrantClient(url=config.qdrant_url)
        self.ollama_client = ollama.Client(host=config.ollama_url)
        
        logger.info(f"RAG Service инициализирован. Qdrant: {config.qdrant_url}, Коллекция: {config.qdrant_collection}")
    
    def embed_query(self, query: str) -> List[float]:
        """
        Векторизация запроса пользователя через Ollama
        
        Args:
            query: Текст запроса
            
        Returns:
            Вектор эмбеддинга
        """
        try:
            response = self.ollama_client.embeddings(
                model=self.config.ollama_embedding_model,
                prompt=query
            )
            embedding = response['embedding']
            logger.info(f"Запрос векторизован. Размерность: {len(embedding)}")
            return embedding
        except Exception as e:
            logger.error(f"Ошибка при векторизации запроса: {e}")
            raise
    
    def search_context(self, query_vector: List[float]) -> List[Dict[str, Any]]:
        """
        Поиск релевантных фрагментов документации в Qdrant
        
        Args:
            query_vector: Вектор запроса
            
        Returns:
            Список найденных документов с метаданными и скорами
        """
        try:
            # Используем правильный API метод для qdrant-client >= 1.7
            search_results = self.qdrant_client.query_points(
                collection_name=self.config.qdrant_collection,
                query=query_vector,
                limit=self.config.top_k,
                score_threshold=self.config.score_threshold
            )
            
            contexts = []
            for result in search_results.points:
                contexts.append({
                    'text': result.payload.get('text', ''),
                    'score': result.score,
                    'id': result.id
                })
                logger.debug(f"Найден фрагмент ID={result.id}, score={result.score:.3f}")
            
            logger.info(
                f"Найдено {len(contexts)} релевантных фрагментов "
                f"(порог: {self.config.score_threshold}, top_k: {self.config.top_k})"
            )
            
            if len(contexts) > 0:
                scores = [ctx['score'] for ctx in contexts]
                logger.info(f"Диапазон скоров: {min(scores):.3f} - {max(scores):.3f}")
            
            return contexts
            
        except Exception as e:
            logger.error(f"Ошибка при поиске в Qdrant: {e}")
            raise
    
    def generate_answer(self, question: str, contexts: List[Dict[str, Any]]) -> Tuple[str, bool]:
        """
        Генерация ответа через OpenRouter API
        
        Args:
            question: Вопрос пользователя
            contexts: Список релевантных контекстов
            
        Returns:
            Tuple[str, bool]: (Ответ в формате markdown, Флаг успешности поиска)
        """
        # Формируем контекст из найденных фрагментов
        context_text = "\n\n".join([
            f"Фрагмент {i+1} (релевантность: {ctx['score']:.2f}):\n{ctx['text']}" for i, ctx in enumerate(contexts)
        ])
        
        # Формируем промпт с требованием JSON ответа
        prompt = f"""Ты - эксперт по системе UEM SafeMobile. Отвечай на вопросы пользователей, основываясь на документации.

Выдержки из документации:
{context_text}

Вопрос пользователя: {question}

ФОРМАТ ОТВЕТА - СТРОГО JSON без дополнительного текста:
{{
  "success": true/false,
  "answer": "твой ответ в markdown"
}}

ПРАВИЛА:
1. Если документация содержит ответ на вопрос → success: true
2. Если информации нет или она не релевантна → success: false
3. Отвечай как эксперт:
   ✅ ПРАВИЛЬНО: "Системные требования включают: PostgreSQL 12+, 8GB RAM..."
   ❌ НЕПРАВИЛЬНО: "В предоставленном контексте указано, что..."
   ❌ НЕПРАВИЛЬНО: "Согласно документации..."
4. Используй markdown: **жирный**, *курсив*, `код`, списки, заголовки
5. Структурируй ответ понятно и логично
6. Если success=false, кратко объясни что именно не найдено"""
        
        logger.info(f"Сформирован промпт. Длина: {len(prompt)} символов, контекстов: {len(contexts)}")
        logger.info(f"Полный промпт:\n{'-'*50}\n{prompt}\n{'-'*50}")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config.openrouter_api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": self.config.openrouter_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.config.openrouter_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                
                raw_answer = response.json()['choices'][0]['message']['content']
                logger.info(f"Получен ответ от LLM. Длина: {len(raw_answer)} символов")
                logger.debug(f"Сырой ответ:\n{raw_answer}")
                
                # Парсим JSON ответ
                try:
                    # Убираем возможные markdown блоки кода вокруг JSON
                    json_str = raw_answer.strip()
                    if json_str.startswith('```'):
                        # Убираем ```json и ```
                        json_str = json_str.split('```')[1]
                        if json_str.startswith('json'):
                            json_str = json_str[4:]
                        json_str = json_str.strip()
                    
                    response_data = json.loads(json_str)
                    success = response_data.get('success', False)
                    answer = response_data.get('answer', '')
                    
                    logger.info(f"Ответ распарсен. Success: {success}, длина ответа: {len(answer)}")
                    return answer, success
                    
                except json.JSONDecodeError as je:
                    logger.error(f"Ошибка парсинга JSON ответа: {je}")
                    logger.error(f"Сырой ответ был: {raw_answer}")
                    # Возвращаем сырой ответ как есть
                    return raw_answer, False
            
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа через OpenRouter: {e}")
            raise
    
    def answer_question(self, question: str) -> Tuple[str, bool]:
        """
        Основной метод для получения ответа на вопрос
        
        Args:
            question: Вопрос пользователя
            
        Returns:
            Tuple[str, bool]: (Ответ на вопрос, Флаг успешности)
        """
        try:
            # Шаг 1: Векторизация запроса
            logger.info(f"Обработка вопроса: {question}")
            query_vector = self.embed_query(question)
            
            # Шаг 2: Поиск контекста
            contexts = self.search_context(query_vector)
            
            if not contexts:
                logger.warning("Не найдено ни одного релевантного фрагмента")
                return "К сожалению, я не нашел релевантной информации в документации для ответа на ваш вопрос.", False
            
            # Шаг 3: Генерация ответа
            answer, success = self.generate_answer(question, contexts)
            
            # Если LLM вернула success=False, добавляем отбивку
            if not success:
                logger.info("LLM не смогла найти релевантный ответ в контексте")
                fallback_message = "❌ **Не удалось найти ответ в документации**\n\n"
                if answer:
                    fallback_message += f"_{answer}_"
                else:
                    fallback_message += "_Предоставленные фрагменты документации не содержат информации для ответа на ваш вопрос._"
                return fallback_message, False
            
            return answer, success
            
        except Exception as e:
            error_msg = f"Произошла ошибка при обработке вопроса: {str(e)}"
            logger.error(error_msg)
            return "⚠️ Извините, произошла ошибка при обработке вашего вопроса. Попробуйте позже.", False

