"""
主界面 - 面部表情检测系统
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QStackedWidget, QPushButton, QLabel, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QKeyEvent, QIcon, QPixmap
import os
from App.code.config import APP_NAME, APP_VERSION, ICON_PATH

class HomeWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.is_fullscreen = False  # 全屏状态标记
        self.init_ui()
        
        # 设置窗口图标
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
    
    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setGeometry(50, 50, 1400, 600)
        self.setStyleSheet("background: #0f172a;")
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左侧导航栏
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 右侧内容区
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 4)
        
        central_widget.setLayout(main_layout)
    
    def create_left_panel(self):
        """创建左侧导航栏"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: #1e293b;
                color: #e2e8f0;
            }
        """)
        panel.setMinimumWidth(220)
        panel.setMaximumWidth(300)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 应用标题（带logo）
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.setSpacing(10)
        title_layout.setContentsMargins(0, 10, 0, 0)
        
        # Logo
        logo_label = QLabel()
        if os.path.exists(ICON_PATH):
            pixmap = QPixmap(ICON_PATH)
            # 调整logo大小
            pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        
        # 标题文本
        title_label = QLabel("一零九表情智能检测系统")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            color: #2dd4bf;
            font-weight: bold;
        """)
        
        title_layout.addWidget(logo_label)
        title_layout.addWidget(title_label)
        
        # 添加到主布局
        layout.addLayout(title_layout)
        layout.addSpacing(20)
        

        
        # 导航按钮
        nav_buttons = [
            ("📹 摄像头检测", "camera"),
            ("🖼️ 图片检测", "image"),
            ("📦 批量图片检测", "batch_image"),
            ("🎬 视频检测", "video"),
            ("📊 数据统计", "statistics"),
        ]
        
        # 如果是管理员，添加用户管理选项
        if self.user_data.get('is_admin', False):
            nav_buttons.append(("👥 用户管理", "user_management"))
        
        nav_buttons.append(("⚙️ 系统设置", "settings"))
        
        self.nav_button_map = {}  # 保存按钮引用
        
        for text, page in nav_buttons:
            btn = QPushButton(text)
            btn.setFont(QFont("Microsoft YaHei", 11))
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #94a3b8;
                    text-align: left;
                    padding: 10px 10px;
                    border-radius: 10px;
                    border: none;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(45, 212, 191, 0.1);
                    color: #2dd4bf;
                }
                QPushButton:checked {
                    background: rgba(45, 212, 191, 0.15);
                    color: #2dd4bf;
                    font-weight: bold;
                }
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, p=page: self.switch_page(p))
            layout.addWidget(btn)
            self.nav_button_map[page] = btn
        
        # 设置默认选中第一个页面（摄像头检测）
        if 'camera' in self.nav_button_map:
            self.nav_button_map['camera'].setChecked(True)
        
        layout.addStretch()
        
        # 退出按钮
        logout_btn = QPushButton("🚪 退出程序")
        logout_btn.setFont(QFont("Microsoft YaHei", 11))
        logout_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.15);
                color: #f87171;
                padding: 10px;
                border-radius: 10px;
                border: 1px solid rgba(239, 68, 68, 0.3);
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.25);
                border: 1px solid rgba(239, 68, 68, 0.5);
            }
        """)
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
        
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self):
        """创建右侧内容区"""
        panel = QFrame()
        panel.setStyleSheet("background: #0f172a;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 顶部栏
        top_bar = QFrame()
        top_bar.setStyleSheet("background: #1e293b; border-bottom: 1px solid #334155;")
        top_bar.setFixedHeight(70)
        
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(10, 10, 10, 10)
        
        # 页面标题
        self.page_title = QLabel("摄像头实时检测")
        self.page_title.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        self.page_title.setStyleSheet("color: #e2e8f0;")
        top_layout.addWidget(self.page_title)
        
        top_layout.addStretch()
        
        # 时间显示
        self.time_label = QLabel(self.get_current_time())
        self.time_label.setStyleSheet("color: #94a3b8; font-size: 14px; background: rgba(45, 212, 191, 0.1); padding: 10px 10px; border-radius: 8px;")
        top_layout.addWidget(self.time_label)
        
        # 添加间距
        top_layout.addSpacing(10)
        
        # 用户信息显示
        username = self.user_data['username']
        if self.user_data.get('is_admin', False):
            user_info_text = f"👤 {username} (管理员)"
            user_info_style = "color: #2dd4bf; background: rgba(45, 212, 191, 0.1); padding: 10px 10px; border-radius: 8px;"
        else:
            user_info_text = f"👤 {username}"
            user_info_style = "color: #94a3b8; background: rgba(45, 212, 191, 0.1); padding: 10px 10px; border-radius: 8px;"
        
        self.user_info_label = QLabel(user_info_text)
        self.user_info_label.setStyleSheet(user_info_style)
        top_layout.addWidget(self.user_info_label)
        
        # 添加时间更新定时器
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # 每秒更新一次
        
        top_bar.setLayout(top_layout)
        layout.addWidget(top_bar)
        
        # 内容堆叠区
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background: #0f172a;")

        from App.views.cameraDetection import CameraDetectionPage
        from App.views.imageDetection import ImageDetectionPage
        from App.views.batchImageDetection import BatchImageDetectionPage
        from App.views.videoDetection import VideoDetectionPage
        from App.views.statistics import StatisticsPage
        from App.views.userManagement import UserManagementPage
        from App.views.settings import SettingsPage

        
        self.pages = {}
        
        # 摄像头检测
        self.pages['camera'] = CameraDetectionPage()
        self.content_stack.addWidget(self.pages['camera'])
        
        # 图片检测
        self.pages['image'] = ImageDetectionPage()
        self.content_stack.addWidget(self.pages['image'])
        
        # 批量图片检测
        self.pages['batch_image'] = BatchImageDetectionPage()
        self.content_stack.addWidget(self.pages['batch_image'])
        
        # 视频检测
        self.pages['video'] = VideoDetectionPage()
        self.content_stack.addWidget(self.pages['video'])
        
        # 数据统计
        self.pages['statistics'] = StatisticsPage()
        self.content_stack.addWidget(self.pages['statistics'])
        
        # 用户管理
        self.pages['user_management'] = UserManagementPage()
        self.content_stack.addWidget(self.pages['user_management'])
        
        # 系统设置
        self.pages['settings'] = SettingsPage()
        self.content_stack.addWidget(self.pages['settings'])
        
        layout.addWidget(self.content_stack)
        
        panel.setLayout(layout)
        return panel
    
    def switch_page(self, page_name):
        """切换页面"""
        page_map = {
            'camera': 0,
            'image': 1,
            'batch_image': 2,
            'video': 3,
            'statistics': 4,
            'user_management': 5,
            'settings': 6
        }
        
        if page_name in page_map:
            self.content_stack.setCurrentIndex(page_map[page_name])
            
            # 更新标题
            titles = {
                'camera': '摄像头实时检测',
                'image': '图片检测',
                'batch_image': '批量图片检测',
                'video': '视频检测',
                'statistics': '数据统计',
                'user_management': '用户管理',
                'settings': '系统设置'
            }
            self.page_title.setText(titles.get(page_name, ''))
            
            # 更新导航按钮选中状态
            for page, btn in self.nav_button_map.items():
                btn.setChecked(page == page_name)
    
    def keyPressEvent(self, event: QKeyEvent):
        """键盘事件处理"""
        if event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()
        super().keyPressEvent(event)
    
    def toggle_fullscreen(self):
        """切换全屏"""
        if self.is_fullscreen:
            # 退出全屏
            self.showNormal()
            self.is_fullscreen = False
            print("ℹ️ 已退出全屏模式")
        else:
            # 进入全屏
            self.showFullScreen()
            self.is_fullscreen = True
            print("ℹ️ 已进入全屏模式")
    
    def get_current_time(self):
        """获取当前时间"""
        from datetime import datetime
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")
    
    def update_time(self):
        """更新时间显示"""
        self.time_label.setText(self.get_current_time())
    
    def logout(self):
        """退出程序"""
        import sys
        sys.exit(0)
