from pathlib import Path
import cv2
import numpy as np
import util as ut
img = ut.load_img_path('02-rgb8-channel-shapes.png')
def show_demo_step1():
    ut.show_cv('img', img)
    # 分离通道（注意 OpenCV 是 BGR 顺序）
    b, g, r = cv2.split(img)
    ut.show_cv('img', b)
    ut.show_cv('img', g)
    ut.show_cv('img', r)
    #直接取平均 axis=2是数据维度，把通道压缩掉
    img_avg = np.mean(img, axis=2).astype(np.uint8)
    combined = np.hstack([img, ut.to_3channel(img_avg)])
    ut.show_cv('img', combined)
    # 方法一：OpenCV 标准接口（内部用加权公式）
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    combined = np.hstack([img, ut.to_3channel(img_gray)])
    ut.show_cv('img', combined)
    # 差值图
    diff = cv2.absdiff(img_avg, img_gray)
    ut.show_cv('img', diff)
def show_demo_step2():
     hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
     combined = np.hstack([img, hsv])
     ut.show_cv('img|hsv', combined)
     hls = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)
     combined = np.hstack([img, hls])
     ut.show_cv('img|hls', combined)
     lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
     combined = np.hstack([img, hls])
     ut.show_cv('img|lab', combined)
     img2 = ut.load_img_path('01-gray8-tone-shapes.png')
    # 1. 先定义 img
     img2 = ut.load_img_path('01-gray8-tone-shapes.png')
    
     # 2. 计算直方图
     hist = cv2.calcHist([img2], [0], None, [256], [0, 256])
     hist = hist.flatten()  # ✅ 从 (256, 1) 变成 (256,)
    
     # 3. 归一化到 0~400
     hist_norm = hist / hist.max() * 400
    
     # 4. 创建画布（500×256，白底）
     canvas = np.ones((500, 256, 3), dtype=np.uint8) * 255
    
     # 5. 绘制直方图曲线
     for i in range(256):
        cv2.line(canvas, (i, 500), (i, 500 - int(hist_norm[i])), (0, 0, 0), 1)
    
     # 6. 显示
     ut.show_cv('Histogram', canvas)
show_demo_step2()
   