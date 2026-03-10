"""
实时摄像头情感检测 - 稳定版
"""

import cv2
import torch
import torch.nn as nn
import numpy as np
from torchvision import transforms, models
from PIL import Image
import time
from collections import deque
import sys

print("=" * 60)
print("🎥 PyTorch 实时情感检测")
print("=" * 60)

MODEL_PATH = r"D:\front-back\AiFaceApp\7emotions_96x96_mobilenetv2_3060_train\models\pytorch_best_3060.pth"

# GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
if torch.cuda.is_available():
    print(f"✅ GPU: {torch.cuda.get_device_name(0)}")

class_names = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']

# 加载模型
print(f"\n📥 加载模型...")
try:
    checkpoint = torch.load(MODEL_PATH, map_location=device)
    
    class EmotionClassifier(nn.Module):
        def __init__(self, num_classes=7):
            super().__init__()
            self.backbone = models.mobilenet_v2(weights=None)
            num_features = self.backbone.classifier[1].in_features
            self.backbone.features[0][0] = nn.Conv2d(1, 32, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1), bias=False)
            self.backbone.classifier = nn.Sequential(nn.Dropout(p=0.2), nn.Linear(num_features, num_classes))
        
        def forward(self, x):
            return self.backbone(x)
    
    model = EmotionClassifier(num_classes=7).to(device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    print("✅ 模型加载成功")
except Exception as e:
    print(f"❌ 模型加载失败：{e}")
    sys.exit(1)

# 预处理
transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((96, 96)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])

emotion_buffer = deque(maxlen=5)

# 摄像头
print("\n📷 启动摄像头...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("❌ 无法打开摄像头，尝试默认模式...")
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ 无法访问摄像头！请检查摄像头连接。")
    sys.exit(1)

# 设置参数
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)

# 预热
print("正在初始化摄像头...")
for i in range(20):
    ret, _ = cap.read()
    if not ret:
        break
    time.sleep(0.01)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

print("\n✅ 准备就绪！")
print("使用说明:")
print("  - 将脸部对准摄像头")
print("  - 按 'q' 或 ESC 退出")
print("  - 按 's' 截图")
print("=" * 60)

prev_time = time.time()
frame_count = 0

while True:
    ret, frame = cap.read()
    
    if not ret or frame is None:
        print("⚠️  无法读取摄像头画面")
        time.sleep(0.1)
        continue
    
    # 翻转
    frame = cv2.flip(frame, 1)
    
    # 人脸检测
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
    
    # 处理每个人脸
    for (x, y, w, h) in faces:
        try:
            face_roi = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face_roi, (96, 96))
            face_pil = Image.fromarray(face_resized)
            face_tensor = transform(face_pil).unsqueeze(0).to(device)
            
            with torch.no_grad():
                outputs = model(face_tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)
                conf, pred = torch.max(probs, 1)
                emotion = class_names[pred.item()]
                confidence = conf.item()
            
            emotion_buffer.append(emotion)
            smooth_emotion = max(set(emotion_buffer), key=list(emotion_buffer).count)
            
            colors = {
                'angry': (0, 0, 255), 'disgust': (0, 165, 255), 'fear': (128, 0, 128),
                'happy': (0, 255, 0), 'neutral': (255, 255, 255), 'sad': (255, 0, 0),
                'surprise': (255, 255, 0)
            }
            color = colors.get(smooth_emotion, (0, 255, 0))
            
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            label = f"{smooth_emotion}: {confidence:.2f}"
            cv2.putText(frame, label, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            bar_w = int(w * confidence)
            cv2.rectangle(frame, (x, y+h+5), (x+bar_w, y+h+10), color, -1)
            cv2.rectangle(frame, (x, y+h+5), (x+w, y+h+10), (255, 255, 255), 1)
        except Exception as e:
            continue
    
    # FPS
    curr_time = time.time()
    frame_count += 1
    if curr_time - prev_time >= 1:
        fps = frame_count / (curr_time - prev_time)
        frame_count = 0
        prev_time = curr_time
    else:
        fps = 0
    
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, "Press Q to Exit | S to Screenshot", (10, frame.shape[0]-10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    cv2.imshow('Emotion Detection - Press Q to Quit', frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:
        break
    elif key == ord('s'):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        print(f"✅ 截图已保存：{filename}")

cap.release()
cv2.destroyAllWindows()
print("\n👋 检测结束")
