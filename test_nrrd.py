#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NRRD文件读取测试工具
用于验证系统对NRRD文件的支持
"""

import os
import sys
import numpy as np
from pathlib import Path

def test_nrrd_reading(file_path):
    """测试NRRD文件读取"""
    print(f"测试NRRD文件: {file_path}")
    print("=" * 50)
    
    if not os.path.exists(file_path):
        print("❌ 文件不存在")
        return False
    
    # 方法1: 使用SimpleITK
    print("方法1: 使用SimpleITK读取")
    try:
        import SimpleITK as sitk
        image = sitk.ReadImage(file_path)
        image_array = sitk.GetArrayFromImage(image)
        spacing = image.GetSpacing()
        origin = image.GetOrigin()
        direction = image.GetDirection()
        
        print(f"✅ SimpleITK读取成功")
        print(f"   图像尺寸: {image_array.shape}")
        print(f"   数据类型: {image_array.dtype}")
        print(f"   像素间距: {spacing}")
        print(f"   原点位置: {origin}")
        print(f"   数值范围: [{image_array.min():.2f}, {image_array.max():.2f}]")
        
    except Exception as e:
        print(f"❌ SimpleITK读取失败: {str(e)}")
    
    print()
    
    # 方法2: 使用pynrrd
    print("方法2: 使用pynrrd读取")
    try:
        import nrrd
        data, header = nrrd.read(file_path)
        
        print(f"✅ pynrrd读取成功")
        print(f"   图像尺寸: {data.shape}")
        print(f"   数据类型: {data.dtype}")
        print(f"   数值范围: [{data.min():.2f}, {data.max():.2f}]")
        
        print(f"\n   NRRD Header信息:")
        for key, value in header.items():
            if isinstance(value, (str, int, float)):
                print(f"   {key}: {value}")
            elif isinstance(value, (list, tuple, np.ndarray)):
                if len(str(value)) < 100:
                    print(f"   {key}: {value}")
                else:
                    print(f"   {key}: {type(value)} (长度: {len(value)})")
        
    except ImportError:
        print("⚠️  pynrrd未安装")
        print("   安装命令: pip install pynrrd")
    except Exception as e:
        print(f"❌ pynrrd读取失败: {str(e)}")
    
    print()
    
    # 方法3: 使用系统工具函数
    print("方法3: 使用系统工具函数读取")
    try:
        sys.path.append('.')
        from system.utils import load_medical_image
        
        image_array, meta_info = load_medical_image(file_path)
        
        print(f"✅ 系统工具函数读取成功")
        print(f"   图像尺寸: {image_array.shape}")
        print(f"   数据类型: {image_array.dtype}")
        print(f"   元信息: {meta_info}")
        
    except Exception as e:
        print(f"❌ 系统工具函数读取失败: {str(e)}")
    
    return True

def main():
    if len(sys.argv) != 2:
        print("用法: python test_nrrd.py <nrrd文件路径>")
        print("示例: python test_nrrd.py sample.nrrd")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print("NRRD文件读取测试工具")
    print("=" * 50)
    print(f"目标文件: {file_path}")
    print()
    
    # 检查依赖
    print("检查依赖包:")
    try:
        import SimpleITK
        print("✅ SimpleITK")
    except ImportError:
        print("❌ SimpleITK (必需)")
    
    try:
        import nrrd
        print("✅ pynrrd")
    except ImportError:
        print("⚠️  pynrrd (可选，建议安装)")
    
    print()
    
    # 测试读取
    test_nrrd_reading(file_path)

if __name__ == '__main__':
    main() 