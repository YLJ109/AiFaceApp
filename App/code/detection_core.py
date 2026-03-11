"""
检测核心模块 - 包含所有检测页面的共同算法
"""
import cv2
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from collections import deque
from PyQt6.QtCore import QThread, pyqtSignal
import os
import random
from App.code.config import MODEL_PATH, IMAGE_SIZE, EMOTION_CLASSES, EMOTION_COLORS, EMOTION_CHINESE, APP_DIR

class EmotionClassifier(nn.Module):
    """表情分类模型"""
    def __init__(self, num_classes=7):
        super().__init__()
        from torchvision.models import MobileNet_V2_Weights
        self.backbone = models.mobilenet_v2(weights=MobileNet_V2_Weights.DEFAULT)
        num_features = self.backbone.classifier[1].in_features
        self.backbone.features[0][0] = nn.Conv2d(1, 32, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1), bias=False)
        self.backbone.classifier = nn.Sequential(nn.Dropout(p=0.2), nn.Linear(num_features, num_classes))
    
    def forward(self, x):
        return self.backbone(x)

class DetectionCore:
    """检测核心类 - 单例模式"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DetectionCore, cls).__new__(cls)
            # 初始化只执行一次
            cls._instance.model = None
            cls._instance.transform = None
            cls._instance.device = None
            cls._instance.face_net = None
        return cls._instance
    
    def load_model(self):
        """加载模型"""
        # 如果模型已经加载，直接返回
        if self.model is not None:
            return True
        
        try:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            print(f"使用设备：{self.device}")
            
            checkpoint = torch.load(MODEL_PATH, map_location=self.device)
            
            self.model = EmotionClassifier(num_classes=7).to(self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.eval()
            
            self.transform = transforms.Compose([
                transforms.Grayscale(num_output_channels=1),
                transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5], std=[0.5])
            ])
            
            print("✅ 模型加载成功")
            return True
        except Exception as e:
            print(f"❌ 模型加载失败：{e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_face_net(self):
        """加载人脸检测模型"""
        # 如果人脸检测模型已经加载，直接返回
        if self.face_net is not None:
            return True
        
        try:
            print("🔍 加载人脸检测模型...")
            self.face_net = cv2.dnn.readNetFromCaffe(
                'App/models/deploy.prototxt',
                'App/models/res10_300x300_ssd_iter_140000_fp16.caffemodel'
            )
            # 优化模型运行
            if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                self.face_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                self.face_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
            else:
                self.face_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                self.face_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            print("✅ 人脸检测模型加载成功")
            return True
        except Exception as e:
            print(f"❌ 人脸检测模型加载失败：{e}")
            import traceback
            traceback.print_exc()
            return False
    
    def detect_faces(self, image):
        """检测人脸"""
        if not self.face_net:
            if not self.load_face_net():
                return []
        
        faces = []
        try:
            h, w = image.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
            self.face_net.setInput(blob)
            detections = self.face_net.forward()
            
            for i in range(min(10, detections.shape[2])):  # 限制检测数量
                confidence = detections[0, 0, i, 2]
                if confidence > 0.6:  # 提高置信度阈值减少误检测
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (x, y, x1, y1) = box.astype("int")
                    # 确保边界有效
                    x, y = max(0, x), max(0, y)
                    w_box, h_box = max(10, x1-x), max(10, y1-y)
                    faces.append((x, y, w_box, h_box))
        except Exception as e:
            print(f"人脸检测错误：{e}")
        
        return faces
    
    def predict_emotion(self, face_image):
        """预测表情"""
        if not self.model:
            if not self.load_model():
                return 'neutral', 0.0
        
        try:
            face_tensor = self.transform(face_image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(face_tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)
                conf, pred = torch.max(probs, 1)
                emotion = EMOTION_CLASSES[pred.item()]
                confidence = conf.item()
            
            return emotion, confidence
        except Exception as e:
            print(f"预测错误：{e}")
            return 'neutral', 0.0
    
    def draw_four_corners(self, image, faces, face_results=None):
        """绘制四个角"""
        if not face_results:
            face_results = [{'emotion': 'neutral', 'confidence': 0.0} for _ in faces]
        
        for idx, (x, y, w_box, h_box) in enumerate(faces):
            # 获取对应人脸的颜色
            if idx < len(face_results):
                color = EMOTION_COLORS.get(face_results[idx].get('emotion', 'neutral'), (0, 255, 0))
            else:
                color = EMOTION_COLORS.get('neutral', (0, 255, 0))
            
            # 绘制四个角（带描边）
            # 左上角
            cv2.line(image, (x, y), (x+20, y), (0, 0, 0), 5)  # 黑色描边
            cv2.line(image, (x, y), (x, y+20), (0, 0, 0), 5)  # 黑色描边
            cv2.line(image, (x, y), (x+20, y), color, 3)  # 彩色主线条
            cv2.line(image, (x, y), (x, y+20), color, 3)  # 彩色主线条
            # 右上角
            cv2.line(image, (x+w_box, y), (x+w_box-20, y), (0, 0, 0), 5)  # 黑色描边
            cv2.line(image, (x+w_box, y), (x+w_box, y+20), (0, 0, 0), 5)  # 黑色描边
            cv2.line(image, (x+w_box, y), (x+w_box-20, y), color, 3)  # 彩色主线条
            cv2.line(image, (x+w_box, y), (x+w_box, y+20), color, 3)  # 彩色主线条
            # 左下角
            cv2.line(image, (x, y+h_box), (x+20, y+h_box), (0, 0, 0), 5)  # 黑色描边
            cv2.line(image, (x, y+h_box), (x, y+h_box-20), (0, 0, 0), 5)  # 黑色描边
            cv2.line(image, (x, y+h_box), (x+20, y+h_box), color, 3)  # 彩色主线条
            cv2.line(image, (x, y+h_box), (x, y+h_box-20), color, 3)  # 彩色主线条
            # 右下角
            cv2.line(image, (x+w_box, y+h_box), (x+w_box-20, y+h_box), (0, 0, 0), 5)  # 黑色描边
            cv2.line(image, (x+w_box, y+h_box), (x+w_box, y+h_box-20), (0, 0, 0), 5)  # 黑色描边
            cv2.line(image, (x+w_box, y+h_box), (x+w_box-20, y+h_box), color, 3)  # 彩色主线条
            cv2.line(image, (x+w_box, y+h_box), (x+w_box, y+h_box-20), color, 3)  # 彩色主线条
        
        return image
    
    def draw_labels(self, image, faces, face_results):
        """绘制标签"""
        if not face_results:
            return image
        
        frame_pil_full = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(frame_pil_full)
        
        for idx, (x, y, w_box, h_box) in enumerate(faces):
            if idx < len(face_results):
                result = face_results[idx]
                emotion = result.get('emotion', 'neutral')
                chinese_text = f"👤{idx+1} {EMOTION_CHINESE.get(emotion, 'neutral')}: {result.get('confidence', 0):.2f}"
                
                # 获取对应的表情颜色
                color = EMOTION_COLORS.get(emotion, (0, 255, 0))
                
                try:
                    # 尝试使用高质量字体
                    font = ImageFont.truetype("msyhbd.ttc", 18, encoding="utf-8")
                except:
                    try:
                        font = ImageFont.truetype("simhei.ttf", 18, encoding="utf-8")
                    except:
                        # 如果找不到字体，使用默认字体
                        font = ImageFont.load_default()
                
                # 绘制文字阴影以提高清晰度
                shadow_offset = 2
                draw.text((x + shadow_offset, y - 35 + shadow_offset), chinese_text, font=font, fill=(0, 0, 0))  # 阴影
                draw.text((x, y - 35), chinese_text, font=font, fill=(color[2], color[1], color[0]))  # 主文字（转换为RGB）
        
        return cv2.cvtColor(np.array(frame_pil_full), cv2.COLOR_RGB2BGR)
    
    def play_music(self, emotion, music_dir=None):
        """根据表情播放音乐"""
        try:
            # 如果没有指定音乐目录，使用默认目录（使用中文名称）
            if not music_dir:
                chinese_emotion = EMOTION_CHINESE.get(emotion, emotion)
                music_dir = os.path.join(APP_DIR, 'music', chinese_emotion)
            
            # 检查目录是否存在
            if not os.path.exists(music_dir):
                print(f"⚠️ 音乐目录不存在：{music_dir}")
                return
            
            # 获取目录中的音乐文件
            music_files = [f for f in os.listdir(music_dir) if f.endswith(('.mp3', '.wav', '.ogg', '.flac'))]
            
            if not music_files:
                print(f"⚠️ 音乐目录中没有音乐文件：{music_dir}")
                return
            
            # 随机选择一个音乐文件
            selected_file = random.choice(music_files)
            music_path = os.path.join(music_dir, selected_file)
            
            # 播放音乐（这里只是打印信息，实际播放需要使用相应的库）
            print(f"🎵 正在播放{EMOTION_CHINESE.get(emotion, emotion)}音乐：{selected_file}")
            
            # 实际播放音乐的代码（需要安装相应的库，如pygame或playsound）
            # 例如使用playsound库：
            # from playsound import playsound
            # playsound(music_path)
            
        except Exception as e:
            print(f"❌ 播放音乐错误：{e}")

class PredictionThread(QThread):
    """预测线程"""
    result_ready = pyqtSignal(str, float, int)
    
    def __init__(self, face_image, transform, model, device, face_idx):
        super().__init__()
        self.face_image = face_image
        self.transform = transform
        self.model = model
        self.device = device
        self.face_idx = face_idx
        self.emotion_buffer = deque(maxlen=5)
    
    def run(self):
        try:
            face_tensor = self.transform(self.face_image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(face_tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)
                conf, pred = torch.max(probs, 1)
                emotion = EMOTION_CLASSES[pred.item()]
                confidence = conf.item()
            
            self.emotion_buffer.append(emotion)
            smooth_emotion = max(set(self.emotion_buffer), key=list(self.emotion_buffer).count)
            
            self.result_ready.emit(smooth_emotion, confidence, self.face_idx)
        except Exception as e:
            print(f"预测错误：{e}")
            self.result_ready.emit('neutral', 0.0, self.face_idx)
