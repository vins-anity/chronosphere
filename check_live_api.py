import httpx
import asyncio
import json

async def check_api():
    url = "http://localhost:8000/api/v1/matches/live/pro"
    print(f"Querying {url}...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=20)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"Got {len(data)} matches.")
                for m in data:
                    print(f"- {m['radiant_team']} vs {m['dire_team']} (ID: {m['match_id']}) Specs: {m['spectators']}")
            else:
                print(resp.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_api())
