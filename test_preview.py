#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试NRRD文件预览功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from system.visualization import ResultVisualizer
from system.config import SystemConfig
import uuid

def test_preview(nrrd_file_path):
    """测试预览功能
    
    Args:
        nrrd_file_path: NRRD文件路径
    """
    print("=" * 60)
    print("测试NRRD文件预览功能")
    print("=" * 60)
    
    # 检查文件是否存在
    if not os.path.exists(nrrd_file_path):
        print(f"❌ 错误：文件不存在 - {nrrd_file_path}")
        return False
    
    print(f"✅ 找到文件: {nrrd_file_path}")
    print(f"   文件大小: {os.path.getsize(nrrd_file_path) / (1024*1024):.2f} MB")
    
    try:
        # 初始化配置和可视化器
        config = SystemConfig()
        visualizer = ResultVisualizer(config)
        
        # 生成唯一任务ID
        task_id = str(uuid.uuid4())
        print(f"\n生成任务ID: {task_id}")
        
        # 创建预览图像
        print("\n开始生成预览图像...")
        preview_path = visualizer.create_preview(nrrd_file_path, task_id)
        
        if preview_path:
            full_path = os.path.join(config.VISUALIZATION_FOLDER, preview_path)
            print(f"✅ 预览图像生成成功!")
            print(f"   保存路径: {full_path}")
            print(f"   文件大小: {os.path.getsize(full_path) / 1024:.2f} KB")
            
            # 尝试打开图像查看
            try:
                from PIL import Image
                img = Image.open(full_path)
                print(f"   图像尺寸: {img.size[0]} x {img.size[1]} 像素")
                print("\n提示: 您可以在以下位置查看预览图像:")
                print(f"   {full_path}")
            except Exception as e:
                print(f"   注意: 无法自动打开图像 - {str(e)}")
            
            return True
        else:
            print("❌ 预览图像生成失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print(f"  python {sys.argv[0]} <nrrd文件路径>")
        print("\n示例:")
        print(f"  python {sys.argv[0]} data/sample.nrrd")
        sys.exit(1)
    
    nrrd_file = sys.argv[1]
    success = test_preview(nrrd_file)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 测试通过！预览功能正常工作")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ 测试失败")
        print("=" * 60)
        sys.exit(1)

if __name__ == '__main__':
    main()

