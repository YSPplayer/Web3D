from pathlib import Path
import cv2
import numpy as np

def load_img_path(path:str): 
    script_dir = Path(__file__).resolve().parent
    img_path = script_dir / 'Resource' / path
    with open(img_path, 'rb') as f:
        file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
    return cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
def get_channels(img:any):
    #获取到当前的channels的通道数
    if len(img.shape) == 2:
        channels = 1          # 灰度图
    elif len(img.shape) == 3:
        channels = img.shape[2]  # 3 或 4
    else:
        channels = 0
    return channels
def to_3channel(img):
    if len(img.shape) == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif len(img.shape) == 3 and img.shape[2] == 1:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif len(img.shape) == 3 and img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img
def to_8bit(img):
    if img.dtype == np.uint16:
        return cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return img
def show_cv(title,img):
    cv2.imshow(title, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()