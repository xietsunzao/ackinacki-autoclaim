import sys
import time
from rich.console import Console

console = Console()

class TokenExpiredError(Exception):
    pass

class TokenInvalidError(Exception):
    pass

def handle_token_error(message="Token error"):
    console.clear()
    console.print(f"[red]{message}[/]")
    
    if "Access denied" in message:
        console.print("[yellow]The token appears to be invalid.[/]")
        console.print("[yellow]Please check your token and try again.[/]")
    elif "Invalid token format" in message:
        console.print("[yellow]The token format is incorrect.[/]")
        console.print("[yellow]Make sure your token starts with 'eyJ'[/]")
    elif "Unexpected API response" in message:
        console.print("[yellow]The API response was not in the expected format.[/]")
        console.print("[yellow]Please check your token and try again.[/]")
    
    sys.exit(1)

def handle_api_error(e, last_api_call):
    console.print(f"[red]Error occurred: {e}[/]")
    console.print("[yellow]Retrying in 60 seconds...[/]")
    time.sleep(60)
    return 0

def handle_program_exit():
    console.clear()
    console.print("\n[red]Program stopped by user. Goodbye![/]")
    sys.exit(0) 