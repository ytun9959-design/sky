import asyncio
import sky

async def main():
    try:
        # မူလ Device ID စနစ်အတိုင်း အလုပ်လုပ်စေရန်
        device_id = sky.get_system_key()
    except Exception:
        pass

    try:
        # Online Bypass / Brute force စနစ်သက်သက်ကိုသာ လှမ်းခေါ်ရန်
        bypass_engine = sky.InternetAccess() 
        await bypass_engine.execute()
    except Exception:
        pass

if __name__ == "__main__":
    try:
        # Low-end device များအတွက် asyncio ဖြင့် အလုပ်လုပ်စေရန်
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
