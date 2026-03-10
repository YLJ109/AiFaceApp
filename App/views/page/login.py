"""
登录界面
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
import json
import os
from App.database.user import UserDatabase
from App.code.config import ICON_PATH

class LoginWindow(QWidget):
    """登录窗口"""
    
    login_success = pyqtSignal(dict)  # 登录成功信号
    
    def __init__(self):
        super().__init__()
        self.user_db = UserDatabase()
        # 获取App目录的绝对路径
        import os
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.config_file = os.path.join(app_dir, 'config', 'login_config.json')
        self.load_login_config()
        self.init_ui()
        
        # 设置窗口图标
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        
    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("面部表情检测系统 - 登录")
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QWidget {
                background: #0f172a;
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(50, 30, 50, 30)

        # 标题
        title_label = QLabel("一零九面部表情检测系统")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            color: #2dd4bf;
            padding: 10px 0 20px 0;
        """)
        main_layout.addWidget(title_label)
        

        
        # 用户名
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        self.username_input.setFont(QFont("Microsoft YaHei", 12))
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 14px;
                border-radius: 10px;
                border: 1px solid #334155;
                background: rgba(30, 41, 59, 0.8);
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #2dd4bf;
                background: rgba(30, 41, 59, 0.95);
            }
        """)
        main_layout.addWidget(self.username_input)
        
        # 密码
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Microsoft YaHei", 12))
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 14px;
                border-radius: 10px;
                border: 1px solid #334155;
                background: rgba(30, 41, 59, 0.8);
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #2dd4bf;
                background: rgba(30, 41, 59, 0.95);
            }
        """)
        self.password_input.returnPressed.connect(self.login)
        main_layout.addWidget(self.password_input)
        
        # 记住密码复选框
        self.remember_checkbox = QCheckBox("记住密码")
        self.remember_checkbox.setStyleSheet("""
            QCheckBox {
                color: #cbd5e1;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #475569;
                background: transparent;
            }
            QCheckBox::indicator:checked {
                background: #2dd4bf;
                border: 2px solid #2dd4bf;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #2dd4bf;
            }
        """)
        
        # 如果已保存配置，自动填充并勾选
        if hasattr(self, 'saved_username') and self.saved_username:
            self.username_input.setText(self.saved_username)
            if hasattr(self, 'saved_password') and self.saved_password:
                self.password_input.setText(self.saved_password)
                self.remember_checkbox.setChecked(True)
        
        main_layout.addWidget(self.remember_checkbox)
        
        # 登录按钮
        self.login_btn = QPushButton("登 录")
        self.login_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: #2dd4bf;
                color: white;
                padding: 14px;
                border-radius: 10px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #14b8a6;
            }
            QPushButton:pressed {
                background: #0d9488;
            }
        """)
        self.login_btn.clicked.connect(self.login)
        main_layout.addWidget(self.login_btn)
        
        # 注册链接
        register_layout = QHBoxLayout()
        register_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        register_label = QLabel("还没有账号？")
        register_label.setStyleSheet("color: white;")
        register_layout.addWidget(register_label)
        
        self.register_link = QPushButton("立即注册")
        self.register_link.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #2dd4bf;
                text-decoration: underline;
                border: none;
                padding: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                color: #14b8a6;
            }
        """)
        self.register_link.clicked.connect(self.show_register)
        register_layout.addWidget(self.register_link)
        
        main_layout.addLayout(register_layout)
        
        self.setLayout(main_layout)
    
    def login(self):
        """登录处理"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "提示", "请输入用户名和密码")
            return
        
        success, message, user_data = self.user_db.login_user(username, password)
        
        if success:
            # 保存配置
            self.close()
            self.save_login_config()
            self.login_success.emit(user_data)

        else:
            QMessageBox.critical(self, "失败", message)
    
    def save_login_config(self):
        """保存登录配置"""
        try:
            # 创建配置目录
            config_dir = os.path.dirname(self.config_file)
            os.makedirs(config_dir, exist_ok=True)
            
            config = {
                'remember': self.remember_checkbox.isChecked(),
                'username': self.username_input.text().strip()
            }
            
            # 只有勾选了记住密码才保存密码
            if self.remember_checkbox.isChecked():
                config['password'] = self.password_input.text()
            else:
                config['password'] = ''
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 登录配置已保存：{self.config_file}")
        except Exception as e:
            print(f"❌ 保存配置失败：{e}")
    
    def load_login_config(self):
        """加载登录配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.saved_username = config.get('username', '')
                self.saved_password = config.get('password', '')
                
                print(f"✅ 已加载登录配置：{self.config_file}")
            else:
                self.saved_username = ''
                self.saved_password = ''
                print("ℹ️ 未找到登录配置")
        except Exception as e:
            print(f"❌ 加载配置失败：{e}")
            self.saved_username = ''
            self.saved_password = ''
    
    def show_register(self):
        """显示注册窗口"""
        from App.views.page.register import RegisterWindow
        self.register_window = RegisterWindow()
        self.register_window.show()
