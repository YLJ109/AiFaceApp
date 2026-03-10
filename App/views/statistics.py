"""
数据统计页面
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QFrame, QDateEdit, QComboBox, QGridLayout)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
import sqlite3
import os
from datetime import datetime
from App.code.config import EMOTION_CHINESE

class StatisticsPage(QWidget):
    """数据统计页面"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_database()
        self.load_data()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        

        
        # 筛选区域
        filter_frame = QFrame()
        filter_frame.setStyleSheet("background: #1e293b; border-radius: 12px; padding: 10px;")
        filter_layout = QGridLayout()
        filter_layout.setSpacing(10)
        
        # 日期筛选
        date_label = QLabel("日期范围:")
        date_label.setFont(QFont("Microsoft YaHei", 12))
        date_label.setStyleSheet("color: #94a3b8;")
        filter_layout.addWidget(date_label, 0, 0, 1, 1)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setCalendarPopup(True)
        self.start_date.setFont(QFont("Microsoft YaHei", 12))
        self.start_date.setFixedHeight(30)
        self.start_date.setMinimumWidth(180)
        self.start_date.setStyleSheet("""
            QDateEdit {
                background: #0f172a;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 0 10px;
            }
            QDateEdit:hover {
                border: 1px solid #2dd4bf;
            }
        """)
        filter_layout.addWidget(self.start_date, 0, 1, 1, 1)
        
        to_label = QLabel("至")
        to_label.setFont(QFont("Microsoft YaHei", 12))
        to_label.setStyleSheet("color: #94a3b8;")
        filter_layout.addWidget(to_label, 0, 2, 1, 1)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setFont(QFont("Microsoft YaHei", 12))
        self.end_date.setFixedHeight(30)
        self.end_date.setMinimumWidth(180)
        self.end_date.setStyleSheet("""
            QDateEdit {
                background: #0f172a;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 0 10px;
            }
            QDateEdit:hover {
                border: 1px solid #2dd4bf;
            }
        """)
        filter_layout.addWidget(self.end_date, 0, 3, 1, 1)
        
        # 来源筛选
        source_label = QLabel("来源:")
        source_label.setFont(QFont("Microsoft YaHei", 12))
        source_label.setStyleSheet("color: #94a3b8;")
        filter_layout.addWidget(source_label, 1, 0, 1, 1)
        
        self.source_combo = QComboBox()
        self.source_combo.addItems(["全部", "摄像头检测", "图片检测", "批量图片检测", "视频检测"])
        self.source_combo.setFont(QFont("Microsoft YaHei", 12))
        self.source_combo.setFixedHeight(30)
        self.source_combo.setMinimumWidth(380)
        self.source_combo.setStyleSheet("""
            QComboBox {
                background: #0f172a;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 0 10px;
            }
            QComboBox:hover {
                border: 1px solid #2dd4bf;
            }
            QComboBox::drop-down {
                border-left: 1px solid #334155;
            }
            QComboBox::down-arrow {
                image: url(:/icons/down_arrow.png);
                width: 16px;
                height: 16px;
            }
        """)
        filter_layout.addWidget(self.source_combo, 1, 1, 1, 3)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # 搜索按钮
        search_btn = QPushButton("🔍 搜索")
        search_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Medium))
        search_btn.setFixedHeight(30)
        search_btn.setMinimumWidth(120)
        search_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2dd4bf, stop:1 #14b8a6);
                color: white;
                font-size: 14px;
                padding: 0 10px;
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
        search_btn.clicked.connect(self.load_data)
        button_layout.addWidget(search_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Medium))
        refresh_btn.setFixedHeight(30)
        refresh_btn.setMinimumWidth(120)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #64748b, stop:1 #475569);
                color: white;
                font-size: 14px;
                padding: 0 10px;
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
        refresh_btn.clicked.connect(self.load_data)
        button_layout.addWidget(refresh_btn)
        
        filter_layout.addLayout(button_layout, 2, 0, 1, 4)
        
        filter_frame.setLayout(filter_layout)
        layout.addWidget(filter_frame,1)
        
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
                font-size: 12px;
                font-weight: bold;
                border: none;
            }
            QTableWidgetItem {
                padding: 12px;
                font-size: 12px;
                font-family: 'Microsoft YaHei';
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
        """)
        
        # 设置表格行高
        self.table.verticalHeader().setDefaultSectionSize(40)
        
        # 设置表格列
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["编号", "图片名称", "标签", "置信度", "来源", "时间"])
        
        # 设置列宽
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 330)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 160)  # 增加置信度列宽度
        self.table.setColumnWidth(4, 160)
        self.table.setColumnWidth(5, 200)
        
        # 设置表格高度
        self.table.setMinimumHeight(400)
        
        # 设置表格为只读模式
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table,8)
        
        # 统计信息
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background: #1e293b; border-radius: 12px; padding: 5px;")
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        stats_frame.setFixedHeight(60)
        
        # 总记录数
        self.total_label = QLabel("总记录: 0")
        self.total_label.setFont(QFont("Microsoft YaHei", 12))
        self.total_label.setStyleSheet("color: #94a3b8;")
        stats_layout.addWidget(self.total_label)
        
        # 按来源统计
        self.source_stats = QLabel("各来源统计: ")
        self.source_stats.setFont(QFont("Microsoft YaHei", 12))
        self.source_stats.setStyleSheet("color: #94a3b8;")
        stats_layout.addWidget(self.source_stats)
        
        stats_layout.addStretch()
        stats_frame.setLayout(stats_layout)
        layout.addWidget(stats_frame,1)
        
        self.setLayout(layout)
    
    def init_database(self):
        """初始化数据库"""
        db_path = "App/data/detection_data.db"
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_name TEXT,
                emotion TEXT,
                confidence REAL,
                source TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_data(self):
        """加载数据"""
        db_path = "App/data/detection_data.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 构建查询
        query = "SELECT id, image_name, emotion, confidence, source, timestamp FROM detection_data WHERE 1=1"
        params = []
        
        # 日期筛选
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        query += " AND DATE(timestamp) >= ? AND DATE(timestamp) <= ?"
        params.extend([start_date, end_date])
        
        # 来源筛选
        source = self.source_combo.currentText()
        if source != "全部":
            query += " AND source = ?"
            params.append(source)
        
        # 按时间倒序
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # 清空表格
        self.table.setRowCount(0)
        
        # 填充表格
        for row_idx, row in enumerate(results):
            self.table.insertRow(row_idx)
            
            for col_idx, value in enumerate(row):
                # 格式化置信度，只显示两位小数
                if col_idx == 3:
                    item = QTableWidgetItem(f"{float(value):.2f}")
                # 转换标签为中文
                elif col_idx == 2:
                    chinese_emotion = EMOTION_CHINESE.get(str(value), str(value))
                    item = QTableWidgetItem(chinese_emotion)
                else:
                    item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # 置信度设置颜色
                if col_idx == 3:
                    confidence = float(value)
                    if confidence >= 0.8:
                        item.setForeground(QColor(45, 212, 191))  # 绿色
                    elif confidence >= 0.6:
                        item.setForeground(QColor(251, 191, 36))  # 黄色
                    else:
                        item.setForeground(QColor(239, 68, 68))  # 红色
                
                self.table.setItem(row_idx, col_idx, item)
        
        # 更新统计信息
        self.total_label.setText(f"总记录: {len(results)}")
        
        # 统计各来源数据
        cursor.execute("SELECT source, COUNT(*) FROM detection_data GROUP BY source")
        source_counts = cursor.fetchall()
        source_text = "各来源统计: "
        for source, count in source_counts:
            source_text += f"{source}: {count}  "
        self.source_stats.setText(source_text)
        
        conn.close()
    
    @staticmethod
    def add_detection_data(image_name, emotion, confidence, source):
        """添加检测数据到数据库"""
        db_path = "App/data/detection_data.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO detection_data (image_name, emotion, confidence, source, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (image_name, emotion, confidence, source, timestamp))
        
        conn.commit()
        conn.close()