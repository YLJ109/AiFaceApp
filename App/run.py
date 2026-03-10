"""
面部表情检测系统 - 主启动脚本
"""
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from App.code.config import APP_NAME, ICON_PATH
from App.views.page.login import LoginWindow

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName(APP_NAME)
    app.setStyle('Fusion')
    
    # 设置应用图标
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))
    
    # 显示登录窗口
    login_window = LoginWindow()
    
    def on_login_success(user_data):
        """登录成功后的处理"""
        # 动态导入 HomeWindow
        from App.views.page.home import HomeWindow
        home_window = HomeWindow(user_data)
        home_window.show()
    
    login_window.login_success.connect(on_login_success)
    login_window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
