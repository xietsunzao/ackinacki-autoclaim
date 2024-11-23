import sys
import time
from datetime import datetime
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
    
    try:
        while True:
            try:
                current_time = time.time()
                
                if current_time - last_api_call >= 5:
                    user_data = api.get_user_data()
                    last_api_call = current_time
                    
                    # Check if farming needs to be started
                    daily_farming = user_data.get('daily_farming', {}).get('daily_farming_v2', {})
                    if not daily_farming or daily_farming.get('claim_at') is None:
                        console.print("[yellow]Starting farming session...[/]")
                        api.start_farming()
                        time.sleep(5)
                        continue
                    
                    claim_time = datetime.fromisoformat(daily_farming['claim_at'].replace('Z', '+00:00')).timestamp()
                    reward = daily_farming.get('reward', 0)
                    
                    # Update display
                    display_info(user_data, claim_time, reward, first_run=(last_display_update == 0))
                    last_display_update = current_time
                
                # Update timer more frequently
                elif current_time - last_display_update >= 1:
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