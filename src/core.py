from datetime import datetime, timezone, timedelta
import time
from rich.console import Console

console = Console()

def read_or_create_token():
    token = None
    
    # First check if token file exists
    try:
        with open('token.txt', 'r') as file:
            token = file.read().strip()
    except FileNotFoundError:
        pass
    
    # If no token found or file is empty, get from user input
    if not token:
        console.print("[yellow]Please enter your telegram-data token:[/]")
        token = input().strip()
        
        if not token:
            console.print("[red]No token provided. Exiting...[/]")
            return None
        
        # Basic validation before saving
        if not token.startswith('eyJ'):
            console.print("[red]Invalid token format. Token should start with 'eyJ'[/]")
            console.print("[yellow]Please check your token and try again.[/]")
            return None
        
        # Save valid token
        try:
            with open('token.txt', 'w') as file:
                file.write(token)
            console.print("[green]Token saved successfully![/]")
        except Exception as e:
            console.print(f"[red]Error saving token: {e}[/]")
            return None
    
    return token

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def display_info(user_data, end_time, reward, first_run=False, waiting_for_next=False, next_start_time=None):
    if first_run or waiting_for_next:
        console.clear()
        
        # Get user info
        username = user_data['user']['username']
        level = user_data['daily_farming']['daily_farming_v2']['metadata']['index']
        boost_points = user_data['queue']['boost']
        friends_count = user_data.get('friends', 0)
        
        # Display static information
        console.print(f"🎮 {username}⭐ {boost_points:,} Points")
        console.print(f"👥 {friends_count} Friends")
        console.print(f"[green]Farm Boosts[/] [white]lvl {level}[/]")
        console.print("[grey]Take all 5 Boosts in 24 hours to farm higher Boost next day[/]")
        
        # Display boost boxes
        current_index = user_data['daily_farming']['daily_farming_v2']['metadata'].get('subindex', 0)
        boost_boxes = []
        for i in range(5):
            if i < current_index:
                boost_boxes.append(f"[bright_green on black]⭐ {reward}[/]")
            elif i == current_index:
                boost_boxes.append(f"[bright_yellow on black]⭐ {reward}[/]")
            else:
                boost_boxes.append(f"[dim white]⭐ {reward}[/]")
        
        console.print(f"{' '.join(boost_boxes)}")
        print() # Add empty line for timer

    # Timer display
    current_time = datetime.now(timezone.utc)
    
    if waiting_for_next and next_start_time:
        wait_time = next_start_time - current_time
        remaining_seconds = int(wait_time.total_seconds())
        if first_run:
            print(f"Next farming will unlock in {format_time(remaining_seconds)}", end='', flush=True)
        else:
            print(f"\rNext farming will unlock in {format_time(remaining_seconds)}", end='', flush=True)
    else:
        remaining = max(0, int(end_time - time.time()))
        if first_run:
            print(f"Remaining Time {format_time(remaining)}", end='', flush=True)
        else:
            print(f"\rRemaining Time {format_time(remaining)}", end='', flush=True)
    