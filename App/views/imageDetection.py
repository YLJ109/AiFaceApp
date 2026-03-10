"""
图片检测
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QFrame, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QImage, QPixmap
import cv2
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from collections import deque
from App.code.config import MODEL_PATH, IMAGE_SIZE, EMOTION_CLASSES, EMOTION_COLORS, EMOTION_CHINESE, SHOW_BOX, SHOW_LABEL, ENABLE_DETECTION

class ImageDetectionPage(QWidget):
    """图片检测页面"""
    
    def __init__(self):
        super().__init__()
        self.model = None
        self.transform = None
        self.device = None
        self.model_loaded = False
        self.current_image = None  # 保存当前处理的图像
        self.current_image_path = None  # 保存当前处理的图像路径
        self.init_ui()
    
    def ensure_model_loaded(self):
        """确保模型已加载"""
        if not self.model_loaded:
            self.load_model()
            self.model_loaded = True
    
    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 左侧：实时数据面板
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border-radius: 12px;
                border: 2px solid #334155;
            }
        """)
        left_panel.setFixedWidth(300)
        
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)
        
        # 标题
        title = QLabel("📊 实时数据")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2dd4bf;
            padding: 10px 0;
        """)
        left_layout.addWidget(title)
        
        # 人脸信息卡片容器
        self.faces_container = QWidget()
        self.faces_layout = QVBoxLayout()
        self.faces_layout.setContentsMargins(0, 0, 0, 0)
        self.faces_layout.setSpacing(8)
        self.faces_container.setLayout(self.faces_layout)
        left_layout.addWidget(self.faces_container)
        
        # 初始化人脸信息标签列表 - 使用卡片式布局
        self.face_info_labels = []
        for i in range(10):  # 最多10个人脸
            face_widget = QFrame()
            face_widget.setStyleSheet("""
                QFrame {
                    background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
                    border-radius: 12px;
                    border: none;
                }
                QFrame:hover {
                    background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 1));
                }
            """)
            face_layout = QHBoxLayout()
            face_layout.setContentsMargins(12, 10, 12, 10)
            face_layout.setSpacing(12)
            
            # 左侧：人脸编号圆形图标
            number_label = QLabel(f"{i+1}")
            number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            number_label.setStyleSheet("""
                QLabel {
                    background: rgba(45, 212, 191, 0.2);
                    color: #2dd4bf;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 15px;
                    min-width: 30px;
                    max-width: 30px;
                    min-height: 30px;
                    max-height: 30px;
                }
            """)
            face_layout.addWidget(number_label)
            
            # 中间：表情和准确率
            info_layout = QVBoxLayout()
            info_layout.setSpacing(4)
            
            emotion_label = QLabel("未检测")
            emotion_label.setStyleSheet("""
                font-size: 15px;
                font-weight: bold;
                color: #e2e8f0;
            """)
            info_layout.addWidget(emotion_label)
            
            confidence_label = QLabel("--%")
            confidence_label.setStyleSheet("""
                font-size: 12px;
                color: #94a3b8;
            """)
            info_layout.addWidget(confidence_label)
            
            face_layout.addLayout(info_layout, stretch=1)
            
            # 右侧：表情图标（初始为空）
            icon_label = QLabel("")
            icon_label.setStyleSheet("""
                font-size: 20px;
                padding: 0 5px;
                min-width: 30px;
            """)
            face_layout.addWidget(icon_label)
            
            face_widget.setLayout(face_layout)
            face_widget.setVisible(False)  # 默认隐藏
            
            # 添加到垂直布局，每行一个人脸
            self.faces_layout.addWidget(face_widget)
            
            self.face_info_labels.append((face_widget, emotion_label, confidence_label, icon_label, number_label))
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        main_layout.addWidget(left_panel, 3)
        
        # 右侧：图片显示和控制面板
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border-radius: 12px;
                border: 2px solid #334155;
            }
        """)
        
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)
        
        # 标题
        video_title = QLabel("🖼 图片画面")
        video_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2dd4bf;
            padding: 10px 0;
        """)
        right_layout.addWidget(video_title)
        
        # 图片显示
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(600, 400)
        self.image_label.setStyleSheet("""
            background: #1e293b;
            border-radius: 10px;
            color: #94a3b8;
            font-size: 16px;
            border: 2px solid #334155;
        """)
        self.image_label.setText("请选择图片")
        right_layout.addWidget(self.image_label, 9)
        

        
        # 控制面板
        control_panel = QFrame()
        control_panel.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border-radius: 12px;
                border: 2px solid #334155;
            }
        """)
        
        control_layout = QVBoxLayout()
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)
        

        
        # 选择图片按钮
        select_btn = QPushButton("📂 选择图片")
        select_btn.setStyleSheet("""
            QPushButton {
                background: #2dd4bf;
                color: white;
                font-size: 16px;
                padding: 15px;
                border-radius: 10px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #14b8a6;
            }
        """)
        control_layout.addWidget(select_btn)
        select_btn.clicked.connect(self.select_image)
        
        # 拍照按钮
        self.capture_btn = QPushButton("📷 保存图片")
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background: #8b5cf6;
                color: white;
                font-size: 16px;
                padding: 15px;
                border-radius: 10px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
            QPushButton:disabled {
                background: #475569;
                color: #94a3b8;
            }
        """)
        self.capture_btn.clicked.connect(self.save_image)
        self.capture_btn.setEnabled(False)
        control_layout.addWidget(self.capture_btn)
        

        
        control_panel.setLayout(control_layout)
        right_layout.addWidget(control_panel)
        right_panel.setLayout(right_layout)
        main_layout.addWidget(right_panel, 7)
        
        self.setLayout(main_layout)
    
    def load_model(self):
        """加载模型"""
        try:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            print(f"使用设备：{self.device}")
            
            checkpoint = torch.load(MODEL_PATH, map_location=self.device)
            
            class EmotionClassifier(nn.Module):
                def __init__(self, num_classes=7):
                    super().__init__()
                    from torchvision.models import MobileNet_V2_Weights
                    self.backbone = models.mobilenet_v2(weights=MobileNet_V2_Weights.DEFAULT)
                    num_features = self.backbone.classifier[1].in_features
                    self.backbone.features[0][0] = nn.Conv2d(1, 32, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1), bias=False)
                    self.backbone.classifier = nn.Sequential(nn.Dropout(p=0.2), nn.Linear(num_features, num_classes))
                def forward(self, x):
                    return self.backbone(x)
            
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
        except Exception as e:
            print(f"❌ 模型加载失败：{e}")
            import traceback
            traceback.print_exc()
    
    def select_image(self):
        """选择图片"""
        self.ensure_model_loaded()
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.xpm *.jpg *.jpeg)")
        if file_path:
            print(f"✅ 已选择：{file_path}")
            self.current_image_path = file_path
            self.detect_image(file_path)
    
    def detect_image(self, file_path):
        """检测图片中的表情"""
        try:
            # 读取图片
            image = cv2.imread(file_path)
            if image is None:

                return
            
            # 显示原图
            self.display_image(image)
            
            if ENABLE_DETECTION:
                # 确保人脸检测模型已加载
                if not hasattr(self, 'face_net') or self.face_net is None:
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
                
                # 使用Caffe模型进行人脸检测
                h, w = image.shape[:2]
                blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
                self.face_net.setInput(blob)
                detections = self.face_net.forward()
                
                # 解析检测结果
                faces = []
                for i in range(detections.shape[2]):
                    confidence = detections[0, 0, i, 2]
                    if confidence > 0.6:  # 置信度阈值
                        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                        (x, y, x1, y1) = box.astype("int")
                        # 确保边界有效
                        x, y = max(0, x), max(0, y)
                        w_box, h_box = max(10, x1-x), max(10, y1-y)
                        faces.append((x, y, w_box, h_box))
                
                if len(faces) == 0:
                    return
                
                # 处理所有人脸
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                results = []
                
                for idx, (x, y, w, h) in enumerate(faces):
                    # 提取人脸区域
                    face_roi = gray[y:y+h, x:x+w]
                    face_resized = cv2.resize(face_roi, (96, 96))
                    
                    # 模型预测
                    face_pil = Image.fromarray(face_resized)
                    face_tensor = self.transform(face_pil).unsqueeze(0).to(self.device)
                    
                    with torch.no_grad():
                        outputs = self.model(face_tensor)
                        probs = torch.nn.functional.softmax(outputs, dim=1)
                        conf, pred = torch.max(probs, 1)
                        emotion = EMOTION_CLASSES[pred.item()]
                        confidence = conf.item()
                    
                    results.append((x, y, w, h, emotion, confidence))
                
                # 计算图片大小，动态调整字体大小
                h_img, w_img = image.shape[:2]
                base_font_size = max(18, min(36, int(min(w_img, h_img) * 0.03)))
                
                # 先处理所有绘制
                result_texts = []
                
                # 绘制矩形框
                for idx, (x, y, w, h, emotion, confidence) in enumerate(results):
                    color = EMOTION_COLORS.get(emotion, (0, 255, 0))
                    
                    if SHOW_BOX:
                        # 绘制矩形框
                        cv2.rectangle(image, (x, y), (x+w, y+h), color, 3)
                        # 添加内层细线
                        cv2.rectangle(image, (x+1, y+1), (x+w-1, y+h-1), (255, 255, 255), 1)
                    
                    result_texts.append(f"{idx+1}: {EMOTION_CHINESE.get(emotion, emotion)} (准确率：{confidence*100:.1f}%)")
                
                # 然后绘制文字标签
                if SHOW_LABEL:
                    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                    draw = ImageDraw.Draw(image_pil)
                    
                    for idx, (x, y, w, h, emotion, confidence) in enumerate(results):
                        color = EMOTION_COLORS.get(emotion, (0, 255, 0))
                        
                        # 表情图标映射
                        emotion_icons = {
                            'angry': '😠', 'disgust': '🤢', 'fear': '😨',
                            'happy': '😊', 'neutral': '😐', 'sad': '😢', 'surprise': '😲'
                        }
                        
                        # 使用PIL绘制中文标签，加上表情图标
                        chinese_text = f"{emotion_icons.get(emotion, '😐')} 👤{idx+1} {EMOTION_CHINESE.get(emotion, emotion)}: {confidence:.2f}"
                        
                        try:
                            font = ImageFont.truetype("msyhbd.ttc", base_font_size, encoding="utf-8")
                        except:
                            try:
                                font = ImageFont.truetype("simhei.ttf", base_font_size, encoding="utf-8")
                            except:
                                font = ImageFont.load_default()
                        
                        # 绘制文字阴影
                        shadow_offset = 2
                        draw.text((x + shadow_offset, y - base_font_size - 10 + shadow_offset), chinese_text, 
                                  font=font, fill=(0, 0, 0))
                        # 绘制主文字
                        draw.text((x, y - base_font_size - 10), chinese_text, 
                                  font=font, fill=(color[2], color[1], color[0]))
                    
                    # 转换回OpenCV格式
                    image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
                
                # 更新显示
                self.display_image(image)
                
                # 表情图标映射
                emotion_icons = {
                    'happy': '😊',
                    'sad': '😢',
                    'angry': '😠',
                    'surprise': '😮',
                    'fear': '😨',
                    'disgust': '🤢',
                    'neutral': '😐'
                }
                
                # 更新左侧人脸信息卡片
                for i, (face_widget, emotion_label, confidence_label, icon_label, number_label) in enumerate(self.face_info_labels):
                    if i < len(results):
                        x, y, w, h, emotion, confidence = results[i]
                        emotion_label.setText(EMOTION_CHINESE.get(emotion, emotion))
                        confidence_label.setText(f"{confidence*100:.1f}%")
                        icon_label.setText(emotion_icons.get(emotion, ''))
                        # 显示卡片
                        face_widget.setVisible(True)
                    else:
                        # 清空未使用的卡片
                        emotion_label.setText("未检测")
                        confidence_label.setText("--%")
                        icon_label.setText("")
                        # 隐藏多余的卡片
                        face_widget.setVisible(False)
                
                # 添加数据统计
                from App.views.statistics import StatisticsPage
                import os
                image_name = os.path.basename(self.current_image_path)
                
                if results:
                    print(f"✅ 检测到 {len(results)} 个人脸")
                    for text in result_texts:
                        print(f"  {text}")
                    
                    # 统计检测到的人脸数据
                    for x, y, w, h, emotion, confidence in results:
                        StatisticsPage.add_detection_data(
                            image_name=image_name,
                            emotion=emotion,
                            confidence=confidence,
                            source="图片检测"
                        )
                    print("📊 数据已统计")
                else:
                    # 统计未检测到人脸的数据
                    StatisticsPage.add_detection_data(
                        image_name=image_name,
                        emotion="未检测",
                        confidence=0.0,
                        source="图片检测"
                    )
                    print("📊 数据已统计（未检测到人脸）")
            
        except Exception as e:
            print(f"❌ 检测失败：{e}")
            import traceback
            traceback.print_exc()
    
    def save_image(self):
        """保存图片"""
        try:
            if self.current_image is not None:
                # 确保保存目录存在
                import os
                # 获取App目录的绝对路径
                app_dir = os.path.dirname(os.path.dirname(__file__))
                capture_dir = os.path.join(app_dir, 'capture', 'image')
                os.makedirs(capture_dir, exist_ok=True)
                
                # 生成唯一的文件名
                import time
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"image_{timestamp}.jpg"
                filepath = os.path.join(capture_dir, filename)
                
                # 保存图像
                cv2.imwrite(filepath, self.current_image)
                print(f"📷 图片保存成功：{filepath}")
                
                # 显示保存成功提示
                from PyQt6.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setWindowTitle("保存成功")
                msg.setText("图片已成功保存！")
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
                
                # 打印保存成功消息
                print("✅ 图片已保存")
            else:
                print("❌ 保存失败：没有可保存的图片")
        except Exception as e:
            print(f"❌ 保存图片错误：{e}")
    
    def display_image(self, image):
        """显示图片"""
        try:
            # 保存当前图像
            self.current_image = image.copy()
            
            # 启用保存按钮
            self.capture_btn.setEnabled(True)
            
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
                self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
        except Exception as e:
            print(f"❌ 显示图片失败：{e}")
