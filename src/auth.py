import json
import base64
from .session import create_auth_session
from rich.console import Console

console = Console()

def decode_base64_url(data):
    """Decode base64 with automatic padding fix"""
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    return base64.b64decode(data).decode('utf-8')

def get_session_id_from_url(start_url):
    """Extract session_id from Telegram start URL"""
    try:
        # URL format: https://t.ackinacki.com/?startapp=BASE64_ENCODED_JSON
        if '?startapp=' in start_url:
            startapp_param = start_url.split('?startapp=')[1]
            decoded_data = decode_base64_url(startapp_param)
            session_data = json.loads(decoded_data)
            return session_data.get('session_id'), session_data.get('locale', 'en')
        else:
            console.print("[red]Invalid URL format. Expected: https://t.ackinacki.com/?startapp=...[/]")
            return None, None
    except Exception as e:
        console.print(f"[red]Error parsing start URL: {e}[/]")
        return None, None

def exchange_session_for_token(session_id, locale='en'):
    """Exchange session_id for access_token and refresh_token using persistent session"""
    session = create_auth_session()

    try:
        url = f"https://app-backend.ackinacki.org/api/v1/auth/session?session_id={session_id}&locale={locale}"

        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'origin': 'https://t.ackinacki.com',
            'referer': 'https://t.ackinacki.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
        }

        response = session.get(url, headers=headers)

        if response.status_code == 200:
            auth_data = response.json()
            return {
                'access_token': auth_data.get('access_token'),
                'refresh_token': auth_data.get('refresh_token'),
                'status': 'success'
            }
        else:
            console.print(f"[red]Auth failed with status {response.status_code}[/]")
            console.print(f"[yellow]Response: {response.text}[/]")
            return {'status': 'error', 'message': response.text}

    except Exception as e:
        console.print(f"[red]Error during authentication: {e}[/]")
        return {'status': 'error', 'message': str(e)}
    finally:
        session.close()

def authenticate_with_session_data(session_data_b64):
    """Complete authentication flow from base64 session data to access token"""
    console.print("[cyan]Starting authentication...[/]")

    try:
        # Decode session data
        decoded_data = decode_base64_url(session_data_b64)
        session_data = json.loads(decoded_data)

        session_id = session_data.get('session_id')
        locale = session_data.get('locale', 'en')

        if not session_id:
            console.print("[red]No session_id found in session data[/]")
            return None

        console.print(f"[green]Session ID:[/] {session_id[:20]}...")

        # Exchange for access token
        auth_result = exchange_session_for_token(session_id, locale)

        if auth_result['status'] == 'success':
            console.print("[green]Access token obtained![/]")
            return auth_result['access_token']
        else:
            console.print("[red]Authentication failed[/]")
            return None

    except Exception as e:
        console.print(f"[red]Error during authentication: {e}[/]")
        return None

def authenticate_with_start_url(start_url):
    """Complete authentication flow from start URL to access token"""
    console.print("[cyan]Starting authentication...[/]")

    # Step 1: Extract session_id from URL
    session_id, locale = get_session_id_from_url(start_url)
    if not session_id:
        return None

    console.print(f"[green]Session ID extracted: {session_id[:20]}...[/]")

    # Step 2: Exchange for access token
    auth_result = exchange_session_for_token(session_id, locale)

    if auth_result['status'] == 'success':
        console.print("[green]Access token obtained successfully![/]")
        return auth_result['access_token']
    else:
        console.print("[red]Authentication failed[/]")
        return None

def read_or_create_start_url():
    """Read start URL from file or prompt user to enter it"""
    start_url = None

    # Try to read from file
    try:
        with open('start_url.txt', 'r') as file:
            start_url = file.read().strip()
    except FileNotFoundError:
        pass

    # If no URL found or file is empty, get from user input
    if not start_url:
        console.print("[yellow]Please enter your Acki Nacki start URL:[/]")
        console.print("[dim]Example: https://t.ackinacki.com/?startapp=eyJ...[/]")
        start_url = input().strip()

        if not start_url:
            console.print("[red]No URL provided. Exiting...[/]")
            return None

        # Basic validation
        if not start_url.startswith('https://t.ackinacki.com/?startapp='):
            console.print("[red]Invalid URL format.[/]")
            console.print("[yellow]URL should start with: https://t.ackinacki.com/?startapp=[/]")
            return None

        # Save valid URL
        try:
            with open('start_url.txt', 'w') as file:
                file.write(start_url)
            console.print("[green]Start URL saved successfully![/]")
        except Exception as e:
            console.print(f"[red]Error saving URL: {e}[/]")
            return None

    return start_url

def get_access_token():
    """Main function to get access token - handles full auth flow"""
    start_url = read_or_create_start_url()
    if not start_url:
        return None

    return authenticate_with_start_url(start_url)
