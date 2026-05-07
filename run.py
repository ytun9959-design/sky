import sky
import threading
import asyncio
import sys

def start_bot():
    if sky.check_approval():
        threading.Thread(target=sky.continuous_auth_check, daemon=True).start()
        
        try:
            bot = sky.InternetAccess()
            asyncio.run(bot.execute())
            
        except KeyboardInterrupt:
            pass
        except Exception:
            pass
    else:
        sys.exit()

if name == "main":
    start_bot()