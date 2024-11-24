import sys
import time
from datetime import datetime, timezone
from src import (
    AckinackiAPI, 
    read_or_create_token, 
    display_info, 
    console,
    handle_api_error,
    handle_program_exit,
    handle_token_error,
    TokenExpiredError,
    TokenInvalidError
)

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
    
    telegram_data = read_or_create_token()
    if not telegram_data:
        console.print("[red]No token provided. Exiting...[/]")
        return
    
    console.print("[green]Starting bot...[/]")
    time.sleep(1)
    console.clear()
    
    api = AckinackiAPI(telegram_data)
    last_api_call = 0
    last_display_update = 0
    claiming_attempted = False
    start_time = None
    
    try:
        while True:
            try:
                current_time = time.time()
                current_time_dt = datetime.now(timezone.utc)
                
                if current_time - last_api_call >= 5:
                    user_data = api.get_user_data()
                    last_api_call = current_time
                    
                    daily_farming = user_data.get('daily_farming', {}).get('daily_farming_v2', {})
                    reward = daily_farming.get('reward', 0)
                    
                    if daily_farming and 'metadata' in daily_farming:
                        start_time_str = daily_farming['metadata'].get('start_at')
                        if start_time_str:
                            start_time = parse_datetime(start_time_str)
                    
                    if daily_farming.get('claimed', False) or not daily_farming or daily_farming.get('claim_at') is None:
                        if start_time and current_time_dt < start_time:
                            display_info(user_data, 0, reward, first_run=True, 
                                       waiting_for_next=True, next_start_time=start_time)
                            last_display_update = current_time
                            time.sleep(1)
                            continue
                        
                        start_response = api.start_farming()
                        if isinstance(start_response, dict) and start_response['status'] == 'waiting':
                            display_info(user_data, 0, reward, first_run=True, 
                                       waiting_for_next=True, next_start_time=start_time)
                            last_display_update = current_time
                            time.sleep(5)
                            continue
                        
                        time.sleep(5)
                        continue
                    
                    claim_time = parse_datetime(daily_farming['claim_at']).timestamp()
                    
                    if current_time >= claim_time and not claiming_attempted:
                        console.print("\n[green]Claiming farming reward...[/]")
                        claim_response = api.claim_farming()
                        claiming_attempted = True
                        
                        if claim_response.status_code == 200:
                            console.print("[green]Successfully claimed reward![/]")
                            last_api_call = 0  # Force refresh user data
                        else:
                            console.print(f"[red]Failed to claim reward: {claim_response.status_code}[/]")
                            claiming_attempted = False  # Allow retry on next iteration
                        
                        time.sleep(5)
                        continue
                    
                    if start_time and current_time_dt < start_time:
                        display_info(user_data, 0, reward, first_run=(last_display_update == 0), 
                                   waiting_for_next=True, next_start_time=start_time)
                    else:
                        display_info(user_data, claim_time, reward, first_run=(last_display_update == 0))
                    last_display_update = current_time
                
                elif current_time - last_display_update >= 1:
                    if start_time and current_time_dt < start_time:
                        display_info(user_data, 0, reward, first_run=False, 
                                   waiting_for_next=True, next_start_time=start_time)
                    else:
                        display_info(user_data, claim_time, reward, first_run=False)
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

if __name__ == "__main__":
    main()