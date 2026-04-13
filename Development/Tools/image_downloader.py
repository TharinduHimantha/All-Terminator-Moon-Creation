import os
import requests
from pathlib import Path  

base_dir = Path(__file__).resolve().parent  
out = base_dir / "../../Assets-&-Artifacts/Initiation/moon_1920x1080_16x9_30p"  
out = out.resolve()  

base = "https://svs.gsfc.nasa.gov/vis/a000000/a005400/a005415/frames/1920x1080_16x9_30p/plain//moon."

out.mkdir(parents=True, exist_ok=True)

for i in range(5043, 5063):
    num = str(i).zfill(4)
    url = f"{base}{num}.tif"
    path = f"{out}/moon.{num}.tif"

    if os.path.exists(path):
        continue

    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        print("OK", num)
    else:
        print("MISS", num)