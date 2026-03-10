import os
import random
import shutil

# ===================== 关键修改：用绝对路径 =====================
# 替换成你实际的数据集train文件夹路径（复制你电脑里的真实路径）
source_dir = r"D:\front-back\AiFaceApp\7emotions_96x96_mobilenetv2_3060_train\dataset\train"
# val文件夹会自动创建在dataset目录下
target_dir = r"D:\front-back\AiFaceApp\7emotions_96x96_mobilenetv2_3060_train\dataset\val"

split_ratio = 0.2  # 20% 数据作为验证集
random.seed(42)    # 固定随机种子，确保每次划分结果一致

# 检查源文件夹是否存在（新增：避免路径错了还继续运行）
if not os.path.exists(source_dir):
    print(f"错误：源文件夹不存在 → {source_dir}")
    print("请检查路径是否正确，比如：")
    print("1. 确认dataset/train文件夹是否存在")
    print("2. 确认路径里的文件夹名没有拼写错误（比如大小写、下划线）")
    exit(1)

# 获取所有表情类别文件夹
classes = [d for d in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, d))]
if not classes:
    print("错误：源文件夹下没有找到表情类别子文件夹（如angry、happy等）")
    exit(1)

# 遍历每个类别，划分数据
for cls in classes:
    cls_source = os.path.join(source_dir, cls)
    cls_target = os.path.join(target_dir, cls)
    
    # 自动创建val下的类别文件夹（不存在则创建）
    os.makedirs(cls_target, exist_ok=True)
    
    # 获取该类别下所有图片文件（只处理常见图片格式）
    all_files = [
        f for f in os.listdir(cls_source) 
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))
    ]
    
    if len(all_files) == 0:
        print(f"警告：{cls} 文件夹下没有图片文件，跳过")
        continue
    
    # 打乱文件顺序（保证随机划分）
    random.shuffle(all_files)
    
    # 计算验证集数量
    val_count = int(len(all_files) * split_ratio)
    # 至少保证每个类别有1张验证集图片（避免val_count=0）
    val_count = max(val_count, 1)
    
    # 移动验证集图片到val文件夹
    val_files = all_files[:val_count]
    for file_name in val_files:
        src_path = os.path.join(cls_source, file_name)
        dst_path = os.path.join(cls_target, file_name)
        # 用copy2保留文件属性，避免误删（如果想移动用shutil.move）
        shutil.copy2(src_path, dst_path)
        print(f"复制：{src_path} → {dst_path}")
    
    print(f"✅ {cls} 类划分完成：训练集{len(all_files)-val_count}张，验证集{val_count}张")

print("\n🎉 所有类别数据划分完成！")
print(f"验证集保存路径：{target_dir}")