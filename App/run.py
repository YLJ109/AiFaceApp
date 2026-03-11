"""
面部表情检测系统 - 主启动脚本
"""
import sys
import os

# 设置 Windows 应用程序 ID，确保任务栏图标正确显示
if sys.platform == 'win32':
    import ctypes
    # 设置环境变量，确保图标正确显示
    os.environ['QT_QPA_PLATFORM'] = 'windows:darkmode=0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('AiFaceApp.EmotionDetection.v1.0')

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
    
    # 设置应用图标 - 使用绝对路径
    icon_absolute_path = os.path.abspath(ICON_PATH)
    print(f"图标路径: {icon_absolute_path}")
    print(f"图标文件存在: {os.path.exists(icon_absolute_path)}")
    
    if os.path.exists(icon_absolute_path):
        app_icon = QIcon(icon_absolute_path)
        if not app_icon.isNull():
            app.setWindowIcon(app_icon)
            # 同时设置应用程序的图标，确保任务栏显示正确
            app.setApplicationDisplayName(APP_NAME)
            print("✅ 应用程序图标设置成功")
        else:
            print("❌ 图标加载失败：QIcon is null")
    else:
        print(f"❌ 图标文件不存在: {icon_absolute_path}")
    
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
