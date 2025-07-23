from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from enum import Enum


# Базовые типы сообщений
class MessageType(str, Enum):
    """Типы сообщений в системе акторов"""
    PING = 'ping'
    PONG = 'pong'
    ERROR = 'error'
    SHUTDOWN = 'shutdown'
    DLQ_QUEUED = 'dlq_queued'
    DLQ_PROCESSED = 'dlq_processed'
    DLQ_CLEANUP = 'dlq_cleanup'
    USER_MESSAGE = 'user_message'
    GENERATE_RESPONSE = 'generate_response'
    BOT_RESPONSE = 'bot_response'
    STREAMING_CHUNK = 'streaming_chunk'
    SESSION_CREATED = 'session_created'
    SESSION_UPDATED = 'session_updated'
    CACHE_HIT_METRIC = 'cache_hit_metric'
    PROMPT_INCLUSION = 'prompt_inclusion'
    JSON_MODE_FAILURE = 'json_mode_failure'
    TELEGRAM_MESSAGE_RECEIVED = 'telegram_message_received'
    PROCESS_USER_MESSAGE = 'process_user_message'
    SEND_TELEGRAM_RESPONSE = 'send_telegram_response'


# Для обратной совместимости
MESSAGE_TYPES = {
    'PING': MessageType.PING,
    'PONG': MessageType.PONG,
    'ERROR': MessageType.ERROR,
    'SHUTDOWN': MessageType.SHUTDOWN,
    'DLQ_QUEUED': MessageType.DLQ_QUEUED,
    'DLQ_PROCESSED': MessageType.DLQ_PROCESSED,
    'DLQ_CLEANUP': MessageType.DLQ_CLEANUP,
    'USER_MESSAGE': MessageType.USER_MESSAGE,
    'GENERATE_RESPONSE': MessageType.GENERATE_RESPONSE,
    'BOT_RESPONSE': MessageType.BOT_RESPONSE,
    'STREAMING_CHUNK': MessageType.STREAMING_CHUNK,
    'SESSION_CREATED': MessageType.SESSION_CREATED,
    'SESSION_UPDATED': MessageType.SESSION_UPDATED,
    'CACHE_HIT_METRIC': MessageType.CACHE_HIT_METRIC,
    'PROMPT_INCLUSION': MessageType.PROMPT_INCLUSION,
    'JSON_MODE_FAILURE': MessageType.JSON_MODE_FAILURE,
    'TELEGRAM_MESSAGE_RECEIVED': MessageType.TELEGRAM_MESSAGE_RECEIVED,
    'PROCESS_USER_MESSAGE': MessageType.PROCESS_USER_MESSAGE,
    'SEND_TELEGRAM_RESPONSE': MessageType.SEND_TELEGRAM_RESPONSE
}


@dataclass
class ActorMessage:
    """Базовый класс для всех сообщений между акторами"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: Optional[str] = None
    message_type: str = ''
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def create(cls, 
               sender_id: Optional[str] = None,
               message_type: str = '',
               payload: Optional[Dict[str, Any]] = None) -> 'ActorMessage':
        """Фабричный метод для удобного создания сообщений"""
        return cls(
            sender_id=sender_id,
            message_type=message_type,
            payload=payload or {}
        )