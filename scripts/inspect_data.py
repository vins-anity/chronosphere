import json
import pandas as pd
from pathlib import Path

def inspect():
    path = Path("data/processed/training_data.jsonl")
    if not path.exists():
        print("No training data found.")
        return

    data = []
    with open(path, "r") as f:
        for line in f:
            data.append(json.loads(line))
    
    if not data:
        print("Empty file.")
        return

    df = pd.DataFrame(data)
    
    # Select interesting columns
    cols = [
        "match_id", "game_time", 
        "draft_score_diff", 
        "radiant_pace_score", "radiant_aggression_score",
        "networth_gini", "carry_efficiency_index"
    ]
    
    print(f"\nLoaded {len(df)} rows.")
    print("\nSample Data (Non-Zero Checks):")
    print("-" * 50)
    
    # Check for non-zero values in new features
    for col in cols[2:]:
        non_zeros = df[df[col] != 0].shape[0]
        if col == "carry_efficiency_index":
             non_zeros = df[df[col] != 1.0].shape[0] # baseline is 1.0
             
        print(f"{col}: {non_zeros} non-default values")
        
    print("\nFirst 5 rows:")
    print(df[cols].head(5).to_string())

if __name__ == "__main__":
    inspect()
