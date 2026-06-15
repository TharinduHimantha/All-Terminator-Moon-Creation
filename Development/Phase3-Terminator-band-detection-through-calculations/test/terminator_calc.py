import cv2
import numpy as np

# =====================================================
# INPUT DATA
# =====================================================

    # {
    #     "time": "30 Jun 2025 23:00 UT",
    #     "phase": 32.37,
    #     "age": 5.52,
    #     "diameter": 1817.4,
    #     "distance": 394368,
    #     "j2000": {
    #         "ra": 11.2857,
    #         "dec": 4.844
    #     },
    #     "subsolar": {
    #         "lon": 116.296,
    #         "lat": 1.473
    #     },
    #     "subearth": {
    #         "lon": 5.652,
    #         "lat": -0.283
    #     },
    #     "posangle": 21.454
    # }

subsolar_lon = 116.296
subsolar_lat = 1.473

subearth_lon = 5.652
subearth_lat = -0.283

position_angle = 21.454

# =====================================================
# IMAGE
# =====================================================

img = cv2.imread("moon4344.tif")

h, w = img.shape[:2]

cx = w // 2
cy = h // 2

Rpix = 472

# =====================================================
# SPHERICAL -> CARTESIAN
# =====================================================

def latlon_to_xyz(lat_deg, lon_deg):

    lat = np.radians(lat_deg)
    lon = np.radians(lon_deg)

    return np.array([
        np.cos(lat)*np.cos(lon),
        np.cos(lat)*np.sin(lon),
        np.sin(lat)
    ])

sun = latlon_to_xyz(subsolar_lat, subsolar_lon)
earth = latlon_to_xyz(subearth_lat, subearth_lon)

# =====================================================
# OBSERVER COORDINATE SYSTEM
# =====================================================

z_cam = earth
z_cam /= np.linalg.norm(z_cam)

north = np.array([0.0, 0.0, 1.0])

# avoid singularity if earth near pole
if abs(np.dot(z_cam, north)) > 0.99:
    north = np.array([0.0, 1.0, 0.0])

x_cam = np.cross(north, z_cam)
x_cam /= np.linalg.norm(x_cam)

y_cam = np.cross(z_cam, x_cam)
y_cam /= np.linalg.norm(y_cam)

# Moon-fixed -> observer frame

R = np.vstack([
    x_cam,
    y_cam,
    z_cam
])

# =====================================================
# APPLY POSITION ANGLE
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
# TERMINATOR BASIS
# =====================================================

a = np.array([1.0,0.0,0.0])

if abs(np.dot(a, sun_obs)) > 0.95:
    a = np.array([0.0,1.0,0.0])

u = np.cross(sun_obs, a)
u /= np.linalg.norm(u)

v = np.cross(sun_obs, u)
v /= np.linalg.norm(v)

# =====================================================
# GENERATE TERMINATOR
# =====================================================

# curve = []

# for t in np.linspace(0, 2*np.pi, 4000):

#     p = u*np.cos(t) + v*np.sin(t)

#     # visible hemisphere only
#     if p[2] > 0:

#         x = cx + Rpix*p[0]
#         y = cy - Rpix*p[1]

#         curve.append([int(x), int(y)])

# curve = np.array(curve)

# # =====================================================
# # DRAW
# # =====================================================

# cv2.polylines(
#     img,
#     [curve],
#     False,
#     (0,255,0),
#     2,
#     cv2.LINE_AA
# )

# cv2.namedWindow("Terminator", cv2.WINDOW_NORMAL)
# cv2.resizeWindow("Terminator", w//2, h//2)  # width, height

# cv2.imshow("Terminator", img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()


# -----------------------------------------------------
# PARAMETERS
# -----------------------------------------------------

INNER = 80.0
OUTER = 90.0

# -----------------------------------------------------
# BUILD PIXEL GRID
# -----------------------------------------------------

yy, xx = np.mgrid[0:h, 0:w]

x = (xx - cx) / Rpix
y = -(yy - cy) / Rpix

r2 = x*x + y*y

visible_disk = r2 <= 1.0

# sphere z coordinate

z = np.zeros_like(x)
z[visible_disk] = np.sqrt(1.0 - r2[visible_disk])

# observer-frame surface normals

nx = x
ny = y
nz = z

# -----------------------------------------------------
# INCIDENCE ANGLE
# -----------------------------------------------------

cos_i = (
    nx * sun_obs[0] +
    ny * sun_obs[1] +
    nz * sun_obs[2]
)

cos_i = np.clip(cos_i, -1.0, 1.0)

incidence = np.degrees(np.arccos(cos_i))

# -----------------------------------------------------
# TERMINATOR BAND
# -----------------------------------------------------

band = (
    visible_disk &
    (incidence >= INNER) &
    (incidence <= OUTER)
)

# -----------------------------------------------------
# GRADIENT WEIGHT
# -----------------------------------------------------

weight = np.zeros_like(incidence)

weight[band] = (
    (incidence[band] - INNER)
    / (OUTER - INNER)
)

weight = np.clip(weight, 0.0, 1.0)

# -----------------------------------------------------
# CREATE OVERLAY
# -----------------------------------------------------

overlay = img.copy()

overlay[:,:,1] = np.maximum(
    overlay[:,:,1],
    (255 * weight).astype(np.uint8)
)

overlay[:,:,2] = np.maximum(
    overlay[:,:,2],
    (100 * weight).astype(np.uint8)
)

# -----------------------------------------------------
# BLEND
# -----------------------------------------------------

result = cv2.addWeighted(
    img,
    1.0,
    overlay,
    0.6,
    0
)

cv2.namedWindow("Terminator", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Terminator", w//2, h//2)  # width, height

cv2.imshow("Terminator", result)
cv2.waitKey(0)
cv2.destroyAllWindows()