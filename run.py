import sys
import asyncio
import threading
import sky

if __name__ == "__main__":
    if sky.check_approval():
        threading.Thread(target=sky.continuous_auth_check, daemon=True).start()
        
        try:
            asyncio.run(sky.InternetAccess().execute())
        except KeyboardInterrupt:
            print("\n\033[1;31m[!] Stopped.\033[1;00m")
    else:
        sys.exit()
