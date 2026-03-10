"""
视频检测 - 与实时检测相同的样式和功能
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QFileDialog, QSlider, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QImage, QPixmap
import cv2
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from collections import deque
import pyqtgraph as pg
from App.code.config import MODEL_PATH, IMAGE_SIZE, EMOTION_CLASSES, EMOTION_COLORS, EMOTION_CHINESE
from App.code.settings_manager import settings_manager

class VideoPredictionThread(QThread):
    """视频预测线程"""
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

class VideoDetectionPage(QWidget):
    """视频检测页面 - 与实时检测相同的样式"""
    
    def __init__(self):
        super().__init__()
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.model = None
        self.transform = None
        self.device = None
        self.emotion_stats = {emotion: 0 for emotion in EMOTION_CLASSES}
        self.is_processing = False
        self.last_prediction_time = 0
        self.frame_count = 0
        self.last_fps_time = 0
        self.current_fps = 0
        self.face_net = None
        self.face_results = []
        self.face_emotion_buffers = []
        self.face_threads = []
        self.is_playing = False
        self.video_path = None
        self.init_ui()
        self.load_model()
    
    def init_ui(self):
        """初始化 UI - 与实时检测相同的布局"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 左侧数据面板
        left_panel = self.create_data_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 右侧视频和控制面板
        right_panel = self.create_video_panel()
        main_layout.addWidget(right_panel, 3)
        
        self.setLayout(main_layout)
    
    def create_data_panel(self):
        """创建数据面板 - 与实时检测相同的样式"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border-radius: 12px;
                border: 2px solid #334155;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题
        title = QLabel("📊 实时数据")
        title.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #2dd4bf;
            padding: 10px 0;
            border-bottom: 2px solid #334155;
        """)
        layout.addWidget(title)
        
        # 多个人脸信息面板
        layout.addSpacing(10)
        
        # 创建多个人脸信息容器
        self.faces_container = QWidget()
        self.faces_layout = QVBoxLayout()
        self.faces_layout.setContentsMargins(0, 0, 0, 0)
        self.faces_layout.setSpacing(8)
        self.faces_container.setLayout(self.faces_layout)
        layout.addWidget(self.faces_container)
        
        # 初始化人脸信息标签列表
        self.face_info_labels = []
        for i in range(5):
            face_widget = QFrame()
            face_widget.setStyleSheet("""
                QFrame {
                    background: linear-gradient(135deg, rgba(30, 41, 59, 0.5), rgba(15, 23, 42, 0.6));
                    border-radius: 12px;
                    border: none;
                }
                QFrame:hover {
                    background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.7));
                }
            """)
            face_layout = QHBoxLayout()
            face_layout.setContentsMargins(12, 10, 12, 10)
            face_layout.setSpacing(12)
            
            # 左侧：人脸编号
            number_label = QLabel(f"{i+1}")
            number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            number_label.setStyleSheet("""
                QLabel {
                    background: rgba(100, 116, 139, 0.2);
                    color: #64748b;
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
                color: #64748b;
            """)
            info_layout.addWidget(emotion_label)
            
            confidence_label = QLabel("--%")
            confidence_label.setStyleSheet("""
                font-size: 12px;
                color: #94a3b8;
            """)
            info_layout.addWidget(confidence_label)
            
            face_layout.addLayout(info_layout, stretch=1)
            
            # 右侧：表情图标
            icon_label = QLabel("")
            icon_label.setStyleSheet("""
                font-size: 20px;
                padding: 0 5px;
                min-width: 30px;
            """)
            face_layout.addWidget(icon_label)
            
            face_widget.setLayout(face_layout)
            face_widget.setVisible(True)
            self.faces_layout.addWidget(face_widget)
            
            self.face_info_labels.append((face_widget, emotion_label, confidence_label, icon_label, number_label))
        
        layout.addSpacing(10)
        
        # 表情统计折线图
        graph_title = QLabel("📈 表情分布")
        graph_title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #e2e8f0;
            padding: 10px 0;
        """)
        layout.addWidget(graph_title)
        
        # 创建折线图
        self.emotion_graph = pg.PlotWidget()
        self.emotion_graph.setStyleSheet("""
            background-color: #1e293b;
            border: 2px solid #334155;
            border-radius: 10px;
        """)
        
        self.emotion_graph.setBackground(None)
        self.emotion_graph.setLabel('left', '数量', color='#94a3b8')
        self.emotion_graph.setLabel('bottom', '表情', color='#94a3b8')
        self.emotion_graph.hideAxis('top')
        self.emotion_graph.hideAxis('right')
        self.emotion_graph.showGrid(x=True, y=True, alpha=0.2)
        
        self.emotion_curve = self.emotion_graph.plot(
            x=list(range(len(EMOTION_CLASSES))),
            y=[0]*len(EMOTION_CLASSES),
            pen=pg.mkPen(color='#2dd4bf', width=2)
        )
        
        ticks = []
        for i, emotion in enumerate(EMOTION_CLASSES):
            ticks.append((i, EMOTION_CHINESE.get(emotion, emotion)))
        
        x_axis = self.emotion_graph.getAxis('bottom')
        x_axis.setTicks([ticks])
        
        self.emotion_graph.setXRange(-0.5, len(EMOTION_CLASSES)-0.5, padding=0)
        self.emotion_graph.setYRange(0, 10, padding=0.1)
        
        view_box = self.emotion_graph.getViewBox()
        view_box.setMouseEnabled(x=False, y=False)
        view_box.setMenuEnabled(False)
        
        self.emotion_graph.setMinimumHeight(200)
        layout.addWidget(self.emotion_graph)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_video_panel(self):
        """创建视频面板 - 与实时检测相同的样式"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: #0f172a;
                border-radius: 12px;
                border: 2px solid #334155;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题和帧率
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        title_label = QLabel("🎬 视频画面")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2dd4bf; padding: 10px 0;")
        title_layout.addWidget(title_label)
        
        self.fps_label = QLabel("帧率：-- FPS")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fps_label.setStyleSheet("""
            font-size: 16px;
            color: #f59e0b;
            padding: 10px;
            background: rgba(245, 158, 11, 0.15);
            border-radius: 8px;
        """)
        title_layout.addWidget(self.fps_label)
        
        layout.addLayout(title_layout)
        
        # 视频显示区域
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("""
            background: #1e293b;
            border-radius: 10px;
            color: #94a3b8;
            font-size: 16px;
            border: 2px solid #334155;
        """)
        self.video_label.setText("选择一个视频文件进行面部表情分析")
        layout.addWidget(self.video_label, 9)
        
        # 进度条
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #334155;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #2dd4bf;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #2dd4bf;
                border-radius: 4px;
            }
        """)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderReleased.connect(self.seek_video)
        layout.addWidget(self.progress_slider)
        

        
        # 控制按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.select_btn = QPushButton("📁 选择视频")
        self.select_btn.setStyleSheet("""
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
        self.select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_btn.clicked.connect(self.select_video)
        btn_layout.addWidget(self.select_btn)
        
        self.play_btn = QPushButton("▶️ 播放")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                font-size: 16px;
                padding: 15px;
                border-radius: 10px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:disabled {
                background: #475569;
            }
        """)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.toggle_play)
        btn_layout.addWidget(self.play_btn)
        
        self.capture_btn = QPushButton("📷 拍照")
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background: #f59e0b;
                color: white;
                font-size: 16px;
                padding: 15px;
                border-radius: 10px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #d97706;
            }
            QPushButton:disabled {
                background: #475569;
            }
        """)
        self.capture_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.capture_btn.setEnabled(False)
        self.capture_btn.clicked.connect(self.capture_image)
        btn_layout.addWidget(self.capture_btn)
        
        layout.addLayout(btn_layout)
        panel.setLayout(layout)
        return panel
    
    def load_model(self):
        """加载模型 - 与实时检测相同"""
        # 加载表情识别模型
        try:
            # 自动检测并使用CUDA（如果可用）
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            print(f"使用设备: {self.device}")
            
            # 尝试加载模型 - 处理不同的模型结构
            from torchvision.models import MobileNet_V2_Weights
            self.model = models.mobilenet_v2(weights=MobileNet_V2_Weights.DEFAULT)
            # 修改模型以使用1通道输入（灰度图）
            self.model.features[0][0] = nn.Conv2d(1, 32, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1), bias=False)
            self.model.classifier[1] = nn.Linear(self.model.last_channel, 7)
            
            checkpoint = torch.load(MODEL_PATH, map_location=self.device, weights_only=True)
            
            # 检查模型结构
            if 'model_state_dict' in checkpoint:
                # 新格式
                state_dict = checkpoint['model_state_dict']
            else:
                # 旧格式
                state_dict = checkpoint
            
            # 尝试加载状态字典
            try:
                self.model.load_state_dict(state_dict)
            except Exception as e:
                # 如果失败，尝试处理 backbone 前缀
                print(f"尝试处理模型结构...")
                new_state_dict = {}
                for k, v in state_dict.items():
                    # 移除 backbone 前缀
                    if k.startswith('backbone.'):
                        new_k = k[9:]  # 移除 'backbone.'
                        new_state_dict[new_k] = v
                    else:
                        new_state_dict[k] = v
                self.model.load_state_dict(new_state_dict)
            
            self.model.to(self.device)
            self.model.eval()
            
            self.transform = transforms.Compose([
                transforms.Grayscale(num_output_channels=1),
                transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5], std=[0.5])
            ])
            
            print("✅ 表情识别模型加载成功")
        except Exception as e:
            print(f"❌ 表情识别模型加载失败：{e}")
            import traceback
            traceback.print_exc()
        
        # 加载人脸检测模型（单独的try块）
        try:
            self.face_net = cv2.dnn.readNetFromCaffe(
                'App/models/deploy.prototxt',
                'App/models/res10_300x300_ssd_iter_140000_fp16.caffemodel'
            )
            print("✅ 人脸检测模型加载成功")
        except Exception as e:
            print(f"❌ 人脸检测模型加载失败：{e}")
            import traceback
            traceback.print_exc()
    
    def select_video(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", 
            "视频文件 (*.mp4 *.avi *.mov *.mkv);;所有文件 (*.*)"
        )
        
        if file_path:
            self.video_path = file_path
            self.load_video()
    
    def load_video(self):
        """加载视频"""
        if self.cap:
            self.cap.release()
        
        self.cap = cv2.VideoCapture(self.video_path)
        
        if not self.cap.isOpened():
            print("❌ 无法打开视频文件")
            return
        
        # 设置进度条
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.progress_slider.setMaximum(total_frames)
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(True)
        
        # 启用按钮
        self.play_btn.setEnabled(True)
        self.capture_btn.setEnabled(True)
        
        # 显示第一帧
        ret, frame = self.cap.read()
        if ret:
            self.display_frame(frame)
        
        # 重置统计数据
        self.emotion_stats = {emotion: 0 for emotion in EMOTION_CLASSES}
        self.face_results = []
        self.face_emotion_buffers = []
        
        print(f"✅ 视频已加载: {self.video_path}")
    
    def toggle_play(self):
        """切换播放/暂停"""
        if self.is_playing:
            self.pause_video()
        else:
            self.play_video()
    
    def play_video(self):
        """播放视频"""
        if not self.cap:
            return
        
        self.is_playing = True
        self.play_btn.setText("⏸️ 暂停")
        self.timer.start(30)
    
    def pause_video(self):
        """暂停视频"""
        self.is_playing = False
        self.play_btn.setText("▶️ 播放")
        self.timer.stop()
    
    def seek_video(self):
        """跳转到指定位置"""
        if self.cap:
            frame_pos = self.progress_slider.value()
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
    
    def update_frame(self):
        """更新视频帧 - 与实时检测相同的处理逻辑"""
        if not self.cap or not self.is_playing:
            return
        
        ret, frame = self.cap.read()
        if not ret:
            self.pause_video()
            return
        
        # 更新进度条
        current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        self.progress_slider.setValue(current_frame)
        
        # 处理帧
        self.process_frame(frame)
    
    def process_frame(self, frame):
        """处理帧 - 与实时检测相同的算法"""
        from App.code.config import ENABLE_DETECTION, SHOW_BOX, SHOW_LABEL, MAX_FACES
        
        # 使用Caffe模型进行人脸检测
        faces = []
        if ENABLE_DETECTION and self.face_net is not None:
            try:
                h, w = frame.shape[:2]
                blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
                self.face_net.setInput(blob)
                detections = self.face_net.forward()
                
                for i in range(detections.shape[2]):
                    confidence = detections[0, 0, i, 2]
                    if confidence > 0.5:
                        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                        (x, y, x1, y1) = box.astype("int")
                        faces.append((x, y, x1-x, y1-y))
            except Exception as e:
                print(f"人脸检测错误：{e}")
        
        # 限制检测频率
        import time
        current_time = time.time()
        should_detect = not self.is_processing and (current_time - self.last_prediction_time >= 0.2)
        
        # 总是更新结果列表长度
        num_faces = len(faces[:MAX_FACES])
        if len(self.face_results) != num_faces:
            self.face_results = [{'emotion': 'neutral', 'confidence': 0.0} for _ in range(num_faces)]
        
        if should_detect and faces:
            self.is_processing = True
            self.last_prediction_time = current_time
            
            for idx, (x, y, w, h) in enumerate(faces[:MAX_FACES]):
                try:
                    # 只有在表情识别模型加载成功时才进行表情识别
                    if self.model and self.transform:
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        face_roi = gray[y:y+h, x:x+w]
                        face_resized = cv2.resize(face_roi, (96, 96))
                        face_pil = Image.fromarray(face_resized)
                        
                        thread = VideoPredictionThread(
                            face_pil, self.transform, self.model, self.device, idx
                        )
                        thread.result_ready.connect(self.on_prediction_ready)
                        thread.finished.connect(lambda t=thread: self.on_thread_finished(t))
                        thread.start()
                        
                        self.face_threads.append(thread)
                        
                        if len(self.face_emotion_buffers) <= idx:
                            self.face_emotion_buffers.append(deque(maxlen=5))
                
                except Exception as e:
                    print(f"预测错误：{e}")
                    continue
            
            QTimer.singleShot(200, lambda: setattr(self, 'is_processing', False))
        
        # 绘制框和标签
        if SHOW_BOX or (SHOW_LABEL and self.face_results):
            if SHOW_BOX:
                for idx, (x, y, w, h) in enumerate(faces[:MAX_FACES]):
                    if idx < len(self.face_results):
                        color = EMOTION_COLORS.get(self.face_results[idx].get('emotion', 'neutral'), (0, 255, 0))
                    else:
                        color = EMOTION_COLORS.get('neutral', (0, 255, 0))
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
                    cv2.rectangle(frame, (x+1, y+1), (x+w-1, y+h-1), (255, 255, 255), 1)
            
            if SHOW_LABEL and self.face_results:
                for idx, (x, y, w, h) in enumerate(faces[:MAX_FACES]):
                    if idx < len(self.face_results):
                        result = self.face_results[idx]
                        emotion = result.get('emotion', 'neutral')
                        chinese_text = f"👤{idx+1} {EMOTION_CHINESE.get(emotion, 'neutral')}: {result.get('confidence', 0):.2f}"
                        
                        color = EMOTION_COLORS.get(emotion, (0, 255, 0))
                        
                        frame_pil_full = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        draw = ImageDraw.Draw(frame_pil_full)
                        
                        try:
                            font = ImageFont.truetype("msyhbd.ttc", 24, encoding="utf-8")
                        except:
                            try:
                                font = ImageFont.truetype("simhei.ttf", 24, encoding="utf-8")
                            except:
                                font = ImageFont.load_default()
                        
                        shadow_offset = 2
                        draw.text((x + shadow_offset, y - 30 + shadow_offset), chinese_text, font=font, fill=(0, 0, 0))
                        draw.text((x, y - 30), chinese_text, font=font, fill=(color[2], color[1], color[0]))
                        
                        frame = cv2.cvtColor(np.array(frame_pil_full), cv2.COLOR_RGB2BGR)
        
        # 计算帧率
        self.frame_count += 1
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time
            self.fps_label.setText(f"帧率：{self.current_fps:.1f} FPS")
        
        # 显示帧
        self.display_frame(frame)
        
        # 更新数据显示
        self.update_data_display()
    
    def display_frame(self, frame):
        """显示帧"""
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        label_size = self.video_label.size()
        scaled_pixmap = pixmap.scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.video_label.setPixmap(scaled_pixmap)
    
    def on_prediction_ready(self, emotion, confidence, face_idx):
        """预测完成回调"""
        if face_idx < len(self.face_emotion_buffers):
            self.face_emotion_buffers[face_idx].append(emotion)
            smooth_emotion = max(set(self.face_emotion_buffers[face_idx]), key=list(self.face_emotion_buffers[face_idx]).count)
        else:
            smooth_emotion = emotion
        
        if face_idx < len(self.face_results):
            # 保存原始置信度，不使用平滑情绪时的置信度
            self.face_results[face_idx] = {'emotion': smooth_emotion, 'confidence': confidence}
        else:
            self.face_results.append({'emotion': smooth_emotion, 'confidence': confidence})
        
        self.emotion_stats[smooth_emotion] += 1
    
    def on_thread_finished(self, thread):
        """线程完成回调"""
        if thread in self.face_threads:
            self.face_threads.remove(thread)
        thread.deleteLater()
    
    def update_data_display(self):
        """更新数据显示 - 与实时检测相同的样式"""
        emotion_icons = {
            'angry': '😠', 'disgust': '🤢', 'fear': '😨',
            'happy': '😊', 'neutral': '😐', 'sad': '😢', 'surprise': '😲'
        }
        
        for i, (face_widget, emotion_label, confidence_label, icon_label, number_label) in enumerate(self.face_info_labels):
            if i < len(self.face_results):
                result = self.face_results[i]
                emotion = result.get('emotion', 'neutral')
                confidence = result.get('confidence', 0)
                
                emotion_text = EMOTION_CHINESE.get(emotion, emotion)
                emotion_label.setText(emotion_text)
                confidence_label.setText(f"{confidence*100:.1f}%")
                icon_label.setText(emotion_icons.get(emotion, ''))
                
                color = EMOTION_COLORS.get(emotion, (0, 255, 0))
                emotion_label.setStyleSheet(f"""
                    font-size: 15px;
                    font-weight: bold;
                    color: rgb({color[2]}, {color[1]}, {color[0]});
                """)
                
                number_label.setStyleSheet(f"""
                    QLabel {{
                        background: rgba({color[2]}, {color[1]}, {color[0]}, 0.2);
                        color: rgb({color[2]}, {color[1]}, {color[0]});
                        font-size: 14px;
                        font-weight: bold;
                        border-radius: 15px;
                        min-width: 30px;
                        max-width: 30px;
                        min-height: 30px;
                        max-height: 30px;
                    }}
                """)
                
                face_widget.setStyleSheet(f"""
                    QFrame {{
                        background: linear-gradient(135deg, rgba({color[2]}, {color[1]}, {color[0]}, 0.15), rgba(15, 23, 42, 0.9));
                        border-radius: 12px;
                        border: none;
                    }}
                    QFrame:hover {{
                        background: linear-gradient(135deg, rgba({color[2]}, {color[1]}, {color[0]}, 0.25), rgba(15, 23, 42, 1));
                    }}
                """)
            else:
                emotion_label.setText("未检测")
                confidence_label.setText("--%")
                icon_label.setText("")
                emotion_label.setStyleSheet("""
                    font-size: 15px;
                    font-weight: bold;
                    color: #64748b;
                """)
                number_label.setStyleSheet("""
                    QLabel {
                        background: rgba(100, 116, 139, 0.2);
                        color: #64748b;
                        font-size: 14px;
                        font-weight: bold;
                        border-radius: 15px;
                        min-width: 30px;
                        max-width: 30px;
                        min-height: 30px;
                        max-height: 30px;
                    }
                """)
                face_widget.setStyleSheet("""
                    QFrame {
                        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5), rgba(15, 23, 42, 0.6));
                        border-radius: 12px;
                        border: none;
                    }
                    QFrame:hover {
                        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.7));
                    }
                """)
        
        # 更新图表
        if hasattr(self, 'emotion_curve'):
            y_data = [self.emotion_stats[emotion] for emotion in EMOTION_CLASSES]
            self.emotion_curve.setData(x=list(range(len(EMOTION_CLASSES))), y=y_data)
            max_value = max(y_data) if y_data else 10
            self.emotion_graph.setYRange(0, max_value + 5, padding=0.1)
    

    
    def capture_image(self):
        """拍照功能"""
        try:
            if self.cap and self.cap.isOpened():
                current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                ret, frame = self.cap.read()
                if ret:
                    import os
                    from datetime import datetime
                    
                    # 获取App目录的绝对路径
                    app_dir = os.path.dirname(os.path.dirname(__file__))
                    save_dir = os.path.join(app_dir, 'capture', 'video')
                    os.makedirs(save_dir, exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"video_capture_{timestamp}.jpg"
                    filepath = os.path.join(save_dir, filename)
                    
                    # 应用与显示相同的处理逻辑
                    from App.code.config import ENABLE_DETECTION, SHOW_BOX, SHOW_LABEL
                    
                    if ENABLE_DETECTION and self.face_results:
                        for idx, result in enumerate(self.face_results):
                            emotion = result.get('emotion', 'neutral')
                            color = EMOTION_COLORS.get(emotion, (0, 255, 0))
                            
                            if SHOW_BOX:
                                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                                faces = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml').detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
                                for (x, y, w, h) in faces:
                                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                            
                            if SHOW_LABEL:
                                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                                faces = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml').detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
                                for (x, y, w, h) in faces:
                                    chinese_text = f"{EMOTION_CHINESE.get(emotion, emotion)}: {result.get('confidence', 0):.2f}"
                                    frame_pil_full = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                                    draw = ImageDraw.Draw(frame_pil_full)
                                    
                                    try:
                                        font = ImageFont.truetype("msyhbd.ttc", 20, encoding="utf-8")
                                    except:
                                        font = ImageFont.truetype("simhei.ttf", 20, encoding="utf-8")
                                    
                                    draw.text((x, y - 30), chinese_text, font=font, fill=(color[2], color[1], color[0]))
                                    frame = cv2.cvtColor(np.array(frame_pil_full), cv2.COLOR_RGB2BGR)
                    
                    cv2.imwrite(filepath, frame)
                    print(f"✅ 照片已保存：{filepath}")
                    
                    # 添加数据统计
                    from App.views.statistics import StatisticsPage
                    if ENABLE_DETECTION and self.face_results:
                        for idx, result in enumerate(self.face_results):
                            emotion = result.get('emotion', 'neutral')
                            confidence = result.get('confidence', 0)
                            StatisticsPage.add_detection_data(
                                image_name=filename,
                                emotion=emotion,
                                confidence=confidence,
                                source="视频检测"
                            )
                        print("📊 数据已统计")
                    
                    # 显示保存成功提示
                    from PyQt6.QtWidgets import QMessageBox
                    msg = QMessageBox()
                    msg.setWindowTitle("保存成功")
                    msg.setText("照片已成功保存！")
                    msg.setIcon(QMessageBox.Icon.Information)
                    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                    msg.exec()
                    
                    # 打印保存成功消息
                    print("✅ 照片已保存")
                    
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
        except Exception as e:
            print(f"❌ 拍照失败：{e}")
            import traceback
            traceback.print_exc()
