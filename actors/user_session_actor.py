from typing import Dict, Optional
from datetime import datetime
from actors.base_actor import BaseActor
from actors.messages import ActorMessage, MESSAGE_TYPES
from actors.events import BaseEvent
from config.prompts import PROMPT_CONFIG
from utils.monitoring import measure_latency
from utils.event_utils import EventVersionManager

class UserSession:
    """Данные сессии пользователя"""
    def __init__(self, user_id: str, username: Optional[str] = None):
        self.user_id = user_id
        self.username = username
        self.message_count = 0
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.cache_metrics = []  # Для адаптивной стратегии
        
        # Расширяемость для будущего
        self.emotional_state = None  # Для PerceptionActor
        self.style_vector = None     # Для PersonalityActor
        self.memory_buffer = []      # Для MemoryActor


class UserSessionActor(BaseActor):
    """
    Координатор сессий пользователей.
    Управляет жизненным циклом сессий и определяет необходимость системного промпта.
    """
    
    def __init__(self):
        super().__init__("user_session", "UserSession")
        self._sessions: Dict[str, UserSession] = {}
        self._event_version_manager = EventVersionManager()
        
    async def initialize(self) -> None:
        """Инициализация актора"""
        self.logger.info("UserSessionActor initialized")
        
    async def shutdown(self) -> None:
        """Освобождение ресурсов"""
        session_count = len(self._sessions)
        self._sessions.clear()
        self.logger.info(f"UserSessionActor shutdown, cleared {session_count} sessions")
        
    @measure_latency
    async def handle_message(self, message: ActorMessage) -> Optional[ActorMessage]:
        """Обработка входящих сообщений"""
        
        # Обработка USER_MESSAGE
        if message.message_type == MESSAGE_TYPES['USER_MESSAGE']:
            generate_msg = await self._handle_user_message(message)
            # Отправляем в GenerationActor
            if generate_msg and self.get_actor_system():
                await self.get_actor_system().send_message("generation", generate_msg)
            
        # Обработка метрик кэша для адаптивной стратегии
        elif message.message_type == MESSAGE_TYPES['CACHE_HIT_METRIC']:
            await self._update_cache_metrics(message)
            
        return None
    
    async def _handle_user_message(self, message: ActorMessage) -> ActorMessage:
        """Обработка сообщения от пользователя"""
        user_id = message.payload['user_id']
        username = message.payload.get('username')
        text = message.payload['text']
        chat_id = message.payload['chat_id']
        
        # Получаем или создаем сессию
        session = await self._get_or_create_session(user_id, username)
        
        # Обновляем счетчики
        session.message_count += 1
        session.last_activity = datetime.now()
        
        # Определяем необходимость системного промпта
        include_prompt = self._should_include_prompt(session)
        
        # Логируем решение о промпте
        if include_prompt:
            prompt_event = BaseEvent.create(
                stream_id=f"user_{user_id}",
                event_type="PromptInclusionEvent",
                data={
                    "user_id": user_id,
                    "message_count": session.message_count,
                    "strategy": PROMPT_CONFIG["prompt_strategy"],
                    "reason": self._get_prompt_reason(session)
                }
            )
            await self._append_event(prompt_event)
        
        # Создаем сообщение для GenerationActor
        generate_msg = ActorMessage.create(
            sender_id=self.actor_id,
            message_type=MESSAGE_TYPES['GENERATE_RESPONSE'],
            payload={
                'user_id': user_id,
                'chat_id': chat_id,
                'text': text,
                'include_prompt': include_prompt,
                'message_count': session.message_count,
                'session_data': {
                    'username': session.username,
                    'created_at': session.created_at.isoformat()
                }
            }
        )
        
        self.logger.info(f"Created GENERATE_RESPONSE for user {user_id}")
        return generate_msg
    
    async def _get_or_create_session(self, user_id: str, username: Optional[str]) -> UserSession:
        """Получить существующую или создать новую сессию"""
        if user_id not in self._sessions:
            session = UserSession(user_id, username)
            self._sessions[user_id] = session
            
            # Событие о создании сессии
            event = BaseEvent.create(
                stream_id=f"user_{user_id}",
                event_type="SessionCreatedEvent",
                data={
                    "user_id": user_id,
                    "username": username,
                    "created_at": session.created_at.isoformat()
                }
            )
            
            # Сохраняем событие
            await self._append_event(event)
            
            self.logger.info(f"Created new session for user {user_id}")
        
        return self._sessions[user_id]
    
    def _should_include_prompt(self, session: UserSession) -> bool:
        """Определить необходимость включения системного промпта"""
        strategy = PROMPT_CONFIG["prompt_strategy"]
        
        if not PROMPT_CONFIG["enable_periodic_prompt"]:
            return True  # Всегда включать если периодичность отключена
            
        if strategy == "always":
            return True
            
        elif strategy == "periodic":
            # Каждое N-ое сообщение
            interval = PROMPT_CONFIG["system_prompt_interval"]
            return session.message_count % interval == 1
            
        elif strategy == "adaptive":
            # Адаптивная стратегия на основе метрик
            if session.message_count % PROMPT_CONFIG["system_prompt_interval"] == 1:
                return True  # Базовая периодичность
                
            # Проверяем метрики кэша
            if len(session.cache_metrics) >= 5:
                avg_cache_hit = sum(session.cache_metrics[-5:]) / 5
                if avg_cache_hit < PROMPT_CONFIG["cache_hit_threshold"]:
                    # Cache hit rate слишком низкий, включаем промпт
                    return True
                    
        return False
    
    def _get_prompt_reason(self, session: UserSession) -> str:
        """Получить причину включения промпта для логирования"""
        strategy = PROMPT_CONFIG["prompt_strategy"]
        
        if strategy == "always":
            return "always_strategy"
        elif strategy == "periodic":
            return f"periodic_interval_{PROMPT_CONFIG['system_prompt_interval']}"
        elif strategy == "adaptive":
            if len(session.cache_metrics) >= 5:
                avg_cache_hit = sum(session.cache_metrics[-5:]) / 5
                if avg_cache_hit < PROMPT_CONFIG["cache_hit_threshold"]:
                    return f"low_cache_hit_rate_{avg_cache_hit:.2f}"
            return "adaptive_periodic"
        
        return "unknown"
    
    async def _update_cache_metrics(self, message: ActorMessage) -> None:
        """Обновить метрики кэша для адаптивной стратегии"""
        user_id = message.payload.get('user_id')
        if not user_id or user_id not in self._sessions:
            return
            
        session = self._sessions[user_id]
        cache_hit_rate = message.payload.get('cache_hit_rate', 0.0)
        
        # Сохраняем метрику
        session.cache_metrics.append(cache_hit_rate)
        
        # Ограничиваем размер истории
        if len(session.cache_metrics) > 20:
            session.cache_metrics = session.cache_metrics[-20:]
    
    async def _append_event(self, event: BaseEvent) -> None:
        """Добавить событие через менеджер версий"""
        await self._event_version_manager.append_event(event, self.get_actor_system())