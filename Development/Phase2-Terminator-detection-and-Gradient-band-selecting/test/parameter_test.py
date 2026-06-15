import cv2
import numpy as np

IMAGE = "moon4370.tif"

img = cv2.imread(
    IMAGE,
    cv2.IMREAD_UNCHANGED
)

if img.shape[2] == 4:
    bgr = img[:, :, :3]
    alpha = img[:, :, 3]
else:
    bgr = img
    alpha = np.ones(
        bgr.shape[:2],
        np.uint8
    ) * 255


def nothing(x):
    pass


cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)

cv2.createTrackbar(
    "illum_sigma",
    "Controls",
    40,
    150,
    nothing
)

cv2.createTrackbar(
    "gradient_thresh",
    "Controls",
    8,
    50,
    nothing
)

cv2.createTrackbar(
    "outlier_window",
    "Controls",
    40,
    200,
    nothing
)

cv2.createTrackbar(
    "outlier_thresh",
    "Controls",
    20,
    100,
    nothing
)

cv2.createTrackbar(
    "smooth_radius",
    "Controls",
    50,
    200,
    nothing
)

cv2.createTrackbar(
    "band_width",
    "Controls",
    40,
    150,
    nothing
)

cv2.createTrackbar(
    "overlay_pct",
    "Controls",
    70,
    100,
    nothing
)

while True:

    sigma = cv2.getTrackbarPos(
        "illum_sigma",
        "Controls"
    )

    gradient_threshold = cv2.getTrackbarPos(
        "gradient_thresh",
        "Controls"
    )

    outlier_window = max(
        1,
        cv2.getTrackbarPos(
            "outlier_window",
            "Controls"
        )
    )

    outlier_threshold = cv2.getTrackbarPos(
        "outlier_thresh",
        "Controls"
    )

    radius = cv2.getTrackbarPos(
        "smooth_radius",
        "Controls"
    )

    band_width = max(
        1,
        cv2.getTrackbarPos(
            "band_width",
            "Controls"
        )
    )

    overlay_pct = (
        cv2.getTrackbarPos(
            "overlay_pct",
            "Controls"
        ) / 100.0
    )

    moon_mask = alpha > 0

    gray0 = cv2.cvtColor(
        bgr,
        cv2.COLOR_BGR2GRAY
    ).astype(np.float32)

    gray = cv2.GaussianBlur(
        gray0,
        (0, 0),
        sigmaX=max(1, sigma)
    )

    # gray = gray0 / (
    #     illumination + 1e-6
    # )

    # gray = cv2.normalize(
    #     gray,
    #     None,
    #     0,
    #     255,
    #     cv2.NORM_MINMAX
    # )

    gray = gray.astype(
        np.uint8
    )

    h, w = gray.shape

    points = []

    for y in range(h):

        xs = np.where(
            moon_mask[y]
        )[0]

        if len(xs) < 40:
            continue

        left = xs[0]
        right = xs[-1]

        profile = gray[
            y,
            left:right+1
        ]

        profile = cv2.GaussianBlur(
            profile.reshape(1, -1),
            (1, 11),
            0
        ).flatten()

        grad = np.gradient(
            profile
        )

        margin = min(
            20,
            len(grad)//4
        )

        if margin < 2:
            continue

        search = grad[
            margin:-margin
        ]

        if len(search) == 0:
            continue

        strength = np.max(
            np.abs(search)
        )

        if strength < gradient_threshold:
            continue

        idx = np.argmax(
            np.abs(search)
        )

        x = left + margin + idx

        points.append([x, y])

    curve_vis = cv2.cvtColor(
        gray,
        cv2.COLOR_GRAY2BGR
    )

    if len(points) > 30:

        points = np.array(
            points,
            np.float32
        )

        xs = points[:, 0]

        keep = np.ones(
            len(xs),
            dtype=bool
        )

        for i in range(
            outlier_window,
            len(xs)-outlier_window
        ):

            local_median = np.median(
                xs[
                    i-outlier_window:
                    i+outlier_window
                ]
            )

            if abs(
                xs[i]
                -
                local_median
            ) > outlier_threshold:

                keep[i] = False

        points = points[keep]

        xs = points[:, 0]
        ys = points[:, 1]

        smooth_x = []

        for i in range(
            len(xs)
        ):

            a = max(
                0,
                i-radius
            )

            b = min(
                len(xs),
                i+radius+1
            )

            smooth_x.append(
                np.mean(xs[a:b])
            )

        smooth_x = np.array(
            smooth_x
        )

        curve = np.column_stack(
            [smooth_x, ys]
        ).astype(np.int32)

        cv2.polylines(
            curve_vis,
            [curve],
            False,
            (0, 255, 0),
            2
        )

        overlay = bgr.copy()

        left_brightness = np.mean(
            gray[:, :w//4][
                moon_mask[:, :w//4]
            ]
        )

        right_brightness = np.mean(
            gray[:, 3*w//4:][
                moon_mask[:, 3*w//4:]
            ]
        )

        bright_on_left = (
            left_brightness >
            right_brightness
        )

        for y in range(
            len(curve)
        ):

            cx = curve[y, 0]
            row = curve[y, 1]

            xmin = max(
                0,
                cx-band_width
            )

            xmax = min(
                w,
                cx+band_width
            )

            for x in range(
                xmin,
                xmax
            ):

                d = abs(
                    x-cx
                )

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
                    (1-overlay_pct)
                    * overlay[row, x]
                    +
                    overlay_pct
                    * np.array(color)
                )

    else:
        overlay = bgr.copy()

    preview_w = 600
    preview_h = 300

    gray_preview = cv2.resize(
        gray,
        (preview_w, preview_h)
    )

    curve_preview = cv2.resize(
        curve_vis,
        (preview_w, preview_h)
    )

    overlay_preview = cv2.resize(
        overlay,
        (preview_w, preview_h)
    )

    cv2.imshow("Gray", gray_preview)
    cv2.imshow("Curve", curve_preview)
    cv2.imshow("Overlay", overlay_preview)

    key = cv2.waitKey(30)

    if key == 27:
        break

cv2.destroyAllWindows()