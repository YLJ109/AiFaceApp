"""
注册界面
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from App.database.user import UserDatabase

class RegisterWindow(QWidget):
    """注册窗口"""
    
    def __init__(self):
        super().__init__()
        self.user_db = UserDatabase()
        self.init_ui()
        
    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("用户注册")
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QWidget {
                background: #0f172a;
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(50, 30, 50, 30)
        
        # 标题
        title_label = QLabel("一零九面部表情检测系统")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            color: #2dd4bf;
            padding: 20px 0 10px 0;
        """)
        main_layout.addWidget(title_label)

        
        # 用户名
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名（至少 3 个字符）")
        self.username_input.setFont(QFont("Microsoft YaHei", 11))
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #334155;
                background: rgba(30, 41, 59, 0.8);
                color: #e2e8f0;
            }
            QLineEdit:focus {
                border: 1px solid #2dd4bf;
                background: rgba(30, 41, 59, 0.95);
            }
        """)
        main_layout.addWidget(self.username_input)
        
        # 密码
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码（至少 6 个字符）")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Microsoft YaHei", 11))
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #334155;
                background: rgba(30, 41, 59, 0.8);
                color: #e2e8f0;
            }
            QLineEdit:focus {
                border: 1px solid #2dd4bf;
                background: rgba(30, 41, 59, 0.95);
            }
        """)
        main_layout.addWidget(self.password_input)
        
        # 确认密码
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("确认密码")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setFont(QFont("Microsoft YaHei", 11))
        self.confirm_password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #334155;
                background: rgba(30, 41, 59, 0.8);
                color: #e2e8f0;
            }
            QLineEdit:focus {
                border: 1px solid #2dd4bf;
                background: rgba(30, 41, 59, 0.95);
            }
        """)
        main_layout.addWidget(self.confirm_password_input)
        
        # 邮箱（可选）
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("邮箱（可选）")
        self.email_input.setFont(QFont("Microsoft YaHei", 11))
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #334155;
                background: rgba(30, 41, 59, 0.8);
                color: #e2e8f0;
            }
            QLineEdit:focus {
                border: 1px solid #2dd4bf;
                background: rgba(30, 41, 59, 0.95);
            }
        """)
        main_layout.addWidget(self.email_input)
        
        # 注册按钮
        self.register_btn = QPushButton("注 册")
        self.register_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.register_btn.setStyleSheet("""
            QPushButton {
                background: #2dd4bf;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #14b8a6;
            }
        """)
        self.register_btn.clicked.connect(self.register)
        main_layout.addWidget(self.register_btn)
        
        # 返回登录
        back_btn = QPushButton("返回登录")
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #2dd4bf;
                border: 1px solid #2dd4bf;
                padding: 8px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: rgba(45, 212, 191, 0.1);
            }
        """)
        back_btn.clicked.connect(self.close)
        main_layout.addWidget(back_btn)
        
        self.setLayout(main_layout)
    
    def register(self):
        """注册处理"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        email = self.email_input.text().strip()
        
        # 验证
        if not username or not password:
            QMessageBox.warning(self, "提示", "请填写必填项")
            return
        
        if len(username) < 3:
            QMessageBox.warning(self, "提示", "用户名至少 3 个字符")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "提示", "密码至少 6 个字符")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "提示", "两次输入的密码不一致")
            return
        
        # 注册
        success, message = self.user_db.register_user(username, password, email)
        
        if success:
            QMessageBox.information(self, "成功", message)
            self.close()
        else:
            QMessageBox.critical(self, "失败", message)
