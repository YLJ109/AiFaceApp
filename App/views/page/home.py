"""
主界面 - 面部表情检测系统
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QPushButton, QLabel, QFrame, QSlider)
from PyQt6.QtCore import QSize
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QKeyEvent, QIcon, QPixmap
import os
import random
import sys
import warnings
# 屏蔽pkg_resources相关的废弃警告
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
import pygame
from App.code.config import APP_NAME, APP_VERSION, ICON_PATH, APP_DIR, EMOTION_CHINESE, EMOTION_CLASSES

class MusicInitThread(QThread):
    """音乐初始化线程"""
    init_finished = pyqtSignal()
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
    
    def run(self):
        """运行初始化"""
        # 初始化音乐目录和文件列表
        for emotion in EMOTION_CLASSES:
            chinese_emotion = EMOTION_CHINESE.get(emotion, emotion)
            self.parent.music_dirs[emotion] = os.path.join(self.parent.default_music_dir, chinese_emotion)
            # 获取音乐文件列表
            try:
                music_files = [f for f in os.listdir(self.parent.music_dirs[emotion]) if f.endswith(('.mp3', '.wav', '.ogg', '.flac'))]
            except:
                music_files = []
            self.parent.music_files[emotion] = music_files
            self.parent.current_music_index[emotion] = 0
        self.init_finished.emit()

class HomeWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.is_fullscreen = False  # 全屏状态标记
        
        # 初始化pygame.mixer
        pygame.mixer.init()
        
        # 音乐播放相关属性
        self.is_playing = True  # 默认自动播放
        self.current_music = None
        self.current_emotion = None
        self.music_dirs = {}
        self.default_music_dir = os.path.join(APP_DIR, 'music')
        self.music_files = {}  # 存储每个情绪的音乐文件列表
        self.current_music_index = {}  # 存储每个情绪的当前音乐索引
        self.is_muted = False  # 静音状态
        
        # 初始化UI
        self.init_ui()
        
        # 设置窗口图标
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        
        # 启动音乐初始化线程
        music_thread = MusicInitThread(self)
        music_thread.init_finished.connect(self.on_music_init_finished)
        music_thread.start()
    
    def on_music_init_finished(self):
        """音乐初始化完成后的处理"""
        print("🎵 音乐目录初始化完成")
        # 初始化完成后，可以开始播放音乐
        QTimer.singleShot(1000, self.check_emotion_and_play_music)
    
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
        global QIcon, QSize, QPixmap
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
            ("摄像头检测", "camera", "摄像头检测.png"),
            ("图片检测", "image", "图片检测.png"),
            ("批量图片检测", "batch_image", "批量图片检测.png"),
            ("视频检测", "video", "视频检测.png"),
            ("数据统计", "statistics", "数据统计.png"),
            ("适配音乐", "music", "适配音乐.png"),
        ]
        
        # 如果是管理员，添加用户管理选项
        if self.user_data.get('is_admin', False):
            nav_buttons.append(("用户管理", "user_management", "用户管理.png"))
        
        nav_buttons.append(("系统设置", "settings", "设置.png"))
        
        self.nav_button_map = {}  # 保存按钮引用
        
        for text, page, icon_name in nav_buttons:
            btn = QPushButton(text)
            # 设置图标
            icon_path = os.path.join(APP_DIR, 'icons', icon_name)
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                btn.setIcon(icon)
                btn.setIconSize(QSize(20, 20))
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
        
        # 音乐播放器
        music_frame = QFrame()
        music_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e293b, stop:1 #334155);
                border-radius: 16px;
                border: 1px solid rgba(45, 212, 191, 0.3);
                padding: 10px;
            }
        """)
        music_layout = QVBoxLayout()
        music_layout.setContentsMargins(0, 0, 0, 0)
        music_layout.setSpacing(12)
        
        # 音乐播放器标题
        music_title = QLabel("🎵 音乐播放")
        music_title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        music_title.setStyleSheet("color: #2dd4bf;")
        music_layout.addWidget(music_title)
        
        # 音乐名称
        self.music_name_label = QLabel("未播放")
        self.music_name_label.setFont(QFont("Microsoft YaHei", 11))
        self.music_name_label.setStyleSheet("color: #e2e8f0;")
        self.music_name_label.setWordWrap(True)
        self.music_name_label.setMinimumHeight(40)
        music_layout.addWidget(self.music_name_label)
        
        # 音乐控制按钮
        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)
        control_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 上一曲按钮
        from PyQt6.QtGui import QIcon
        
        # 使用 APP_DIR 来构建图标路径
        self.prev_btn = QPushButton()
        prev_icon_path = os.path.join(APP_DIR, 'icons', '上一个.png')
        if os.path.exists(prev_icon_path):
            self.prev_btn.setIcon(QIcon(prev_icon_path))
        else:
            self.prev_btn.setIcon(QIcon.fromTheme("media-skip-backward"))
        self.prev_btn.setIconSize(QSize(30, 30))
        self.prev_btn.setFixedSize(55, 55)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background: rgba(51, 65, 85, 0.8);
                color: #e2e8f0;
                border-radius: 8px;
                border: 1px solid rgba(45, 212, 191, 0.2);
            }
            QPushButton:hover {
                background: rgba(71, 85, 105, 0.9);
                border-color: rgba(45, 212, 191, 0.5);
            }
        """)
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self.play_previous_music)
        control_layout.addWidget(self.prev_btn)
        
        # 播放/暂停按钮
        self.play_pause_btn = QPushButton()
        pause_icon_path = os.path.join(APP_DIR, 'icons', '音乐暂停.png')
        if os.path.exists(pause_icon_path):
            self.play_pause_btn.setIcon(QIcon(pause_icon_path))
        else:
            self.play_pause_btn.setIcon(QIcon.fromTheme("media-playback-pause"))
        self.play_pause_btn.setIconSize(QSize(24, 24))
        self.play_pause_btn.setFixedSize(55, 55)
        self.play_pause_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2dd4bf, stop:1 #14b8a6);
                color: #1e293b;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #14b8a6, stop:1 #0d9488);
            }
        """)
        self.play_pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        control_layout.addWidget(self.play_pause_btn)
        
        # 下一曲按钮
        self.next_btn = QPushButton()
        next_icon_path = os.path.join(APP_DIR, 'icons', '下一个.png')
        if os.path.exists(next_icon_path):
            self.next_btn.setIcon(QIcon(next_icon_path))
        else:
            self.next_btn.setIcon(QIcon.fromTheme("media-skip-forward"))
        self.next_btn.setIconSize(QSize(30, 30))
        self.next_btn.setFixedSize(55, 55)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background: rgba(51, 65, 85, 0.8);
                color: #e2e8f0;
                border-radius: 8px;
                border: 1px solid rgba(45, 212, 191, 0.2);
            }
            QPushButton:hover {
                background: rgba(71, 85, 105, 0.9);
                border-color: rgba(45, 212, 191, 0.5);
            }
        """)
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.clicked.connect(self.play_next_music)
        control_layout.addWidget(self.next_btn)
        
        music_layout.addLayout(control_layout)
        
        # 音量控制器
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(8)
        volume_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 声音图标
        sound_icon_label = QLabel()
        sound_icon_path = os.path.join(APP_DIR, 'icons', '声音.png')
        if os.path.exists(sound_icon_path):
            sound_pixmap = QPixmap(sound_icon_path)
            if not sound_pixmap.isNull():
                sound_icon_label.setPixmap(sound_pixmap.scaled(25, 25, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        sound_icon_label.setFixedSize(50, 50)
        sound_icon_label.setStyleSheet("background: transparent;border:none;")
        volume_layout.addWidget(sound_icon_label)
        
        # 音量滑动条
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)  # 默认音量100%
        self.volume_slider.setFixedWidth(180)
        self.volume_slider.setStyleSheet("""
            QSlider {
                height: 8px;
                background: transparent;
            }
            QSlider::groove:horizontal {
                background: #334155;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #337bf9;
                width: 20px;
                height: 20px;
                border-radius: 10px;
                margin: -8px 0;
                border: none;
            }
            QSlider::handle:horizontal:hover {
                background: #337bf9;
                width: 22px;
                height: 22px;
                margin: -9px 0;
            }
            QSlider::handle:horizontal:pressed {
                background: #337bf9;
                width: 24px;
                height: 24px;
                margin: -10px 0;
            }
        """)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(self.volume_slider)
        
        music_layout.addLayout(volume_layout)
        
        # 静音按钮
        self.mute_btn = QPushButton()
        self.mute_btn.setFixedSize(55, 55)
        volume_icon_path = os.path.join(APP_DIR, 'icons', '音量.png')
        if os.path.exists(volume_icon_path):
            self.mute_btn.setIcon(QIcon(volume_icon_path))
        else:
            self.mute_btn.setText("🔊")
        self.mute_btn.setIconSize(QSize(24, 24))
        self.mute_btn.setStyleSheet("""
            QPushButton {
                background: rgba(51, 65, 85, 0.8);
                color: #e2e8f0;
                padding: 8px 12px;
                border-radius: 8px;
                border: 1px solid rgba(45, 212, 191, 0.2);
            }
            QPushButton:hover {
                background: rgba(71, 85, 105, 0.9);
                border-color: rgba(45, 212, 191, 0.5);
            }
        """)
        self.mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mute_btn.clicked.connect(self.toggle_mute)
        control_layout.addWidget(self.mute_btn)
        
        music_frame.setLayout(music_layout)
        layout.addWidget(music_frame)
        
        # 退出按钮
        logout_btn = QPushButton("退出程序")
        # 设置图标
        logout_icon_path = os.path.join(APP_DIR, 'icons', '退出.png')
        if os.path.exists(logout_icon_path):
            logout_icon = QIcon(logout_icon_path)
            logout_btn.setIcon(logout_icon)
            logout_btn.setIconSize(QSize(20, 20))
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
        self.time_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.time_label.setStyleSheet("color: #94a3b8; background: rgba(45, 212, 191, 0.1); padding: 8px 10px; border-radius: 8px;")
        top_layout.addWidget(self.time_label)

        # 添加间距
        top_layout.addSpacing(10)
        
        # 用户信息显示
        username = self.user_data['username']
        if self.user_data.get('is_admin', False):
            user_info_text = f"👤 {username} (管理员)"
            user_info_style = "color: #2dd4bf; background: rgba(45, 212, 191, 0.1); padding: 8px 10px; border-radius: 8px;"
        else:
            user_info_text = f"👤 {username}"
            user_info_style = "color: #94a3b8; background: rgba(45, 212, 191, 0.1); padding: 8px 10px; border-radius: 8px;"
        
        self.user_info_label = QLabel(user_info_text)
        self.user_info_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.user_info_label.setStyleSheet(user_info_style)
        top_layout.addWidget(self.user_info_label)
        
        # 添加时间更新定时器
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # 每秒更新一次
        
        # 添加音乐检测定时器
        self.music_timer = QTimer()
        self.music_timer.timeout.connect(self.check_emotion_and_play_music)
        self.music_timer.start(5000)  # 每5秒检测一次
        
        # 程序启动时立即检测情绪并播放音乐
        QTimer.singleShot(1000, self.check_emotion_and_play_music)
        
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
        from App.views.music import MusicPage

        
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
        
        # 适配音乐
        self.pages['music'] = MusicPage()
        self.content_stack.addWidget(self.pages['music'])
        
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
        # 显示加载指示器
        self.show_loading_indicator()
        
        # 停止其他页面的资源
        self.stop_other_resources(page_name)
        
        page_map = {
            'camera': 0,
            'image': 1,
            'batch_image': 2,
            'video': 3,
            'statistics': 4,
            'music': 5,
            'user_management': 6,
            'settings': 7
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
                'music': '适配音乐',
                'user_management': '用户管理',
                'settings': '系统设置'
            }
            self.page_title.setText(titles.get(page_name, ''))
            
            # 更新导航按钮选中状态
            for page, btn in self.nav_button_map.items():
                btn.setChecked(page == page_name)
            
            # 延迟隐藏加载指示器，确保页面有足够时间加载
            QTimer.singleShot(300, self.hide_loading_indicator)
    
    def show_loading_indicator(self):
        """显示加载指示器"""
        # 检查是否已存在加载指示器
        if not hasattr(self, 'loading_indicator'):
            from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
            from PyQt6.QtCore import Qt
            
            # 创建加载指示器
            self.loading_indicator = QWidget(self)
            self.loading_indicator.setGeometry(0, 0, self.width(), self.height())
            self.loading_indicator.setStyleSheet("background: rgba(15, 23, 42, 0.8);")
            
            layout = QVBoxLayout()
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            loading_label = QLabel("加载中...")
            loading_label.setFont(QFont("Microsoft YaHei", 14))
            loading_label.setStyleSheet("color: #2dd4bf;")
            
            layout.addWidget(loading_label)
            self.loading_indicator.setLayout(layout)
        
        self.loading_indicator.show()
    
    def hide_loading_indicator(self):
        """隐藏加载指示器"""
        if hasattr(self, 'loading_indicator'):
            self.loading_indicator.hide()
    
    def stop_other_resources(self, current_page):
        """停止其他页面的资源"""
        # 停止摄像头检测
        if current_page != 'camera' and 'camera' in self.pages:
            camera_page = self.pages['camera']
            if hasattr(camera_page, 'stop_camera'):
                camera_page.stop_camera()
        
        # 停止视频检测
        if current_page != 'video' and 'video' in self.pages:
            video_page = self.pages['video']
            if hasattr(video_page, 'stop_video'):
                video_page.stop_video()
        
        # 停止批量图片检测
        if current_page != 'batch_image' and 'batch_image' in self.pages:
            batch_image_page = self.pages['batch_image']
            if hasattr(batch_image_page, 'stop_processing'):
                batch_image_page.stop_processing()
    
    def keyPressEvent(self, event: QKeyEvent):
        """键盘事件处理"""
        if event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()
    
    def toggle_play_pause(self):
        """切换播放/暂停状态"""
        from PyQt6.QtGui import QIcon
        
        if self.is_playing:
            self.stop_music()
            self.is_playing = False
            # 尝试设置播放图标
            play_icon_path = os.path.join(APP_DIR, 'icons', '音乐播放.png')
            if os.path.exists(play_icon_path):
                self.play_pause_btn.setIcon(QIcon(play_icon_path))
            else:
                self.play_pause_btn.setIcon(QIcon.fromTheme("media-playback-start"))
            self.music_name_label.setText("已暂停")
        else:
            # 开始播放音乐，默认使用当前情绪
            self.is_playing = True
            # 尝试设置暂停图标
            pause_icon_path = os.path.join(APP_DIR, 'icons', '音乐暂停.png')
            if os.path.exists(pause_icon_path):
                self.play_pause_btn.setIcon(QIcon(pause_icon_path))
            else:
                self.play_pause_btn.setIcon(QIcon.fromTheme("media-playback-pause"))
            self.check_emotion_and_play_music(manual_play=True)
    
    def check_emotion_and_play_music(self, manual_play=False):
        """每五秒检测一次情绪并更新音乐"""
        try:
            # 检查是否启用了根据表情适配播放
            music_page = self.pages.get('music')
            if music_page and hasattr(music_page, 'play_checkbox'):
                if not music_page.play_checkbox.isChecked() and not manual_play:
                    # 复选框未勾选且不是手动播放，停止音乐
                    if self.is_playing:
                        self.stop_music()
                        self.is_playing = False
                        # 更新播放图标
                        play_icon_path = os.path.join(APP_DIR, 'icons', '音乐播放.png')
                        if os.path.exists(play_icon_path):
                            self.play_pause_btn.setIcon(QIcon(play_icon_path))
                        else:
                            self.play_pause_btn.setIcon(QIcon.fromTheme("media-playback-start"))
                        self.music_name_label.setText("未启用")
                    return
            
            # 获取当前页面
            current_index = self.content_stack.currentIndex()
            current_page = None
            
            # 确定当前页面类型
            if current_index == 0:  # 摄像头检测
                current_page = self.pages.get('camera')
            elif current_index == 1:  # 图片检测
                current_page = self.pages.get('image')
            elif current_index == 3:  # 视频检测
                current_page = self.pages.get('video')
            
            if not current_page:
                # 没有检测页面，停止播放音乐
                if not manual_play:
                    self.stop_music()
                    self.is_playing = False
                    # 更新播放图标
                    play_icon_path = os.path.join(APP_DIR, 'icons', '音乐播放.png')
                    if os.path.exists(play_icon_path):
                        self.play_pause_btn.setIcon(QIcon(play_icon_path))
                    else:
                        self.play_pause_btn.setIcon(QIcon.fromTheme("media-playback-start"))
                    self.music_name_label.setText("未检测")
                return
            
            # 检查页面是否正在检测
            is_detecting = False
            if current_index == 0:  # 摄像头检测
                # 检查摄像头是否打开
                is_detecting = hasattr(current_page, 'cap') and current_page.cap and current_page.cap.isOpened()
            elif current_index == 1:  # 图片检测
                # 图片检测是一次性的，只要有检测结果就认为正在检测
                is_detecting = hasattr(current_page, 'current_emotion') and current_page.current_emotion and current_page.current_emotion != "未检测"
            elif current_index == 3:  # 视频检测
                # 检查视频是否正在播放
                is_detecting = hasattr(current_page, 'cap') and current_page.cap and current_page.cap.isOpened()
            
            # 如果停止检测，音乐也跟着停止
            if not is_detecting and not manual_play:
                if self.is_playing:
                    self.stop_music()
                    self.is_playing = False
                    # 更新播放图标
                    play_icon_path = os.path.join(APP_DIR, 'icons', '音乐播放.png')
                    if os.path.exists(play_icon_path):
                        self.play_pause_btn.setIcon(QIcon(play_icon_path))
                    else:
                        self.play_pause_btn.setIcon(QIcon.fromTheme("media-playback-start"))
                    self.music_name_label.setText("已停止")
                return
            
            if is_detecting or manual_play:
                # 正在检测或用户手动播放，确保音乐播放器处于播放状态
                if not self.is_playing:
                    self.is_playing = True
                    # 更新暂停图标
                    pause_icon_path = os.path.join(APP_DIR, 'icons', '音乐暂停.png')
                    if os.path.exists(pause_icon_path):
                        self.play_pause_btn.setIcon(QIcon(pause_icon_path))
                    else:
                        self.play_pause_btn.setIcon(QIcon.fromTheme("media-playback-pause"))
                
                # 获取当前检测到的情绪
                if hasattr(current_page, 'face_results') and current_page.face_results:
                    # 统计所有人脸的表情
                    emotion_counts = {}
                    for result in current_page.face_results:
                        emotion = result.get('emotion', 'neutral')
                        if emotion != "未检测":
                            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                    
                    # 选择出现频率最高的表情
                    if emotion_counts:
                        detected_emotion = max(emotion_counts, key=emotion_counts.get)
                        
                        # 如果情绪有变化，切换音乐
                        if detected_emotion != self.current_emotion:
                            self.current_emotion = detected_emotion
                            self.current_music_index[detected_emotion] = 0  # 重置音乐索引
                            self.play_music(detected_emotion)
                        else:
                            # 情绪未变化，检查音乐是否播放完毕
                            self.check_music_end()
                    else:
                        # 没有检测到有效表情，显示等待检测
                        self.music_name_label.setText("等待检测...")
                elif hasattr(current_page, 'current_emotion') and current_page.current_emotion and current_page.current_emotion != "未检测":
                    # 兼容单表情检测
                    detected_emotion = current_page.current_emotion
                    
                    # 如果情绪有变化，切换音乐
                    if detected_emotion != self.current_emotion:
                        self.current_emotion = detected_emotion
                        self.current_music_index[detected_emotion] = 0  # 重置音乐索引
                        self.play_music(detected_emotion)
                    else:
                        # 情绪未变化，检查音乐是否播放完毕
                        self.check_music_end()
                else:
                    # 没有检测，停止播放音乐
                    self.stop_music()
                    self.is_playing = False
                    # 更新播放图标
                    play_icon_path = os.path.join(APP_DIR, 'icons', '音乐播放.png')
                    if os.path.exists(play_icon_path):
                        self.play_pause_btn.setIcon(QIcon(play_icon_path))
                    else:
                        self.play_pause_btn.setIcon(QIcon.fromTheme("media-playback-start"))
                    self.music_name_label.setText("未检测")
        except KeyboardInterrupt:
             # 中断时优雅关闭
            print("\n程序被手动终止，正在关闭界面...")
            sys.exit(0)
    
    def play_music(self, emotion):
        """根据情绪播放音乐"""
        try:
            # 检查emotion参数
            if not emotion:
                print("⚠️ 情绪未检测到")
                return
            
            # 检查音乐目录是否初始化完成
            if not self.music_dirs or not self.music_files:
                print("⚠️ 音乐目录初始化中")
                return
            
            # 检查音乐目录是否存在
            if emotion not in self.music_dirs:
                print(f"⚠️ 音乐目录不存在：{emotion}")
                return
            
            # 获取音乐文件列表
            music_files = self.music_files.get(emotion, [])
            if not music_files:
                print(f"⚠️ 音乐目录中没有音乐文件：{self.music_dirs.get(emotion)}")
                return
            
            # 获取当前音乐索引
            index = self.current_music_index.get(emotion, 0)
            if index >= len(music_files):
                # 循环播放
                index = 0
                self.current_music_index[emotion] = 0
            
            # 选择音乐文件
            selected_file = music_files[index]
            music_path = os.path.join(self.music_dirs[emotion], selected_file)
            
            # 停止当前播放的音乐
            self.stop_music()
            
            # 播放音乐
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play()
            print(f"🎵 正在播放{EMOTION_CHINESE.get(emotion, emotion)}音乐：{selected_file}")
            
            # 更新音乐播放器显示
            self.current_music = selected_file
            self.music_name_label.setText(f"{EMOTION_CHINESE.get(emotion, emotion)} - {os.path.splitext(selected_file)[0]}")
            
            # 增加音乐索引
            self.current_music_index[emotion] += 1
            
        except Exception as e:
            print(f"❌ 播放音乐错误：{e}")
    
    def stop_music(self):
        """停止音乐"""
        pygame.mixer.music.stop()
    
    def play_previous_music(self):
        """播放上一曲"""
        if not self.current_emotion:
            return
        
        # 减少音乐索引
        index = self.current_music_index.get(self.current_emotion, 0) - 2
        if index < 0:
            index = len(self.music_files.get(self.current_emotion, [])) - 1
        self.current_music_index[self.current_emotion] = index
        
        # 播放音乐
        self.play_music(self.current_emotion)
    
    def play_next_music(self):
        """播放下一曲"""
        if not self.current_emotion:
            return
        
        # 播放音乐
        self.play_music(self.current_emotion)
    
    def toggle_mute(self):
        """切换静音状态"""
        from PyQt6.QtGui import QIcon
        
        self.is_muted = not self.is_muted
        if self.is_muted:
            pygame.mixer.music.set_volume(0)
            # 尝试设置静音图标
            mute_icon_path = os.path.join(APP_DIR, 'icons', '静音.png')
            if os.path.exists(mute_icon_path):
                self.mute_btn.setIcon(QIcon(mute_icon_path))
            else:
                self.mute_btn.setIcon(QIcon.fromTheme("audio-volume-muted"))
        else:
            # 恢复之前的音量
            volume = self.volume_slider.value() / 100
            pygame.mixer.music.set_volume(volume)
            # 尝试设置音量图标
            volume_icon_path = os.path.join(APP_DIR, 'icons', '音量.png')
            if os.path.exists(volume_icon_path):
                self.mute_btn.setIcon(QIcon(volume_icon_path))
            else:
                self.mute_btn.setIcon(QIcon.fromTheme("audio-volume-high"))
    
    def set_volume(self, value):
        """设置音量"""
        if not self.is_muted:
            volume = value / 100
            pygame.mixer.music.set_volume(volume)
    
    def check_music_end(self):
        """检查音乐是否播放完毕，实现循环播放"""
        if not self.is_playing or not self.current_emotion:
            return
        
        if not pygame.mixer.music.get_busy():
            # 音乐播放完毕，播放下一首
            self.play_music(self.current_emotion)
    
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
        try:
            self.time_label.setText(self.get_current_time())
        except KeyboardInterrupt:
            pass
    
    def logout(self):
        """退出程序"""
        import sys
        sys.exit(0)
