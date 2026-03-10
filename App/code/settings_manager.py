"""
设置管理器 - 管理设置变更和通知
"""
from PyQt6.QtCore import QObject, pyqtSignal

class SettingsManager(QObject):
    """设置管理器"""
    
    # 定义设置变更信号
    camera_settings_changed = pyqtSignal()
    display_settings_changed = pyqtSignal()
    interface_settings_changed = pyqtSignal()
    face_settings_changed = pyqtSignal()
    all_settings_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._instance = None
    
    @classmethod
    def instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def notify_camera_settings_changed(self):
        """通知摄像头设置变更"""
        self.camera_settings_changed.emit()
        self.all_settings_changed.emit()
    
    def notify_display_settings_changed(self):
        """通知显示设置变更"""
        self.display_settings_changed.emit()
        self.all_settings_changed.emit()
    
    def notify_interface_settings_changed(self):
        """通知界面设置变更"""
        self.interface_settings_changed.emit()
        self.all_settings_changed.emit()
    
    def notify_face_settings_changed(self):
        """通知多个人脸设置变更"""
        self.face_settings_changed.emit()
        self.all_settings_changed.emit()
    
    def notify_all_settings_changed(self):
        """通知所有设置变更"""
        self.all_settings_changed.emit()

# 创建全局设置管理器实例
settings_manager = SettingsManager()