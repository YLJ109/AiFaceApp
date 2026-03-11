"""
配置文件
"""
import os
import json

# 获取App目录的绝对路径
APP_DIR = os.path.dirname(os.path.dirname(__file__))

# 应用信息
APP_NAME = "一零九表情智能检测系统"
APP_VERSION = "1.0.0"
APP_WIDTH = 1280
APP_HEIGHT = 720

# 模型配置
MODEL_PATH = os.path.join(APP_DIR, 'models', 'pytorch_final_3060.pth')
IMAGE_SIZE = 96
EMOTION_CLASSES = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
MODEL_INPUT_CHANNELS = 1
MODEL_NUM_CLASSES = 7
MODEL_BACKBONE = "mobilenet_v2"

# 中英文表情映射
EMOTION_CHINESE = {
    'angry': '愤怒',
    'disgust': '厌恶',
    'fear': '恐惧',
    'happy': '快乐',
    'neutral': '平静',
    'sad': '悲伤',
    'surprise': '惊讶'
}

# 颜色配置 (BGR)
EMOTION_COLORS = {
    'angry': (0, 0, 255),      # 红色
    'disgust': (0, 165, 255),  # 橙色
    'fear': (128, 0, 128),     # 紫色
    'happy': (0, 255, 0),      # 绿色
    'neutral': (255, 255, 255),# 白色
    'sad': (255, 0, 0),        # 蓝色
    'surprise': (255, 255, 0)  # 青色
}

# 摄像头配置
CAMERA_INDEX = 0  # 优先使用默认摄像头
CAMERA_WIDTH = 320  # 降低分辨率提高性能
CAMERA_HEIGHT = 240
FRAME_RATE = 20  # 降低帧率减少计算负担

# 显示配置
SHOW_BOX = True
SHOW_LABEL = True
ENABLE_DETECTION = True

# 多人脸配置
MAX_FACES = 5

# 数据库配置
DB_PATH = os.path.join(APP_DIR, 'database', 'app.db')
DB_TYPE = 'sqlite'  # 数据库类型：sqlite, mysql, postgresql等

# 默认管理员账户（首次启动时创建）
DEFAULT_ADMIN = {
    'username': 'root',
    'password': '123456',
    'email': 'admin@system.com'
}

# MySQL/PostgreSQL 数据库配置（如果使用）
DB_HOST = 'localhost'
DB_PORT = 3306
DB_NAME = 'aifaceapp'
DB_USER = 'root'
DB_PASSWORD = 'password'

# 日志配置
LOG_DIR = os.path.join(APP_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 截图保存目录
SCREENSHOT_DIR = os.path.join(APP_DIR, 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# 视频处理临时目录
TEMP_DIR = os.path.join(APP_DIR, 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)

# 配置文件路径
CONFIG_FILE = os.path.join(APP_DIR, 'config', 'app_config.json')

# 图标配置
ICON_PATH = os.path.join(APP_DIR, 'icons', 'logo.png')

# 设备设置
USE_CUDA = True  # 是否使用CUDA

def save_config():
    """保存配置到JSON文件"""
    config_data = {
        'CAMERA_INDEX': CAMERA_INDEX,
        'CAMERA_WIDTH': CAMERA_WIDTH,
        'CAMERA_HEIGHT': CAMERA_HEIGHT,
        'FRAME_RATE': FRAME_RATE,
        'SHOW_BOX': SHOW_BOX,
        'SHOW_LABEL': SHOW_LABEL,
        'ENABLE_DETECTION': ENABLE_DETECTION,
        'APP_WIDTH': APP_WIDTH,
        'APP_HEIGHT': APP_HEIGHT,
        'ICON_PATH': 'icons/logo.png',
        'USE_CUDA': USE_CUDA,
        'DEFAULT_ADMIN': DEFAULT_ADMIN,
        'DB_TYPE': DB_TYPE,
        'DB_HOST': DB_HOST,
        'DB_PORT': DB_PORT,
        'DB_NAME': DB_NAME,
        'DB_USER': DB_USER,
        'DB_PASSWORD': DB_PASSWORD
    }
    
    try:
        # 确保配置目录存在
        config_dir = os.path.dirname(CONFIG_FILE)
        os.makedirs(config_dir, exist_ok=True)
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        
        print(f"✅ 配置已保存到: {CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")
        return False

def load_config():
    """从JSON文件加载配置"""
    global CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, FRAME_RATE
    global SHOW_BOX, SHOW_LABEL, ENABLE_DETECTION
    global APP_WIDTH, APP_HEIGHT
    global ICON_PATH
    global USE_CUDA
    global DEFAULT_ADMIN
    global DB_TYPE, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 更新配置变量
            if 'CAMERA_INDEX' in config_data:
                CAMERA_INDEX = config_data['CAMERA_INDEX']
            if 'CAMERA_WIDTH' in config_data:
                CAMERA_WIDTH = config_data['CAMERA_WIDTH']
            if 'CAMERA_HEIGHT' in config_data:
                CAMERA_HEIGHT = config_data['CAMERA_HEIGHT']
            if 'FRAME_RATE' in config_data:
                FRAME_RATE = config_data['FRAME_RATE']
            if 'SHOW_BOX' in config_data:
                SHOW_BOX = config_data['SHOW_BOX']
            if 'SHOW_LABEL' in config_data:
                SHOW_LABEL = config_data['SHOW_LABEL']
            if 'ENABLE_DETECTION' in config_data:
                ENABLE_DETECTION = config_data['ENABLE_DETECTION']
            if 'APP_WIDTH' in config_data:
                APP_WIDTH = config_data['APP_WIDTH']
            if 'APP_HEIGHT' in config_data:
                APP_HEIGHT = config_data['APP_HEIGHT']
            if 'ICON_PATH' in config_data:
                # 使用APP_DIR构建完整路径
                ICON_PATH = os.path.join(APP_DIR, config_data['ICON_PATH'])
            if 'USE_CUDA' in config_data:
                USE_CUDA = config_data['USE_CUDA']
            if 'DEFAULT_ADMIN' in config_data:
                DEFAULT_ADMIN = config_data['DEFAULT_ADMIN']
            if 'DB_TYPE' in config_data:
                DB_TYPE = config_data['DB_TYPE']
            if 'DB_HOST' in config_data:
                DB_HOST = config_data['DB_HOST']
            if 'DB_PORT' in config_data:
                DB_PORT = config_data['DB_PORT']
            if 'DB_NAME' in config_data:
                DB_NAME = config_data['DB_NAME']
            if 'DB_USER' in config_data:
                DB_USER = config_data['DB_USER']
            if 'DB_PASSWORD' in config_data:
                DB_PASSWORD = config_data['DB_PASSWORD']
            
            print(f"✅ 配置已从 {CONFIG_FILE} 加载")
            return True
        else:
            print(f"ℹ️ 配置文件不存在，使用默认配置: {CONFIG_FILE}")
            return False
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return False

# 应用启动时自动加载配置
load_config()
