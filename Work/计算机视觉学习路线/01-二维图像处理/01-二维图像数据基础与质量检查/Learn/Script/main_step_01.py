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
def get_channels(img:any):
    #获取到当前的channels的通道数
    if len(img.shape) == 2:
        channels = 1          # 灰度图
    elif len(img.shape) == 3:
        channels = img.shape[2]  # 3 或 4
    else:
        channels = 0
    return channels
def get_core_pixel(img:any):
    h,w = img.shape[:2] # 只取得前2个值
    # 提取像素（彩色图自动返回 [B,G,R] 数组，灰度图返回标量）
    leftUp = img[0, 0]
    rightUp = img[0, w - 1]
    leftDown = img[h - 1, 0]
    rightDown = img[h - 1, w - 1]
    center_h = h // 2 #// 是整除
    center_w = w // 2
    center = img[center_h, center_w]
    return {
        (center_h,center_w) : center,
        (0,0) : leftUp,
        (0,w - 1) : rightUp,
        (h - 1,0) : leftDown,
        (h - 1,w - 1) : rightDown,
     }
#转三通道
def to_3channel(img):
    if len(img.shape) == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif len(img.shape) == 3 and img.shape[2] == 1:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif len(img.shape) == 3 and img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img
def stat_core_pixel(img:any):
    channels = get_channels(img)
    result = {}
    if channels == 3:
        b, g, r = cv2.split(img)
        for name, channel in [('B', b), ('G', g), ('R', r)]:
            result[f'{name}_min'] = np.min(channel)
            result[f'{name}_max'] = np.max(channel)
            result[f'{name}_mean'] = np.mean(channel)
            result[f'{name}_median'] = np.median(channel)
            result[f'{name}_std'] = np.std(channel) #像素值相对于平均值的波动大小
    else:
            result[f'min'] = np.min(img)
            result[f'max'] = np.max(img)
            result[f'mean'] = np.mean(img)
            result[f'median'] = np.median(img)
            result[f'std'] = np.std(img) #像素值相对于平均值的波动大小
    return result

#16位转8位
def to_8bit(img):
    if img.dtype == np.uint16:
        return cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return img
def show_cv(title,img):
    cv2.imshow(title, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
def show_demo_step1():
    # 图片位于 main.py 同级的 Resource 目录 u8灰度数据
    img = load_img_path('01-gray8-tone-shapes.png')
    print(img.shape) #数据类别
    print(img.dtype) #数据存储类型
    print(get_core_pixel(img))
    print(stat_core_pixel(img))


    #图像位于
    img = load_img_path('02-rgb8-channel-shapes.png')
    print(img.shape) #数据类别
    print(img.dtype) #数据存储类型
    print(get_core_pixel(img))
    print(stat_core_pixel(img))
    #获取像素通道数
    p1 = np.percentile(img, 1)
    p5 = np.percentile(img, 5)
    p95 = np.percentile(img, 95)
    p99 = np.percentile(img, 99)
    print(p1)
    print(p5)
    print(p95)
    print(p99)
    # 统计等于最小值的像素数量
    count_min = np.sum(img == img.min())
    # 统计等于最大值的像素数量
    count_max = np.sum(img == img.max())
    print(f"等于最小值的像素数: {count_min}")
    print(f"等于最大值的像素数: {count_max}")


    #BGR转RGB，opencv默认读取的通道就是BGR形式的
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    combined = np.hstack([img, img_rgb])
    show_cv('Left: BGR| Right: RGB', combined)


    #16位图像
    img_16 = load_img_path('04-preview-gray16-gradient.png')
    img_8 = to_8bit(img_16)
    img_16_vis = to_3channel(img_16)  # 16位转8位后用于显示
    img_8_vis = to_3channel(img_8)   # 同上
    combined = np.hstack([img_16_vis, img_8_vis])
    show_cv('Left: 16bit (normalized) | Right: 8bit', combined)

    #二值图
    img = load_img_path('07-rgb8-coordinate-corners.png')

    # ROI 坐标
    x, y, w, h = 10, 20, 10, 10
    # 在原图上绘制绿色矩形框（不裁剪）
    img_marked = img.copy()  # 复制一份，避免修改原图
    cv2.rectangle(img_marked, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.imshow('ROI', img_marked)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    # 像素值 > 254 变黑 小于254变白 大于254变0，小于254变我们设置的值
    #最简单的mask
    _, mask = cv2.threshold(img, 254, 255, cv2.THRESH_BINARY_INV)
    combined = np.hstack([mask, img])
    show_cv('Left: mask (normalized) | Right: mask', combined)

def show_demo_step2():
    #图像截断
    img = load_img_path('01-gray8-tone-shapes.png')
    img_display = np.clip(img, 0, 100).astype(np.uint8)
    combined = np.hstack([img, img_display])
    show_cv('Left: img| Right: img_display', combined)
    #图像归一化0~255，让最小值变为0，最大值变为255
    img_stretched = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    combined = np.hstack([img, img_stretched])
    show_cv('Left: img| Right: img_stretched', combined)
    p1 = np.percentile(img, 1)
    p99 = np.percentile(img, 99)
    # 截断到 [p1, p99]
    img_clipped = np.clip(img, p1, p99)
    # 线性拉伸到 [0, 255]
    img_stretched = ((img_clipped - p1) / (p99 - p1) * 255).astype(np.uint8)
    combined = np.hstack([img, img_stretched])
    show_cv('Left: img| Right: img_stretched_p1_p99', combined)
    # 伪彩色
    img_c3 = to_3channel(img)
    img_color_gary = cv2.applyColorMap(img_c3, cv2.COLORMAP_BONE)
    img_color = cv2.applyColorMap(img_c3, cv2.COLORMAP_JET)
    combined = np.hstack([img_c3, img_color])
    show_cv('Left: img|Mid: img_gary|Right:img_color', combined)
show_demo_step2()

