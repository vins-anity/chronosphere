import subprocess
import time
import urllib.request
import json
import sys
import os

def verify():
    print("Starting verification for Phase 2 (The Brain)...")
    cmd = [sys.executable, "-m", "uvicorn", "app.ingest.main:app", "--port", "8001", "--host", "127.0.0.1"]
    print(f"Running command: {' '.join(cmd)}")
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.getcwd()
    )
    
    print("Started uvicorn process. Waiting 10 seconds for startup...")
    time.sleep(10) 
    
    if proc.poll() is not None:
        print("Uvicorn process died unexpectedly!")
        stdout, stderr = proc.communicate()
        print(stderr)
        return

    try:
        # Send request with realistic GSI data
        url = "http://127.0.0.1:8001/api/v1/gsi"
        
        # Simulate a sequence of ticks
        for i in range(5):
            clock_time = 100 + i
            payload = {
                "provider": {"timestamp": 123456789 + i},
                "map": {
                    "clock_time": clock_time,
                    "radiant_win_chance": 50 + i # Mock data
                }
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Sending tick {i+1} (Clock: {clock_time})...")
            with urllib.request.urlopen(req) as response:
                pass
            time.sleep(0.5)
            
        print("Waiting for worker to process...")
        time.sleep(3) 
        
        # Terminate and check logs
        proc.terminate()
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
        
        print("\n--- Uvicorn Stderr ---")
        print(stderr)
        print("----------------------\n")
        
        if "Win Prob:" in stderr:
            print("✅ SUCCESS: Worker generated a win probability.")
        else:
            print("❌ FAILURE: Worker did not log win probability.")
            
    except Exception as e:
        print(f"Error during verification: {e}")
        proc.kill()
        stdout, stderr = proc.communicate()
        print(stderr)

if __name__ == "__main__":
    verify()
