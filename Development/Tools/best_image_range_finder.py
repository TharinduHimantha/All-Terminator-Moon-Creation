import pandas as pd
import numpy as np
import json
from pathlib import Path  

base_dir = Path(__file__).resolve().parent  


def total_variation(lon_w, lat_w):

    lon_range = lon_w.max() - lon_w.min()
    lat_range = lat_w.max() - lat_w.min()
    
    score = (lon_range**2) + (lat_range**2)

    return score



# Load data
with open(base_dir / "../../Assets-&-Artifacts/Initiation/mooninfo_2025.json") as f:
    data = json.load(f)

df = pd.json_normalize(data)

# Sort by time
df["time"] = pd.to_datetime(df["time"], format="%d %b %Y %H:%M UT")
df = df.sort_values("time").reset_index(drop=True)

# Extract lon/lat
lon = df["subearth.lon"].values
lat = df["subearth.lat"].values

window_size = 720  # 30 days


best_change = float("inf")
best_start = 0

# Slide window
for i in range(len(df) - window_size + 1):
    lon_w = lon[i:i+window_size]
    lat_w = lat[i:i+window_size]
    
    change = total_variation(lon_w, lat_w)

    # print(f"{i}: {change}")
    
    if change < best_change:
        best_change = change
        best_start = i

best_end = best_start + window_size - 1

print("Best window (1-based index):", best_start + 1, "to", best_end + 1)
print("Minimum change:", best_change)