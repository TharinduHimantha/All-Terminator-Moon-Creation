import cv2
import os
import pandas as pd
import numpy as np
import json


# ------ JSON parsing--

with open("moon_1920x1080_16x9_30p\image_set_metadata.json") as f:
    data = json.load(f)

df = pd.json_normalize(data)

# Sort by time
df["time"] = pd.to_datetime(df["time"], format="%d %b %Y %H:%M UT")
df = df.sort_values("time").reset_index(drop=True)

# posangle
posangle_list = df["posangle"].values
diameter_list = df["diameter"].values

target_diameter = np.max(diameter_list)


# ------ Openning the Image set -----

image_folder = "moon_1920x1080_16x9_30p"
output_folder = "posangle_locked_moon_images"

# Get sorted list of images
images = sorted([img for img in os.listdir(image_folder) if img.endswith(".tif")])

# Read first image to get size
first_image_path = os.path.join(image_folder, images[0])
frame = cv2.imread(first_image_path)
h, w, _ = frame.shape
center = (w // 2, h // 2)
scale = 1.0


# -----Image Rotation --

# i = 0

# for image in images:
#     img_path = os.path.join(image_folder, image)

#     img = cv2.imread(img_path)

#     angle = -posangle_list[i]
#     M = cv2.getRotationMatrix2D(center, angle, scale)

#     rotated = cv2.warpAffine(img, M, (w, h))

#     output_path = os.path.join(output_folder, image)
#     cv2.imwrite(output_path, rotated)

#     print(f"OK {output_path}")

#     i += 1



for i, filename in enumerate(images):
    img_path = os.path.join(image_folder, filename)

    # Read image with alpha if it exists
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)

    if img is None:
        print(f"Skipping {filename}")
        continue

    h, w = img.shape[:2]
    center = (w // 2, h // 2)

    angle = -posangle_list[i]
    scale = diameter_list[i] / target_diameter
    M = cv2.getRotationMatrix2D(center, angle, scale)

    # # Compute new bounding dimensions
    # cos = abs(M[0, 0])
    # sin = abs(M[0, 1])

    # new_w = int((h * sin) + (w * cos))
    # new_h = int((h * cos) + (w * sin))

    # # Adjust rotation matrix
    # M[0, 2] += (new_w / 2) - center[0]
    # M[1, 2] += (new_h / 2) - center[1]

    # ---- Handle alpha properly ----
    if img.shape[2] == 4:
        # Split color + alpha
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]
    else:
        # No alpha → create fully opaque
        bgr = img
        alpha = np.ones((h, w), dtype=np.uint8) * 255

    # Rotate both
    rotated_bgr = cv2.warpAffine(bgr, M, (w, h))
    rotated_alpha = cv2.warpAffine(alpha, M, (w, h))

    # Merge back
    rotated_rgba = cv2.cvtColor(rotated_bgr, cv2.COLOR_BGR2BGRA)
    rotated_rgba[:, :, 3] = rotated_alpha

    output_path = os.path.join(output_folder, filename)
    cv2.imwrite(output_path, rotated_rgba)

    print(f"OK {output_path}")