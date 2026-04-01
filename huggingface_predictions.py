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
    
    def generate_prediction(self, user_data):
        if not self.available:
            return None
            
        try:
            user_name = user_data.get('name', 'друг')
            user_question = user_data.get('question', '')
            
            prompt = f"""Создай доброе, вдохновляющее предсказание для {user_name}.
Вопрос: {user_question if user_question else 'о будущем'}
Напиши 2-3 предложения на русском, используя имя человека.
Предсказание:"""
            
            response = self.client.text_generation(
                prompt,
                model="microsoft/DialoGPT-medium",
                max_new_tokens=150,
                temperature=0.9,
                do_sample=True
            )
            return response.strip()
        except Exception as e:
            logger.error(f"HuggingFace error: {e}")
            return None
    
    def generate_horoscope(self, zodiac_sign):
        if not self.available:
            return None
            
        try:
            prompt = f"""Создай юмористический гороскоп для знака {zodiac_sign}.
Сделай его коротким, веселым, 1-2 предложения.
Гороскоп:"""
            
            response = self.client.text_generation(
                prompt,
                model="microsoft/DialoGPT-medium",
                max_new_tokens=100,
                temperature=0.85,
                do_sample=True
            )
            return response.strip()
        except Exception as e:
            logger.error(f"HuggingFace error: {e}")
            return None

hf = HuggingFacePredictor(config.HF_API_KEY)