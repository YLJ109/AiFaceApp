"""
用户管理页面
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QFrame, QLineEdit, QDialog, QFormLayout, 
                             QComboBox, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from App.database.user import UserDatabase

class UserManagementPage(QWidget):
    """用户管理页面"""
    
    def __init__(self):
        super().__init__()
        self.user_db = UserDatabase()
        self.init_ui()
        self.load_users()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        

        
        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # 添加用户按钮
        add_btn = QPushButton("➕ 添加用户")
        add_btn.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Medium))
        add_btn.setFixedHeight(50)
        add_btn.setMinimumWidth(160)
        add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2dd4bf, stop:1 #14b8a6);
                color: white;
                font-size: 14px;
                padding: 0 24px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #14b8a6, stop:1 #0d9488);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0d9488, stop:1 #0f766e);
            }
        """)
        add_btn.clicked.connect(self.add_user)
        button_layout.addWidget(add_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Medium))
        refresh_btn.setFixedHeight(50)
        refresh_btn.setMinimumWidth(130)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #64748b, stop:1 #475569);
                color: white;
                font-size: 14px;
                padding: 0 24px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #475569, stop:1 #334155);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #334155, stop:1 #1e293b);
            }
        """)
        refresh_btn.clicked.connect(self.load_users)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 数据表格
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                background: #1e293b;
                color: #e2e8f0;
                border-radius: 12px;
                border: 1px solid #334155;
                alternate-background-color: rgba(15, 23, 42, 0.5);
            }
            QHeaderView::section {
                background: #334155;
                color: #e2e8f0;
                padding: 12px;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-right: 1px solid #475569;
            }
            QHeaderView::section:last {
                border-right: none;
            }
            QTableWidgetItem {
                padding: 12px;
                font-size: 13px;
                font-family: 'Microsoft YaHei';
            }
            QTableWidget::item:selected {
                background: rgba(45, 212, 191, 0.2);
                color: #e2e8f0;
            }
            QScrollBar:vertical {
                background: #0f172a;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #475569;
            }
            QScrollBar::add-line:vertical {
                background: #0f172a;
                height: 10px;
                border-radius: 5px;
            }
            QScrollBar::sub-line:vertical {
                background: #0f172a;
                height: 10px;
                border-radius: 5px;
            }
        """)
        
        # 设置表格列
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "用户名", "邮箱", "创建时间", "最后登录", "状态", "操作"])
        
        # 设置列宽
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 180)
        self.table.setColumnWidth(2, 220)
        self.table.setColumnWidth(3, 160)
        self.table.setColumnWidth(4, 160)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 270)
        
        # 设置表格行高
        self.table.verticalHeader().setDefaultSectionSize(45)
        
        # 设置表格高度
        self.table.setMinimumHeight(500)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
    
    def load_users(self):
        """加载用户列表"""
        users = self.user_db.get_all_users()
        
        # 清空表格
        self.table.setRowCount(0)
        
        # 填充表格
        for row_idx, user in enumerate(users):
            self.table.insertRow(row_idx)
            
            # ID
            id_item = QTableWidgetItem(str(user['id']))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 0, id_item)
            
            # 用户名
            username_item = QTableWidgetItem(user['username'])
            username_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if user['is_admin']:
                username_item.setText(f"{user['username']} (管理员)")
                username_item.setForeground(QColor(45, 212, 191))
            self.table.setItem(row_idx, 1, username_item)
            
            # 邮箱
            email_item = QTableWidgetItem(user['email'] or "")
            email_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 2, email_item)
            
            # 创建时间
            created_at_item = QTableWidgetItem(str(user['created_at']))
            created_at_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 3, created_at_item)
            
            # 最后登录
            last_login_item = QTableWidgetItem(str(user['last_login']) if user['last_login'] else "")
            last_login_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 4, last_login_item)
            
            # 状态
            status_item = QTableWidgetItem("活跃" if user['is_active'] else "禁用")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(QColor(45, 212, 191) if user['is_active'] else QColor(239, 68, 68))
            self.table.setItem(row_idx, 5, status_item)
            
            # 操作按钮
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(10, 10, 10, 10)
            action_layout.setSpacing(8)
            
            # 编辑按钮
            edit_btn = QPushButton("编辑")
            edit_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Medium))
            edit_btn.setFixedHeight(25)
            edit_btn.setFixedWidth(60)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #64748b, stop:1 #475569);
                    color: white;
                    border-radius: 6px;
                    border: none;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #475569, stop:1 #334155);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #334155, stop:1 #1e293b);
                }
            """)
            edit_btn.clicked.connect(lambda _, uid=user['id']: self.edit_user(uid))
            action_layout.addWidget(edit_btn)
            
            # 删除按钮
            delete_btn = QPushButton("删除")
            delete_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Medium))
            delete_btn.setFixedHeight(25)
            delete_btn.setFixedWidth(60)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ef4444, stop:1 #dc2626);
                    color: white;
                    border-radius: 6px;
                    border: none;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #dc2626, stop:1 #b91c1c);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b91c1c, stop:1 #991b1b);
                }
            """)
            delete_btn.clicked.connect(lambda _, uid=user['id']: self.delete_user(uid))
            action_layout.addWidget(delete_btn)
            
            # 权限按钮
            admin_btn = QPushButton("设为管理员" if not user['is_admin'] else "取消管理员")
            admin_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Medium))
            admin_btn.setFixedHeight(25)
            admin_btn.setFixedWidth(100)
            admin_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8b5cf6, stop:1 #7c3aed);
                    color: white;
                    border-radius: 6px;
                    border: none;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7c3aed, stop:1 #6d28d9);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6d28d9, stop:1 #5b21b6);
                }
            """)
            admin_btn.clicked.connect(lambda _, uid=user['id'], is_admin=user['is_admin']: self.toggle_admin(uid, not is_admin))
            action_layout.addWidget(admin_btn)
            
            action_widget.setLayout(action_layout)
            self.table.setCellWidget(row_idx, 6, action_widget)
    
    def add_user(self):
        """添加用户"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加用户")
        dialog.setFixedSize(480, 350)
        dialog.setStyleSheet("""
            QDialog {
                background: #1e293b;
                border-radius: 12px;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 14px;
                font-weight: 500;
                margin-bottom: 5px;
            }
            QLineEdit {
                background: #0f172a;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-family: 'Microsoft YaHei';
            }
            QLineEdit:hover {
                border: 1px solid #2dd4bf;
            }
            QLineEdit:focus {
                border: 1px solid #2dd4bf;
                outline: none;
            }
            QComboBox {
                background: #0f172a;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-family: 'Microsoft YaHei';
            }
            QComboBox:hover {
                border: 1px solid #2dd4bf;
            }
            QComboBox::drop-down {
                border-left: 1px solid #334155;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QComboBox::down-arrow {
                image: url(:/icons/down_arrow.png);
                width: 16px;
                height: 16px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2dd4bf, stop:1 #14b8a6);
                color: white;
                border-radius: 8px;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #14b8a6, stop:1 #0d9488);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0d9488, stop:1 #0f766e);
            }
            QPushButton#cancel_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #64748b, stop:1 #475569);
            }
            QPushButton#cancel_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #475569, stop:1 #334155);
            }
            QPushButton#cancel_btn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #334155, stop:1 #1e293b);
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 20)
        layout.setSpacing(20)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(0, 0, 0, 10)
        
        # 用户名
        username_input = QLineEdit()
        username_input.setPlaceholderText("请输入用户名")
        username_input.setFixedHeight(40)
        form_layout.addRow("用户名:", username_input)
        
        # 密码
        password_input = QLineEdit()
        password_input.setPlaceholderText("请输入密码")
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_input.setFixedHeight(40)
        form_layout.addRow("密码:", password_input)
        
        # 邮箱
        email_input = QLineEdit()
        email_input.setPlaceholderText("请输入邮箱")
        email_input.setFixedHeight(40)
        form_layout.addRow("邮箱:", email_input)
        
        # 管理员权限
        admin_checkbox = QComboBox()
        admin_checkbox.addItems(["普通用户", "管理员"])
        admin_checkbox.setFixedHeight(40)
        form_layout.addRow("权限:", admin_checkbox)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 10, 0, 0)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton("确认")
        confirm_btn.setFixedHeight(40)
        confirm_btn.setMinimumWidth(100)
        confirm_btn.clicked.connect(lambda: self._confirm_add_user(dialog, username_input, password_input, email_input, admin_checkbox))
        button_layout.addWidget(confirm_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()
    
    def _confirm_add_user(self, dialog, username_input, password_input, email_input, admin_checkbox):
        """确认添加用户"""
        username = username_input.text().strip()
        password = password_input.text().strip()
        email = email_input.text().strip()
        is_admin = admin_checkbox.currentIndex() == 1
        
        if not username or not password:
            QMessageBox.warning(self, "警告", "用户名和密码不能为空")
            return
        
        success, message = self.user_db.add_user(username, password, email, is_admin)
        if success:
            QMessageBox.information(self, "成功", message)
            dialog.accept()
        else:
            QMessageBox.warning(self, "错误", message)
    
    def edit_user(self, user_id):
        """编辑用户"""
        # 这里可以实现编辑用户的功能
        QMessageBox.information(self, "提示", f"编辑用户功能待实现")
    
    def delete_user(self, user_id):
        """删除用户"""
        reply = QMessageBox.question(self, "确认删除", "确定要删除这个用户吗？", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.user_db.delete_user(user_id)
            if success:
                QMessageBox.information(self, "成功", message)
                self.load_users()
            else:
                QMessageBox.warning(self, "错误", message)
    
    def toggle_admin(self, user_id, is_admin):
        """切换管理员权限"""
        success, message = self.user_db.update_user(user_id, is_admin=is_admin)
        if success:
            QMessageBox.information(self, "成功", f"用户权限已{'提升为管理员' if is_admin else '降级为普通用户'}")
            self.load_users()
        else:
            QMessageBox.warning(self, "错误", message)
