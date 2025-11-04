# 檔案: captcha_utils.py
# (請完整取代您電腦中的同名檔案)

import cv2
import numpy as np
import os

# ===================================================================
# 區塊一：您在 Notebook 中開發的 5 個影像處理工具
# ===================================================================

def binarize_image(img):
    """
    將灰階或 RGB 圖二值化 (Otsu)
    """
    if len(img.shape) == 3:  # RGB → 灰階
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def erode_image(binary_img, kernel_size=(3,1), iterations=1):
    """
    對二值圖做腐蝕
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    eroded = cv2.erode(binary_img, kernel, iterations=iterations)
    return eroded

def crop_white_region(binary_img):
    """
    找出二值圖中白色區域的 bounding box 並裁切二值圖
    """
    ys, xs = np.where(binary_img == 255)
    if len(xs) > 0 and len(ys) > 0:
        xmin, xmax = xs.min(), xs.max()
        ymin, ymax = ys.min(), ys.max()
        cropped_binary = binary_img[ymin:ymax+1, xmin:xmax+1]
        return cropped_binary, (xmin, xmax, ymin, ymax)
    else:
        # print("沒有偵測到白色區域")
        return binary_img, (0, binary_img.shape[1], 0, binary_img.shape[0])

def k_based_segmentation_with_merge(binary_img, k=20, h_thresh_ratio=0.4):
    """
    K 值切割法
    """
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_img, connectivity=8)
    boxes = []
    small_blocks = []
    heights = stats[1:, cv2.CC_STAT_HEIGHT]
    if len(heights) == 0:
        return []
    h_thresh = h_thresh_ratio * heights.max()
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        if h < h_thresh:
            small_blocks.append((x, y, x+w, y+h))
        else:
            boxes.append([x, y, x+w, y+h])
    for sxmin, symin, sxmax, symax in small_blocks:
        min_dist = float('inf')
        target_idx = -1
        for idx, (xmin, ymin, xmax, ymax) in enumerate(boxes):
            dist = abs((sxmin+sxmax)/2 - (xmin+xmax)/2)
            if dist < min_dist:
                min_dist = dist
                target_idx = idx
        if target_idx >= 0:
            xmin, ymin, xmax, ymax = boxes[target_idx]
            boxes[target_idx] = [min(xmin, sxmin), min(ymin, symin), max(xmax, sxmax), max(ymax, symax)]
    all_boxes = []
    for xmin, ymin, xmax, ymax in boxes:
        width = xmax - xmin
        num_letters = max(1, int(np.ceil(width / k)))
        if num_letters == 1:
            all_boxes.append((xmin, ymin, xmax, ymax))
        else:
            new_centers_x = np.linspace(xmin, xmax, num_letters+2)[1:-1]
            for nx in new_centers_x:
                sub_xmin = int(nx - width/(2*num_letters))
                sub_xmax = int(nx + width/(2*num_letters))
                all_boxes.append((sub_xmin, ymin, sub_xmax, ymax))
    return all_boxes

def add_padding(img, pad=2):
    """
    img: 二值圖 (numpy array)
    pad: 邊界出血大小 (像素)
    """
    h, w = img.shape
    padded = np.zeros((h+2*pad, w+2*pad), dtype=img.dtype)  # 黑色 padding
    padded[pad:pad+h, pad:pad+w] = img
    return padded

# ===================================================================
# 區塊二：「總管函式」 (給 ai_core.py 呼叫)
# ===================================================================

def get_preprocessed_chars(raw_image_bytes: bytes, k_value=22, pad=2) -> list:
    """
    將「單張」原始驗證碼圖片(bytes)，處理成可用於 CNN 預測的字元圖片列表。
    """
    
    # 1. 將 bytes 轉為 OpenCV 格式
    np_arr = np.frombuffer(raw_image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    if img is None:
        print("[Error] Preprocessor: 無法解碼圖片 bytes。")
        return []

    # 2. 執行預處理流水線 (Pipeline)
    img_prcd = binarize_image(img)
    img_prcd = erode_image(img_prcd)
    img_prcd, _ = crop_white_region(img_prcd)
    
    # 3. 執行 K 值切割
    char_boxes = k_based_segmentation_with_merge(img_prcd, k=k_value)
    
    if not char_boxes:
        print("[Warning] Preprocessor: 偵測不到任何字元。")
        return []
        
    # 4. 根據 X 座標排序字元
    char_boxes_sorted = sorted(char_boxes, key=lambda x: x[0])

    # 5. 裁切並加上 Padding
    char_imgs = []
    for (xmin, ymin, xmax, ymax) in char_boxes_sorted:
        char_img = img_prcd[ymin:ymax, xmin:xmax]
        char_img = add_padding(char_img, pad=pad)
        char_imgs.append(char_img)
        
    return char_imgs

# 【注意】
# 檔案末端的 Demo 和 preprocess 函式都已被移除
# 因為它們只在「訓練」和「實驗」時需要