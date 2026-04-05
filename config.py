import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CRYPTOPAY_TOKEN = os.getenv("CRYPTOPAY_TOKEN", "")
HF_API_KEY = os.getenv("HF_API_KEY", "")
PRICE_USDT = float(os.getenv("PRICE_USDT", "0.20"))

TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_database.db")
RENDER_URL = os.getenv("RENDER_URL", "")

print("=" * 50)
print("🚀 FORTUNE BOT CONFIGURATION")
print("=" * 50)
print(f"Bot Token: {'✅ Set' if BOT_TOKEN else '❌ Missing'}")
print(f"CryptoPay: {'✅ Set' if CRYPTOPAY_TOKEN else '❌ Missing'}")
print(f"HuggingFace: {'✅ Set' if HF_API_KEY and HF_API_KEY != 'your_huggingface_key_here' else '❌ Missing'}")
print(f"Test Mode: {'✅ Enabled' if TEST_MODE else '❌ Disabled (REAL PAYMENTS)'}")
print(f"Price: {PRICE_USDT} USDT")
print("=" * 50)