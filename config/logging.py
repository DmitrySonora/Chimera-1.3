import logging
import sys
from pathlib import Path
from pythonjsonlogger import jsonlogger
from config.settings import (
    LOG_LEVEL, 
    LOG_FORMAT, 
    LOG_DATE_FORMAT,
    ENABLE_JSON_LOGGING,
    JSON_LOG_FILE,
    LOG_ROTATION_ENABLED,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT
)
from logging.handlers import RotatingFileHandler


def setup_logging():
    """Настройка системы логирования с поддержкой текстового и JSON форматов"""
    # Создаем директорию для логов если её нет
    if ENABLE_JSON_LOGGING:
        log_dir = Path(JSON_LOG_FILE).parent
        log_dir.mkdir(exist_ok=True)
    
    # Создаем форматтеры
    text_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt=LOG_DATE_FORMAT
    )
    
    # Создаем обработчик для вывода в консоль (текстовый формат)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(text_formatter)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    root_logger.addHandler(console_handler)
    
    # Добавляем JSON обработчик если включен
    if ENABLE_JSON_LOGGING:
        if LOG_ROTATION_ENABLED:
            # Используем RotatingFileHandler для автоматической ротации
            json_handler = RotatingFileHandler(
                JSON_LOG_FILE,
                maxBytes=LOG_MAX_BYTES,
                backupCount=LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
        else:
            # Обычный FileHandler без ротации
            json_handler = logging.FileHandler(JSON_LOG_FILE, encoding='utf-8')
        
        json_handler.setFormatter(json_formatter)
        root_logger.addHandler(json_handler)
    
    # Отключаем лишние логи от библиотек
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Получить логгер с указанным именем"""
    return logging.getLogger(name)