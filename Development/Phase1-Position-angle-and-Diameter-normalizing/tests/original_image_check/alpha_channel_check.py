import cv2
import numpy as np

# Load image with alpha channel (unchanged)
image = cv2.imread("test_img.tif", cv2.IMREAD_UNCHANGED)

# Check if image has 4 channels (RGBA)
if image is None:
    print("Failed to load image.")
elif image.shape[2] < 4:
    print("Image does not have an alpha channel.")
else:
    # Extract alpha channel (4th channel)
    alpha_channel = image[:, :, 3]

    # Check if any pixel has alpha = 0
    has_transparent_pixels = np.any(alpha_channel == 0)

    if has_transparent_pixels:
        print("Image contains fully transparent (alpha = 0) pixels.")
    else:
        print("No fully transparent pixels found.")