import cv2
import numpy as np

# =====================================================
# INPUT DATA
# =====================================================

subsolar_lon = 116.296
subsolar_lat = 1.473

subearth_lon = 5.652
subearth_lat = -0.283

position_angle = 21.454

# =====================================================
# IMAGE
# =====================================================

img = cv2.imread("moon4344.tif")

if img is None:
    raise RuntimeError("Could not load image")

h, w = img.shape[:2]

cx = w // 2
cy = h // 2

# Lunar radius in pixels
Rpix = 472

# =====================================================
# PARAMETERS
# =====================================================

INNER = 80.0
OUTER = 90.0

# Overlay opacity
ALPHA = 0.55

# =====================================================
# LAT/LON -> XYZ
# =====================================================

def latlon_to_xyz(lat_deg, lon_deg):

    lat = np.radians(lat_deg)
    lon = np.radians(lon_deg)

    return np.array([
        np.cos(lat) * np.cos(lon),
        np.cos(lat) * np.sin(lon),
        np.sin(lat)
    ])

sun = latlon_to_xyz(subsolar_lat, subsolar_lon)
earth = latlon_to_xyz(subearth_lat, subearth_lon)

# =====================================================
# OBSERVER FRAME
# =====================================================

z_cam = earth.copy()
z_cam /= np.linalg.norm(z_cam)

north = np.array([0.0, 0.0, 1.0])

if abs(np.dot(z_cam, north)) > 0.99:
    north = np.array([0.0, 1.0, 0.0])

x_cam = np.cross(north, z_cam)
x_cam /= np.linalg.norm(x_cam)

y_cam = np.cross(z_cam, x_cam)
y_cam /= np.linalg.norm(y_cam)

R = np.vstack([
    x_cam,
    y_cam,
    z_cam
])

# =====================================================
# POSITION ANGLE ROTATION
# =====================================================

pa = np.radians(position_angle)

Rpa = np.array([
    [ np.cos(pa), -np.sin(pa), 0 ],
    [ np.sin(pa),  np.cos(pa), 0 ],
    [ 0,           0,          1 ]
])

Rtotal = Rpa @ R

sun_obs = Rtotal @ sun

# =====================================================
# PIXEL GRID
# =====================================================

yy, xx = np.mgrid[0:h, 0:w]

x = (xx - cx) / Rpix
y = -(yy - cy) / Rpix

r2 = x*x + y*y

visible_disk = r2 <= 1.0

z = np.zeros_like(x)
z[visible_disk] = np.sqrt(1.0 - r2[visible_disk])

# Surface normals in observer frame

nx = x
ny = y
nz = z

# =====================================================
# SOLAR INCIDENCE ANGLE
# =====================================================

cos_i = (
    nx * sun_obs[0] +
    ny * sun_obs[1] +
    nz * sun_obs[2]
)

cos_i = np.clip(cos_i, -1.0, 1.0)

incidence = np.degrees(np.arccos(cos_i))

# =====================================================
# SELECT BAND
# =====================================================

band = (
    visible_disk &
    (incidence >= INNER) &
    (incidence <= OUTER)
)

# =====================================================
# NORMALIZE WITHIN BAND
# 75° -> 0
# 85° -> 255
# =====================================================

norm = np.zeros_like(incidence)

norm[band] = (
    (incidence[band] - INNER)
    / (OUTER - INNER)
)

heat = np.zeros((h, w), dtype=np.uint8)

heat[band] = (255 * norm[band]).astype(np.uint8)

# =====================================================
# COLOR MAP
# =====================================================

heat_color = cv2.applyColorMap(
    heat,
    cv2.COLORMAP_TURBO
)

# =====================================================
# OVERLAY ONLY ON BAND
# =====================================================

result = img.copy()

for c in range(3):

    result[:,:,c] = np.where(
        band,
        (
            img[:,:,c].astype(np.float32) * (1.0 - ALPHA)
            + heat_color[:,:,c].astype(np.float32) * ALPHA
        ),
        img[:,:,c]
    )

result = result.astype(np.uint8)

# =====================================================
# DISPLAY
# =====================================================

cv2.namedWindow("Terminator Band", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Terminator Band", w // 2, h // 2)

cv2.imshow("Terminator Band", result)

cv2.waitKey(0)
cv2.destroyAllWindows()