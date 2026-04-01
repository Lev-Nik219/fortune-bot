import requests
from utils import logger
import config

class CryptoPay:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://pay.crypt.bot/api"
    
    def create_invoice(self, amount, currency="USDT", description="Предсказание"):
        if not self.token:
            return None
        
        try:
            headers = {'Crypto-Pay-API-Token': self.token, 'Content-Type': 'application/json'}
            data = {
                'asset': 'USDT',
                'amount': str(amount),
                'description': description,
                'paid_btn_name': 'callback',
                'paid_btn_url': 'https://t.me/ln_Fortune_Bot'
            }
            
            response = requests.post(f"{self.api_url}/createInvoice", headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return result['result']
            return None
        except Exception as e:
            logger.error(f"Create invoice error: {e}")
            return None
    
    def check_payment(self, invoice_id):
        if not self.token:
            return False
        
        try:
            headers = {'Crypto-Pay-API-Token': self.token, 'Content-Type': 'application/json'}
            response = requests.get(f"{self.api_url}/getInvoices", headers=headers, params={'invoice_ids': invoice_id}, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok') and result['result']['items']:
                    return result['result']['items'][0].get('status') == 'paid'
            return False
        except Exception as e:
            logger.error(f"Check payment error: {e}")
            return False

crypto_pay = CryptoPay(config.CRYPTOPAY_TOKEN)