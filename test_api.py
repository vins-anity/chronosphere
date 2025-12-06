"""Debug collector issue."""
import asyncio
from app.ml.collect import OpenDotaCollector

async def debug():
    collector = OpenDotaCollector()
    
    print("Testing fetch_pro_matches...")
    try:
        matches = await collector.fetch_pro_matches(limit=10)
        print(f"Got {len(matches)} matches")
        if matches:
            print(f"First: {matches[0]}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug())
