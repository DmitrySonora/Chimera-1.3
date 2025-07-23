"""
Главный файл запуска Telegram бота Химера
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.logging import setup_logging
from config.settings import DEEPSEEK_API_KEY, TELEGRAM_BOT_TOKEN
from actors.actor_system import ActorSystem
from actors.events import EventStore

# Импортируем наши акторы
from actors.user_session_actor import UserSessionActor
from actors.generation_actor import GenerationActor  
from actors.telegram_actor import TelegramInterfaceActor


async def main():
    """Главная функция запуска бота"""
    # Настраиваем логирование
    setup_logging()
    
    # Проверяем конфигурацию
    if not DEEPSEEK_API_KEY:
        print("ERROR: Please set DEEPSEEK_API_KEY in config/settings.py")
        return
        
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: Please set TELEGRAM_BOT_TOKEN in config/settings.py")
        return
    
    print("=== Starting Chimera Bot ===")
    
    # Создаем систему акторов
    system = ActorSystem("chimera-bot")
    
    # Создаем Event Store
    event_store = EventStore()
    system.set_event_store(event_store)
    
    # Создаем акторы
    session_actor = UserSessionActor()
    generation_actor = GenerationActor()
    telegram_actor = TelegramInterfaceActor()
    
    # Регистрируем акторы
    await system.register_actor(session_actor)
    await system.register_actor(generation_actor)
    await system.register_actor(telegram_actor)
    
    # Запускаем систему
    await system.start()
    
    print("=== Chimera Bot is running ===")
    print("Press Ctrl+C to stop")
    
    try:
        # Бесконечный цикл
        while True:
            await asyncio.sleep(60)
            
            # Периодически выводим метрики
            dlq_metrics = system.get_dlq_metrics()
            if dlq_metrics['current_size'] > 0:
                print(f"DLQ: {dlq_metrics['current_size']} messages")
                
    except KeyboardInterrupt:
        print("\n=== Stopping Chimera Bot ===")
        
    finally:
            
        # Останавливаем систему
        await system.stop()
        print("=== Chimera Bot stopped ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown completed")