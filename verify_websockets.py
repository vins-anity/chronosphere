import asyncio
import websockets
import json
import httpx
import uvicorn
import multiprocessing
import time
import sys
import os

# Function to run uvicorn in a separate process
def run_server():
    sys.path.append(os.getcwd())
    uvicorn.run("app.ingest.main:app", host="127.0.0.1", port=8001, log_level="info")

async def verify():
    print("Starting verification for Phase 3 (The Eyes)...")
    
    # Start server
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()
    print("Started uvicorn process. Waiting 5 seconds for startup...")
    await asyncio.sleep(5)
    
    try:
        # Connect to WebSocket
        uri = "ws://127.0.0.1:8001/ws/live"
        print(f"Connecting to WebSocket {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket Connected!")
            
            # Send GSI Data via HTTP
            url = "http://127.0.0.1:8001/api/v1/gsi"
            payload = {
                "provider": {"timestamp": 123456789},
                "map": {
                    "clock_time": 100,
                    "radiant_win_chance": 50
                }
            }
            print("Sending GSI data via HTTP...")
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                print(f"HTTP Response: {response.status_code}")
            
            # Wait for WebSocket Message
            print("Waiting for WebSocket message...")
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)
            
            print(f"Received WS Message: {data}")
            
            if data.get("type") == "update" and "win_probability" in data:
                print("✅ SUCCESS: Received win probability update via WebSocket.")
            else:
                print("❌ FAILURE: Invalid message format.")
                
    except Exception as e:
        print(f"Error during verification: {e}")
    finally:
        server_process.terminate()
        server_process.join()

if __name__ == "__main__":
    # Install required packages for verification if missing
    # subprocess.run(["uv", "add", "websockets", "httpx"]) 
    # Assuming they are installed or available. If not, user might need to install.
    # Actually, let's just run it.
    asyncio.run(verify())
