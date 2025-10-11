import sys
import time
import json
from datetime import datetime, timezone
from src import (
    AckinackiAPI,
    authenticate_with_session_data,
    read_or_create_session_data,
    display_info,
    console,
    handle_api_error,
    handle_program_exit,
    handle_token_error,
    TokenExpiredError,
    TokenInvalidError,
    PopitsManager
)
from src.display import (
    display_enhanced_info,
    display_compact_info,
    show_claim_animation,
    show_start_animation
)

# Configuration: Set display mode
# Options: 'compact' (original style), 'enhanced' (with panels and tables)
DISPLAY_MODE = 'compact'  # Change to 'enhanced' for more visual display
SHOW_API_STATUS = False   # Set to True to show spinners during API calls

# Configuration: Popits Feature
POPITS_CONFIG = {
    # Feature toggle
    'enabled': True,           # Set to True to enable Popits feature

    # Timing
    'check_interval': 300,         # Check every 5 minutes (300 seconds)
    'watch_delay': 3,              # Wait 3s between watching reels

    # Reels watching
    'reels_to_watch_per_cycle': 10,  # Watch ~10 unwatched reels per cycle

    # Strategy: Farm mints first, tap when max reached
    'max_vdf_per_cycle': 3,         # Max tapping challenges when mints = 3

    # VDF Human Simulation (CRITICAL: Stay under 100 taps!)
    'vdf_min_taps': 40,          # Minimum taps (SAFE)
    'vdf_max_taps': 85,          # Maximum taps (UNDER 100!)

    # Safety
    'respect_daily_limit': True, # Stop at max_count
    'stop_if_banned': True,      # Stop if unban_at != null
    'verify_taps': True,         # Always verify (anti-bot)

    # Display
    'show_progress': True,       # Show tapping animation
    'show_stats': True,          # Show session stats
}

