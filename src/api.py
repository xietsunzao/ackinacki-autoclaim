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

    def __init__(self, access_token):
        self.access_token = access_token

    def _get_headers(self):
        return {
            'accept': 'application/json, text/plain, */*',
            'origin': 'https://t.ackinacki.com',
            'referer': 'https://t.ackinacki.com/',
            'jwt-auth': self.access_token,
            'user-agent': generate_user_agent()
        }
    
    def get_user_data(self):
        response = requests.get(f'{self.BASE_URL}/users/me', headers=self._get_headers())

        # Check status code first before trying to parse JSON
        if response.status_code == 401:
            raise TokenExpiredError("Token has expired")

        # Try to parse JSON response
        try:
            data = response.json()
        except ValueError as e:
            console.print(f"[red]API Response Error:[/] Status {response.status_code}")
            console.print(f"[yellow]Response text:[/] {response.text[:200]}")
            raise TokenInvalidError(f"Invalid API response - not JSON (Status: {response.status_code})")

        # Check for error messages first
        if isinstance(data, dict):
            if 'message' in data:
                if 'Unauthorized' in data['message']:
                    raise TokenExpiredError("Token has expired or is invalid")
                elif 'Access denied' in data['message']:
                    raise TokenInvalidError("Access denied - Invalid token")
                elif 'Error decoding auth header' in data['message']:
                    raise TokenInvalidError("Invalid token format")

            # New API response format has 'user', 'friends', 'queue' structure
            if 'user' in data and 'queue' in data:
                return data

        raise TokenExpiredError("Unexpected API response format")

    def get_farming_task(self):
        """Get farming task status - NEW API"""
        response = requests.get(f'{self.BASE_URL}/users/tasks/farm/v2', headers=self._get_headers())

        if response.status_code == 200:
            return response.json()
        else:
            console.print(f"[red]Failed to get farming task: {response.status_code}[/]")
            return None

    def start_farming(self):
        """Start farming task - NEW API"""
        headers = self._get_headers()
        headers['content-length'] = '0'
        response = requests.post(f'{self.BASE_URL}/users/tasks/farm/v2', headers=headers)

        # POST returns empty response on success
        return {
            'status': 'success' if response.status_code == 200 else 'error',
            'status_code': response.status_code
        }

    def claim_farming(self, task_id):
        """Claim farming task reward - NEW API"""
        headers = self._get_headers()
        headers['content-type'] = 'application/json'

        payload = {'task_id': task_id}
        response = requests.post(f'{self.BASE_URL}/users/tasks/claim', headers=headers, json=payload)

        return {
            'status': 'success' if response.status_code == 200 else 'error',
            'status_code': response.status_code,
            'response': response
        } 