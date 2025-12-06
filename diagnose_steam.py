import asyncio
import httpx
import json

API_KEY = "F6564639F5701B62C18EC360814F0080" # From .env.example (User's key might be different, but I'll try without first or use the one from code if accessible)
# Actually better to import settings
from app.core.config import settings

async def diagnose():
    url = "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v1/"
    params = {"key": settings.STEAM_API_KEY}
    
    print(f"Fetching from {url}...")
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(resp.text)
            return
            
        data = resp.json()
        games = data.get("result", {}).get("games", [])
        print(f"Total Games found: {len(games)}")
        
        found_tundra = False
        
        for g in games:
            r_name = g.get("radiant_team", {}).get("team_name", "Unknown")
            d_name = g.get("dire_team", {}).get("team_name", "Unknown")
            specs = g.get("spectators", 0)
            scoreboard = g.get("scoreboard")
            
            # Check if this is the target match
            if "Tundra" in r_name or "Tundra" in d_name or "MOUZ" in r_name or "MOUZ" in d_name:
                found_tundra = True
                print("\n!!! FOUND TARGET MATCH !!!")
                print(f"Match ID: {g.get('match_id')}")
                print(f"Teams: {r_name} vs {d_name}".encode('utf-8', 'replace').decode('utf-8'))
                print(f"Spectators: {specs}")
                print(f"Scoreboard present: {bool(scoreboard)}")
                if scoreboard:
                    print(f"Duration: {scoreboard.get('duration')}")
                else:
                    print("Duration: None (Drafting?)")
                
                # Simulate Filter Logic
                has_default = r_name in ["radiant", "Unknown", ""] and d_name in ["dire", "Unknown", ""]
                is_pop = specs > 100
                print(f"Filter Check: DefaultNames={has_default}, Popular={is_pop}")
            
            # Print minimal info for all potential pros
            if specs > 5:
                 msg = f"High Spec Match: {r_name} vs {d_name} ({specs} specs) - Scoreboard: {bool(scoreboard)}"
                 print(msg.encode('utf-8', 'replace').decode('utf-8'))

        if not found_tundra:
            print("\n❌ Tundra match NOT found in Steam response.")

if __name__ == "__main__":
    asyncio.run(diagnose())
