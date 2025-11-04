# 檔案: ai_core.py
# (已修正：採用「自動調整 K 值」邏輯)

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import cv2
from torchvision import datasets, transforms # 保留 transforms
import os # 檢查檔案是否存在

# --- 1. 匯入您的「影像處理工具」 ---
try:
    from captcha_utils import get_preprocessed_chars, binarize_image, erode_image, crop_white_region, k_based_segmentation_with_merge, add_padding
except ImportError:
    print("[AI_CORE_ERROR] 找不到 captcha_utils.py 檔案。")
    # 定義假的函式以避免後續程式碼崩潰
    def get_preprocessed_chars(*args, **kwargs):
        print("[AI_CORE_ERROR] get_preprocessed_chars 函式未載入！")
        return []

# --- 2. 複製您的「CNN 模型架構」 ---
# (這段程式碼必須和您訓練時用的「一模一樣」)
class ImprovedCNN(nn.Module):
    def __init__(self, num_classes):
        super(ImprovedCNN, self).__init__()
        # Conv blocks
        self.conv1 = nn.Conv2d(1,   32, 3, padding=1)
        self.bn1   = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32,  64, 3, padding=1)
        self.bn2   = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.bn3   = nn.BatchNorm2d(128)
        self.conv4 = nn.Conv2d(128, 256, 3, padding=1)  # 第四層
        self.bn4   = nn.BatchNorm2d(256)
        self.pool = nn.MaxPool2d(2, 2)  # 每層後都池化
        # 尺寸流：64→32→16→8→4，因此 in_features = 256*4*4
        self.fc1 = nn.Linear(256 * 4 * 4, 256)
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(256, num_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.bn1(self.conv1(x))))  # 64 -> 32
        x = self.pool(F.relu(self.bn2(self.conv2(x))))  # 32 -> 16
        x = self.pool(F.relu(self.bn3(self.conv3(x))))  # 16 -> 8
        x = self.pool(F.relu(self.bn4(self.conv4(x))))  # 8  -> 4
        x = x.view(x.size(0), -1)                       # (B, 256*4*4)
        x = self.dropout(F.relu(self.fc1(x)))
        x = self.fc2(x)
        return x

# --- 3. 準備模型與相關設定 ---
MODEL_PATH = "cnn_model.pth"    # 您訓練好的模型權重
# (!!!) 根據您的訓練日誌，您有 26 個類別 (a-z)
CLASSES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 
           'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 
           'u', 'v', 'w', 'x', 'y', 'z']
NUM_CLASSES = len(CLASSES)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# (這是您訓練時用的「測試集」轉換，預測時必須用一樣的)
predict_transform = transforms.Compose([
    transforms.ToPILImage(), # 先轉成 PIL 圖片 (因為 cv2 傳來的是 numpy)
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

# --- 4. 載入模型 (程式啟動時執行一次) ---
model = None # 先宣告
if os.path.exists(MODEL_PATH):
    try:
        model = ImprovedCNN(num_classes=NUM_CLASSES).to(DEVICE)
        # 載入您訓練好的「大腦」
        model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
        model.eval() # 【關鍵】設為評估模式 (關閉 Dropout)
        print(f"[AI_CORE] 模型 {MODEL_PATH} 載入成功，使用 {DEVICE}。")
    except Exception as e:
        print(f"[AI_CORE_ERROR] 無法載入模型 {MODEL_PATH}。錯誤: {e}")
else:
    print(f"[AI_CORE_ERROR] 找不到模型檔案: {MODEL_PATH}")
    print("請先執行「訓練腳本」 (image_char_classifier.ipynb) 來產生模型檔案。")

# ===================================================================
# ▼▼▼ 這就是您要給 ticketBot.py 呼叫的「總管函式」 ▼▼▼
# ===================================================================

def crack_captcha(image_bytes: bytes, k_value: int = 20) -> str:
    """
    接收驗證碼的二進位圖片資料，回傳辨識後的字串。
    (已修正：採用自動調整 K 值，直到切出 4 個字為止)
    """
    if model is None:
        return "MODEL_NOT_LOADED"
        
    # --- ▼▼▼ 這是「自動調整 K 值」的新邏輯 ▼▼▼ ---
    # 1. 將 bytes 轉為 OpenCV 格式 (只需做一次)
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("無法解碼圖片 bytes")
            
        # 2. 執行一次性的預處理流水線
        img_prcd = binarize_image(img)
        img_prcd = erode_image(img_prcd)
        img_prcd, _ = crop_white_region(img_prcd)
        
    except Exception as e:
        print(f"[AI_CORE_ERROR] 預處理 (bytes 轉 cv2) 失敗: {e}")
        return "PREPROCESS_FAIL"

    # 3. 【關鍵修正】自動調整 K 值，直到切出 4 個字
    # (此邏輯與 preprocess.ipynb 完全一致)
    k = k_value # 從 ticketBot 傳來的 k_value (20 或 22) 開始
    max_iter = 50     # 與 preprocess.ipynb 的呼叫 保持一致
    target_chars = 4  # 您的要求
    char_boxes = []   # 初始化

    for i in range(max_iter):
        # 我們直接呼叫 captcha_utils.py 中的切割函式
        char_boxes = k_based_segmentation_with_merge(img_prcd, k=k)
        
        if len(char_boxes) == target_chars:
            # 找到了！
            print(f"[AI_CORE] K 值搜尋成功: K={k}, 切割出 {len(char_boxes)} 個字元。")
            break
        elif len(char_boxes) > target_chars:
            # 切出太多 (e.g., 5)，增加 K 值讓合併更積極
            k += 1
        else:
            # 切出太少 (e.g., 3)，減少 K 值讓切割更積極
            k = max(1, k - 1)
        
        # 如果迴圈結束還沒找到
        if i == max_iter - 1:
            print(f"[AI_CORE_ERROR] K 值搜尋失敗。在 K={k} 時切出 {len(char_boxes)} 個字元 (非 4)。")
            return "PREDICT_K_SEARCH_FAIL"
    
    # --- ▲▲▲ 修正結束 ▲▲▲ ---

    # 4. 根據 X 座標排序字元
    char_boxes_sorted = sorted(char_boxes, key=lambda x: x[0])

    # 5. 裁切並加上 Padding
    char_imgs_list = []
    for (xmin, ymin, xmax, ymax) in char_boxes_sorted:
        char_img = img_prcd[ymin:ymax, xmin:xmax]
        char_img = add_padding(char_img, pad=2) #
        char_imgs_list.append(char_img)

    # 6. 依序預測
    final_prediction = ""
    with torch.no_grad(): # 【關鍵】預測時不需要計算梯度
        for char_img in char_imgs_list:
            
            # 影像轉換
            try:
                tensor = predict_transform(char_img).to(DEVICE)
                tensor = tensor.unsqueeze(0) # 增加 batch 維度 (C, H, W) -> (B, C, H, W)
            except Exception as e:
                print(f"[AI_CORE_ERROR] 影像轉換 (transform) 失敗: {e}")
                continue

            # 模型預測
            output = model(tensor)
            _, pred_index = torch.max(output, 1)
            
            # 轉回文字
            try:
                final_prediction += CLASSES[pred_index.item()]
            except IndexError:
                print(f"[AI_CORE_ERROR] 預測索引 {pred_index.item()} 超出 CLASSES 範圍！")
                final_prediction += "?"

    print(f"[AI_CORE] 辨識結果: {final_prediction}")
    return final_prediction

# 【注意】
# 檔案末端所有「訓練」和「評估」程式碼 (Epoch 1/20...) 都已被移除