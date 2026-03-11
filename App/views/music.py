"""
适配音乐页面
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QFileDialog, QCheckBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon
import os
from App.code.config import APP_DIR, EMOTION_CLASSES, EMOTION_CHINESE

class MusicPage(QWidget):
    """适配音乐页面"""
    
    def __init__(self):
        super().__init__()
        self.music_dirs = {}
        self.default_music_dir = os.path.join(APP_DIR, 'music')
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 页面标题已移至顶部统一位置
        
        # 根据表情适配播放选项
        play_layout = QHBoxLayout()
        play_layout.setSpacing(10)
        
        play_label = QLabel("根据表情适配播放：")
        play_label.setFont(QFont("Microsoft YaHei", 14))
        play_label.setStyleSheet("color: #94a3b8;")
        play_layout.addWidget(play_label)
        
        self.play_checkbox = QCheckBox()
        self.play_checkbox.setChecked(True)
        self.play_checkbox.setStyleSheet("""
            QCheckBox {
                width: 24px;
                height: 24px;
            }
            QCheckBox::indicator {
                width: 24px;
                height: 24px;
                border: 2px solid #334155;
                border-radius: 4px;
                background: #1e293b;
            }
            QCheckBox::indicator:checked {
                background: #2dd4bf;
                border: 2px solid #2dd4bf;
            }
        """)
        play_layout.addWidget(self.play_checkbox)
        
        main_layout.addLayout(play_layout)
        
        # 音乐文件夹设置
        music_frame = QFrame()
        music_frame.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border-radius: 12px;
                border: 2px solid #334155;
            }
        """)
        music_layout = QVBoxLayout()
        music_layout.setContentsMargins(20, 20, 20, 20)
        music_layout.setSpacing(15)
        
        music_title = QLabel("音乐文件夹设置")
        music_title.setMaximumHeight(80)
        music_title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        music_title.setStyleSheet("color: #2dd4bf;")
        music_layout.addWidget(music_title)
        
        # 七个表情对应的音乐文件夹
        for emotion in EMOTION_CLASSES:
            emotion_layout = QHBoxLayout()
            emotion_layout.setSpacing(10)
            
            # 为每个表情添加对应的emoji
            emoji_map = {
                'angry': '😠',
                'disgust': '🤢',
                'fear': '😨',
                'happy': '😊',
                'neutral': '😐',
                'sad': '😢',
                'surprise': '😮'
            }
            emoji = emoji_map.get(emotion, '')
            
            emotion_label = QLabel(f"{emoji} {EMOTION_CHINESE.get(emotion, emotion)}：")
            emotion_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
            emotion_label.setStyleSheet("color: #94a3b8;")
            emotion_label.setFixedWidth(120)
            emotion_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            emotion_layout.addWidget(emotion_label)
            
            # 文件夹路径显示（使用中文名称）
            chinese_emotion = EMOTION_CHINESE.get(emotion, emotion)
            default_folder = os.path.join(self.default_music_dir, chinese_emotion)
            self.music_dirs[emotion] = default_folder
            
            path_label = QLabel(default_folder if os.path.exists(default_folder) else "未设置")
            path_label.setFont(QFont("Microsoft YaHei", 12))
            path_label.setStyleSheet("color: #e2e8f0;")
            path_label.setObjectName(f"path_{emotion}")
            emotion_layout.addWidget(path_label, stretch=1)
            
            # 选择文件夹按钮
            select_btn = QPushButton("选择")
            select_btn.setMaximumHeight(50)
            select_btn.setFont(QFont("Microsoft YaHei", 11))
            select_btn.setStyleSheet("""
                QPushButton {
                    background: #334155;
                    color: #e2e8f0;
                    padding: 5px 5px;
                    border-radius: 6px;
                    border: none;
                }
                QPushButton:hover {
                    background: #475569;
                }
            """)
            select_btn.setFixedWidth(100)
            select_btn.clicked.connect(lambda checked, e=emotion: self.select_music_folder(e))
            emotion_layout.addWidget(select_btn)
            
            music_layout.addLayout(emotion_layout)
        
        music_frame.setLayout(music_layout)
        main_layout.addWidget(music_frame)
        
        # 底部提示
        hint_label = QLabel("提示：请确保每个表情都设置了对应的音乐文件夹，系统会根据检测到的表情自动播放相应的音乐。")
        hint_label.setMaximumHeight(40)
        hint_label.setFont(QFont("Microsoft YaHei", 11))
        hint_label.setStyleSheet("color: #64748b;")
        hint_label.setWordWrap(True)
        main_layout.addWidget(hint_label)
        
        self.setLayout(main_layout)
    
    def select_music_folder(self, emotion):
        """选择音乐文件夹"""
        folder = QFileDialog.getExistingDirectory(self, f"选择{EMOTION_CHINESE.get(emotion, emotion)}的音乐文件夹")
        if folder:
            self.music_dirs[emotion] = folder
            path_label = self.findChild(QLabel, f"path_{emotion}")
            if path_label:
                path_label.setText(folder)
            print(f"✅ 已选择{EMOTION_CHINESE.get(emotion, emotion)}的音乐文件夹：{folder}")
    
    def get_music_dir(self, emotion):
        """获取指定表情的音乐文件夹"""
        return self.music_dirs.get(emotion, os.path.join(self.default_music_dir, emotion))
    
    def is_play_enabled(self):
        """是否启用根据表情适配播放"""
        return self.play_checkbox.isChecked()
