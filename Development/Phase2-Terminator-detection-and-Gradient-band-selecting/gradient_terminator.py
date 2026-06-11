import cv2
import numpy as np
import os

input_folder = "moon_1920x1080_16x9_30p"
output_folder = "terminator_gradient_band"

os.makedirs(output_folder, exist_ok=True)

images = sorted(
    f for f in os.listdir(input_folder)
    if f.lower().endswith(".tif")
)

previous_curve = None

for filename in images:

    path = os.path.join(input_folder, filename)

    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)

    if img is None:
        continue

    # -----------------------------
    # Alpha handling
    # -----------------------------

    if img.shape[2] == 4:
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]
    else:
        bgr = img
        alpha = np.ones(
            bgr.shape[:2],
            dtype=np.uint8
        ) * 255

    moon_mask = alpha > 0

    gray = cv2.cvtColor(
        bgr,
        cv2.COLOR_BGR2GRAY
    ).astype(np.float32)

    h, w = gray.shape

    points = []

    gradient_threshold = 8

    # -----------------------------
    # Find terminator points
    # -----------------------------

    for y in range(h):

        xs = np.where(
            moon_mask[y]
        )[0]

        if len(xs) < 40:
            continue

        left = xs[0]
        right = xs[-1]

        profile = gray[y, left:right+1]

        if len(profile) < 40:
            continue

        profile = cv2.GaussianBlur(
            profile.reshape(1, -1),
            (1, 11),
            0
        ).flatten()

        grad = np.gradient(profile)

        margin = min(20, len(grad)//4)

        if margin < 2:
            continue

        search = grad[margin:-margin]

        if len(search) == 0:
            continue

        strength = np.max(
            np.abs(search)
        )

        # reject rows without a strong
        # illumination transition

        if strength < gradient_threshold:
            continue

        idx = np.argmax(
            np.abs(search)
        )

        x = left + margin + idx

        points.append([x, y])

    if len(points) < 30:
        print("Too few points:", filename)
        continue

    points = np.array(
        points,
        dtype=np.float32
    )

    # -----------------------------
    # Outlier rejection
    # -----------------------------

    xs = points[:, 0]

    keep = np.ones(
        len(xs),
        dtype=bool
    )

    window = 40
    threshold = 20

    for i in range(window,
                   len(xs)-window):

        local_median = np.median(
            xs[i-window:i+window]
        )

        if abs(xs[i] - local_median) > threshold:
            keep[i] = False

    points = points[keep]

    xs = points[:, 0]
    ys = points[:, 1]

    # # -----------------------------
    # # Moving average smoothing
    # # -----------------------------

    # radius = 15

    # smooth_x = []

    # for i in range(len(xs)):

    #     a = max(0, i-radius)
    #     b = min(len(xs), i+radius+1)

    #     smooth_x.append(
    #         np.mean(xs[a:b])
    #     )

    # smooth_x = np.array(
    #     smooth_x,
    #     dtype=np.float32
    # )

    # # -----------------------------
    # # Temporal smoothing
    # # -----------------------------

    # if previous_curve is not None:

    #     n = min(
    #         len(previous_curve),
    #         len(smooth_x)
    #     )

    #     smooth_x[:n] = (
    #         0.4 * smooth_x[:n]
    #         +
    #         0.6 * previous_curve[:n]
    #     )

    # previous_curve = smooth_x.copy()

    # curve = np.column_stack(
    #     [smooth_x, ys]
    # ).astype(np.int32)


    # -----------------------------
    # Moving average smoothing
    # -----------------------------

    radius = 50

    smooth_x = []

    for i in range(len(xs)):

        a = max(0, i-radius)
        b = min(len(xs), i+radius+1)

        smooth_x.append(
            np.mean(xs[a:b])
        )

    smooth_x = np.array(
        smooth_x,
        dtype=np.float32
    )

    # -----------------------------
    # Temporal smoothing
    # -----------------------------

    if previous_curve is not None:

        n = min(
            len(previous_curve),
            len(smooth_x)
        )

        smooth_x[:n] = (
            0.4 * smooth_x[:n]
            +
            0.6 * previous_curve[:n]
        )

    previous_curve = smooth_x.copy()

    curve = np.column_stack(
        [smooth_x, ys]
    ).astype(np.int32)

    # -----------------------------
    # Create curve mask
    # -----------------------------

    curve_mask = np.zeros(
        (h, w),
        dtype=np.uint8
    )

    cv2.polylines(
        curve_mask,
        [curve],
        False,
        255,
        1,
        cv2.LINE_AA
    )

    # -----------------------------
    # Distance transform
    # -----------------------------

    inverse = 255 - curve_mask

    dist = cv2.distanceTransform(
        inverse,
        cv2.DIST_L2,
        5
    )

    band_width = 40

    band_mask = (
        dist < band_width
    )

    # -----------------------------
    # Determine illuminated side
    # -----------------------------

    left_brightness = np.mean(
        gray[:, :w//4][moon_mask[:, :w//4]]
    )

    right_brightness = np.mean(
        gray[:, 3*w//4:][moon_mask[:, 3*w//4:]]
    )

    bright_on_left = (
        left_brightness >
        right_brightness
    )

    # -----------------------------
    # Gradient coloring
    # -----------------------------

    overlay = bgr.copy()

    for y in range(len(curve)):

        cx = curve[y, 0]

        row = curve[y, 1]

        xmin = max(0, cx-band_width)
        xmax = min(w, cx+band_width)

        for x in range(xmin, xmax):

            d = abs(x - cx)

            t = d / band_width

            if bright_on_left:

                bright_side = x < cx

            else:

                bright_side = x > cx

            if bright_side:

                color = (
                    0,
                    int(255*(1-t)),
                    255
                )

            else:

                color = (
                    255,
                    int(255*(1-t)),
                    0
                )

            overlay[row, x] = (
                0.3*overlay[row, x]
                + 0.7*np.array(color)
            )

    # -----------------------------
    # Save
    # -----------------------------

    result = cv2.cvtColor(
        overlay,
        cv2.COLOR_BGR2BGRA
    )

    result[:, :, 3] = alpha

    cv2.imwrite(
        os.path.join(
            output_folder,
            filename
        ),
        result
    )

    print("OK", filename)