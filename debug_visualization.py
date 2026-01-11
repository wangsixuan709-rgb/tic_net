#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化调试工具
用于测试和调试图像加载与可视化生成
"""

import sys
import os
import traceback
from pathlib import Path

# 添加项目路径
sys.path.append('.')

from system.config import SystemConfig
from system.visualization import ResultVisualizer

def debug_visualization(image_path: str):
    """调试可视化功能"""
    print("=" * 60)
    print("可视化调试工具")
    print("=" * 60)
    
    try:
        # 检查文件是否存在
        if not os.path.exists(image_path):
            print(f"❌ 文件不存在: {image_path}")
            return False
        
        print(f"✅ 文件存在: {image_path}")
        print(f"文件大小: {os.path.getsize(image_path) / (1024*1024):.2f} MB")
        
        # 初始化配置和可视化器
        config = SystemConfig()
        visualizer = ResultVisualizer(config)
        
        print("\n测试图像加载...")
        
        # 测试图像加载
        try:
            image_data = visualizer._load_image(image_path)
            print(f"✅ 图像加载成功")
            print(f"图像形状: {image_data.shape}")
            print(f"数据类型: {image_data.dtype}")
            print(f"数值范围: [{image_data.min()}, {image_data.max()}]")
        except Exception as e:
            print(f"❌ 图像加载失败: {str(e)}")
            traceback.print_exc()
            return False
        
        print("\n测试可视化生成...")
        
        # 创建模拟检测结果
        detections = [
            {
                'bbox': [100, 100, 30, 120, 120, 35],
                'confidence': 0.85,
                'class': 'nodule',
                'volume': 1000.0,
                'center': [110, 110, 32],
                'size': [20, 20, 5]
            },
            {
                'bbox': [200, 150, 40, 220, 170, 45], 
                'confidence': 0.65,
                'class': 'nodule',
                'volume': 800.0,
                'center': [210, 160, 42],
                'size': [20, 20, 5]
            }
        ]
        
        statistics = {
            'total_detections': len(detections),
            'high_confidence_count': 1,
            'medium_confidence_count': 1,
            'low_confidence_count': 0,
            'average_confidence': 0.75
        }
        
        results = {
            'detections': detections,
            'statistics': statistics
        }
        
        # 测试可视化创建
        task_id = "debug_test"
        try:
            visualization_paths = visualizer.create_visualizations(
                image_path, results, task_id
            )
            
            print(f"✅ 可视化生成成功")
            for viz_type, path in visualization_paths.items():
                full_path = os.path.join(config.VISUALIZATION_FOLDER, path)
                if os.path.exists(full_path):
                    print(f"  ✅ {viz_type}: {path} ({os.path.getsize(full_path)} bytes)")
                else:
                    print(f"  ❌ {viz_type}: {path} (文件未生成)")
                    
        except Exception as e:
            print(f"❌ 可视化生成失败: {str(e)}")
            traceback.print_exc()
            return False
        
        print("\n🎉 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 调试失败: {str(e)}")
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) != 2:
        print("用法: python debug_visualization.py <图像文件路径>")
        print("示例: python debug_visualization.py test.nrrd")
        sys.exit(1)
    
    image_path = sys.argv[1]
    success = debug_visualization(image_path)
    
    if success:
        print("\n✅ 可视化调试成功！")
        sys.exit(0)
    else:
        print("\n❌ 可视化调试失败！")
        sys.exit(1)

if __name__ == '__main__':
    main() 