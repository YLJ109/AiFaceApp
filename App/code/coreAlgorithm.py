"""
核心算法模块 - 情感识别模型
"""
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import numpy as np
from collections import deque
from App.code.config import MODEL_PATH, IMAGE_SIZE, EMOTION_CLASSES

class EmotionClassifier(nn.Module):
    """情感分类器模型"""
    def __init__(self, num_classes=7):
        super().__init__()
        from torchvision.models import MobileNet_V2_Weights
        self.backbone = models.mobilenet_v2(weights=MobileNet_V2_Weights.DEFAULT)
        num_features = self.backbone.classifier[1].in_features
        self.backbone.features[0][0] = nn.Conv2d(1, 32, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1), bias=False)
        self.backbone.classifier = nn.Sequential(nn.Dropout(p=0.2), nn.Linear(num_features, num_classes))
    
    def forward(self, x):
        return self.backbone(x)

class EmotionDetector:
    """情感检测器"""
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.transform = None
        self.emotion_buffer = deque(maxlen=5)
        self.load_model()
        
    def load_model(self):
        """加载模型"""
        try:
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
            print(f"✅ 模型加载成功 - 设备：{self.device}")
        except Exception as e:
            print(f"❌ 模型加载失败：{e}")
            raise
    
    def predict(self, face_image):
        """
        预测单张图片的情绪
        :param face_image: numpy array 或 PIL Image
        :return: (emotion_name, confidence)
        """
        try:
            # 转换为 PIL Image
            if isinstance(face_image, np.ndarray):
                face_pil = Image.fromarray(face_image)
            else:
                face_pil = face_image
            
            # 预处理
            face_tensor = self.transform(face_pil).unsqueeze(0).to(self.device)
            
            # 预测
            with torch.no_grad():
                outputs = self.model(face_tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)
                conf, pred = torch.max(probs, 1)
                emotion = EMOTION_CLASSES[pred.item()]
                confidence = conf.item()
            
            # 平滑处理
            self.emotion_buffer.append(emotion)
            smooth_emotion = max(set(self.emotion_buffer), key=list(self.emotion_buffer).count)
            
            return smooth_emotion, confidence
        except Exception as e:
            print(f"预测错误：{e}")
            return 'neutral', 0.0
    
    def reset_buffer(self):
        """重置情绪缓冲区"""
        self.emotion_buffer.clear()
