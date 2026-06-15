import cv2
import os
import pandas as pd
import numpy as np
import json

# =====================================================
# LOAD METADATA
# =====================================================

with open("moon_1920x1080_16x9_30p/image_set_metadata.json") as f:
    data = json.load(f)

df = pd.json_normalize(data)

df["time"] = pd.to_datetime(df["time"], format="%d %b %Y %H:%M UT")
df = df.sort_values("time").reset_index(drop=True)

# Ensure alignment with images
posangle_list = df["posangle"].values
subsolar_lon_list = df["subsolar.lon"].values
subsolar_lat_list = df["subsolar.lat"].values
subearth_lon_list = df["subearth.lon"].values
subearth_lat_list = df["subearth.lat"].values


# =====================================================
# PATHS
# =====================================================

image_folder = "moon_1920x1080_16x9_30p"
output_folder = "terminator_calc_outputs"
os.makedirs(output_folder, exist_ok=True)

images = sorted([f for f in os.listdir(image_folder) if f.endswith(".tif")])


# =====================================================
# IMAGE CONSTANTS (NO RESIZE LOGIC HERE)
# =====================================================

TARGET_W = 1920
TARGET_H = 1080

cx = TARGET_W // 2
cy = TARGET_H // 2

Rpix = 472  # keep your calibrated value


# =====================================================
# PARAMETERS
# =====================================================

INNER = 85.0
OUTER = 90.0
ALPHA = 0.55


# =====================================================
# HELPERS
# =====================================================

def latlon_to_xyz(lat_deg, lon_deg):
    lat = np.radians(lat_deg)
    lon = np.radians(lon_deg)

    return np.array([
        np.cos(lat) * np.cos(lon),
        np.cos(lat) * np.sin(lon),
        np.sin(lat)
    ])


# =====================================================
# PROCESS LOOP
# =====================================================

for i, filename in enumerate(images):

    path = os.path.join(image_folder, filename)
    img = cv2.imread(path)

    if img is None:
        print("Skipping", filename)
        continue

    h, w = img.shape[:2]

    # -------------------------------------------------
    # EPHEMERIS INPUT
    # -------------------------------------------------

    sun = latlon_to_xyz(
        subsolar_lat_list[i],
        subsolar_lon_list[i]
    )

    earth = latlon_to_xyz(
        subearth_lat_list[i],
        subearth_lon_list[i]
    )

    # -------------------------------------------------
    # CAMERA FRAME (EARTH UP)
    # -------------------------------------------------

    z_cam = earth / np.linalg.norm(earth)

    north = np.array([0.0, 0.0, 1.0])

    if abs(np.dot(z_cam, north)) > 0.99:
        north = np.array([0.0, 1.0, 0.0])

    x_cam = np.cross(north, z_cam)
    x_cam /= np.linalg.norm(x_cam)

    y_cam = np.cross(z_cam, x_cam)
    y_cam /= np.linalg.norm(y_cam)

    R = np.vstack([x_cam, y_cam, z_cam])

    # -------------------------------------------------
    # POSITION ANGLE ROTATION
    # -------------------------------------------------

    pa = np.radians(posangle_list[i])

    Rpa = np.array([
        [np.cos(pa), -np.sin(pa), 0],
        [np.sin(pa),  np.cos(pa), 0],
        [0, 0, 1]
    ])

    Rtotal = Rpa @ R

    sun_obs = Rtotal @ sun

    # -------------------------------------------------
    # PIXEL GRID
    # -------------------------------------------------

    yy, xx = np.mgrid[0:h, 0:w]

    x = (xx - cx) / Rpix
    y = -(yy - cy) / Rpix

    r2 = x*x + y*y

    visible = r2 <= 1.0

    z = np.zeros_like(x)
    z[visible] = np.sqrt(1.0 - r2[visible])

    nx, ny, nz = x, y, z

    # -------------------------------------------------
    # INCIDENCE ANGLE
    # -------------------------------------------------

    cos_i = (
        nx * sun_obs[0] +
        ny * sun_obs[1] +
        nz * sun_obs[2]
    )

    cos_i = np.clip(cos_i, -1, 1)

    incidence = np.degrees(np.arccos(cos_i))

    # -------------------------------------------------
    # BAND
    # -------------------------------------------------

    band = (
        visible &
        (incidence >= INNER) &
        (incidence <= OUTER)
    )

    # -------------------------------------------------
    # GRADIENT (75 → 0, 85 → 1)
    # -------------------------------------------------

    norm = np.zeros_like(incidence)

    norm[band] = (incidence[band] - INNER) / (OUTER - INNER)

    heat = np.zeros((h, w), dtype=np.uint8)
    heat[band] = (255 * norm[band]).astype(np.uint8)

    heat_color = cv2.applyColorMap(heat, cv2.COLORMAP_TURBO)

    # -------------------------------------------------
    # OVERLAY ONLY ON BAND
    # -------------------------------------------------

    result = img.copy()

    mask3 = np.repeat(band[:, :, None], 3, axis=2)

    result[mask3] = (
        img[mask3].astype(np.float32) * (1 - ALPHA)
        + heat_color[mask3].astype(np.float32) * ALPHA
    ).astype(np.uint8)

    # -------------------------------------------------
    # SAVE
    # -------------------------------------------------

    out_path = os.path.join(output_folder, filename)
    cv2.imwrite(out_path, result)

    print("Saved:", out_path)