from huggingface_hub import InferenceClient
from utils import logger
import config
import random

class HuggingFacePredictor:
    def __init__(self, api_key):
        if api_key:
            try:
                # Используем новый URL
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
        """Генерация предсказания через Hugging Face"""
        if not self.available:
            return None
            
        try:
            user_name = user_data.get('name', 'друг')
            user_gender = user_data.get('gender', 'other')
            user_question = user_data.get('question', '')
            user_zodiac = user_data.get('zodiac', '')
            
            # Создаем разнообразные промпты
            prompts = [
                f"""Ты - добрый предсказатель. Создай уникальное предсказание для {user_name}.
Вопрос: {user_question if user_question else 'о будущем'}
Напиши 3-4 предложения на русском, используя имя. Будь оптимистичен и вдохновляющ.
Предсказание:""",
                
                f"""Создай персональное предсказание для {user_name}.
Пол: {user_gender}
Знак зодиака: {user_zodiac if user_zodiac else 'не указан'}
Волнует: {user_question if user_question else 'жизненный путь'}
Напиши 2-3 предложения с мудростью и поддержкой на русском языке.
Предсказание:""",
                
                f"""Ты - таинственный оракул. Составь мистическое предсказание для {user_name}.
Используй метафоры, будь поэтичен. 3-4 предложения на русском.
Предсказание:"""
            ]
            
            # Выбираем случайный промпт
            prompt = random.choice(prompts)
            
            # Используем другую модель, которая стабильнее работает
            response = self.client.text_generation(
                prompt,
                model="google/flan-t5-base",  # Более стабильная модель
                max_new_tokens=150,
                temperature=0.9,
                do_sample=True
            )
            
            if response and len(response) > 10:
                return response.strip()
            else:
                return None
                
        except Exception as e:
            logger.error(f"HuggingFace prediction error: {e}")
            return None
    
    def generate_horoscope(self, zodiac_sign):
        """Генерация гороскопа через Hugging Face"""
        if not self.available:
            return None
            
        try:
            prompt = f"""Создай короткий юмористический гороскоп для знака {zodiac_sign}.
Сделай его веселым, с легкой иронией. 1-2 предложения на русском.
Гороскоп:"""
            
            response = self.client.text_generation(
                prompt,
                model="google/flan-t5-base",
                max_new_tokens=80,
                temperature=0.85,
                do_sample=True
            )
            
            if response and len(response) > 10:
                return response.strip()
            else:
                return None
                
        except Exception as e:
            logger.error(f"HuggingFace horoscope error: {e}")
            return None

# Инициализация
hf = HuggingFacePredictor(config.HF_API_KEY)