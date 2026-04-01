import requests
import json
from utils import logger
import config

class CryptoPay:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://pay.crypt.bot/api"
        
    def create_invoice(self, amount, currency="USDT", description="Предсказание"):
        """
        Создание счета через CryptoPay
        """
        if not self.token:
            logger.error("CryptoPay token is not set")
            return None
            
        try:
            headers = {
                'Crypto-Pay-API-Token': self.token,
                'Content-Type': 'application/json'
            }
            
            # Создаем инвойс в USDT
            data = {
                'asset': 'USDT',  # Используем USDT
                'amount': str(amount),  # Сумма в USDT
                'description': description,
                'paid_btn_name': 'callback',
                'paid_btn_url': 'https://t.me/ln_Fortune_Bot',  # Исправленный username
                'allow_comments': True
            }
            
            logger.info(f"Creating USDT invoice: {amount} USDT")
            
            response = requests.post(
                f"{self.api_url}/createInvoice",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    invoice = result['result']
                    logger.info(f"Invoice created: {invoice['invoice_id']}, amount: {invoice['amount']} {invoice['asset']}")
                    return invoice
                else:
                    logger.error(f"Error creating invoice: {result}")
                    return None
            else:
                logger.error(f"HTTP error: {response.status_code}, response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            return None
    
    def check_payment(self, invoice_id):
        """
        Проверка статуса оплаты по invoice_id
        """
        if not self.token:
            return False
            
        try:
            headers = {
                'Crypto-Pay-API-Token': self.token,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.api_url}/getInvoices",
                headers=headers,
                params={'invoice_ids': invoice_id},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok') and result['result']['items']:
                    invoice = result['result']['items'][0]
                    status = invoice.get('status')
                    logger.info(f"Invoice {invoice_id} status: {status}")
                    return status == 'paid'
                else:
                    logger.error(f"Error checking invoice: {result}")
                    return False
            else:
                logger.error(f"HTTP error checking payment: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking payment: {e}")
            return False

# Инициализация
crypto_pay = CryptoPay(config.CRYPTOPAY_TOKEN)