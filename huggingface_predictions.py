import requests
import json
from utils import logger
import config
import random

class HuggingFacePredictor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api-inference.huggingface.co/models/"
        self.headers = {"Authorization": f"Bearer {api_key}"}
        
        if api_key and api_key != "your_huggingface_key_here":
            self.available = True
            logger.info("✅ HuggingFace API configured (will attempt to use)")
        else:
            self.available = False
            logger.warning("⚠️ HuggingFace API key not provided - using templates only")
    
    def _query(self, model, prompt, max_tokens=200):
        """Выполняет запрос к Hugging Face API"""
        try:
            url = self.api_url + model
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": max_tokens,
                    "temperature": 0.8,
                    "do_sample": True
                }
            }
            
            logger.info(f"🔄 Sending request to HuggingFace API...")
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result and isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '')
                    # Убираем промпт из ответа
                    if generated_text.startswith(prompt):
                        generated_text = generated_text[len(prompt):]
                    return generated_text.strip()
            elif response.status_code == 503:
                logger.warning("⏳ Model is loading, please wait...")
                return None
            else:
                logger.error(f"❌ API error {response.status_code}: {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Query error: {e}")
            return None
    
    def generate_prediction(self, user_data):
        """Генерация предсказания через Hugging Face"""
        if not self.available:
            return None
            
        try:
            user_name = user_data.get('name', 'друг')
            user_question = user_data.get('question', '')
            
            prompt = f"Создай доброе предсказание для {user_name}. {user_question if user_question else 'У него всё будет хорошо'}. Напиши 3-4 предложения на русском языке. Предсказание:"
            
            # Пробуем разные модели
            models = [
                "microsoft/DialoGPT-medium",
                "google/flan-t5-base"
            ]
            
            for model in models:
                response = self._query(model, prompt, max_tokens=200)
                if response and len(response.split()) > 20:
                    logger.info(f"✅ AI prediction generated with {model}")
                    return response
            
            return None
                
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None
    
    def generate_horoscope(self, zodiac_sign):
        """Генерация гороскопа через Hugging Face"""
        if not self.available:
            return None
            
        try:
            prompt = f"Напиши короткий юмористический гороскоп для знака {zodiac_sign} на сегодня. 2-3 предложения на русском языке. Гороскоп:"
            
            models = [
                "microsoft/DialoGPT-medium",
                "google/flan-t5-base"
            ]
            
            for model in models:
                response = self._query(model, prompt, max_tokens=150)
                if response and len(response.split()) > 10:
                    logger.info(f"✅ AI horoscope generated with {model}")
                    return response
            
            return None
                
        except Exception as e:
            logger.error(f"Horoscope error: {e}")
            return None

# Инициализация
hf = HuggingFacePredictor(config.HF_API_KEY)