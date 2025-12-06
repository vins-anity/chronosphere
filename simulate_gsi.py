"""
GSI Simulation Script for Development Testing
Simulates a Dota 2 match progressing over time, sending realistic game state data.
"""
import asyncio
import aiohttp
import random
import time

GSI_ENDPOINT = "http://localhost:8000/api/v1/gsi"

async def send_gsi_tick(session, game_time: int, radiant_gold: int, dire_gold: int, 
                         radiant_xp: int, dire_xp: int, radiant_kills: int, dire_kills: int):
    """Send a single GSI tick to the backend."""
    payload = {
        "provider": {
            "name": "Dota 2",
            "appid": 570,
            "version": 47,
            "timestamp": int(time.time())
        },
        "map": {
            "name": "start",
            "matchid": "test_simulation_001",
            "game_time": game_time,
            "clock_time": game_time,
            "daytime": game_time % 600 < 300,  # Day/night cycle
            "nightstalker_night": False,
            "game_state": "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS",
            "paused": False,
            "win_team": "none",
            "customgamename": "",
            "radiant_ward_purchase_cooldown": 0,
            "dire_ward_purchase_cooldown": 0,
            "roshan_state": "alive",
            "roshan_state_end_seconds": 0,
            "radiant_score": radiant_kills,
            "dire_score": dire_kills
        },
        "player": {
            "steamid": "76561198000000000",
            "name": "Spectator",
            "activity": "watching",
            "kills": 0,
            "deaths": 0,
            "assists": 0,
            "last_hits": 0,
            "denies": 0,
            "kill_streak": 0,
            "commands_issued": 0,
            "gold": 0,
            "gold_reliable": 0,
            "gold_unreliable": 0,
            "gpm": 0,
            "xpm": 0
        },
        # Custom fields for our ML model
        "radiant": {
            "net_worth": radiant_gold,
            "total_xp": radiant_xp,
            "kills": radiant_kills
        },
        "dire": {
            "net_worth": dire_gold,
            "total_xp": dire_xp,
            "kills": dire_kills
        }
    }
    
    try:
        async with session.post(GSI_ENDPOINT, json=payload) as response:
            if response.status == 200:
                return True
            else:
                print(f"GSI tick failed: {response.status}")
                return False
    except Exception as e:
        print(f"Error sending GSI tick: {e}")
        return False

async def simulate_match():
    """Simulate a 30-minute match with realistic progression."""
    print("=" * 60)
    print("GSI MATCH SIMULATION")
    print("=" * 60)
    print("Simulating a 30-minute match with realistic game state changes")
    print("Watch your browser at http://localhost:3000 for live updates!")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Initial game state
        game_time = 0
        radiant_gold = 3000  # Starting gold for team (5 heroes x 600)
        dire_gold = 3000
        radiant_xp = 0
        dire_xp = 0
        radiant_kills = 0
        dire_kills = 0
        
        # Simulate 30 minutes (1800 seconds) in fast-forward
        # Each tick = 30 seconds of game time, sent every 1 second real time
        tick_interval = 1.0  # seconds between ticks
        game_time_per_tick = 30  # game seconds per tick
        
        total_ticks = 60  # 30 minutes of game time
        
        for tick in range(total_ticks):
            game_time = tick * game_time_per_tick
            
            # Simulate gold gain (GPM varies based on game phase)
            base_gpm = 200 + (game_time // 300) * 50  # GPM increases over time
            radiant_gold += int(base_gpm * (game_time_per_tick / 60) * random.uniform(0.9, 1.1))
            dire_gold += int(base_gpm * (game_time_per_tick / 60) * random.uniform(0.9, 1.1))
            
            # Simulate XP gain
            base_xpm = 300 + (game_time // 300) * 30
            radiant_xp += int(base_xpm * (game_time_per_tick / 60) * random.uniform(0.9, 1.1))
            dire_xp += int(base_xpm * (game_time_per_tick / 60) * random.uniform(0.9, 1.1))
            
            # Simulate kills (more frequent as game progresses)
            kill_chance = 0.1 + (game_time / 1800) * 0.2
            if random.random() < kill_chance:
                if random.random() < 0.5:
                    radiant_kills += 1
                    radiant_gold += 300  # Kill bounty
                else:
                    dire_kills += 1
                    dire_gold += 300
            
            # Add some variance - sometimes one team gets ahead
            if tick == 20:  # At 10 minutes, radiant gets a small lead
                radiant_gold += 2000
                radiant_kills += 2
                print(">>> RADIANT gets first blood advantage!")
            
            if tick == 40:  # At 20 minutes, dire makes a comeback
                dire_gold += 3000
                dire_kills += 3
                print(">>> DIRE makes a comeback with a teamfight win!")
            
            # Send the GSI tick
            success = await send_gsi_tick(
                session, game_time, radiant_gold, dire_gold,
                radiant_xp, dire_xp, radiant_kills, dire_kills
            )
            
            # Calculate current advantage
            gold_diff = radiant_gold - dire_gold
            advantage = "RADIANT" if gold_diff > 0 else "DIRE"
            
            # Print status
            minutes = game_time // 60
            seconds = game_time % 60
            print(f"[{minutes:02d}:{seconds:02d}] Gold: R {radiant_gold:,} vs D {dire_gold:,} | "
                  f"Diff: {gold_diff:+,} ({advantage}) | "
                  f"Kills: {radiant_kills}-{dire_kills} | "
                  f"{'✓' if success else '✗'}")
            
            await asyncio.sleep(tick_interval)
        
        print("=" * 60)
        print("MATCH COMPLETE!")
        print(f"Final Gold: Radiant {radiant_gold:,} vs Dire {dire_gold:,}")
        print(f"Final Kills: {radiant_kills} - {dire_kills}")
        print("=" * 60)

if __name__ == "__main__":
    print("\nStarting GSI simulation...")
    print("Make sure your backend is running on port 8000")
    print("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(simulate_match())
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
