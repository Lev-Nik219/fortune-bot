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
            
            # Определяем обращение в зависимости от пола
            if user_gender == 'male':
                pronoun = 'ты'
            elif user_gender == 'female':
                pronoun = 'ты'
            else:
                pronoun = 'ты'
            
            # Создаем разнообразные промпты с разной стилистикой
            prompts = [
                f"""<|system|>
Ты - добрый и мудрый предсказатель с чувством юмора. Твои предсказания всегда уникальны и разные.
<|user|>
Создай УНИКАЛЬНОЕ предсказание для человека. Оно должно отличаться от всех предыдущих.

Информация:
- Имя: {user_name}
- Пол: {user_gender}
- Вопрос: {user_question if user_question else 'будущее'}
- Знак зодиака: {user_zodiac if user_zodiac else 'не указан'}

Стиль: добрый, вдохновляющий, с легким юмором
Объем: 3-4 предложения
Язык: русский

ВАЖНО: Сделай предсказание максимально разным и уникальным!

Предсказание:
<|assistant|>""",

                f"""Создай вдохновляющее предсказание для {user_name}. 
Обратись к нему/ней лично. Используй имя. 
Добавь мудрости и оптимизма. 
Будь креативен и уникален в каждом предсказании.
Тема: {user_question if user_question else 'жизненный путь'}
Напиши 3-4 предложения на русском:""",

                f"""Ты - таинственный оракул. 
Составь мистическое, но оптимистичное предсказание для {user_name}.
Используй метафоры, образы, сделай его поэтичным.
Объем: 3-4 предложения.
Язык: русский.
Предсказание:"""
            ]
            
            # Выбираем случайный промпт для разнообразия
            prompt = random.choice(prompts)
            
            response = self.client.text_generation(
                prompt,
                model="microsoft/DialoGPT-medium",
                max_new_tokens=200,
                temperature=0.9,  # Повышаем температуру для большей вариативности
                top_p=0.95,
                do_sample=True,
                repetition_penalty=1.1  # Избегаем повторений
            )
            
            # Очищаем ответ
            prediction = response.strip()
            if prediction:
                # Убираем возможные повторы
                if len(prediction) > 200:
                    prediction = prediction[:200] + "..."
                logger.info(f"Generated unique prediction for {user_name}")
                return prediction
            else:
                logger.warning("Empty response from HuggingFace")
                return None
                
        except Exception as e:
            logger.error(f"HuggingFace prediction error: {e}")
            return None
    
    def generate_horoscope(self, zodiac_sign, user_name=""):
        """Генерация уникального гороскопа через Hugging Face"""
        if not self.available:
            return None
            
        try:
            # База разных стилей для гороскопов
            horoscope_styles = [
                f"""Создай юмористический гороскоп для знака {zodiac_sign}.
Сделай его слегка пошлым, но правдивым и актуальным.
Добавь конкретные ситуации из жизни.
Объем: 2-3 предложения.
Язык: русский.
Гороскоп:""",

                f"""Составь шутливый гороскоп на сегодня для {zodiac_sign}.
Добавь элементы: любовь, работа, юмор.
Сделай его уникальным и непохожим на другие гороскопы.
Объем: 2-3 предложения.
Гороскоп:""",

                f"""Ты - астролог с отличным чувством юмора.
Напиши гороскоп для {zodiac_sign}.
Используй современные отсылки, будь остроумным.
Добавь совет на день.
Объем: 2-3 предложения.
Язык: русский.
Гороскоп:""",

                f"""Придумай креативный гороскоп для знака {zodiac_sign}.
Смешай астрологию с реальной жизнью.
Сделай его запоминающимся и веселым.
Объем: 2-3 предложения.
Гороскоп:"""
            ]
            
            # Выбираем случайный стиль
            prompt = random.choice(horoscope_styles)
            
            response = self.client.text_generation(
                prompt,
                model="microsoft/DialoGPT-medium",
                max_new_tokens=150,
                temperature=0.85,  # Высокая температура для разнообразия
                top_p=0.95,
                do_sample=True,
                repetition_penalty=1.1
            )
            
            horoscope = response.strip()
            if horoscope:
                logger.info(f"Generated unique horoscope for {zodiac_sign}")
                return horoscope
            else:
                return None
                
        except Exception as e:
            logger.error(f"HuggingFace horoscope error: {e}")
            return None

# Инициализация
hf = HuggingFacePredictor(config.HF_API_KEY)