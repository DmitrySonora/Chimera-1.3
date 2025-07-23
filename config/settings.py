import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


# Лимиты для демо-доступа
DAILY_MESSAGE_LIMIT = 10  # Количество сообщений в день для неавторизованных

# Actor System настройки
ACTOR_SYSTEM_NAME = "chimera"
ACTOR_MESSAGE_QUEUE_SIZE = 1000     # Максимальный размер очереди сообщений
ACTOR_SHUTDOWN_TIMEOUT = 5.0        # Секунды
ACTOR_MESSAGE_TIMEOUT = 1.0         # Таймаут ожидания сообщения в message loop

# Retry настройки
ACTOR_MESSAGE_RETRY_ENABLED = True  # Включить retry механизм
ACTOR_MESSAGE_MAX_RETRIES = 3       # Максимальное количество попыток
ACTOR_MESSAGE_RETRY_DELAY = 0.1     # Начальная задержка между попытками (сек)
ACTOR_MESSAGE_RETRY_MAX_DELAY = 2.0 # Максимальная задержка между попытками (сек)

# Circuit Breaker настройки
CIRCUIT_BREAKER_ENABLED = True          # Включить Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5   # Количество ошибок для открытия
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60   # Время восстановления в секундах

# Логирование
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# JSON логирование
ENABLE_JSON_LOGGING = True  # Включить JSON логирование параллельно с текстовым
JSON_LOG_FILE = "logs/chimera.json"  # Путь к файлу JSON логов

# Ротация логов
LOG_ROTATION_ENABLED = True  # Включить ротацию файлов логов
LOG_MAX_BYTES = 1 * 1024 * 1024  # Максимальный размер файла логов (1 МБ)
LOG_BACKUP_COUNT = 5  # Количество архивных файлов логов

# Мониторинг
ENABLE_PERFORMANCE_METRICS = True
METRICS_LOG_INTERVAL = 60  # Секунды
SLOW_OPERATION_THRESHOLD = 0.1  # Порог для медленных операций (секунды)

# Dead Letter Queue настройки
DLQ_MAX_SIZE = 1000  # Максимальный размер очереди перед автоочисткой
DLQ_CLEANUP_INTERVAL = 3600  # Интервал очистки в секундах (1 час)
DLQ_METRICS_ENABLED = True  # Включить метрики DLQ

# Event Store настройки
EVENT_STORE_TYPE = "memory"              # Тип хранилища (будет "postgres" в фазе 3)
EVENT_STORE_MAX_MEMORY_EVENTS = 10000    # Максимум событий в памяти
EVENT_STORE_STREAM_CACHE_SIZE = 100      # Размер LRU кэша потоков
EVENT_STORE_CLEANUP_INTERVAL = 3600      # Интервал очистки старых событий (сек)
EVENT_STORE_CLEANUP_BATCH_SIZE = 100     # Размер батча при очистке

# Сериализация событий
EVENT_SERIALIZATION_FORMAT = "json"
EVENT_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

# DeepSeek API настройки
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_TIMEOUT = 30  # Секунды
DEEPSEEK_MAX_RETRIES = 3

# Telegram Bot настройки
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_POLLING_TIMEOUT = 30
TELEGRAM_TYPING_UPDATE_INTERVAL = 5
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
TELEGRAM_TYPING_CLEANUP_THRESHOLD = 100  # Порог для очистки завершенных typing задач
TELEGRAM_API_DEFAULT_TIMEOUT = 10        # Таймаут по умолчанию для API вызовов
TELEGRAM_MAX_TYPING_TASKS = 1000         # Максимальное количество одновременных typing задач

# Метрики и адаптивная стратегия
CACHE_HIT_LOG_INTERVAL = 10
MIN_CACHE_HIT_RATE = 0.5
