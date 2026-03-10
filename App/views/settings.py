"""
设置页面 - 简洁版
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QSpinBox, QCheckBox, QGroupBox,
                             QTabWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from App.code.config import (CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, 
                             FRAME_RATE, SHOW_BOX, SHOW_LABEL, ENABLE_DETECTION,
                             APP_WIDTH, APP_HEIGHT, IMAGE_SIZE, MODEL_PATH,
                             EMOTION_CLASSES, EMOTION_CHINESE, EMOTION_COLORS,
                             APP_NAME, APP_VERSION, USE_CUDA)
from App.code.settings_manager import settings_manager

class SettingsPage(QWidget):
    """设置页面 - 简洁版"""
    
    def __init__(self):
        super().__init__()
        self.current_settings = {}
        self.init_ui()
        self.load_current_settings()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        

        
        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Microsoft YaHei", 12))
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #334155;
                border-radius: 10px;
                background: #1e293b;
            }
            QTabBar::tab {
                background: #334155;
                color: #94a3b8;
                padding: 12px 24px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #2dd4bf;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: #475569;
                color: #e2e8f0;
            }
        """)
        
        # 创建各个标签页
        self.create_camera_tab()
        self.create_display_tab()
        self.create_model_tab()
        self.create_interface_tab()
        self.create_system_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # 保存按钮
        save_btn = QPushButton("💾 保存所有设置")
        save_btn.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        save_btn.setStyleSheet("""
            QPushButton {
                background: #2dd4bf;
                color: white;
                padding: 15px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background: #14b8a6;
            }
        """)
        save_btn.clicked.connect(self.save_all_settings)
        main_layout.addWidget(save_btn)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Microsoft YaHei", 12))
        self.status_label.setStyleSheet("""
            color: #2dd4bf;
            padding: 10px;
        """)
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)
    
    def create_camera_tab(self):
        """创建摄像头设置标签页"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 摄像头设置组
        camera_group = QGroupBox("摄像头参数")
        camera_group.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        camera_group.setStyleSheet("""
            QGroupBox {
                color: #2dd4bf;
                border: 2px solid #334155;
                border-radius: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        camera_layout = QVBoxLayout()
        camera_layout.setContentsMargins(20, 30, 20, 20)
        camera_layout.setSpacing(20)
        
        # 摄像头索引
        camera_index_layout = QHBoxLayout()
        camera_index_label = QLabel("摄像头索引:")
        camera_index_label.setFont(QFont("Microsoft YaHei", 12))
        camera_index_label.setStyleSheet("color: #94a3b8; min-width: 120px;")
        self.camera_index_spin = QSpinBox()
        self.camera_index_spin.setRange(0, 5)
        self.camera_index_spin.setValue(CAMERA_INDEX)
        self.camera_index_spin.setStyleSheet("""
            QSpinBox {
                color: #e2e8f0;
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        camera_index_layout.addWidget(camera_index_label)
        camera_index_layout.addWidget(self.camera_index_spin)
        camera_layout.addLayout(camera_index_layout)
        
        # 摄像头宽度
        camera_width_layout = QHBoxLayout()
        camera_width_label = QLabel("摄像头宽度:")
        camera_width_label.setFont(QFont("Microsoft YaHei", 12))
        camera_width_label.setStyleSheet("color: #94a3b8; min-width: 120px;")
        self.camera_width_spin = QSpinBox()
        self.camera_width_spin.setRange(640, 1920)
        self.camera_width_spin.setValue(CAMERA_WIDTH)
        self.camera_width_spin.setSingleStep(160)
        self.camera_width_spin.setStyleSheet("""
            QSpinBox {
                color: #e2e8f0;
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        camera_width_layout.addWidget(camera_width_label)
        camera_width_layout.addWidget(self.camera_width_spin)
        camera_layout.addLayout(camera_width_layout)
        
        # 摄像头高度
        camera_height_layout = QHBoxLayout()
        camera_height_label = QLabel("摄像头高度:")
        camera_height_label.setFont(QFont("Microsoft YaHei", 12))
        camera_height_label.setStyleSheet("color: #94a3b8; min-width: 120px;")
        self.camera_height_spin = QSpinBox()
        self.camera_height_spin.setRange(480, 1080)
        self.camera_height_spin.setValue(CAMERA_HEIGHT)
        self.camera_height_spin.setSingleStep(120)
        self.camera_height_spin.setStyleSheet("""
            QSpinBox {
                color: #e2e8f0;
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        camera_height_layout.addWidget(camera_height_label)
        camera_height_layout.addWidget(self.camera_height_spin)
        camera_layout.addLayout(camera_height_layout)
        
        # 帧率
        frame_rate_layout = QHBoxLayout()
        frame_rate_label = QLabel("帧率:")
        frame_rate_label.setFont(QFont("Microsoft YaHei", 12))
        frame_rate_label.setStyleSheet("color: #94a3b8; min-width: 120px;")
        self.frame_rate_spin = QSpinBox()
        self.frame_rate_spin.setRange(1, 60)
        self.frame_rate_spin.setValue(FRAME_RATE)
        self.frame_rate_spin.setStyleSheet("""
            QSpinBox {
                color: #e2e8f0;
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        frame_rate_layout.addWidget(frame_rate_label)
        frame_rate_layout.addWidget(self.frame_rate_spin)
        camera_layout.addLayout(frame_rate_layout)
        
        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)
        layout.addStretch()
        page.setLayout(layout)
        self.tab_widget.addTab(page, "🎥 摄像头")
    
    def create_display_tab(self):
        """创建显示设置标签页"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 显示设置组
        display_group = QGroupBox("显示参数")
        display_group.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        display_group.setStyleSheet("""
            QGroupBox {
                color: #2dd4bf;
                border: 2px solid #334155;
                border-radius: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        display_layout = QVBoxLayout()
        display_layout.setContentsMargins(20, 30, 20, 20)
        display_layout.setSpacing(20)
        
        # 显示框
        self.show_box_check = QCheckBox("显示人脸框")
        self.show_box_check.setChecked(SHOW_BOX)
        self.show_box_check.setFont(QFont("Microsoft YaHei", 12))
        self.show_box_check.setStyleSheet("""
            QCheckBox {
                color: #94a3b8;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #334155;
                border-radius: 4px;
                background: #0f172a;
            }
            QCheckBox::indicator:checked {
                background: #2dd4bf;
                border-color: #2dd4bf;
            }
        """)
        display_layout.addWidget(self.show_box_check)
        
        # 显示标签
        self.show_label_check = QCheckBox("显示标签")
        self.show_label_check.setChecked(SHOW_LABEL)
        self.show_label_check.setFont(QFont("Microsoft YaHei", 12))
        self.show_label_check.setStyleSheet("""
            QCheckBox {
                color: #94a3b8;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #334155;
                border-radius: 4px;
                background: #0f172a;
            }
            QCheckBox::indicator:checked {
                background: #2dd4bf;
                border-color: #2dd4bf;
            }
        """)
        display_layout.addWidget(self.show_label_check)
        
        # 启用检测
        self.enable_detection_check = QCheckBox("启用检测")
        self.enable_detection_check.setChecked(ENABLE_DETECTION)
        self.enable_detection_check.setFont(QFont("Microsoft YaHei", 12))
        self.enable_detection_check.setStyleSheet("""
            QCheckBox {
                color: #94a3b8;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #334155;
                border-radius: 4px;
                background: #0f172a;
            }
            QCheckBox::indicator:checked {
                background: #2dd4bf;
                border-color: #2dd4bf;
            }
        """)
        display_layout.addWidget(self.enable_detection_check)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        layout.addStretch()
        page.setLayout(layout)
        self.tab_widget.addTab(page, "👁️ 显示")
    
    def create_model_tab(self):
        """创建模型设置标签页"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 模型设置组
        model_group = QGroupBox("模型参数")
        model_group.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        model_group.setStyleSheet("""
            QGroupBox {
                color: #2dd4bf;
                border: 2px solid #334155;
                border-radius: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        model_layout = QVBoxLayout()
        model_layout.setContentsMargins(20, 30, 20, 20)
        model_layout.setSpacing(20)
        
        # 模型路径
        model_path_layout = QVBoxLayout()
        model_path_label = QLabel("模型路径:")
        model_path_label.setFont(QFont("Microsoft YaHei", 12))
        model_path_label.setStyleSheet("color: #94a3b8;")
        self.model_path_label = QLabel(MODEL_PATH)
        self.model_path_label.setFont(QFont("Microsoft YaHei", 10))
        self.model_path_label.setStyleSheet("""
            color: #64748b;
            background: #0f172a;
            padding: 12px;
            border-radius: 8px;
        """)
        self.model_path_label.setWordWrap(True)
        model_path_layout.addWidget(model_path_label)
        model_path_layout.addWidget(self.model_path_label)
        model_layout.addLayout(model_path_layout)
        
        # 图像尺寸
        image_size_layout = QHBoxLayout()
        image_size_label = QLabel("图像尺寸:")
        image_size_label.setFont(QFont("Microsoft YaHei", 12))
        image_size_label.setStyleSheet("color: #94a3b8; min-width: 120px;")
        self.image_size_label = QLabel(f"{IMAGE_SIZE} x {IMAGE_SIZE}")
        self.image_size_label.setFont(QFont("Microsoft YaHei", 12))
        self.image_size_label.setStyleSheet("color: #e2e8f0;")
        image_size_layout.addWidget(image_size_label)
        image_size_layout.addWidget(self.image_size_label)
        model_layout.addLayout(image_size_layout)
        
        # 表情类别
        emotion_classes_layout = QVBoxLayout()
        emotion_classes_label = QLabel("表情类别:")
        emotion_classes_label.setFont(QFont("Microsoft YaHei", 12))
        emotion_classes_label.setStyleSheet("color: #94a3b8;")
        emotion_classes_text = ", ".join([EMOTION_CHINESE.get(e, e) for e in EMOTION_CLASSES])
        self.emotion_classes_label = QLabel(emotion_classes_text)
        self.emotion_classes_label.setFont(QFont("Microsoft YaHei", 10))
        self.emotion_classes_label.setStyleSheet("""
            color: #64748b;
            background: #0f172a;
            padding: 12px;
            border-radius: 8px;
        """)
        self.emotion_classes_label.setWordWrap(True)
        emotion_classes_layout.addWidget(emotion_classes_label)
        emotion_classes_layout.addWidget(self.emotion_classes_label)
        model_layout.addLayout(emotion_classes_layout)
        
        # 使用CUDA
        use_cuda_layout = QHBoxLayout()
        use_cuda_label = QLabel("使用CUDA:")
        use_cuda_label.setFont(QFont("Microsoft YaHei", 12))
        use_cuda_label.setStyleSheet("color: #94a3b8; min-width: 120px;")
        self.use_cuda_check = QCheckBox()
        self.use_cuda_check.setChecked(USE_CUDA)
        self.use_cuda_check.setStyleSheet("""
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #334155;
                border-radius: 4px;
                background: #0f172a;
            }
            QCheckBox::indicator:checked {
                background: #2dd4bf;
                border-color: #2dd4bf;
            }
        """)
        use_cuda_layout.addWidget(use_cuda_label)
        use_cuda_layout.addWidget(self.use_cuda_check)
        model_layout.addLayout(use_cuda_layout)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        layout.addStretch()
        page.setLayout(layout)
        self.tab_widget.addTab(page, "🤖 模型")
    
    def create_interface_tab(self):
        """创建界面设置标签页"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 界面设置组
        interface_group = QGroupBox("界面参数")
        interface_group.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        interface_group.setStyleSheet("""
            QGroupBox {
                color: #2dd4bf;
                border: 2px solid #334155;
                border-radius: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        interface_layout = QVBoxLayout()
        interface_layout.setContentsMargins(20, 30, 20, 20)
        interface_layout.setSpacing(20)
        
        # 窗口宽度
        app_width_layout = QHBoxLayout()
        app_width_label = QLabel("窗口宽度:")
        app_width_label.setFont(QFont("Microsoft YaHei", 12))
        app_width_label.setStyleSheet("color: #94a3b8; min-width: 120px;")
        self.app_width_spin = QSpinBox()
        self.app_width_spin.setRange(800, 1920)
        self.app_width_spin.setValue(APP_WIDTH)
        self.app_width_spin.setSingleStep(100)
        self.app_width_spin.setStyleSheet("""
            QSpinBox {
                color: #e2e8f0;
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        app_width_layout.addWidget(app_width_label)
        app_width_layout.addWidget(self.app_width_spin)
        interface_layout.addLayout(app_width_layout)
        
        # 窗口高度
        app_height_layout = QHBoxLayout()
        app_height_label = QLabel("窗口高度:")
        app_height_label.setFont(QFont("Microsoft YaHei", 12))
        app_height_label.setStyleSheet("color: #94a3b8; min-width: 120px;")
        self.app_height_spin = QSpinBox()
        self.app_height_spin.setRange(600, 1080)
        self.app_height_spin.setValue(APP_HEIGHT)
        self.app_height_spin.setSingleStep(100)
        self.app_height_spin.setStyleSheet("""
            QSpinBox {
                color: #e2e8f0;
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        app_height_layout.addWidget(app_height_label)
        app_height_layout.addWidget(self.app_height_spin)
        interface_layout.addLayout(app_height_layout)
        
        interface_group.setLayout(interface_layout)
        layout.addWidget(interface_group)
        layout.addStretch()
        page.setLayout(layout)
        self.tab_widget.addTab(page, "🎨 界面")
    
    def create_system_tab(self):
        """创建系统设置标签页"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 系统信息组
        system_group = QGroupBox("系统信息")
        system_group.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        system_group.setStyleSheet("""
            QGroupBox {
                color: #2dd4bf;
                border: 2px solid #334155;
                border-radius: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        system_layout = QVBoxLayout()
        system_layout.setContentsMargins(20, 30, 20, 20)
        system_layout.setSpacing(20)
        
        # 应用名称
        app_name_layout = QHBoxLayout()
        app_name_label = QLabel("应用名称:")
        app_name_label.setFont(QFont("Microsoft YaHei", 12))
        app_name_label.setStyleSheet("color: #94a3b8; min-width: 120px;")
        self.app_name_label = QLabel(APP_NAME)
        self.app_name_label.setFont(QFont("Microsoft YaHei", 12))
        self.app_name_label.setStyleSheet("color: #e2e8f0;")
        app_name_layout.addWidget(app_name_label)
        app_name_layout.addWidget(self.app_name_label)
        system_layout.addLayout(app_name_layout)
        
        # 应用版本
        app_version_layout = QHBoxLayout()
        app_version_label = QLabel("应用版本:")
        app_version_label.setFont(QFont("Microsoft YaHei", 12))
        app_version_label.setStyleSheet("color: #94a3b8; min-width: 120px;")
        self.app_version_label = QLabel(APP_VERSION)
        self.app_version_label.setFont(QFont("Microsoft YaHei", 12))
        self.app_version_label.setStyleSheet("color: #e2e8f0;")
        app_version_layout.addWidget(app_version_label)
        app_version_layout.addWidget(self.app_version_label)
        system_layout.addLayout(app_version_layout)
        
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)
        layout.addStretch()
        page.setLayout(layout)
        self.tab_widget.addTab(page, "💾 系统")
    
    def load_current_settings(self):
        """加载当前设置"""
        self.current_settings = {
            'camera_index': CAMERA_INDEX,
            'camera_width': CAMERA_WIDTH,
            'camera_height': CAMERA_HEIGHT,
            'frame_rate': FRAME_RATE,
            'show_box': SHOW_BOX,
            'show_label': SHOW_LABEL,
            'enable_detection': ENABLE_DETECTION,
            'app_width': APP_WIDTH,
            'app_height': APP_HEIGHT,
            'use_cuda': USE_CUDA
        }
    
    def save_all_settings(self):
        """保存所有设置"""
        try:
            # 保存到配置文件
            import App.code.config as config
            
            # 记录旧值用于比较
            old_camera_index = config.CAMERA_INDEX
            old_camera_width = config.CAMERA_WIDTH
            old_camera_height = config.CAMERA_HEIGHT
            old_frame_rate = config.FRAME_RATE
            old_show_box = config.SHOW_BOX
            old_show_label = config.SHOW_LABEL
            old_enable_detection = config.ENABLE_DETECTION
            old_app_width = config.APP_WIDTH
            old_app_height = config.APP_HEIGHT
            old_use_cuda = config.USE_CUDA
            
            # 更新新值
            config.CAMERA_INDEX = self.camera_index_spin.value()
            config.CAMERA_WIDTH = self.camera_width_spin.value()
            config.CAMERA_HEIGHT = self.camera_height_spin.value()
            config.FRAME_RATE = self.frame_rate_spin.value()
            config.SHOW_BOX = self.show_box_check.isChecked()
            config.SHOW_LABEL = self.show_label_check.isChecked()
            config.ENABLE_DETECTION = self.enable_detection_check.isChecked()
            config.APP_WIDTH = self.app_width_spin.value()
            config.APP_HEIGHT = self.app_height_spin.value()
            config.USE_CUDA = self.use_cuda_check.isChecked()
            
            # 持久化保存到JSON文件
            config.save_config()
            
            # 更新当前设置
            self.load_current_settings()
            
            # 通知设置变更
            self.notify_settings_changed(
                old_camera_index, old_camera_width, old_camera_height, old_frame_rate,
                old_show_box, old_show_label, old_enable_detection,
                old_app_width, old_app_height, old_use_cuda
            )
            
            # 显示成功提示（非弹窗）
            self.status_label.setText("✅ 设置已保存")
            QTimer.singleShot(2000, lambda: self.status_label.setText(""))
            
            print("✅ 所有设置已保存")
        except Exception as e:
            print(f"❌ 保存设置失败: {e}")
    
    def notify_settings_changed(self, old_camera_index, old_camera_width, old_camera_height, old_frame_rate,
                               old_show_box, old_show_label, old_enable_detection,
                               old_app_width, old_app_height, old_use_cuda):
        """通知设置变更"""
        import App.code.config as config
        
        # 检查摄像头设置是否变更
        if (old_camera_index != config.CAMERA_INDEX or 
            old_camera_width != config.CAMERA_WIDTH or 
            old_camera_height != config.CAMERA_HEIGHT or 
            old_frame_rate != config.FRAME_RATE):
            settings_manager.notify_camera_settings_changed()
        
        # 检查显示设置是否变更
        if (old_show_box != config.SHOW_BOX or 
            old_show_label != config.SHOW_LABEL or 
            old_enable_detection != config.ENABLE_DETECTION):
            settings_manager.notify_display_settings_changed()
        
        # 检查界面设置是否变更
        if (old_app_width != config.APP_WIDTH or 
            old_app_height != config.APP_HEIGHT):
            settings_manager.notify_interface_settings_changed()
        
        # 总是发送全局变更通知
        settings_manager.notify_all_settings_changed()
