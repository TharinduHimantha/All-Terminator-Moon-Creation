import cv2
import os
import pandas as pd
import numpy as np
import json
from pathlib import Path  

base_dir = Path(__file__).resolve().parent  
img_path = base_dir / "../../Assets-&-Artifacts/Initiation/moon_1920x1080_16x9_30p"  
img_path = img_path.resolve()  


# ---------------- JSON parsing ----------------

with open(img_path / "image_set_metadata.json") as f:
    data = json.load(f)

df = pd.json_normalize(data)

# Sort by time
df["time"] = pd.to_datetime(df["time"], format="%d %b %Y %H:%M UT")
df = df.sort_values("time").reset_index(drop=True)

posangle_list = df["posangle"].values
diameter_list = df["diameter"].values


# ---------------- Image paths ----------------

image_folder = img_path
output_folder_name = "posangle_locked_moon_images"
output_folder = base_dir / "../../Assets-&-Artifacts/Phase-1-Artifacts" / output_folder_name
os.makedirs(output_folder, exist_ok=True)

images = sorted([img for img in os.listdir(image_folder) if img.endswith(".tif")])

# ---------------- Target settings ----------------

TARGET_W = 1920
TARGET_H = 1080

target_diameter = np.median(diameter_list)

# limit scaling (prevents warping)
MIN_SCALE = 0.97
MAX_SCALE = 1.03


# ---------------- Processing ----------------

for i, filename in enumerate(images):

    img_path = os.path.join(image_folder, filename)
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)

    if img is None:
        print(f"Skipping {filename}")
        continue

    h, w = img.shape[:2]

    # ---------------- Handle alpha ----------------
    if img.shape[2] == 4:
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]
    else:
        bgr = img
        alpha = np.ones((h, w), dtype=np.uint8) * 255

    # ---------------- Compute scale ----------------
    current_diameter = diameter_list[i]
    scale = target_diameter / current_diameter

    # Clamp scaling
    scale = np.clip(scale, MIN_SCALE, MAX_SCALE)

    # ---------------- Resize FIRST ----------------
    new_w = int(w * scale)
    new_h = int(h * scale)

    bgr = cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    alpha = cv2.resize(alpha, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    # ---------------- Pad to avoid clipping ----------------
    diag = int(np.sqrt(new_w * new_w + new_h * new_h))

    pad_x = (diag - new_w) // 2
    pad_y = (diag - new_h) // 2

    bgr_padded = cv2.copyMakeBorder(
        bgr,
        pad_y, pad_y,
        pad_x, pad_x,
        borderType=cv2.BORDER_CONSTANT,
        value=(0, 0, 0)
    )

    alpha_padded = cv2.copyMakeBorder(
        alpha,
        pad_y, pad_y,
        pad_x, pad_x,
        borderType=cv2.BORDER_CONSTANT,
        value=0
    )

    ph, pw = bgr_padded.shape[:2]
    center = (pw // 2, ph // 2)

    # ---------------- Rotate ONLY (no scaling here) ----------------
    angle = -posangle_list[i]

    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    rotated_bgr = cv2.warpAffine(
        bgr_padded, M, (pw, ph),
        flags=cv2.INTER_CUBIC
    )

    rotated_alpha = cv2.warpAffine(
        alpha_padded, M, (pw, ph),
        flags=cv2.INTER_CUBIC
    )

    # ---------------- Merge RGBA ----------------
    rotated_rgba = cv2.cvtColor(rotated_bgr, cv2.COLOR_BGR2BGRA)
    rotated_rgba[:, :, 3] = rotated_alpha

    # ---------------- Center crop to 1920x1080 ----------------
    start_x = (pw - TARGET_W) // 2
    start_y = (ph - TARGET_H) // 2

    final = rotated_rgba[
        start_y:start_y + TARGET_H,
        start_x:start_x + TARGET_W
    ]

    # ---------------- Save ----------------
    output_path = os.path.join(output_folder, filename)
    cv2.imwrite(output_path, final)

    print(f"OK {output_path} | scale={scale:.4f}")