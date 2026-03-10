"""
主程序入口
"""
import sys
import os

# 添加 App 目录到路径
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, app_dir)

from PyQt6.QtWidgets import QApplication

# 直接导入而不是作为包
config_path = os.path.join(app_dir, 'code', 'config.py')
import importlib.util
spec = importlib.util.spec_from_file_location("config", config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

from App.views.page.login import LoginWindow
from App.views.page.home import HomeWindow

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName(config.APP_NAME)
    app.setStyle('Fusion')
    
    # 显示登录窗口
    login_window = LoginWindow()
    
    def on_login_success(user_data):
        """登录成功后的处理"""
        home_window = HomeWindow(user_data)
        home_window.show()
    
    login_window.login_success.connect(on_login_success)
    login_window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
