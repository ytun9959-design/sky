import sky

print("[*] Starting Sky Blue Scanner...")

try:
    sky.start_bot()
except Exception as e:
    print(f"Error occurred: {e}")
