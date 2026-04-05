from huggingface_hub import InferenceClient
from utils import logger
import config
import random

class HuggingFacePredictor:
    def __init__(self, api_key):
        if api_key:
            try:
                # Используем новый URL для Hugging Face
                self.client = InferenceClient(token=api_key, timeout=30)
                self.available = True
                logger.info("✅ HuggingFace API initialized successfully")
                logger.info("📍 Using endpoint: router.huggingface.co")
            except Exception as e:
                logger.error(f"Failed to initialize HuggingFace: {e}")
                self.available = False
        else:
            self.available = False
            logger.warning("⚠️ HuggingFace API key not provided - using templates only")
    
    def generate_prediction(self, user_data):
        """Генерация предсказания через Hugging Face"""
        if not self.available:
            return None
            
        try:
            user_name = user_data.get('name', 'друг')
            user_question = user_data.get('question', '')
            user_zodiac = user_data.get('zodiac', '')
            
            # Упрощенный промпт для более быстрой генерации
            prompt = f"""Ты — мудрый предсказатель. Напиши предсказание для {user_name}.
Вопрос: {user_question if user_question else 'о будущем'}

Требования:
- 3-4 предложения
- Оптимистичный тон
- На русском языке

Предсказание:"""
            
            # Используем более легкую и стабильную модель
            response = self.client.text_generation(
                prompt,
                model="google/flan-t5-large",
                max_new_tokens=200,
                temperature=0.8,
                do_sample=True,
                wait_for_model=True
            )
            
            if response and len(response.split()) > 15:
                logger.info(f"✅ Hugging Face generated prediction for {user_name}")
                return response.strip()
            return None
                
        except Exception as e:
            logger.error(f"HuggingFace prediction error: {e}")
            return None
    
    def generate_horoscope(self, zodiac_sign):
        """Генерация гороскопа через Hugging Face"""
        if not self.available:
            return None
            
        try:
            prompt = f"""Напиши короткий юмористический гороскоп для знака {zodiac_sign}.
Требования:
- 2-3 предложения
- С юмором
- На русском языке

Гороскоп:"""
            
            response = self.client.text_generation(
                prompt,
                model="google/flan-t5-large",
                max_new_tokens=150,
                temperature=0.85,
                do_sample=True,
                wait_for_model=True
            )
            
            if response and len(response.split()) > 10:
                logger.info(f"✅ Hugging Face generated horoscope for {zodiac_sign}")
                return response.strip()
            return None
                
        except Exception as e:
            logger.error(f"HuggingFace horoscope error: {e}")
            return None

# Инициализация
hf = HuggingFacePredictor(config.HF_API_KEY)