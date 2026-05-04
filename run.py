import asyncio
import sky

async def main():
    try:
        device_id = sky.get_system_key()
        print(f"Device ID: {device_id}")
    except Exception:
        pass

    try:
        bypass_engine = sky.InternetAccess() 
        await bypass_engine.execute()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
