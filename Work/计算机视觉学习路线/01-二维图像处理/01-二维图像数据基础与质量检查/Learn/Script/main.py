from pathlib import Path
import cv2
import numpy as np
#加载图像数据
def load_img_path(path:str): 
    script_dir = Path(__file__).resolve().parent
    img_path = script_dir / 'Resource' / path
    with open(img_path, 'rb') as f:
        file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
    return cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)

def get_core_pixel(img:any):
    h,w = img.shape[:2] # 只取得前2个值
    leftUp = img[0,0]
    rightUp = img[0,w - 1]
    leftDown = img[h - 1,0]
    rightDown = img[h - 1,w - 1]
    center_h = int(h / 2) 
    center_w = int(w / 2)
    center = img[center_h,center_w]
    return {
        (center_h,center_w) : center,
        (0,0) : leftUp,
        (0,w - 1) : rightUp,
        (h - 1,0) : leftDown,
        (h - 1,w - 1) : rightDown,
     }
    


# 图片位于 main.py 同级的 Resource 目录 u8灰度数据
img = load_img_path('01-gray8-tone-shapes.png')
print(img.shape)
print(get_core_pixel(img))
