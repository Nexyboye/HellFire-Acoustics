


import matplotlib.pyplot as plt    
import numpy as np
from PIL import Image, ImageDraw, ImageFont



def draw_text(
    arr: np.ndarray,
    text: str,
    font_height: int = 18,
    color=(255, 255, 255),
    thickness: int = 1,
    font_path: str = "consola.ttf",
    inplace: bool = True,
) -> np.ndarray:
    """
    Draw unicode text into a numpy array with shape (h,w,3).
    """
    if text == "": return arr
    
    size = arr.shape
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, font_height)
    stroke = thickness - 1 if thickness > 1 else 0

    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    text_h = bbox[3] - bbox[1]
    y = (size[0] - text_h) // 2
   
    draw.text(
        (0, y),
        text,
        font=font,
        fill=color,
        stroke_width=stroke,
        stroke_fill=color,
    )
    
    if inplace:
        arr[:] = np.array(img)
    else:
        return arr