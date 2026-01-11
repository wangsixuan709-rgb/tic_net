#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型文件完整性检查工具
用于检查哪些权重文件可以正常加载
"""

import os
import sys
from pathlib import Path

def test_model_file(model_path):
    """测试单个模型文件是否可以加载"""
    print(f"\n测试文件: {model_path}")
    
    # 检查文件大小
    try:
        file_size = os.path.getsize(model_path) / (1024 * 1024)
        print(f"  文件大小: {file_size:.1f} MB")
    except Exception as e:
        print(f"  ❌ 无法获取文件大小: {str(e)}")
        return False
    
    # 检查文件是否为空
    if file_size < 1:
        print(f"  ❌ 文件太小，可能损坏")
        return False
    
    # 尝试作为二进制文件读取前几个字节
    try:
        with open(model_path, 'rb') as f:
            header = f.read(16)
            print(f"  文件头: {header.hex()}")
            
            # PyTorch文件通常以PK开头（ZIP格式）
            if header.startswith(b'PK'):
                print(f"  ✅ 文件格式正确 (ZIP/PyTorch)")
            else:
                print(f"  ⚠️  文件格式异常")
                return False
                
    except Exception as e:
        print(f"  ❌ 无法读取文件: {str(e)}")
        return False
    
    # 尝试用PyTorch加载（如果可用）
    try:
        # 只做基本导入测试，不实际加载
        print(f"  📦 尝试PyTorch格式验证...")
        
        # 简单的ZIP完整性检查
        import zipfile
        with zipfile.ZipFile(model_path, 'r') as zip_file:
            zip_file.testzip()
        print(f"  ✅ ZIP文件完整性检查通过")
        return True
        
    except zipfile.BadZipFile:
        print(f"  ❌ ZIP文件损坏")
        return False
    except Exception as e:
        print(f"  ⚠️  其他错误: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("TiCNet 模型文件完整性检查")
    print("=" * 60)
    
    # 检查模型目录
    model_dir = Path('results/ticnet/2_fold/model')
    
    if not model_dir.exists():
        print(f"❌ 模型目录不存在: {model_dir}")
        return
    
    pth_files = list(model_dir.glob('*.pth'))
    if not pth_files:
        print(f"❌ 没有找到.pth文件")
        return
    
    print(f"找到 {len(pth_files)} 个模型文件")
    
    good_files = []
    bad_files = []
    
    for pth_file in sorted(pth_files):
        if test_model_file(pth_file):
            good_files.append(pth_file)
        else:
            bad_files.append(pth_file)
    
    print(f"\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)
    
    if good_files:
        print(f"\n✅ 可用的模型文件 ({len(good_files)}):")
        for file in good_files:
            file_size = os.path.getsize(file) / (1024 * 1024)
            print(f"  - {file.name} ({file_size:.1f} MB)")
    
    if bad_files:
        print(f"\n❌ 损坏的模型文件 ({len(bad_files)}):")
        for file in bad_files:
            print(f"  - {file.name}")
    
    # 推荐使用的文件
    if good_files:
        # 优先推荐best文件，然后是最大epoch数
        best_candidates = [f for f in good_files if 'best' in f.name]
        if best_candidates:
            recommended = best_candidates[0]
        else:
            # 按数字排序，选择最大的
            try:
                numbered_files = [(int(f.stem), f) for f in good_files if f.stem.isdigit()]
                if numbered_files:
                    recommended = max(numbered_files, key=lambda x: x[0])[1]
                else:
                    recommended = good_files[0]
            except:
                recommended = good_files[0]
        
        print(f"\n🎯 推荐使用: {recommended.name}")
        print(f"   完整路径: {recommended}")
        
        return str(recommended)
    else:
        print(f"\n❌ 没有可用的模型文件！")
        return None

if __name__ == '__main__':
    main() 