def save_tokens(access_token, refresh_token):
    """Save tokens to file for persistence"""
    try:
        tokens = {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
        with open('tokens.json', 'w') as f:
            json.dump(tokens, f, indent=2)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not save tokens: {e}[/]")

def load_tokens():
    """Load tokens from file"""
    try:
        with open('tokens.json', 'r') as f:
            tokens = json.load(f)
            return tokens.get('access_token'), tokens.get('refresh_token')
    except FileNotFoundError:
        return None, None
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load tokens: {e}[/]")
        return None, None

def parse_datetime(date_str):
    try:
        # First try the standard format
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        # If that fails, try removing microseconds beyond 6 digits
        parts = date_str.split('.')
        if len(parts) == 2:
            base, fraction = parts
            # Truncate to 6 digits for microseconds
            fraction = fraction[:6] + 'Z' if fraction.endswith('Z') else fraction[:6]
            modified_date_str = f"{base}.{fraction}"
            return datetime.fromisoformat(modified_date_str.replace('Z', '+00:00'))
        raise

def main():
    sys.tracebacklimit = 0

    # Try to load saved tokens first
    access_token, refresh_token = load_tokens()

    # If no saved tokens, authenticate with session data
    if not access_token or not refresh_token:
        # Read session data from token.txt
        session_data = read_or_create_session_data()
        if not session_data:
            console.print("[red]No session data provided. Exiting...[/]")
            return

        # Exchange session for access token and refresh token
        auth_result = authenticate_with_session_data(session_data)
        if not auth_result or auth_result.get('status') == 'error':
            console.print("[red]Authentication failed. Exiting...[/]")
            return

        access_token = auth_result['access_token']
        refresh_token = auth_result['refresh_token']

        # Save tokens for future use
        save_tokens(access_token, refresh_token)
    else:
        console.print("[cyan]Using saved tokens...[/]")

    console.print("[green]Starting bot...[/]")
    time.sleep(1)
    console.clear()

    # Create API with token refresh callback
    api = AckinackiAPI(
        access_token,
        refresh_token,
        show_status=SHOW_API_STATUS,
        on_token_refresh=save_tokens
    )

    # Initialize Popits Manager if enabled
    popits_manager = None
    last_popits_check = 0
    if POPITS_CONFIG['enabled']:
        console.print("[green]✓ Popits feature enabled[/]")
        popits_manager = PopitsManager(api, POPITS_CONFIG)
    else:
        console.print("[dim]Popits feature disabled (set POPITS_CONFIG['enabled'] = True to enable)[/]")

    last_api_call = 0
    last_display_update = 0
    claiming_attempted = False
    user_data = None
    farming_task = None
    claim_time = 0

    try:
        while True:
            try:
                current_time = time.time()
                current_time_dt = datetime.now(timezone.utc)

                # Run Popits cycle if enabled and interval passed
                if popits_manager and (current_time - last_popits_check >= POPITS_CONFIG['check_interval']):
                    console.print("\n[bold yellow]═══════════════════════════════════[/]")
                    console.print("[bold yellow]   Popits Cycle Triggered   [/]")
                    console.print("[bold yellow]═══════════════════════════════════[/]\n")
                    popits_manager.run_cycle()
                    last_popits_check = current_time
                    console.print(f"\n[cyan]Next Popits check in {POPITS_CONFIG['check_interval']//60} minutes[/]\n")

                if current_time - last_api_call >= 5:
                    # Get user data and farming task status
                    user_data = api.get_user_data()
                    farming_task = api.get_farming_task()
                    last_api_call = current_time

                    if not farming_task or not farming_task.get('reward'):
                        # No farming task, try to start one
                        if DISPLAY_MODE == 'enhanced':
                            show_start_animation()
                        else:
                            console.print("[yellow]No active farming task. Starting...[/]")
                        api.start_farming()
                        time.sleep(2)
                        continue

                    reward_data = farming_task['reward']
                    task_id = farming_task['id']

                    # Check if already claimed
                    if reward_data.get('claimed', False):
                        # Already claimed, start new farming
                        if DISPLAY_MODE == 'enhanced':
                            show_start_animation()
                        else:
                            console.print("[yellow]Reward already claimed. Starting new farming...[/]")
                        api.start_farming()
                        claiming_attempted = False
                        time.sleep(2)
                        continue

                    # Get claim time
                    claim_time = parse_datetime(reward_data['claim_at']).timestamp()

                    # Check if ready to claim
                    if current_time >= claim_time and not claiming_attempted:
                        if DISPLAY_MODE == 'enhanced':
                            show_claim_animation()
                        else:
                            console.print("\n[green]Claiming farming reward...[/]")

                        claim_response = api.claim_farming(task_id)
                        claiming_attempted = True

                        if claim_response['status'] == 'success':
                            console.print("[green]Successfully claimed reward![/]")
                            last_api_call = 0  # Force refresh
                        else:
                            console.print(f"[red]Failed to claim reward: {claim_response['status_code']}[/]")
                            claiming_attempted = False

                        time.sleep(5)
                        continue

                    # Display info based on mode
                    if DISPLAY_MODE == 'enhanced':
                        display_enhanced_info(user_data, farming_task, claim_time, first_run=(last_display_update == 0))
                    else:
                        display_compact_info(user_data, farming_task, claim_time, first_run=(last_display_update == 0))
                    last_display_update = current_time

                elif current_time - last_display_update >= 1:
                    # Update display every second (only if we have data)
                    if user_data and farming_task:
                        if DISPLAY_MODE == 'enhanced':
                            display_enhanced_info(user_data, farming_task, claim_time, first_run=False)
                        else:
                            display_compact_info(user_data, farming_task, claim_time, first_run=False)
                        last_display_update = current_time

                time.sleep(0.1)

            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except TokenExpiredError:
                handle_token_error()
            except Exception as e:
                last_api_call = handle_api_error(e, last_api_call)

    except KeyboardInterrupt:
        handle_program_exit()
    finally:
        # Clean up: close API session
        api.close()
        console.print("[dim]Session closed.[/]")

if __name__ == "__main__":
    main()