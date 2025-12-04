import asyncio
import httpx
import uvicorn
import multiprocessing
import time
import sys
import os


# Function to run uvicorn in a separate process
def run_server():
    sys.path.append(os.getcwd())
    # Configure logging to file
    from uvicorn.config import LOGGING_CONFIG
    
    # Redirect stdout/stderr to file
    sys.stdout = open("uvicorn_stdout.log", "w")
    sys.stderr = open("uvicorn_stderr.log", "w")
    
    uvicorn.run("app.ingest.main:app", host="127.0.0.1", port=8002, log_level="info")

async def verify():
    print("Starting verification for Phase 4 (Database)...")
    
    # Start server
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()
    print("Started uvicorn process. Waiting 5 seconds for startup...")
    await asyncio.sleep(5)
    
    try:
        # Send GSI Data via HTTP
        url = "http://127.0.0.1:8002/api/v1/gsi"
        print("Sending 10 mock GSI ticks...")
        
        async with httpx.AsyncClient() as client:
            for i in range(15):
                payload = {
                    "provider": {"timestamp": 123456789 + i},
                    "map": {
                        "clock_time": 100 + i,
                        "radiant_win_chance": 50
                    }
                }
                await client.post(url, json=payload)
                await asyncio.sleep(0.2) # Send over 3 seconds
        
        print("Sent 15 ticks. Waiting 2 seconds...")
        await asyncio.sleep(2)
        
        # Check Database
        print("Checking Database for ticks...")
        # Check Database
        print("Checking Database for ticks...")
        from app.core.db import get_session
        from app.models import Tick
        from sqlmodel import select

        async for session in get_session():
            statement = select(Tick)
            results = await session.exec(statement)
            ticks = results.all()
            print(f"Found {len(ticks)} ticks in the database.")
            
            if len(ticks) > 0:
                print("✅ SUCCESS: Ticks persisted to Database.")
                print(f"Sample Tick: {ticks[0]}")
            else:
                print("❌ FAILURE: No ticks found in Database.")
            break
                
    except Exception as e:
        print(f"Error during verification: {e}")
    finally:
        server_process.terminate()
        server_process.join()

if __name__ == "__main__":
    asyncio.run(verify())
