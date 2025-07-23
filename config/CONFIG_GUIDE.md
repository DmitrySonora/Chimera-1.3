# Руководство по конфигурации Химера 2.0

## Actor System

### Основные настройки
- `ACTOR_SYSTEM_NAME` - имя системы акторов для логирования (по умолчанию: "chimera")
- `ACTOR_MESSAGE_QUEUE_SIZE` - максимальный размер очереди сообщений для каждого актора (по умолчанию: 1000)
- `ACTOR_SHUTDOWN_TIMEOUT` - время ожидания graceful shutdown в секундах (по умолчанию: 5.0)
- `ACTOR_MESSAGE_TIMEOUT` - таймаут ожидания нового сообщения в message loop (по умолчанию: 1.0)

### Retry механизм
- `ACTOR_MESSAGE_RETRY_ENABLED` - включить механизм повторной отправки сообщений при переполнении очереди (по умолчанию: True)
- `ACTOR_MESSAGE_MAX_RETRIES` - максимальное количество попыток отправки сообщения (по умолчанию: 3)
- `ACTOR_MESSAGE_RETRY_DELAY` - начальная задержка между попытками в секундах (по умолчанию: 0.1)
- `ACTOR_MESSAGE_RETRY_MAX_DELAY` - максимальная задержка между попытками в секундах (по умолчанию: 2.0)

### Dead Letter Queue
- `DLQ_MAX_SIZE` - максимальный размер Dead Letter Queue перед автоочисткой (по умолчанию: 1000)
- `DLQ_CLEANUP_INTERVAL` - интервал автоматической очистки DLQ в секундах (по умолчанию: 3600)
- `DLQ_METRICS_ENABLED` - включить сбор метрик по Dead Letter Queue (по умолчанию: True)

## Логирование

