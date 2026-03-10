"""
批量图片检测
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QFrame, QScrollArea, QGridLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QImage, QPixmap
import cv2
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
from App.code.config import MODEL_PATH, IMAGE_SIZE, EMOTION_CLASSES, EMOTION_COLORS, EMOTION_CHINESE, SHOW_BOX, SHOW_LABEL, ENABLE_DETECTION

class BatchImageDetectionPage(QWidget):
    """批量图片检测页面"""
    
    def __init__(self):
        super().__init__()
        self.model = None
        self.transform = None
        self.device = None
        self.model_loaded = False
        self.batch_images = []  # 批量检测的图片列表
        self.batch_save_dir = None  # 批量检测的保存目录
        self.processed_images = {}  # 存储处理后的图片路径
        self.init_ui()
        self.load_model()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("批量图片检测")
        self.setStyleSheet("""
            QWidget {
                background: #0f172a;
                color: #e2e8f0;
            }
        """)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 左侧：控制面板
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border-radius: 12px;
                border: 2px solid #334155;
            }
        """)
        left_panel.setFixedWidth(350)
        
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)
        
        # 标题
        title = QLabel("🗃️ 批量图片检测")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2dd4bf;
            padding: 10px 0;
        """)
        left_layout.addWidget(title)
        
        # 批量检测控制面板
        batch_control = QFrame()
        batch_control.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.6);
                border-radius: 10px;
                border: 1px solid #334155;
            }
        """)
        batch_layout = QVBoxLayout()
        batch_layout.setContentsMargins(10, 10, 10, 10)
        batch_layout.setSpacing(12)
        
        # 选择文件夹按钮
        batch_select_folder_btn = QPushButton("📂 选择文件夹")
        batch_select_folder_btn.setStyleSheet("""
            QPushButton {
                background: #2dd4bf;
                color: white;
                font-size: 16px;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #14b8a6;
            }
        """)
        batch_select_folder_btn.clicked.connect(self.batch_select_folder)
        batch_layout.addWidget(batch_select_folder_btn)
        
        # 选择保存目录按钮
        batch_save_btn = QPushButton("💾 选择保存目录")
        batch_save_btn.setStyleSheet("""
            QPushButton {
                background: #8b5cf6;
                color: white;
                font-size: 16px;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
        """)
        batch_save_btn.clicked.connect(self.batch_select_save_dir)
        batch_layout.addWidget(batch_save_btn)
        
        # 开始批量检测按钮
        self.batch_start_btn = QPushButton("🚀 开始检测")
        self.batch_start_btn.setStyleSheet("""
            QPushButton {
                background: #f59e0b;
                color: white;
                font-size: 16px;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #d97706;
            }
        """)
        self.batch_start_btn.clicked.connect(self.batch_start_detection)
        batch_layout.addWidget(self.batch_start_btn)
        
        # 清空选择按钮（放在最下面）
        clear_btn = QPushButton("🗑️ 清空选择")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                font-size: 16px;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        clear_btn.clicked.connect(self.clear_selection)
        batch_layout.addWidget(clear_btn)
        
        batch_control.setLayout(batch_layout)
        left_layout.addWidget(batch_control)
        
        # 统计信息
        self.stats_label = QLabel("已选择 0 张图片")
        self.stats_label.setStyleSheet("""
            font-size: 14px;
            color: #94a3b8;
            padding: 5px 0;
        """)
        left_layout.addWidget(self.stats_label)
        
        # 状态信息
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 14px;
            color: #94a3b8;
            padding: 10px;
            background: rgba(45, 212, 191, 0.1);
            border-radius: 8px;
        """)
        self.status_label.setText("就绪")
        left_layout.addWidget(self.status_label)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        main_layout.addWidget(left_panel, 2)
        
        # 右侧：图片预览区域
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
        preview_title = QLabel("🔍️ 图片预览")
        preview_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2dd4bf;
            padding: 10px 0;
        """)
        right_layout.addWidget(preview_title)
        
        # 图片预览滚动区域
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setStyleSheet("""
            QScrollArea {
                background: #0f172a;
                border: 2px solid #334155;
                border-radius: 10px;
            }
            QScrollBar:vertical {
                background: #1e293b;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #475569;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #64748b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: #1e293b;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #475569;
                border-radius: 6px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #64748b;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        self.preview_scroll.setWidgetResizable(True)
        
        # 预览容器
        self.preview_container = QWidget()
        self.preview_grid = QGridLayout()
        self.preview_grid.setContentsMargins(10, 10, 10, 10)
        self.preview_grid.setSpacing(10)
        self.preview_container.setLayout(self.preview_grid)
        self.preview_scroll.setWidget(self.preview_container)
        right_layout.addWidget(self.preview_scroll, 1)
        
        right_panel.setLayout(right_layout)
        main_layout.addWidget(right_panel, 8)
        
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
            self.model_loaded = True
        except Exception as e:
            print(f"❌ 模型加载失败：{e}")
            import traceback
            traceback.print_exc()
    
    def batch_select_folder(self):
        """选择文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
            added_count = 0
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in image_extensions):
                        file_path = os.path.join(root, file)
                        if file_path not in self.batch_images:
                            self.batch_images.append(file_path)
                            added_count += 1
            self.update_preview_grid()
            self.update_start_button()
            self.update_stats()
            print(f"✅ 已从文件夹添加 {added_count} 张新图片")
    
    def clear_selection(self):
        """清空选择"""
        self.batch_images.clear()
        self.processed_images.clear()
        self.update_preview_grid()
        self.update_start_button()
        self.update_stats()
        self.status_label.setText("已清空选择")
        print("✅ 已清空所有选择")
    
    def batch_select_save_dir(self):
        """选择保存目录"""
        save_dir = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if save_dir:
            self.batch_save_dir = save_dir
            self.update_start_button()
            self.status_label.setText(f"保存目录：{os.path.basename(save_dir)}")
            print(f"✅ 已选择保存目录：{save_dir}")
    
    def update_stats(self):
        """更新统计信息"""
        self.stats_label.setText(f"已选择 {len(self.batch_images)} 张图片")
    
    def update_preview_grid(self):
        """更新预览网格 - 一行五张正方形图片"""
        # 清空现有网格
        while self.preview_grid.count():
            item = self.preview_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.batch_images:
            # 显示空状态提示
            empty_label = QLabel("选择图片后将显示预览")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("""
                font-size: 18px;
                color: #64748b;
                padding: 50px;
            """)
            self.preview_grid.addWidget(empty_label, 0, 0)
            return
        
        # 创建图片预览项 - 每行5个
        for i, img_path in enumerate(self.batch_images):
            row = i // 5
            col = i % 5
            
            preview_item = self.create_preview_item(img_path, i)
            self.preview_grid.addWidget(preview_item, row, col)
    
    def create_preview_item(self, img_path, index):
        """创建单个预览项"""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border-radius: 8px;
                border: 2px solid #334155;
            }
            QFrame:hover {
                border: 2px solid #2dd4bf;
            }
        """)
        item.setFixedSize(140, 180)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # 图片显示区域（正方形）
        img_label = QLabel()
        img_label.setFixedSize(120, 120)
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setStyleSheet("""
            background: #0f172a;
            border-radius: 6px;
            border: 1px solid #334155;
        """)
        
        # 加载并显示图片
        pixmap = self.load_thumbnail(img_path)
        if pixmap:
            img_label.setPixmap(pixmap)
        else:
            img_label.setText("❌")
            img_label.setStyleSheet("""
                background: #0f172a;
                border-radius: 6px;
                border: 1px solid #ef4444;
                color: #ef4444;
                font-size: 24px;
            """)
        
        layout.addWidget(img_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 文件名
        file_name = os.path.basename(img_path)
        if len(file_name) > 12:
            file_name = file_name[:10] + "..."
        name_label = QLabel(file_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("""
            font-size: 11px;
            color: #94a3b8;
        """)
        layout.addWidget(name_label)
        
        # 序号标签
        index_label = QLabel(f"#{index + 1}")
        index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        index_label.setStyleSheet("""
            font-size: 10px;
            color: #2dd4bf;
            font-weight: bold;
        """)
        layout.addWidget(index_label)
        
        item.setLayout(layout)
        return item
    
    def load_thumbnail(self, img_path, size=120):
        """加载缩略图"""
        try:
            # 检查是否有处理后的图片
            if img_path in self.processed_images:
                img_path = self.processed_images[img_path]
            
            image = cv2.imread(img_path)
            if image is None:
                return None
            
            # 转换为RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 计算裁剪区域（正方形）
            h, w = image.shape[:2]
            min_dim = min(h, w)
            start_y = (h - min_dim) // 2
            start_x = (w - min_dim) // 2
            image = image[start_y:start_y+min_dim, start_x:start_x+min_dim]
            
            # 缩放
            image = cv2.resize(image, (size, size))
            
            # 转换为QPixmap
            height, width, channel = image.shape
            bytes_per_line = channel * width
            q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            return pixmap
        except Exception as e:
            print(f"❌ 加载缩略图失败 {img_path}: {e}")
            return None
    
    def update_start_button(self):
        """更新开始按钮状态"""
        self.batch_start_btn.setEnabled(len(self.batch_images) > 0 and self.batch_save_dir is not None)
    
    def batch_start_detection(self):
        """开始批量检测"""
        import os
        
        if not self.model_loaded:
            self.status_label.setText("❌ 模型未加载")
            return
        
        if not self.batch_images:
            self.status_label.setText("❌ 未选择图片")
            return
        
        if not self.batch_save_dir:
            self.status_label.setText("❌ 未选择保存目录")
            return
        
        # 确保保存目录存在
        os.makedirs(self.batch_save_dir, exist_ok=True)
        
        # 确保应用程序内部临时目录存在
        app_dir = os.path.dirname(os.path.dirname(__file__))
        temp_dir = os.path.join(app_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        print(f"📁 临时目录: {temp_dir}")
        
        self.status_label.setText("🔍 正在检测...")
        self.processed_images.clear()
        
        # 批量处理
        processed = 0
        total = len(self.batch_images)
        
        for img_path in self.batch_images:
            try:
                # 读取图片
                image = cv2.imread(img_path)
                if image is None:
                    self.status_label.setText(f"❌ 无法读取: {os.path.basename(img_path)}")
                    continue
                
                # 检测人脸
                results, image = self.detect_faces(image)
                
                # 保存结果到应用程序内部临时目录（避免权限问题）
                temp_output_path = os.path.join(temp_dir, f"processed_{os.path.basename(img_path)}")
                cv2.imwrite(temp_output_path, image)
                
                # 同时尝试保存到用户指定目录
                try:
                    user_output_path = os.path.join(self.batch_save_dir, f"processed_{os.path.basename(img_path)}")
                    cv2.imwrite(user_output_path, image)
                except Exception as e:
                    print(f"⚠️ 无法保存到用户目录: {e}")
                
                # 记录处理后的图片路径（使用临时目录路径）
                self.processed_images[img_path] = temp_output_path
                
                # 添加数据统计
                from App.views.statistics import StatisticsPage
                image_name = os.path.basename(img_path)
                for x, y, w_box, h_box, emotion, confidence in results:
                    StatisticsPage.add_detection_data(
                        image_name=image_name,
                        emotion=emotion,
                        confidence=confidence,
                        source="批量图片检测"
                    )
                print(f"📊 已统计 {len(results)} 个人脸数据")
                
                processed += 1
                self.status_label.setText(f"处理中：{processed}/{total}")
                
                # 实时更新预览
                self.update_preview_grid()
                
            except Exception as e:
                print(f"❌ 处理失败 {img_path}: {e}")
                import traceback
                traceback.print_exc()
        
        self.status_label.setText(f"✅ 处理完成：{processed}/{total}")
        print(f"✅ 批量处理完成：{processed}/{total}")
        
        # 最终更新预览显示处理后的图片
        self.update_preview_grid()
    
    def detect_faces(self, image):
        """检测人脸"""
        results = []
        
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
                return results, image
            
            # 处理所有人脸
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            for idx, (x, y, w_box, h_box) in enumerate(faces):
                # 提取人脸区域
                face_roi = gray[y:y+h_box, x:x+w_box]
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
                
                results.append((x, y, w_box, h_box, emotion, confidence))
            
            # 绘制矩形框
            for idx, (x, y, w_box, h_box, emotion, confidence) in enumerate(results):
                color = EMOTION_COLORS.get(emotion, (0, 255, 0))
                
                if SHOW_BOX:
                    # 绘制矩形框
                    cv2.rectangle(image, (x, y), (x+w_box, y+h_box), color, 3)
                    # 添加内层细线
                    cv2.rectangle(image, (x+1, y+1), (x+w_box-1, y+h_box-1), (255, 255, 255), 1)
            
            # 绘制文字标签（完全按照图片检测页面的实现）
            if SHOW_LABEL:
                print(f"🔍 开始绘制标签，results: {len(results)}")
                # 计算图片大小，动态调整字体大小（与图片检测页面一致）
                h_img, w_img = image.shape[:2]
                base_font_size = max(18, min(36, int(min(w_img, h_img) * 0.03)))
                print(f"📏 字体大小: {base_font_size}")
                
                image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(image_pil)
                
                for idx, (x, y, w_box, h_box, emotion, confidence) in enumerate(results):
                    color = EMOTION_COLORS.get(emotion, (0, 255, 0))
                    print(f"😀 表情: {emotion}, 置信度: {confidence}, 颜色: {color}")
                    
                    # 表情图标映射
                    emotion_icons = {
                        'angry': '😠', 'disgust': '🤢', 'fear': '😨',
                        'happy': '😊', 'neutral': '😐', 'sad': '😢', 'surprise': '😲'
                    }
                    
                    # 使用PIL绘制中文标签，加上表情图标
                    chinese_text = f"{emotion_icons.get(emotion, '😐')} 👤{idx+1} {EMOTION_CHINESE.get(emotion, emotion)}: {confidence:.2f}"
                    print(f"📝 标签文本: {chinese_text}")
                    
                    try:
                        font = ImageFont.truetype("msyhbd.ttc", base_font_size, encoding="utf-8")
                        print(f"🖋️ 成功加载字体: msyhbd.ttc")
                    except:
                        try:
                            font = ImageFont.truetype("simhei.ttf", base_font_size, encoding="utf-8")
                            print(f"🖋️ 成功加载字体: simhei.ttf")
                        except:
                            font = ImageFont.load_default()
                            print(f"🖋️ 使用默认字体")
                    
                    # 绘制文字阴影（与图片检测页面完全一致）
                    shadow_offset = 2
                    draw.text((x + shadow_offset, y - base_font_size - 10 + shadow_offset), chinese_text, 
                              font=font, fill=(0, 0, 0))
                    # 绘制主文字（与图片检测页面完全一致）
                    draw.text((x, y - base_font_size - 10), chinese_text, 
                              font=font, fill=(color[2], color[1], color[0]))
                    print(f"✅ 标签绘制完成")
                
                # 转换回OpenCV格式
                image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
                print(f"🔄 转换回OpenCV格式")
        
        return results, image
