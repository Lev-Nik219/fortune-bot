from huggingface_hub import InferenceClient
from utils import logger
import config
import random

class HuggingFacePredictor:
    def __init__(self, api_key):
        if api_key:
            try:
                self.client = InferenceClient(token=api_key)
                self.available = True
                logger.info("✅ HuggingFace API initialized successfully")
                # Тестовый запрос для проверки
                try:
                    test = self.client.text_generation(
                        "Test",
                        model="HuggingFaceH4/zephyr-7b-beta",
                        max_new_tokens=5
                    )
                    logger.info("✅ HuggingFace API test passed")
                except Exception as test_e:
                    logger.warning(f"HuggingFace API test failed: {test_e}")
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
            
            # Используем более стабильную модель
            prompt = f"""Ты — мудрый и добрый предсказатель. Напиши предсказание для {user_name}.
Вопрос: {user_question if user_question else 'о будущем'}
Знак зодиака: {user_zodiac if user_zodiac else 'не указан'}

Требования:
- Используй имя человека
- Напиши 3-4 предложения
- Будь оптимистичен и вдохновляющ
- Язык: русский

Предсказание:"""
            
            response = self.client.text_generation(
                prompt,
                model="HuggingFaceH4/zephyr-7b-beta",  # Более стабильная модель
                max_new_tokens=200,
                temperature=0.8,
                do_sample=True
            )
            
            if response and len(response.split()) > 20:
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
            prompt = f"""Напиши юмористический гороскоп для знака {zodiac_sign} на сегодня.
Требования:
- Короткий, 2-3 предложения
- С юмором и легкой иронией
- Язык: русский

Гороскоп:"""
            
            response = self.client.text_generation(
                prompt,
                model="HuggingFaceH4/zephyr-7b-beta",
                max_new_tokens=150,
                temperature=0.85,
                do_sample=True
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