### Основные настройки
- `LOG_LEVEL` - уровень логирования (DEBUG, INFO, WARNING, ERROR) (по умолчанию: "INFO")
- `LOG_FORMAT` - формат сообщений логов (по умолчанию: "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
- `LOG_DATE_FORMAT` - формат даты в логах (по умолчанию: "%Y-%m-%d %H:%M:%S")

### JSON логирование
- `ENABLE_JSON_LOGGING` - включить JSON логирование параллельно с текстовым (по умолчанию: True)
- `JSON_LOG_FILE` - путь к файлу JSON логов (по умолчанию: "logs/chimera.json")

### Ротация логов
- `LOG_ROTATION_ENABLED` - включить автоматическую ротацию файлов логов (по умолчанию: True)
- `LOG_MAX_BYTES` - максимальный размер файла логов в байтах перед ротацией (по умолчанию: 1048576 = 1 МБ)
- `LOG_BACKUP_COUNT` - количество архивных файлов логов для хранения (по умолчанию: 5)

## Мониторинг

### Метрики производительности
- `ENABLE_PERFORMANCE_METRICS` - включить сбор метрик производительности (по умолчанию: True)
- `METRICS_LOG_INTERVAL` - интервал логирования метрик в секундах (по умолчанию: 60)
- `SLOW_OPERATION_THRESHOLD` - порог в секундах для определения медленных операций (по умолчанию: 0.1)

## Event Store

### Основные настройки
- `EVENT_STORE_TYPE` - тип хранилища событий: "memory" для in-memory, будет "postgres" в фазе 3 (по умолчанию: "memory")
- `EVENT_STORE_MAX_MEMORY_EVENTS` - максимальное количество событий в памяти перед автоочисткой (по умолчанию: 10000)
- `EVENT_STORE_STREAM_CACHE_SIZE` - размер LRU кэша для часто используемых потоков событий (по умолчанию: 100)
- `EVENT_STORE_CLEANUP_INTERVAL` - интервал автоматической очистки старых событий в секундах (по умолчанию: 3600)
- `EVENT_STORE_CLEANUP_BATCH_SIZE` - количество событий удаляемых за одну операцию очистки (по умолчанию: 100)

### Сериализация событий
- `EVENT_SERIALIZATION_FORMAT` - формат сериализации событий (по умолчанию: "json")
- `EVENT_TIMESTAMP_FORMAT` - формат timestamp для сериализации событий (по умолчанию: "%Y-%m-%dT%H:%M:%S.%fZ")

## Примечания

1. **Retry механизм** использует exponential backoff - каждая следующая попытка происходит через удвоенное время, но не более `ACTOR_MESSAGE_RETRY_MAX_DELAY`.

2. **Dead Letter Queue** сохраняет сообщения, которые не удалось доставить после всех попыток. Автоочистка удаляет старые сообщения при превышении `DLQ_MAX_SIZE`.

3. **Метрики производительности** логируются только для операций, превышающих `SLOW_OPERATION_THRESHOLD` секунд.

4. **Ротация логов** автоматически архивирует файл логов при достижении `LOG_MAX_BYTES`. Архивные файлы именуются как `chimera.json.1`, `chimera.json.2` и т.д. Когда количество архивов превышает `LOG_BACKUP_COUNT`, самый старый файл удаляется.

## DeepSeek API

### Основные настройки
- `DEEPSEEK_API_KEY` - API ключ для доступа к DeepSeek (обязательный)
- `DEEPSEEK_BASE_URL` - базовый URL API (по умолчанию: "https://api.deepseek.com/v1")
- `DEEPSEEK_MODEL` - модель для использования (по умолчанию: "deepseek-chat")
- `DEEPSEEK_TIMEOUT` - таймаут запросов в секундах (по умолчанию: 30)
- `DEEPSEEK_MAX_RETRIES` - максимальное количество попыток при ошибках (по умолчанию: 3)

## Telegram Bot

### Основные настройки
- `TELEGRAM_BOT_TOKEN` - токен бота от BotFather (обязательный)
- `TELEGRAM_POLLING_TIMEOUT` - таймаут long polling в секундах (по умолчанию: 30)
- `TELEGRAM_TYPING_UPDATE_INTERVAL` - интервал обновления typing индикатора (по умолчанию: 5)
- `TELEGRAM_MAX_MESSAGE_LENGTH` - максимальная длина сообщения Telegram (по умолчанию: 4096)
- `TELEGRAM_TYPING_CLEANUP_THRESHOLD` - количество typing операций до автоматической очистки завершенных задач (по умолчанию: 100)
- `TELEGRAM_API_DEFAULT_TIMEOUT` - таймаут по умолчанию для вызовов Telegram API в секундах (по умолчанию: 10)
- `TELEGRAM_MAX_TYPING_TASKS` - максимальное количество одновременных typing индикаторов для защиты от переполнения памяти (по умолчанию: 1000)

## Промпты и генерация

### Параметры генерации
- `GENERATION_PARAMS` - словарь параметров для DeepSeek:
  - `temperature` - креативность ответов (0.0-2.0)
  - `top_p` - nucleus sampling параметр (0.0-1.0)
  - `max_tokens` - максимальная длина ответа
  - `frequency_penalty` - штраф за повторения
  - `presence_penalty` - штраф за упоминание тем

### Управление промптами
- `PROMPT_CONFIG` - настройки системного промпта:
  - `system_prompt_interval` - включать промпт каждое N сообщение
  - `enable_periodic_prompt` - включить периодичность
  - `prompt_strategy` - стратегия: "always", "periodic", "adaptive"
  - `use_json_mode` - использовать JSON формат ответов
  - `json_fallback_enabled` - автоматический fallback при ошибке JSON

## Метрики и адаптация

- `CACHE_HIT_LOG_INTERVAL` - частота логирования cache hit rate
- `MIN_CACHE_HIT_RATE` - минимальный приемлемый cache hit rate для адаптивной стратегии