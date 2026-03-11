"""
摄像头实时检测 - 优化版本
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                             QPushButton, QFrame, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QFont, QImage, QPixmap, QIcon
import cv2
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from collections import deque
import pyqtgraph as pg
import os
# 只导入常量配置，动态配置在运行时获取
from App.code.config import MODEL_PATH, IMAGE_SIZE, EMOTION_CLASSES, EMOTION_COLORS, EMOTION_CHINESE, APP_DIR
from App.code.settings_manager import settings_manager
from App.code.detection_core import DetectionCore, PredictionThread

class CameraDetectionPage(QWidget):
    """摄像头检测页面"""
    
    def __init__(self):
        super().__init__()
        self.cap = None
        self.timer = QTimer()
        self.detection_core = DetectionCore()  # 创建检测核心实例
        self.emotion_buffer = deque(maxlen=5)
        self.current_emotion = "未检测"
        self.current_confidence = 0.0
        self.emotion_stats = {emotion: 0 for emotion in EMOTION_CLASSES}
        self.prediction_thread = None
        self.is_processing = False  # 防止重复处理
        self.last_prediction_time = 0  # 限制预测频率
        # 帧率计算相关变量
        self.frame_count = 0
        self.last_fps_time = 0
        self.current_fps = 0
        # 多个人脸识别相关
        self.face_results = []  # 存储每个人脸的识别结果
        self.face_emotion_buffers = []  # 存储每个人脸的表情缓冲区
        self.face_threads = []  # 存储人脸识别线程
        self.init_ui()
        self.connect_settings_signals()
        self.load_model()
    
    def connect_settings_signals(self):
        """连接设置变更信号"""
        # 连接摄像头设置变更信号
        settings_manager.camera_settings_changed.connect(self.on_camera_settings_changed)
        
        # 连接显示设置变更信号
        settings_manager.display_settings_changed.connect(self.on_display_settings_changed)
        
        # 连接多个人脸设置变更信号
        settings_manager.face_settings_changed.connect(self.on_face_settings_changed)
        
        # 连接所有设置变更信号
        settings_manager.all_settings_changed.connect(self.on_all_settings_changed)
    
    def init_ui(self):
        """初始化 UI"""
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
        
        # 加载模型
        self.load_model()
    
    def on_face_settings_changed(self):
        """处理多个人脸设置变更"""
        # 这里可以添加多个人脸设置变更时的处理逻辑
        pass
    
    def create_data_panel(self):
        """创建数据面板"""
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
        
        # 创建多个人脸信息容器 - 使用垂直布局，每行一个人脸
        self.faces_container = QWidget()
        self.faces_layout = QVBoxLayout()
        self.faces_layout.setContentsMargins(0, 0, 0, 0)
        self.faces_layout.setSpacing(8)
        self.faces_container.setLayout(self.faces_layout)
        layout.addWidget(self.faces_container)
        
        # 初始化人脸信息标签列表 - 使用卡片式布局
        self.face_info_labels = []
        for i in range(5):  # 最多5个人脸
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
            
            # 左侧：人脸编号圆形图标
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
            
            # 右侧：表情图标（初始为空）
            icon_label = QLabel("")
            icon_label.setStyleSheet("""
                font-size: 20px;
                padding: 0 5px;
                min-width: 30px;
            """)
            face_layout.addWidget(icon_label)
            
            face_widget.setLayout(face_layout)
            face_widget.setVisible(True)  # 始终显示，作为占位
            
            # 添加到垂直布局，每行一个人脸
            self.faces_layout.addWidget(face_widget)
            
            self.face_info_labels.append((face_widget, emotion_label, confidence_label, icon_label, number_label))
        
        layout.addSpacing(10)
        
        # 表情统计折线图
        graph_title = QLabel("📈 表情分布")
        graph_title.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #2dd4bf;
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
        
        # 设置图表属性
        self.emotion_graph.setBackground(None)
        # 不设置前景色，直接在后续设置坐标轴颜色
        
        # 设置坐标轴
        self.emotion_graph.setLabel('left', '数量', color='#94a3b8')
        self.emotion_graph.setLabel('bottom', '表情', color='#94a3b8')
        
        # 只显示正的x和y轴，隐藏其他两个轴
        self.emotion_graph.hideAxis('top')
        self.emotion_graph.hideAxis('right')
        
        # 设置网格
        self.emotion_graph.showGrid(x=True, y=True, alpha=0.2)
        
        # 创建曲线
        self.emotion_curve = self.emotion_graph.plot(
            x=list(range(len(EMOTION_CLASSES))),
            y=[0]*len(EMOTION_CLASSES),
            pen=pg.mkPen(color='#2dd4bf', width=2)
        )
        
        # 设置X轴标签
        ticks = []
        for i, emotion in enumerate(EMOTION_CLASSES):
            ticks.append((i, EMOTION_CHINESE.get(emotion, emotion)))
        
        x_axis = self.emotion_graph.getAxis('bottom')
        x_axis.setTicks([ticks])
        
        # 设置坐标轴范围，确保只显示正值
        self.emotion_graph.setXRange(-0.5, len(EMOTION_CLASSES)-0.5, padding=0)
        self.emotion_graph.setYRange(0, 10, padding=0.1)
        
        # 禁用图表交互功能，防止移动
        view_box = self.emotion_graph.getViewBox()
        view_box.setMouseEnabled(x=False, y=False)
        view_box.setMenuEnabled(False)
        
        self.emotion_graph.setMinimumHeight(200)
        layout.addWidget(self.emotion_graph)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_video_panel(self):
        """创建视频面板"""
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
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        title_label = QLabel("🎥 摄像头画面")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2dd4bf;
            padding: 10px 0;
        """)
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
        self.video_label.setText("点击按钮启动摄像头")
        layout.addWidget(self.video_label,9)
        

        
        # 控制按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.start_btn = QPushButton("启动摄像头")
        # 设置图标
        start_icon_path = os.path.join(APP_DIR, 'icons', '启动摄像头.png')
        if os.path.exists(start_icon_path):
            start_icon = QIcon(start_icon_path)
            self.start_btn.setIcon(start_icon)
            self.start_btn.setIconSize(QSize(24, 24))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #2dd4bf;
                color: white;
                font-size: 16px;
                padding: 15px 15px 15px 40px;
                border-radius: 10px;
                font-weight: bold;
                border: none;
                text-align: center;
            }
            QPushButton:hover {
                background: #14b8a6;
            }
            QPushButton:disabled {
                background: #475569;
                color: #94a3b8;
            }
        """)
        self.start_btn.clicked.connect(self.toggle_camera)
        btn_layout.addWidget(self.start_btn)
        
        # 拍照按钮
        self.capture_btn = QPushButton("拍照")
        # 设置图标
        capture_icon_path = os.path.join(APP_DIR, 'icons', '拍照.png')
        if os.path.exists(capture_icon_path):
            capture_icon = QIcon(capture_icon_path)
            self.capture_btn.setIcon(capture_icon)
            self.capture_btn.setIconSize(QSize(24, 24))
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                font-size: 16px;
                padding: 15px 15px 15px 40px;
                border-radius: 10px;
                font-weight: bold;
                border: none;
                text-align: center;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:disabled {
                background: #475569;
                color: #94a3b8;
            }
        """)
        self.capture_btn.clicked.connect(self.capture_image)
        self.capture_btn.setEnabled(False)
        btn_layout.addWidget(self.capture_btn)
        
        layout.addLayout(btn_layout)
        panel.setLayout(layout)
        return panel
    
    def load_model(self):
        """加载模型"""
        self.detection_core.load_model()
    
    def toggle_camera(self):
        """切换摄像头状态"""
        if self.cap is None or not self.cap.isOpened():
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        """启动摄像头"""
        # 显示加载提示
        if hasattr(self, 'status_label'):
            self.status_label.setText("🔄 正在启动摄像头...")
        
        try:
            if not self.detection_core.model:
                error_msg = "❌ 模型未加载"
                print(error_msg)
                if hasattr(self, 'status_label'):
                    self.status_label.setText(error_msg)
                # 显示错误提示
                from PyQt6.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setWindowTitle("错误")
                msg.setText("模型未加载，请检查模型文件是否存在。")
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
                return
            
            # 动态获取最新配置
            from App.code.config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, FRAME_RATE
            print(f"🎥 启动摄像头，索引: {CAMERA_INDEX}")
            
            # 直接使用DirectShow后端，减少尝试时间
            self.cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
            
            if not self.cap.isOpened():
                error_msg = f"❌ 无法打开摄像头 (索引: {CAMERA_INDEX})"
                print(error_msg)
                if hasattr(self, 'status_label'):
                    self.status_label.setText(error_msg)
                # 显示错误提示
                from PyQt6.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setWindowTitle("错误")
                msg.setText(f"无法打开摄像头 (索引: {CAMERA_INDEX})，请检查摄像头是否连接或被其他程序占用。")
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
                return
            
            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, FRAME_RATE)
            
            # 预加载人脸检测模型
            try:
                self.detection_core.load_face_net()
            except Exception as e:
                error_msg = f"❌ 加载人脸检测模型失败: {e}"
                print(error_msg)
                if hasattr(self, 'status_label'):
                    self.status_label.setText(error_msg)
                # 显示错误提示
                from PyQt6.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setWindowTitle("错误")
                msg.setText(f"加载人脸检测模型失败: {e}")
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
                return
            
            # 连接定时器
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(1000 // FRAME_RATE)
            
            # 更新按钮状态
            self.start_btn.setText("停止摄像头")
            # 设置图标
            stop_icon_path = os.path.join(APP_DIR, 'icons', '停止摄像头.png')
            if os.path.exists(stop_icon_path):
                stop_icon = QIcon(stop_icon_path)
                self.start_btn.setIcon(stop_icon)
                self.start_btn.setIconSize(QSize(24, 24))
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: #ef4444;
                    color: white;
                    font-size: 16px;
                    padding: 15px 15px 15px 40px;
                    border-radius: 10px;
                    font-weight: bold;
                    border: none;
                    text-align: center;
                }
                QPushButton:hover {
                    background: #dc2626;
                }
            """)
            
            # 启用拍照按钮
            self.capture_btn.setEnabled(True)
            
            success_msg = "✅ 摄像头已启动"
            print(success_msg)
            if hasattr(self, 'status_label'):
                self.status_label.setText(success_msg)
            
        except Exception as e:
            error_msg = f"❌ 启动失败：{e}"
            print(error_msg)
            if hasattr(self, 'status_label'):
                self.status_label.setText(error_msg)
            import traceback
            traceback.print_exc()
            # 显示错误提示
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("错误")
            msg.setText(f"启动摄像头失败：{e}")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
    
    def update_frame(self):
        """更新视频帧 - 高性能版本"""
        if not self.cap or not self.cap.isOpened():
            return
        
        # 读取帧
        ret, frame = self.cap.read()
        if not ret:
            return
        
        # 水平翻转
        frame = cv2.flip(frame, 1)
        
        # 动态获取最新设置
        from App.code.config import ENABLE_DETECTION, SHOW_BOX, SHOW_LABEL, MAX_FACES
        
        # 快速人脸检测
        faces = []
        if ENABLE_DETECTION:
            faces = self.detection_core.detect_faces(frame)
        
        # 限制检测频率，每300ms检测一次
        import time
        current_time = time.time()
        
        # 只有在没有正在处理的线程时才进行检测
        should_detect = not self.is_processing and (current_time - self.last_prediction_time >= 0.3)
        
        # 处理检测到的人脸
        if should_detect and faces:
            self.is_processing = True
            self.last_prediction_time = current_time
            
            # 根据检测到的人脸数量初始化结果列表
            num_faces = min(len(faces), MAX_FACES)
            if len(self.face_results) != num_faces:
                self.face_results = [{'emotion': 'neutral', 'confidence': 0.0, 'intensity': '中等'} for _ in range(num_faces)]
            
            # 清理旧线程
            self.face_threads = [t for t in self.face_threads if t.isRunning()]
            
            # 收集所有人脸图片
            face_images = []
            face_indices = []
            
            for idx, (x, y, w_box, h_box) in enumerate(faces[:MAX_FACES]):
                try:
                    # 快速预处理
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    face_roi = gray[y:y+h_box, x:x+w_box]
                    # 使用更快的 resize 方法
                    face_resized = cv2.resize(face_roi, (96, 96), interpolation=cv2.INTER_LINEAR)
                    face_pil = Image.fromarray(face_resized)
                    
                    face_images.append(face_pil)
                    face_indices.append(idx)
                    
                    # 为每个人脸创建独立的缓冲区
                    if len(self.face_emotion_buffers) <= idx:
                        self.face_emotion_buffers.append(deque(maxlen=3))  # 减少缓冲区大小
                    
                except Exception as e:
                    print(f"预测错误：{e}")
                    continue
            
            # 使用批处理预测
            if face_images:
                results = self.detection_core.batch_predict_emotion(face_images)
                
                # 处理预测结果
                for i, (emotion, confidence, intensity) in enumerate(results):
                    if i < len(face_indices):
                        face_idx = face_indices[i]
                        self.on_prediction_ready(emotion, confidence, intensity, face_idx)
            
            # 所有处理完成后，设置一个定时器来重置is_processing
            QTimer.singleShot(300, lambda: setattr(self, 'is_processing', False))
        
        # 显示处理（无论是否检测都显示）
        # 优化：只在需要时才绘制框和标签
        if SHOW_BOX or (SHOW_LABEL and self.face_results):
            if SHOW_BOX:
                frame = self.detection_core.draw_four_corners(frame, faces[:MAX_FACES], self.face_results)
            
            if SHOW_LABEL and self.face_results:
                frame = self.detection_core.draw_labels(frame, faces[:MAX_FACES], self.face_results)
        
        # 快速转换为QImage
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # 优化画面显示质量，使用平滑缩放
        pixmap = QPixmap.fromImage(qt_image)
        label_size = self.video_label.size()
        scaled_pixmap = pixmap.scaled(
            label_size, 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation  # 使用平滑缩放
        )
        
        self.video_label.setPixmap(scaled_pixmap)
        
        # 计算帧率
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time
            self.fps_label.setText(f"帧率：{self.current_fps:.1f} FPS")
        
        # 释放不再使用的资源
        del frame
        del rgb_image
        del qt_image
        del pixmap
        del scaled_pixmap
    
    def on_thread_finished(self, thread):
        """线程完成回调 - 清理已完成的线程"""
        if thread in self.face_threads:
            self.face_threads.remove(thread)
        thread.deleteLater()
    
    def on_prediction_ready(self, emotion, confidence, intensity, face_idx):
        """预测完成回调 - 支持多个人脸"""
        # 更新对应人脸的表情缓冲区
        if face_idx < len(self.face_emotion_buffers):
            self.face_emotion_buffers[face_idx].append(emotion)
            # 使用缓冲区进行平滑处理
            smooth_emotion = max(set(self.face_emotion_buffers[face_idx]), key=list(self.face_emotion_buffers[face_idx]).count)
        else:
            smooth_emotion = emotion
        
        # 更新对应人脸的识别结果
        if face_idx < len(self.face_results):
            self.face_results[face_idx] = {'emotion': smooth_emotion, 'confidence': confidence, 'intensity': intensity}
        else:
            # 如果结果列表不够长，添加新的结果
            self.face_results.append({'emotion': smooth_emotion, 'confidence': confidence, 'intensity': intensity})
        
        # 更新当前表情和置信度（用于拍照时的数据统计）
        if face_idx == 0:  # 只更新第一个人脸的信息
            self.current_emotion = smooth_emotion
            self.current_confidence = confidence
            self.current_intensity = intensity
        
        # 更新表情统计
        self.emotion_stats[smooth_emotion] += 1
        
        # 更新数据显示
        self.update_data_display()
        self.update_emotion_graph()
    
    def update_emotion_graph(self):
        """更新表情统计图表"""
        if hasattr(self, 'emotion_curve'):
            # 获取各表情的数量
            y_data = [self.emotion_stats[emotion] for emotion in EMOTION_CLASSES]
            
            # 更新曲线数据
            self.emotion_curve.setData(
                x=list(range(len(EMOTION_CLASSES))),
                y=y_data
            )
            
            # 自动调整Y轴范围，确保只显示正值
            max_value = max(y_data) if y_data else 10
            self.emotion_graph.setYRange(0, max_value + 5, padding=0.1)
            # 保持X轴范围
            self.emotion_graph.setXRange(-0.5, len(EMOTION_CLASSES)-0.5, padding=0)
    
    def update_data_display(self):
        """更新数据显示 - 支持多个人脸"""
        # 表情图标映射
        emotion_icons = {
            'angry': '😠',
            'disgust': '🤢',
            'fear': '😨',
            'happy': '😊',
            'neutral': '😐',
            'sad': '😢',
            'surprise': '😲'
        }
        
        # 表情强度图标映射
        intensity_icons = {
            '强烈': '🔥',
            '明显': '💡',
            '中等': '⚡',
            '轻微': '💨'
        }
        
        # 更新每个人脸的信息
        for i, (face_widget, emotion_label, confidence_label, icon_label, number_label) in enumerate(self.face_info_labels):
            if i < len(self.face_results):
                # 显示检测到的人脸
                result = self.face_results[i]
                emotion = result.get('emotion', 'neutral')
                confidence = result.get('confidence', 0)
                intensity = result.get('intensity', '中等')
                
                emotion_text = EMOTION_CHINESE.get(emotion, emotion)
                emotion_label.setText(f"{emotion_text} {intensity_icons.get(intensity, '')}")
                confidence_label.setText(f"{confidence*100:.1f}%")
                icon_label.setText(emotion_icons.get(emotion, '😐'))
                
                # 根据表情设置颜色
                color = EMOTION_COLORS.get(emotion, (0, 255, 0))
                emotion_label.setStyleSheet(f"""
                    font-size: 15px;
                    font-weight: bold;
                    color: rgb({color[2]}, {color[1]}, {color[0]});
                """)
                
                # 更新编号颜色
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
                
                # 启用样式
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
                # 未检测到人脸，显示占位状态
                emotion_label.setText("未检测")
                confidence_label.setText("--%")
                icon_label.setText("")  # 不显示表情图标
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
                # 恢复默认样式
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
    

    
    def capture_image(self):
        """拍照功能"""
        try:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    # 翻转图像，保持与显示一致
                    frame = cv2.flip(frame, 1)
                    
                    # 动态获取最新设置
                    from App.code.config import ENABLE_DETECTION, SHOW_BOX, SHOW_LABEL, MAX_FACES
                    
                    # 使用与实时检测相同的人脸检测方法
                    faces = self.detection_core.detect_faces(frame)
                    
                    # 应用与显示相同的处理逻辑
                    if SHOW_BOX or (SHOW_LABEL and self.face_results):
                        if SHOW_BOX:
                            frame = self.detection_core.draw_four_corners(frame, faces[:MAX_FACES], self.face_results)
                        
                        if SHOW_LABEL and self.face_results:
                            frame = self.detection_core.draw_labels(frame, faces[:MAX_FACES], self.face_results)
                    
                    # 确保保存目录存在
                    import os
                    # 获取App目录的绝对路径
                    app_dir = os.path.dirname(os.path.dirname(__file__))
                    capture_dir = os.path.join(app_dir, 'capture', 'camera')
                    os.makedirs(capture_dir, exist_ok=True)
                    
                    # 生成唯一的文件名
                    import time
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"camera_{timestamp}.jpg"
                    filepath = os.path.join(capture_dir, filename)
                    
                    # 保存图像
                    cv2.imwrite(filepath, frame)
                    print(f"📷 拍照成功：{filepath}")
                    
                    # 添加数据统计
                    from App.views.statistics import StatisticsPage
                    StatisticsPage.add_detection_data(
                        image_name=filename,
                        emotion=self.current_emotion,
                        confidence=self.current_confidence,
                        source="摄像头检测"
                    )
                    print("📊 数据已统计")
                    
                    # 显示保存成功提示
                    from PyQt6.QtWidgets import QMessageBox
                    msg = QMessageBox()
                    msg.setWindowTitle("保存成功")
                    msg.setText(f"照片已成功保存！\n\n保存目录：{capture_dir}\n图片名：{filename}")
                    msg.setIcon(QMessageBox.Icon.Information)
                    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                    msg.exec()
                    
                    # 打印保存成功消息
                    print("✅ 照片已保存")
                else:
                    print("❌ 拍照失败：无法获取帧")
            else:
                print("❌ 拍照失败：摄像头未启动")
        except Exception as e:
            print(f"❌ 拍照错误：{e}")
    
    def stop_camera(self):
        """停止摄像头"""
        # 显示加载提示
        if hasattr(self, 'status_label'):
            self.status_label.setText("🔄 正在停止摄像头...")
        
        try:
            if self.timer.isActive():
                self.timer.stop()
            
            if self.cap and self.cap.isOpened():
                self.cap.release()
            
            # 释放Caffe模型资源
            if hasattr(self, 'face_net') and self.face_net is not None:
                self.face_net = None
            
            if self.prediction_thread and self.prediction_thread.isRunning():
                self.prediction_thread.quit()
                self.prediction_thread.wait()
            
            # 清理所有人脸识别线程
            for thread in self.face_threads:
                if thread.isRunning():
                    thread.quit()
                    thread.wait()
                thread.deleteLater()
            self.face_threads.clear()
            
            self.video_label.clear()
            self.video_label.setText("点击按钮启动摄像头")
            
            # 重置按钮
            self.start_btn.setText("启动摄像头")
            # 设置图标
            start_icon_path = os.path.join(APP_DIR, 'icons', '启动摄像头.png')
            if os.path.exists(start_icon_path):
                start_icon = QIcon(start_icon_path)
                self.start_btn.setIcon(start_icon)
                self.start_btn.setIconSize(QSize(24, 24))
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: #2dd4bf;
                    color: white;
                    font-size: 16px;
                    padding: 15px 15px 15px 40px;
                    border-radius: 10px;
                    font-weight: bold;
                    border: none;
                    text-align: center;
                }
                QPushButton:hover {
                    background: #14b8a6;
                }
            """)
            
            # 禁用拍照按钮
            self.capture_btn.setEnabled(False)
            
            # 重置数据
            self.current_emotion = "未检测"
            self.current_confidence = 0.0
            self.current_intensity = "中等"
            self.emotion_stats = {emotion: 0 for emotion in EMOTION_CLASSES}
            self.emotion_buffer.clear()
            
            # 重置多个人脸识别结果
            self.face_results = []
            self.face_emotion_buffers = []
            
            # 重置帧率
            self.frame_count = 0
            self.current_fps = 0
            self.last_fps_time = 0
            
            # 重置显示
            self.fps_label.setText("帧率：-- FPS")
            
            # 重置多个人脸信息显示为占位状态
            for face_widget, emotion_label, confidence_label, icon_label, number_label in self.face_info_labels:
                emotion_label.setText("未检测")
                confidence_label.setText("--%")
                icon_label.setText("")  # 清空表情图标
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
                # 恢复默认占位样式
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
            
            # 重置图表
            if hasattr(self, 'emotion_curve'):
                self.emotion_curve.setData(
                    x=list(range(len(EMOTION_CLASSES))),
                    y=[0]*len(EMOTION_CLASSES)
                )
                self.emotion_graph.setYRange(0, 10, padding=0.1)
            
            success_msg = "👋 摄像头已停止"
            print(success_msg)
            if hasattr(self, 'status_label'):
                self.status_label.setText(success_msg)
                
        except Exception as e:
            error_msg = f"❌ 停止失败：{e}"
            print(error_msg)
            if hasattr(self, 'status_label'):
                self.status_label.setText(error_msg)
            import traceback
            traceback.print_exc()
    
    def on_camera_settings_changed(self):
        """摄像头设置变更处理"""
        print("🔄 摄像头设置已变更，重新配置摄像头...")
        
        # 检查摄像头是否在运行
        was_running = self.cap and self.cap.isOpened()
        
        # 完全停止摄像头
        if was_running:
            self.stop_camera()
        
        # 给一点时间完全释放资源
        import time
        time.sleep(0.3)
        
        # 如果之前在运行，重新启动
        if was_running:
            print("🔄 重新启动摄像头...")
            self.start_camera()
    
    def on_display_settings_changed(self):
        """显示设置变更处理"""
        print("🔄 显示设置已变更，实时更新显示...")
        # 显示设置变更不需要重启摄像头，会在下一帧自动应用
    
    def on_all_settings_changed(self):
        """所有设置变更处理"""
        print("🔄 所有设置已变更，重新加载配置...")
        # 可以在这里处理需要全局重新加载的设置
    
    def closeEvent(self, event):
        """关闭窗口时清理资源"""
        self.stop_camera()
        
        # 断开设置信号连接
        try:
            settings_manager.camera_settings_changed.disconnect(self.on_camera_settings_changed)
            settings_manager.display_settings_changed.disconnect(self.on_display_settings_changed)
            settings_manager.all_settings_changed.disconnect(self.on_all_settings_changed)
        except:
            pass
        
        event.accept()
