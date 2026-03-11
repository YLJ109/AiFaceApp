#!/usr/bin/env python3
"""
模型测试结果可视化脚本
生成表情识别准确率的折线图
"""

import matplotlib.pyplot as plt
import numpy as np
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 模型测试数据
emotions = ['愤怒', '厌恶', '恐惧', '快乐', '平静', '悲伤', '惊讶']
accuracy = [0.7568, 0.9628, 0.7086, 0.9399, 0.8028, 0.7429, 0.8936]
sample_counts = [1184, 1184, 1184, 2279, 1633, 1307, 1184]

# 颜色设置
colors = ['#FF6B6B', '#FFA500', '#9370DB', '#32CD32', '#808080', '#1E90FF', '#00FFFF']

# 创建图表
plt.figure(figsize=(12, 6))

# 绘制准确率折线图
plt.subplot(1, 2, 1)
plt.plot(emotions, accuracy, marker='o', linestyle='-', linewidth=2, color='#4CAF50')
plt.fill_between(emotions, accuracy, alpha=0.2, color='#4CAF50')

# 添加数据标签
for i, (emotion, acc) in enumerate(zip(emotions, accuracy)):
    plt.text(i, acc + 0.01, f'{acc*100:.1f}%', ha='center', va='bottom', fontsize=10)

plt.title('各表情识别准确率', fontsize=14, fontweight='bold')
plt.xlabel('表情', fontsize=12)
plt.ylabel('准确率', fontsize=12)
plt.ylim(0.6, 1.0)
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', alpha=0.3)

# 绘制样本数量条形图
plt.subplot(1, 2, 2)
bars = plt.bar(emotions, sample_counts, color=colors)

# 添加数据标签
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, height + 50, f'{height}', ha='center', va='bottom', fontsize=10)

plt.title('各表情样本数量', fontsize=14, fontweight='bold')
plt.xlabel('表情', fontsize=12)
plt.ylabel('样本数量', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', alpha=0.3)

# 调整布局
plt.tight_layout()

# 保存图表
save_dir = 'visualization'
os.makedirs(save_dir, exist_ok=True)
save_path = os.path.join(save_dir, 'model_accuracy.png')
plt.savefig(save_path, dpi=300, bbox_inches='tight')

# 显示图表
plt.show()

print(f"图表已保存到: {save_path}")
print("\n模型测试结果摘要:")
print("=" * 60)
print(f"总体准确率: {np.mean(accuracy):.4f} ({np.mean(accuracy)*100:.1f}%)")
print(f"最高准确率: {max(accuracy):.4f} ({max(accuracy)*100:.1f}%) - {emotions[accuracy.index(max(accuracy))]}")
print(f"最低准确率: {min(accuracy):.4f} ({min(accuracy)*100:.1f}%) - {emotions[accuracy.index(min(accuracy))]}")
print(f"平均样本数: {np.mean(sample_counts):.1f}")
print(f"总样本数: {sum(sample_counts)}")
print("=" * 60)
