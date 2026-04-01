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
                logger.info("✅ HuggingFace API initialized")
            except Exception as e:
                logger.error(f"Failed to initialize HuggingFace: {e}")
                self.available = False
        else:
            self.available = False
            logger.warning("HuggingFace API key not provided")
    
    def generate_prediction(self, user_data):
        """Генерация предсказания (минимум 3 предложения)"""
        if not self.available:
            return None
            
        try:
            user_name = user_data.get('name', 'друг')
            user_question = user_data.get('question', '')
            user_zodiac = user_data.get('zodiac', '')
            
            prompt = f"""Ты – мудрый и добрый предсказатель. Напиши предсказание для {user_name}.
Вопрос: {user_question if user_question else 'о будущем'}
Знак зодиака: {user_zodiac if user_zodiac else 'не указан'}

Требования:
- Используй имя человека
- Напиши минимум 3 предложения
- Будь оптимистичен, вдохновляющ
- Язык: русский

Предсказание:"""
            
            response = self.client.text_generation(
                prompt,
                model="google/flan-t5-large",
                max_new_tokens=250,
                temperature=0.85,
                do_sample=True
            )
            
            if response and len(response.split()) > 20:
                return response.strip()
            return None
                
        except Exception as e:
            logger.error(f"HuggingFace prediction error: {e}")
            return None
    
    def generate_horoscope(self, zodiac_sign):
        """Генерация гороскопа (минимум 3 предложения)"""
        if not self.available:
            return None
            
        try:
            prompt = f"""Напиши развёрнутый гороскоп для знака {zodiac_sign} на сегодня.
Требования:
- Юмористический, с лёгкой иронией
- Минимум 3 предложения
- Язык: русский

Гороскоп:"""
            
            response = self.client.text_generation(
                prompt,
                model="google/flan-t5-large",
                max_new_tokens=200,
                temperature=0.9,
                do_sample=True
            )
            
            if response and len(response.split()) > 15:
                return response.strip()
            return None
                
        except Exception as e:
            logger.error(f"HuggingFace horoscope error: {e}")
            return None

hf = HuggingFacePredictor(config.HF_API_KEY)