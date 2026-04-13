'''
Save a json file of the intrested portion of the original dataset

'''

import json
from pathlib import Path  

base_dir = Path(__file__).resolve().parent  

# Load your JSON file
with open(base_dir / "../../Assets-&-Artifacts/Initiation/mooninfo_2025.json", "r") as f:
    data = json.load(f)

# Extract records 4344 to 5062 (inclusive)
# change the range as you prefer
subset = data[4344:5063]  

# Save to a new file
with open(base_dir / "../../Assets-&-Artifacts/Initiation/image_set_metadata.json", "w") as f:
    json.dump(subset, f, indent=4)

print(f"Saved {len(subset)} records.")