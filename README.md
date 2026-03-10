# 一零九面部表情检测系统

## 项目简介

一零九面部表情检测系统是一款基于人工智能技术的面部表情识别应用，能够实时检测和分析人脸表情，支持多种检测模式，包括摄像头实时检测、图片检测、批量图片检测和视频检测。

## 功能特性

- **摄像头实时检测**：实时从摄像头捕获画面并进行表情识别
- **图片检测**：上传单张图片进行表情分析
- **批量图片检测**：批量处理多张图片并保存结果
- **视频检测**：分析视频文件中的人脸表情
- **数据统计**：记录和统计检测数据，支持按日期和来源筛选
- **用户管理**：支持多用户登录，管理员可管理用户权限
- **系统设置**：可配置摄像头参数、检测设置等

## 系统要求

- Python 3.8+
- PyQt6
- OpenCV
- PyTorch
- NumPy
- PIL (Pillow)

## 安装说明

1. **克隆项目**

```bash
git clone https://github.com/YLJ109/AiFaceApp
cd AiFaceApp
```

2. **创建虚拟环境**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **安装依赖**

```bash
pip install -r App/requirements.txt
```

4. **运行应用**

```bash
python App/run.py
```

## 使用指南

### 登录系统
- 默认管理员账号：root
- 默认密码：123456

### 检测模式

1. **摄像头检测**
   - 点击左侧导航栏的"摄像头检测"选项
   - 系统会自动启动摄像头并开始实时检测
   - 点击"拍照"按钮可保存当前检测结果

2. **图片检测**
   - 点击左侧导航栏的"图片检测"选项
   - 点击"选择图片"按钮上传图片
   - 系统会自动分析图片中的人脸表情
   - 点击"保存图片"按钮可保存检测结果

3. **批量图片检测**
   - 点击左侧导航栏的"批量图片检测"选项
   - 点击"选择图片"或"选择文件夹"按钮
   - 选择保存目录
   - 点击"开始检测"按钮开始批量处理

4. **视频检测**
   - 点击左侧导航栏的"视频检测"选项
   - 点击"选择视频"按钮上传视频文件
   - 系统会播放视频并实时检测表情
   - 点击"拍照"按钮可保存当前帧的检测结果

### 数据统计
- 点击左侧导航栏的"数据统计"选项
- 可按日期范围和来源筛选数据
- 查看检测统计信息和详细数据表格

### 用户管理
- 管理员账号登录后，左侧导航栏会显示"用户管理"选项
- 可添加新用户、删除用户、修改用户权限
- 可将普通用户升级为管理员，或将管理员降级为普通用户

## 项目结构

```
AiFaceApp/
├── App/
│   ├── capture/          # 捕获的图片和视频
│   ├── code/             # 核心代码
│   │   ├── config.py     # 配置文件
│   │   ├── coreAlgorithm.py # 核心算法
│   │   └── settings_manager.py # 设置管理
│   ├── config/           # 配置文件
│   ├── data/             # 数据文件
│   ├── database/         # 数据库
│   ├── icons/            # 图标资源
│   ├── models/           # 模型文件
│   │   ├── deploy.prototxt
│   │   ├── pytorch_final_3060.pth
│   │   └── res10_300x300_ssd_iter_140000_fp16.caffemodel
│   ├── temp/             # 临时文件
│   ├── views/            # 界面文件
│   │   ├── page/         # 页面组件
│   │   ├── batchImageDetection.py # 批量图片检测
│   │   ├── cameraDetection.py # 摄像头检测
│   │   ├── imageDetection.py # 图片检测
│   │   ├── settings.py   # 系统设置
│   │   ├── statistics.py # 数据统计
│   │   ├── userManagement.py # 用户管理
│   │   └── videoDetection.py # 视频检测
│   ├── __init__.py
│   ├── requirements.txt  # 依赖文件
│   └── run.py            # 主启动脚本
└── README.md             # 项目说明文档
```

## 技术栈

- **前端**：PyQt6 (GUI界面)
- **后端**：Python
- **人脸检测**：OpenCV DNN (Caffe模型)
- **表情识别**：PyTorch (MobileNetV2模型)
- **数据库**：SQLite
- **图像处理**：OpenCV, PIL

## 模型说明

- **人脸检测模型**：res10_300x300_ssd_iter_140000_fp16.caffemodel
- **表情识别模型**：pytorch_final_3060.pth (基于MobileNetV2)
- **支持的表情**：愤怒、厌恶、恐惧、快乐、平静、悲伤、惊讶

## 配置说明

配置文件位于 `App/config/app_config.json`，可修改以下参数：

- `CAMERA_INDEX`：摄像头索引
- `CAMERA_WIDTH`：摄像头宽度
- `CAMERA_HEIGHT`：摄像头高度
- `FRAME_RATE`：帧率
- `SHOW_BOX`：是否显示人脸框
- `SHOW_LABEL`：是否显示标签
- `ENABLE_DETECTION`：是否启用检测
- `APP_WIDTH`：应用窗口宽度
- `APP_HEIGHT`：应用窗口高度
- `ICON_PATH`：图标路径

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题或建议，请联系项目维护者。