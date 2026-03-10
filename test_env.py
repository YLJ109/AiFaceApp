"""
系统测试脚本
"""
import sys

print("=" * 60)
print("🧪 面部表情检测系统 - 环境测试")
print("=" * 60)

# 测试 1: Python 版本
print("\n[1/6] 检查 Python 版本...")
print(f"✅ Python {sys.version}")

# 测试 2: PyQt6
print("\n[2/6] 检查 PyQt6...")
try:
    from PyQt6.QtWidgets import QApplication
    print("✅ PyQt6 已安装")
except ImportError as e:
    print(f"❌ PyQt6 未安装：{e}")
    sys.exit(1)

# 测试 3: PyTorch
print("\n[3/6] 检查 PyTorch...")
try:
    import torch
    print(f"✅ PyTorch {torch.__version__}")
    if torch.cuda.is_available():
        print(f"   ✅ CUDA 可用：{torch.cuda.get_device_name(0)}")
    else:
        print("   ⚠️  CPU 模式")
except Exception as e:
    print(f"❌ PyTorch 错误：{e}")

# 测试 4: OpenCV
print("\n[4/6] 检查 OpenCV...")
try:
    import cv2
    print(f"✅ OpenCV {cv2.__version__}")
except Exception as e:
    print(f"❌ OpenCV 错误：{e}")

# 测试 5: 数据库初始化
print("\n[5/6] 初始化数据库...")
try:
    from App.database.user import UserDatabase
    db = UserDatabase()
    print("✅ 数据库初始化成功")
except Exception as e:
    print(f"❌ 数据库错误：{e}")

# 测试 6: 模型文件检查
print("\n[6/6] 检查模型文件...")
try:
    import os
    from App.code.config import MODEL_PATH
    if os.path.exists(MODEL_PATH):
        print(f"✅ 模型文件存在：{MODEL_PATH}")
    else:
        print(f"⚠️  模型文件不存在：{MODEL_PATH}")
except Exception as e:
    print(f"❌ 配置错误：{e}")

print("\n" + "=" * 60)
print("✅ 环境检查完成！")
print("=" * 60)
print("\n提示：")
print("- 默认管理员账号：root / 123456")
print("- 运行 'python App\\code\\main.py' 启动系统")
print("=" * 60)
