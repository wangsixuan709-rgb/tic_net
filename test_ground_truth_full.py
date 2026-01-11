#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试：模拟实际检测时加载Ground Truth的过程
"""

import sys
import os
import SimpleITK as sitk

# 确保在项目根目录
os.chdir('/home/yangao/LUNG/TiCNet')
sys.path.insert(0, '/home/yangao/LUNG/TiCNet')

from system.annotation_handler import AnnotationHandler

print("=" * 80)
print("完整Ground Truth加载测试")
print("=" * 80)

# 找一个最近上传的文件
uploads_dir = "uploads"
files = []
for filename in os.listdir(uploads_dir):
    if filename.endswith('.nrrd') or filename.endswith('.mhd'):
        file_path = os.path.join(uploads_dir, filename)
        if os.path.isfile(file_path):
            mtime = os.path.getmtime(file_path)
            files.append((mtime, file_path, filename))

files.sort(reverse=True)

if not files:
    print("❌ 没有找到测试文件")
    sys.exit(1)

# 使用最近的文件
_, test_file, test_filename = files[0]

print(f"\n测试文件: {test_filename}")
print(f"完整路径: {test_file}")

# 1. 读取图像信息
print("\n" + "=" * 80)
print("1. 读取图像信息")
print("=" * 80)

try:
    image = sitk.ReadImage(test_file)
    origin = image.GetOrigin()
    spacing = image.GetSpacing()
    size = image.GetSize()
    
    print(f"✅ 成功读取图像")
    print(f"   Size (SimpleITK格式):    {size}")
    print(f"   Origin:  {origin}")
    print(f"   Spacing: {spacing}")
    
    # 转换为NumPy格式的shape
    numpy_shape = (size[2], size[1], size[0])  # (z, y, x)
    print(f"   NumPy Shape (z,y,x):     {numpy_shape}")
    
except Exception as e:
    print(f"❌ 读取图像失败: {str(e)}")
    sys.exit(1)

# 2. 初始化AnnotationHandler并获取truth data
print("\n" + "=" * 80)
print("2. 获取Ground Truth数据")
print("=" * 80)

ann_handler = AnnotationHandler()

# 使用get_truth_data_for_image方法（这是实际检测时调用的）
truth_boxes, truth_labels = ann_handler.get_truth_data_for_image(
    test_file,
    spacing,
    origin,
    size  # SimpleITK格式 (x, y, z)
)

print(f"\n结果:")
print(f"   Truth Boxes数量: {len(truth_boxes)}")
print(f"   Truth Labels数量: {len(truth_labels)}")

if truth_boxes:
    print(f"\n✅ 成功创建Ground Truth boxes:")
    for i, (box, label) in enumerate(zip(truth_boxes, truth_labels), 1):
        print(f"\n   Box {i}:")
        print(f"      [x_min, y_min, z_min, x_max, y_max, z_max]")
        print(f"      [{box[0]:.1f}, {box[1]:.1f}, {box[2]:.1f}, {box[3]:.1f}, {box[4]:.1f}, {box[5]:.1f}]")
        print(f"      Label: {label}")
        
        # 计算中心点和尺寸
        center_x = (box[0] + box[3]) / 2
        center_y = (box[1] + box[4]) / 2
        center_z = (box[2] + box[5]) / 2
        width = box[3] - box[0]
        height = box[4] - box[1]
        depth = box[5] - box[2]
        
        print(f"      中心点: ({center_x:.1f}, {center_y:.1f}, {center_z:.1f})")
        print(f"      尺寸: {width:.1f} × {height:.1f} × {depth:.1f}")
else:
    print(f"\n❌ 未创建任何Ground Truth boxes")
    print(f"\n可能的原因：")
    print(f"   1. 文件的SeriesUID无法提取")
    print(f"   2. annotations.csv中没有该SeriesUID的记录")
    print(f"   3. 坐标转换后超出了图像范围")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

