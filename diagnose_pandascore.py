import asyncio
from app.services.pandascore import pandascore_client
import json

async def diagnose():
    print('Fetching PandaScore live matches...')
    try:
        matches = await pandascore_client.get_live_matches()
        print(f'Found {len(matches)} live matches')
        
        if matches:
            m = matches[0]
            print(f"\nSample Match Keys: {list(m.keys())}")
            print(f"ID: {m.get('id')}")
            print(f"Name: {m.get('name')}")
            print(f"Status: {m.get('status')}")
            print(f"League: {m.get('league')}")
            
            # Check for external IDs in games array
            games = m.get('games', [])
            if games:
                print(f"\nGames array found ({len(games)} games)")
                g = games[0]
                print(f"Game Keys: {list(g.keys())}")
                print(f"Game ID: {g.get('id')}")
                print(f"Match ID (game): {g.get('match_id')}")
                # Look for external ID
                for k, v in g.items():
                    if 'id' in k.lower():
                        print(f"Found ID field: {k} = {v}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose())
