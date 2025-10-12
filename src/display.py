"""
Enhanced display utilities with Rich library features like progress bars and better formatting.
"""

from datetime import datetime, timezone
import time
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich import box

console = Console()

# Global flag to suppress display when Popits is running
_popits_active = False

def set_popits_active(active):
    """Set whether Popits is currently running (suppresses display)"""
    global _popits_active
    _popits_active = active


def format_time(seconds):
    """
    Format seconds into HH:MM:SS format.

    Args:
        seconds (int): Number of seconds to format

    Returns:
        str: Formatted time string (HH:MM:SS)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def create_user_info_table(user_data):
    """
    Create a rich table showing user information.

    Args:
        user_data (dict): User data from API

    Returns:
        Table: Rich table with user info
    """
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    table.add_column("Label", style="cyan", no_wrap=True)
    table.add_column("Value", style="bold green")

    username = user_data['user']['username']
    boost_points = user_data['queue']['boost']
    friends_count = user_data['friends']['count']

    table.add_row("Player", f"{username}")
    table.add_row("Points", f"{boost_points:,}")
    table.add_row("Friends", f"{friends_count}")

    return table


def create_farming_panel(farming_task):
    """
    Create a panel showing farming task information.

    Args:
        farming_task (dict): Farming task data from API

    Returns:
        Panel: Rich panel with farming info
    """
    if not farming_task or not farming_task.get('reward'):
        return Panel(
            "[yellow]No active farming task[/]",
            title="Farming Status",
            border_style="yellow"
        )

    reward = farming_task['reward']['reward']
    level = farming_task['reward']['metadata']['index']
    current_index = farming_task['reward']['metadata'].get('subindex', 0)

    # Create boost boxes visualization
    boost_boxes = []
    for i in range(5):
        if i < current_index:
            boost_boxes.append(f"[bright_green]■[/]")
        elif i == current_index:
            boost_boxes.append(f"[bright_yellow]■[/]")
        else:
            boost_boxes.append(f"[dim white]□[/]")

    content = f"""[green]Farm Boost Level:[/] [white]{level}[/]
[grey]Take all 5 Boosts in 24 hours to farm higher Boost next day[/]

Progress: {' '.join(boost_boxes)}  ([yellow]{reward}[/] points each)
"""

    return Panel(content, title="Farming Status", border_style="green")


def display_farming_progress(farming_task, end_time):
    """
    Display farming progress with a progress bar.

    Args:
        farming_task (dict): Farming task data
        end_time (float): Unix timestamp when farming completes
    """
    if not farming_task or not farming_task.get('reward'):
        return

    # Calculate progress
    start_time = time.time()
    total_duration = end_time - start_time

    if total_duration <= 0:
        console.print("[green]Farming complete! Ready to claim.[/]")
        return

    # Create progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task(
            "[cyan]Farming in progress...",
            total=total_duration
        )

        while not progress.finished:
            current_time = time.time()
            elapsed = current_time - start_time

            if elapsed >= total_duration:
                progress.update(task, completed=total_duration)
                break

            progress.update(task, completed=elapsed)
            time.sleep(0.5)


def display_enhanced_info(user_data, farming_task, end_time, first_run=False):
    """
    Display enhanced information with Rich formatting.

    Args:
        user_data (dict): User data from API
        farming_task (dict): Farming task data
        end_time (float): Unix timestamp when farming completes
        first_run (bool): Whether this is the first display (clear screen)
    """
    if first_run:
        console.clear()

    # Create layout
    console.print("\n[dim]Created by @xietsunzao[/]\n")

    # Display user info table
    user_table = create_user_info_table(user_data)
    console.print(user_table)
    console.print()

    # Display farming panel
    farming_panel = create_farming_panel(farming_task)
    console.print(farming_panel)
    console.print()

    # Display countdown timer
    current_time = time.time()
    remaining = max(0, int(end_time - current_time))

    if first_run:
        console.print(f"[bold cyan]Time Remaining:[/] {format_time(remaining)}", end='', flush=True)
    else:
        console.print(f"\r[bold cyan]Time Remaining:[/] {format_time(remaining)}", end='', flush=True)


def display_compact_info(user_data, farming_task, end_time, first_run=False):
    """
    Display compact information (original style) for continuous monitoring.

    Args:
        user_data (dict): User data from API
        farming_task (dict): Farming task data
        end_time (float): Unix timestamp when farming completes
        first_run (bool): Whether this is the first display (clear screen)
    """
    if first_run:
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
        console.print(f"🎮 {username} ⭐ {boost_points:,} Points")
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
        print()  # Add empty line for timer

    # Timer display (skip if Popits is active)
    if not _popits_active:
        remaining = max(0, int(end_time - time.time()))
        if first_run:
            print(f"Remaining Time {format_time(remaining)}", end='', flush=True)
        else:
            print(f"\rRemaining Time {format_time(remaining)}", end='', flush=True)


def show_claim_animation():
    """Show an animation when claiming rewards."""
    with console.status("[bold green]Claiming reward...", spinner="aesthetic") as status:
        time.sleep(1)
        status.update("[bold yellow]Processing...")
        time.sleep(0.5)
    console.print("[green]✓[/] Reward claimed successfully!", style="bold")


def show_start_animation():
    """Show an animation when starting a new farming session."""
    with console.status("[bold blue]Starting new farming session...", spinner="dots") as status:
        time.sleep(1)
    console.print("[blue]✓[/] Farming session started!", style="bold")
