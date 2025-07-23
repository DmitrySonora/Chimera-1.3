from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


@dataclass(frozen=True)
class BaseEvent:
    """
    Базовый класс для всех событий в системе.
    Иммутабельный (frozen=True) для предотвращения изменений после создания.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stream_id: str = ""
    event_type: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    version: int = 0
    correlation_id: Optional[str] = None
    
    @classmethod
    def create(cls,
               stream_id: str,
               event_type: str,
               data: Optional[Dict[str, Any]] = None,
               version: int = 0,
               correlation_id: Optional[str] = None) -> 'BaseEvent':
        """Фабричный метод для удобного создания событий"""
        return cls(
            stream_id=stream_id,
            event_type=event_type,
            data=data or {},
            version=version,
            correlation_id=correlation_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация события в словарь для JSON"""
        from config.settings import EVENT_TIMESTAMP_FORMAT
        
        return {
            'event_id': self.event_id,
            'stream_id': self.stream_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp.strftime(EVENT_TIMESTAMP_FORMAT),
            'data': self.data,
            'version': self.version,
            'correlation_id': self.correlation_id
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'BaseEvent':
        """Десериализация события из словаря"""
        from config.settings import EVENT_TIMESTAMP_FORMAT
        
        # Преобразуем timestamp обратно в datetime
        timestamp = datetime.strptime(data['timestamp'], EVENT_TIMESTAMP_FORMAT)
        
        return BaseEvent(
            event_id=data['event_id'],
            stream_id=data['stream_id'],
            event_type=data['event_type'],
            timestamp=timestamp,
            data=data['data'],
            version=data['version'],
            correlation_id=data.get('correlation_id')
        )