from typing import Optional, Dict, List
import json
from datetime import datetime
from actors.base_actor import BaseActor
from actors.messages import ActorMessage, MESSAGE_TYPES
from actors.events import BaseEvent
from config.prompts import PROMPTS, GENERATION_PARAMS, PROMPT_CONFIG
from config.settings import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_TIMEOUT,
    CACHE_HIT_LOG_INTERVAL
)
from utils.monitoring import measure_latency
from utils.circuit_breaker import CircuitBreaker
from utils.event_utils import EventVersionManager

# Проверка наличия OpenAI SDK
try:
    from openai import AsyncOpenAI
except ImportError:
    raise ImportError("Please install openai: pip install openai")


class GenerationActor(BaseActor):
    """
    Актор для генерации ответов через DeepSeek API.
    Поддерживает JSON-режим, streaming и адаптивные стратегии промптов.
    """
    
    def __init__(self):
        super().__init__("generation", "Generation")
        self._client = None
        self._circuit_breaker = None
        self._generation_count = 0
        self._total_cache_hits = 0
        self._json_failures = 0
        self._event_version_manager = EventVersionManager()
        
    async def initialize(self) -> None:
        """Инициализация клиента DeepSeek"""
        if not DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY not set in config/settings.py")
            
        self._client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            timeout=DEEPSEEK_TIMEOUT
        )
        
        # Circuit Breaker для защиты от сбоев API
        self._circuit_breaker = CircuitBreaker(
            name="deepseek_api",
            failure_threshold=3,
            recovery_timeout=60,
            expected_exception=Exception  # Ловим все ошибки API
        )
        
        self.logger.info("GenerationActor initialized with DeepSeek API")
        
    async def shutdown(self) -> None:
        """Освобождение ресурсов"""
        if self._client:
            await self._client.close()
        self.logger.info(
            f"GenerationActor shutdown. Generated {self._generation_count} responses, "
            f"JSON failures: {self._json_failures}"
        )
        
    @measure_latency
    async def handle_message(self, message: ActorMessage) -> Optional[ActorMessage]:
        """Обработка запроса на генерацию"""
        if message.message_type != MESSAGE_TYPES['GENERATE_RESPONSE']:
            return None
            
        # Извлекаем данные
        user_id = message.payload['user_id']
        chat_id = message.payload['chat_id']
        text = message.payload['text']
        include_prompt = message.payload.get('include_prompt', True)
        
        self.logger.info(f"Generating response for user {user_id}")
        try:
            # Генерируем ответ
            response_text = await self._generate_response(
                text=text,
                user_id=user_id,
                include_prompt=include_prompt
            )
            
            # Создаем ответное сообщение
            self.logger.info(f"Generated response for user {user_id}: {response_text[:50]}...")
            bot_response = ActorMessage.create(
                sender_id=self.actor_id,
                message_type=MESSAGE_TYPES['BOT_RESPONSE'],
                payload={
                    'user_id': user_id,
                    'chat_id': chat_id,
                    'text': response_text,
                    'generated_at': datetime.now().isoformat()
                }
            )
            
            # Отправляем обратно в TelegramActor
            if self.get_actor_system():
                await self.get_actor_system().send_message("telegram", bot_response)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Generation failed for user {user_id}: {str(e)}")
            
            # Создаем сообщение об ошибке
            error_msg = ActorMessage.create(
                sender_id=self.actor_id,
                message_type=MESSAGE_TYPES['ERROR'],
                payload={
                    'user_id': user_id,
                    'chat_id': chat_id,
                    'error': str(e),
                    'error_type': 'generation_error'
                }
            )
            
            # Отправляем в TelegramActor
            if self.get_actor_system():
                await self.get_actor_system().send_message("telegram", error_msg)
            
            return None
    
    async def _generate_response(
        self, 
        text: str, 
        user_id: str,
        include_prompt: bool = True
    ) -> str:
        """Генерация ответа через DeepSeek API"""
        
        # Формируем контекст
        messages = self._format_context(text, include_prompt)
        
        # Определяем режим
        use_json = PROMPT_CONFIG["use_json_mode"]
        
        # Первая попытка
        try:
            response = await self._call_api(messages, use_json)
            
            if use_json:
                # Пытаемся извлечь текст из JSON
                return await self._extract_from_json(response, user_id)
            else:
                return response
                
        except json.JSONDecodeError as e:
            # JSON парсинг не удался
            self._json_failures += 1
            
            # Логируем событие
            await self._log_json_failure(user_id, str(e))
            
            # Проверяем fallback
            if PROMPT_CONFIG["json_fallback_enabled"] and use_json:
                self.logger.warning(f"JSON parse failed for user {user_id}, using fallback")
                
                # Повторяем без JSON
                messages = self._format_context(text, include_prompt, force_normal=True)
                response = await self._call_api(messages, use_json=False)
                return response
            else:
                # Возвращаем сырой ответ
                return response
    
    def _format_context(
        self, 
        text: str, 
        include_prompt: bool,
        force_normal: bool = False
    ) -> List[Dict[str, str]]:
        """Форматирование контекста для API"""
        messages = []
        
        # Системный промпт (если нужен)
        if include_prompt:
            mode = "base"  # Пока только базовый режим
            use_json = PROMPT_CONFIG["use_json_mode"] and not force_normal
            
            prompt_key = "json" if use_json else "normal"
            system_prompt = PROMPTS[mode][prompt_key]
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # TODO: Здесь будет добавление истории из STM (в следующих этапах)
        
        # Сообщение пользователя
        messages.append({
            "role": "user",
            "content": text
        })
        
        return messages
    
    async def _call_api(
        self, 
        messages: List[Dict[str, str]], 
        use_json: bool
    ) -> str:
        """Вызов DeepSeek API через Circuit Breaker"""
        
        async def api_call():
            # Параметры вызова
            kwargs = {
                "model": DEEPSEEK_MODEL,
                "messages": messages,
                "temperature": GENERATION_PARAMS["temperature"],
                "top_p": GENERATION_PARAMS["top_p"],
                "max_tokens": GENERATION_PARAMS["max_tokens"],
                "frequency_penalty": GENERATION_PARAMS.get("frequency_penalty", 0),
                "presence_penalty": GENERATION_PARAMS.get("presence_penalty", 0),
                "stream": True  # Всегда используем streaming
            }
            
            # JSON режим
            if use_json:
                kwargs["response_format"] = {"type": "json_object"}
            
            # Streaming вызов
            response = await self._client.chat.completions.create(**kwargs)
            
            # Собираем ответ из чанков
            full_response = ""
            prompt_cache_hit_tokens = 0
            prompt_cache_miss_tokens = 0
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    
                    # TODO: Отправлять StreamingChunkEvent для UI
                    
                # Извлекаем метрики кэша (если есть)
                if hasattr(chunk, 'usage') and chunk.usage:
                    prompt_cache_hit_tokens = getattr(
                        chunk.usage, 'prompt_cache_hit_tokens', 0
                    )
                    prompt_cache_miss_tokens = getattr(
                        chunk.usage, 'prompt_cache_miss_tokens', 0
                    )
            
            # Логируем метрики кэша
            await self._log_cache_metrics(
                prompt_cache_hit_tokens,
                prompt_cache_miss_tokens
            )
            
            return full_response
        
        # Вызываем через Circuit Breaker
        return await self._circuit_breaker.call(api_call)
    
    async def _extract_from_json(self, response: str, user_id: str) -> str:
        """Извлечение текста из JSON ответа"""
        try:
            # Парсим JSON
            data = json.loads(response)
            
            # Извлекаем поле response
            if isinstance(data, dict) and 'response' in data:
                return data['response']
            else:
                raise ValueError("JSON doesn't contain 'response' field")
                
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to parse JSON for user {user_id}: {str(e)}")
            self.logger.debug(f"Raw response: {response[:200]}...")
            raise
    
    async def _log_cache_metrics(
        self, 
        hit_tokens: int, 
        miss_tokens: int
    ) -> None:
        """Логирование метрик кэша"""
        self._generation_count += 1
        
        # Вычисляем cache hit rate
        total_tokens = hit_tokens + miss_tokens
        if total_tokens > 0:
            cache_hit_rate = hit_tokens / total_tokens
            self._total_cache_hits += cache_hit_rate
            
            # Логируем периодически
            if self._generation_count % CACHE_HIT_LOG_INTERVAL == 0:
                avg_cache_hit = self._total_cache_hits / self._generation_count
                self.logger.info(
                    f"Cache metrics - Generations: {self._generation_count}, "
                    f"Avg hit rate: {avg_cache_hit:.2%}, "
                    f"Last hit rate: {cache_hit_rate:.2%}"
                )
            
            # Создаем событие метрики
            event = BaseEvent.create(
                stream_id="metrics",
                event_type="CacheHitMetricEvent",
                data={
                    "prompt_cache_hit_tokens": hit_tokens,
                    "prompt_cache_miss_tokens": miss_tokens,
                    "cache_hit_rate": cache_hit_rate,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Сохраняем событие
            await self._append_event(event)
    
    async def _log_json_failure(self, user_id: str, error: str) -> None:
        """Логирование сбоя JSON парсинга"""
        event = BaseEvent.create(
            stream_id=f"user_{user_id}",
            event_type="JSONModeFailureEvent",
            data={
                "user_id": user_id,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        await self._append_event(event)
    
    async def _append_event(self, event: BaseEvent) -> None:
        """Добавить событие через менеджер версий"""
        await self._event_version_manager.append_event(event, self.get_actor_system())