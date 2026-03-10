"""
PyTorch GPU 训练 - RTX 3060 6G 极速版
优化：大 Batch + cuDNN 加速 + 混合精度
预计每轮 30-40 秒，总训练时间 25-35 分钟
"""

import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import transforms, models
from torchvision.datasets import ImageFolder
import time
from tqdm import tqdm

print("=" * 60)
print("🚀 PyTorch GPU 训练 - RTX 3060 6G 极速版")
print("=" * 60)

# GPU 配置
if torch.cuda.is_available():
    device = torch.device('cuda')
    print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
    print(f"   CUDA: {torch.version.cuda}")
    print(f"   显存：{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    
    # 3060 6G 优化配置
    torch.backends.cudnn.benchmark = True  # cuDNN 加速
    torch.backends.cudnn.deterministic = False  # 非确定性模式（更快）
    
    use_amp = True
    print("✅ 混合精度：已启用")
    print("✅ cuDNN 加速：已启用")
    print("✅ 优化模式：性能优先")
else:
    device = torch.device('cpu')
    print("❌ 使用 CPU")
    use_amp = False

# 路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "dataset")
TRAIN_DIR = os.path.join(DATA_DIR, "train")
VAL_DIR = os.path.join(DATA_DIR, "val")
MODEL_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(MODEL_DIR, exist_ok=True)

# 3060 6G 优化超参数
IMG_SIZE = 96
BATCH_SIZE = 128  # 3060 6G 最优 batch
NUM_CLASSES = 7
EPOCHS = 50
LEARNING_RATE = 0.001
NUM_WORKERS = 0  # Windows 单进程

print(f"\n📋 3060 6G 优化配置:")
print(f"   图像：{IMG_SIZE}x{IMG_SIZE}")
print(f"   Batch Size: {BATCH_SIZE} (GPU 优化)")
print(f"   Epochs: {EPOCHS}")
print(f"   Learning Rate: {LEARNING_RATE}")
print(f"   预计每轮：~30-40 秒")
print(f"   预计总时间：25-35 分钟")

# 数据加载
print("\n🔄 加载数据...")
train_transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(10),
    transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])

val_transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])

train_dataset = ImageFolder(TRAIN_DIR, transform=train_transform)
val_dataset = ImageFolder(VAL_DIR, transform=val_transform)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, 
                          num_workers=NUM_WORKERS, pin_memory=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, 
                        num_workers=NUM_WORKERS, pin_memory=True)

print(f"✓ 训练集：{len(train_dataset)} 张")
print(f"✓ 验证集：{len(val_dataset)} 张")
print(f"✓ 每轮批次：{len(train_loader)} (优化后)")

# 构建模型（3060 优化版）
print("\n🏗️ 构建模型...")

class EmotionClassifier(nn.Module):
    def __init__(self, num_classes=7):
        super().__init__()
        # 使用预训练 MobileNetV2
        self.backbone = models.mobilenet_v2(weights=None)
        num_features = self.backbone.classifier[1].in_features
        # 修改第一个卷积层适配灰度图
        self.backbone.features[0][0] = nn.Conv2d(1, 32, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1), bias=False)
        self.backbone.classifier = nn.Sequential(nn.Dropout(p=0.2), nn.Linear(num_features, num_classes))
    
    def forward(self, x):
        return self.backbone(x)

model = EmotionClassifier(num_classes=NUM_CLASSES).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)  # 权重衰减防过拟合
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-6)  # 更好的学习率调度

print(f"✓ 模型参数量：{sum(p.numel() for p in model.parameters()):,}")
print(f"✓ 优化器：Adam + 权重衰减")
print(f"✓ 学习率调度：CosineAnnealing")

# 训练函数（优化版）
def train_epoch(model, loader, criterion, optimizer, device, use_amp, epoch, total_epochs):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    scaler = torch.amp.GradScaler('cuda') if use_amp else None
    
    pbar = tqdm(enumerate(loader), total=len(loader), 
                desc=f'Epoch {epoch}/{total_epochs}',
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]')
    
    for i, (inputs, labels) in pbar:
        inputs, labels = inputs.to(device, non_blocking=True), labels.to(device, non_blocking=True)  # 异步传输
        optimizer.zero_grad()
        
        if use_amp:
            with torch.amp.autocast('cuda'):
                outputs = model(inputs)
                loss = criterion(outputs, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
        
        running_loss += loss.item() * inputs.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        current_loss = running_loss / total
        current_acc = correct / total
        pbar.set_postfix({'loss': f'{current_loss:.4f}', 'acc': f'{current_acc:.4f}'})
    
    return running_loss / total, correct / total

# 验证函数
def validate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for inputs, labels in loader:
            inputs, labels = inputs.to(device, non_blocking=True), labels.to(device, non_blocking=True)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            running_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    
    return running_loss / total, correct / total

# 主训练循环
def main():
    print("\n🚀 开始训练...")
    print("=" * 60)
    
    best_val_acc = 0.0
    patience_counter = 0
    max_patience = 10  # 增加耐心
    
    for epoch in range(1, EPOCHS + 1):
        epoch_start = time.time()
        
        # 训练
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, device, use_amp, epoch, EPOCHS
        )
        
        # 验证
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        epoch_time = time.time() - epoch_start
        
        # 显示结果
        print(f"\n✅ Epoch {epoch}/{EPOCHS} | 耗时：{epoch_time:.1f}s | 速度：{len(train_loader)/epoch_time:.1f} batch/s")
        print(f"   训练集 - Loss: {train_loss:.4f}, 准确率：{train_acc:.4f}")
        print(f"   验证集 - Loss: {val_loss:.4f}, 准确率：{val_acc:.4f}")
        
        # 学习率调整（CosineAnnealing）
        scheduler.step()
        current_lr = scheduler.get_last_lr()[0]
        print(f"   当前学习率：{current_lr:.6f}")
        
        # 保存最佳模型
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
            }, os.path.join(MODEL_DIR, 'pytorch_best_3060.pth'))
            print(f"   ⭐ 新纪录！保存最佳模型 (准确率：{val_acc:.4f})")
            patience_counter = 0
        else:
            patience_counter += 1
            print(f"   未提升 ({patience_counter}/{max_patience})")
        
        # 早停
        if patience_counter >= max_patience:
            print(f"\n⚠️  触发早停机制（{max_patience} 轮未提升）")
            break
    
    # 保存最终模型
    print("\n💾 保存模型...")
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'val_acc': best_val_acc,
    }, os.path.join(MODEL_DIR, 'pytorch_final_3060.pth'))
    
    print(f"✓ 最佳模型：{os.path.join(MODEL_DIR, 'pytorch_best_3060.pth')}")
    print(f"✓ 最终模型：{os.path.join(MODEL_DIR, 'pytorch_final_3060.pth')}")
    
    print("\n" + "=" * 60)
    print("📊 训练总结")
    print("=" * 60)
    print(f"✅ 最佳验证集准确率：{best_val_acc:.4f} ({best_val_acc*100:.2f}%)")
    print(f"✅ 设备：{device}")
    if device.type == 'cuda':
        print(f"✅ GPU 加速：已启用 (RTX 3060 6G)")
        print(f"✅ 混合精度：已启用")
        print(f"✅ cuDNN 加速：已启用")
        print(f"✅ Batch Size: {BATCH_SIZE}")
    
    print("\n🎉 PyTorch GPU 训练完成！")
    print("=" * 60)

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
