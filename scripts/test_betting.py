import httpx
import asyncio

async def test_betting():
    base_url = "http://localhost:8000/api/v1/bets"
    
    async with httpx.AsyncClient() as client:
        # 1. Check Balance (Should create default user)
        print("Checking Balance...")
        resp = await client.get(f"{base_url}/user/balance")
        print(f"Balance Resp: {resp.status_code} - {resp.json()}")
        
        # 2. Place Bet
        print("\nPlacing Bet...")
        bet_data = {
            "match_id": 8592360230, # Random match ID
            "team": "radiant",
            "amount": 100.0,
            "odds": 1.95
        }
        resp = await client.post(f"{base_url}/place", json=bet_data)
        print(f"Place Bet Resp: {resp.status_code} - {resp.json()}")
        
        # 3. Check Balance Again
        print("\nChecking Balance (Post-Bet)...")
        resp = await client.get(f"{base_url}/user/balance")
        print(f"Balance Resp: {resp.status_code} - {resp.json()}")
        
        # 4. Check History
        print("\nChecking History...")
        resp = await client.get(f"{base_url}/history")
        print(f"History Resp: {resp.status_code} - {resp.json()}")

if __name__ == "__main__":
    asyncio.run(test_betting())
