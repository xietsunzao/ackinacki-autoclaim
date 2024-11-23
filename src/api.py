import requests
import random
from .exceptions import TokenExpiredError, TokenInvalidError
from rich.console import Console

console = Console()

def generate_user_agent():
    mobile_devices = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Mozilla/5.0 (Linux; Android 10; SM-A505FN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(mobile_devices)

class AckinackiAPI:
    BASE_URL = 'https://app-backend.ackinacki.org/api'
    
    def __init__(self, telegram_data):
        self.telegram_data = telegram_data
        
    def _get_headers(self):
        return {
            'accept': 'application/json, text/plain, */*',
            'origin': 'https://twa.ackinacki.org',
            'referer': 'https://twa.ackinacki.org/',
            'telegram-data': self.telegram_data,
            'user-agent': generate_user_agent()
        }
    
    def get_user_data(self):
        response = requests.get(f'{self.BASE_URL}/users/me', headers=self._get_headers())
        data = response.json()
        
        if response.status_code == 401:
            raise TokenExpiredError("Token has expired")
        
        # Check for error messages first
        if isinstance(data, dict):
            if 'message' in data:
                if 'Access denied' in data['message']:
                    raise TokenInvalidError("Access denied - Invalid token")
                elif 'Error decoding auth header' in data['message']:
                    raise TokenInvalidError("Invalid token format")
            
            # If we have claimed_summary and daily_farming, it's a valid response
            if 'claimed_summary' in data and 'daily_farming' in data:
                return data
                
        raise TokenExpiredError("Unexpected API response format")
    
    def start_farming(self):
        headers = self._get_headers()
        headers['content-length'] = '0'
        response = requests.post(f'{self.BASE_URL}/users/action/farm/v2', headers=headers)
        return response
    
    def claim_friend_bonus(self):
        response = requests.post(f'{self.BASE_URL}/users/claim/invited_friend', headers=self._get_headers())
        return response
    
    def claim_farming(self):
        response = requests.post(f'{self.BASE_URL}/users/claim/daily_farming_v2', headers=self._get_headers())
        return response 