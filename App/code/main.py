"""
主程序入口
"""
import sys
import os

# 添加 App 目录到路径
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, app_dir)

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# 直接导入而不是作为包
config_path = os.path.join(app_dir, 'code', 'config.py')
import importlib.util
spec = importlib.util.spec_from_file_location("config", config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

from App.views.page.login import LoginWindow
from App.views.page.home import HomeWindow

class HomeInitThread(QThread):
    """HomeWindow初始化线程"""
    init_finished = pyqtSignal(object)  # 初始化完成信号
    
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
    
    def run(self):
        """运行初始化"""
        # 初始化HomeWindow
        home_window = HomeWindow(self.user_data)
        # 发送初始化完成信号
        self.init_finished.emit(home_window)

class LoadingWindow(QWidget):
    """加载提示窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("系统初始化")
        self.setFixedSize(400, 200)
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
        title_label = QLabel("正在进入系统...")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2dd4bf;")
        main_layout.addWidget(title_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 10px;
                border-radius: 5px;
                background: #334155;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #2dd4bf;
                border-radius: 5px;
            }
        """)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        main_layout.addWidget(self.progress_bar)
        
        # 提示信息
        info_label = QLabel("系统正在初始化，请稍候...")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setFont(QFont("Microsoft YaHei", 12))
        info_label.setStyleSheet("color: #e2e8f0;")
        main_layout.addWidget(info_label)
        
        self.setLayout(main_layout)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName(config.APP_NAME)
    app.setStyle('Fusion')
    
    # 显示登录窗口
    login_window = LoginWindow()
    loading_window = None
    home_init_thread = None
    
    def on_login_success(user_data):
        """登录成功后的处理"""
        nonlocal loading_window, home_init_thread
        
        # 显示加载窗口
        loading_window = LoadingWindow()
        loading_window.show()
        
        # 启动HomeWindow初始化线程
        home_init_thread = HomeInitThread(user_data)
        home_init_thread.init_finished.connect(on_home_init_finished)
        home_init_thread.start()
    
    def on_home_init_finished(home_window):
        """HomeWindow初始化完成后的处理"""
        nonlocal loading_window
        
        # 关闭加载窗口
        if loading_window:
            loading_window.close()
        
        # 显示HomeWindow
        home_window.show()
    
    login_window.login_success.connect(on_login_success)
    login_window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
