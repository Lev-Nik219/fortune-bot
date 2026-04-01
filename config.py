import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CRYPTOPAY_TOKEN = os.getenv("CRYPTOPAY_TOKEN", "")
HF_API_KEY = os.getenv("HF_API_KEY", "")

# Стоимость предсказания в USDT
PRICE_USDT = 0.10

# Режим тестирования
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# Настройки деплоя
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_database.db")

# URL для вебхука (на Render)
RENDER_URL = os.getenv("RENDER_URL", "")
WEBHOOK_URL = f"{RENDER_URL}/webhook" if RENDER_URL else None

# Выводим информацию
print("=" * 50)
print("🚀 FORTUNE BOT CONFIGURATION")
print("=" * 50)
print(f"Bot Token: {'✅ Set' if BOT_TOKEN else '❌ Missing'}")
print(f"CryptoPay: {'✅ Set' if CRYPTOPAY_TOKEN else '❌ Missing'}")
print(f"HuggingFace: {'✅ Set' if HF_API_KEY else '❌ Missing'}")
print(f"Test Mode: {'✅ Enabled' if TEST_MODE else '❌ Disabled'}")
print(f"Price: {PRICE_USDT} USDT")
print("=" * 50)