#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试：检查标注文件是否能正确加载
"""

import sys
import os

# 确保在项目根目录
os.chdir('/home/yangao/LUNG/TiCNet')
sys.path.insert(0, '/home/yangao/LUNG/TiCNet')

from system.annotation_handler import AnnotationHandler

print("=" * 80)
print("测试标注文件加载")
print("=" * 80)

# 初始化AnnotationHandler
print("\n1. 初始化AnnotationHandler...")
ann_handler = AnnotationHandler()

print("\n2. 检查标注文件加载情况...")
if ann_handler.annotations_df is not None:
    print(f"   ✅ 成功加载 annotations.csv")
    print(f"   记录数: {len(ann_handler.annotations_df)}")
    print(f"   列名: {list(ann_handler.annotations_df.columns)}")
else:
    print(f"   ❌ 未能加载 annotations.csv")
    print(f"   路径: {ann_handler.annotations_path}")
    print(f"   文件存在: {os.path.exists(ann_handler.annotations_path)}")

if ann_handler.seriesuids_list is not None:
    print(f"\n   ✅ 成功加载 seriesuids.csv")
    print(f"   SeriesUID数量: {len(ann_handler.seriesuids_list)}")
else:
    print(f"\n   ❌ 未能加载 seriesuids.csv")

# 测试特定SeriesUID
test_seriesuid = "1.3.6.1.4.1.14519.5.2.1.6279.6001.997611074084993415992563148335"

print(f"\n3. 测试查找特定SeriesUID的标注...")
print(f"   SeriesUID: {test_seriesuid}")

annotations = ann_handler.get_annotations_for_seriesuid(test_seriesuid)

if annotations:
    print(f"   ✅ 找到 {len(annotations)} 个标注")
    for i, ann in enumerate(annotations, 1):
        print(f"\n   结节 {i}:")
        print(f"      世界坐标: ({ann['coordX']:.2f}, {ann['coordY']:.2f}, {ann['coordZ']:.2f})")
        print(f"      直径: {ann['diameter_mm']:.2f} mm")
else:
    print(f"   ❌ 未找到标注")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

