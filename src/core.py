from datetime import datetime, timezone, timedelta
import time
from rich.console import Console

console = Console()

def read_or_create_session_data():
    """Read or prompt for session data (base64 from start URL)"""
    session_data = None

    # First check if token file exists
    try:
        with open('token.txt', 'r') as file:
            session_data = file.read().strip()
    except FileNotFoundError:
        pass

    # If no data found or file is empty, get from user input
    if not session_data:
        console.print("[yellow]Please enter your session data:[/]")
        console.print("[dim]From URL: https://t.ackinacki.com/?startapp=BASE64_HERE[/]")
        console.print("[dim]Or just paste the base64 part (starts with 'eyJ')[/]")
        session_data = input().strip()

        if not session_data:
            console.print("[red]No session data provided. Exiting...[/]")
            return None

        # If they pasted the full URL, extract the base64 part
        if 'startapp=' in session_data:
            session_data = session_data.split('startapp=')[1].split('&')[0]

        # Basic validation before saving
        if not session_data.startswith('eyJ'):
            console.print("[red]Invalid session data format. Should start with 'eyJ'[/]")
            console.print("[yellow]Please check your session data and try again.[/]")
            return None

        # Save valid session data
        try:
            with open('token.txt', 'w') as file:
                file.write(session_data)
            console.print("[green]Session data saved successfully![/]")
        except Exception as e:
            console.print(f"[red]Error saving session data: {e}[/]")
            return None

    return session_data

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def display_info(user_data, farming_task, end_time, first_run=False, waiting_for_next=False, next_start_time=None):
    if first_run or waiting_for_next:
        console.clear()

        # Get user info from new API structure
        username = user_data['user']['username']
        boost_points = user_data['queue']['boost']
        friends_count = user_data['friends']['count']

        # Get farming info from task
        reward = farming_task['reward']['reward'] if farming_task and farming_task.get('reward') else 0
        level = farming_task['reward']['metadata']['index'] if farming_task and farming_task.get('reward') else 0
        
        # Display credit
        console.print("[dim]Created by @xietsunzao[/]")
        console.print() 
        
        # Display static information
        console.print(f"🎮 {username}⭐ {boost_points:,} Points")
        console.print(f"👥 {friends_count} Friends")
        console.print(f"[green]Farm Boosts[/] [white]lvl {level}[/]")
        console.print("[grey]Take all 5 Boosts in 24 hours to farm higher Boost next day[/]")
        
        # Display boost boxes
        current_index = farming_task['reward']['metadata'].get('subindex', 0) if farming_task and farming_task.get('reward') else 0
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
    