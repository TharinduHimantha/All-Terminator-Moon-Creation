import cv2
import os
import numpy as np
from PIL import Image
from pathlib import Path  

base_dir = Path(__file__).resolve().parent  

image_folder_name = "posangle_locked_moon_images"
output_video_name = "posangle_and_diameter_locked_images.mp4"

image_folder = base_dir / image_folder_name
output_video = base_dir / output_video_name
fps = 24  # frames per second

# Get sorted list of images
images = sorted([img for img in os.listdir(image_folder) if img.endswith(".tif")])

# Read first image to get size
first_image_path = os.path.join(image_folder, images[0])
frame = cv2.imread(first_image_path)
height, width, _ = frame.shape

# Define video writer
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
video = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

for image in images:
    img_path = os.path.join(image_folder, image)
    
    # Open TIF properly (better compatibility)
    pil_img = Image.open(img_path).convert("RGB")
    frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    video.write(frame)

video.release()
print("Video created:", output_video)