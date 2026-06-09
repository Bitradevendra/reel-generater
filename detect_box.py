from PIL import Image
import numpy as np
import sys

try:
    img = Image.open('background.jpeg')
    width, height = img.size

    # Convert to grayscale numpy array
    gray = np.array(img.convert('L'))

    # Find all pixels that are very bright (e.g., > 220, which is white)
    y_indices, x_indices = np.where(gray > 220)

    if len(x_indices) > 0:
        min_x, max_x = np.min(x_indices), np.max(x_indices)
        min_y, max_y = np.min(y_indices), np.max(y_indices)
        bx, by = min_x, min_y
        bw, bh = max_x - min_x, max_y - min_y
        
        print(f'Full Image: {width}x{height}')
        print(f'Found box: x={bx}, y={by}, w={bw}, h={bh}')
        
        # Calculate relative ratios
        pos_x_ratio = (bx + bw/2) / width
        pos_y_ratio = (by + bh/2) / height
        width_ratio = bw / width
        height_ratio = bh / height
        
        print(f'position_x: {pos_x_ratio:.3f}')
        print(f'position_y: {pos_y_ratio:.3f}')
        print(f'max_width_ratio: {width_ratio:.3f}')
        print(f'max_height_ratio: {height_ratio:.3f}')
    else:
        print('No box found.')
except Exception as e:
    print(f"Error: {e}")
