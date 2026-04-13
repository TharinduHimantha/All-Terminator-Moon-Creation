import cv2
import numpy as np

# Load image with alpha channel
img = cv2.imread("test_img.tif", cv2.IMREAD_UNCHANGED)

if img is None:
    raise ValueError("Failed to load image")

if img.shape[2] < 4:
    raise ValueError("Image does not have an alpha channel")

# Copy image to avoid modifying original
result = img.copy()

# Get alpha channel
alpha = result[:, :, 3]

# Set alpha = 255 where alpha == 0
alpha[alpha == 0] = 255

# Put modified alpha back
result[:, :, 3] = alpha

# Save result
cv2.imwrite("alpha_fixed.png", result)