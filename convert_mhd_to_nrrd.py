#!/usr/bin/env python
"""
MHD格式转NRRD格式转换工具

使用方法:
    python convert_mhd_to_nrrd.py input.mhd
    python convert_mhd_to_nrrd.py input.mhd output.nrrd
    python convert_mhd_to_nrrd.py /path/to/folder/  (批量转换)
"""

import os
import sys
import SimpleITK as sitk
from pathlib import Path


def convert_single_file(mhd_path, output_path=None):
    """转换单个MHD文件为NRRD格式
    
    Args:
        mhd_path: MHD文件路径
        output_path: 输出NRRD文件路径（可选，默认同名同目录）
    """
    mhd_path = Path(mhd_path)
    
    if not mhd_path.exists():
        print(f"❌ 错误：文件不存在: {mhd_path}")
        return False
    
    if not mhd_path.suffix.lower() == '.mhd':
        print(f"❌ 错误：不是MHD文件: {mhd_path}")
        return False
    
    # 检查对应的.raw文件是否存在
    raw_path = mhd_path.with_suffix('.raw')
    if not raw_path.exists():
        # 有些MHD文件使用.zraw等其他格式
        print(f"⚠️ 警告：未找到对应的RAW文件: {raw_path}")
        print(f"   尝试读取MHD文件中指定的数据文件...")
    
    try:
        print(f"\n📄 读取MHD文件: {mhd_path.name}")
        image = sitk.ReadImage(str(mhd_path))
        
        # 显示图像信息
        size = image.GetSize()
        spacing = image.GetSpacing()
        origin = image.GetOrigin()
        
        print(f"   ✓ 图像尺寸: {size}")
        print(f"   ✓ 体素间距: {spacing}")
        print(f"   ✓ 原点坐标: {origin}")
        
        # 确定输出路径
        if output_path is None:
            output_path = mhd_path.with_suffix('.nrrd')
        else:
            output_path = Path(output_path)
        
        print(f"\n💾 保存NRRD文件: {output_path.name}")
        sitk.WriteImage(image, str(output_path))
        
        # 检查输出文件大小
        output_size = output_path.stat().st_size / (1024 * 1024)
        print(f"   ✓ 文件大小: {output_size:.2f} MB")
        print(f"   ✓ 转换成功！\n")
        
        return True
        
    except Exception as e:
        print(f"❌ 转换失败: {str(e)}\n")
        return False


def convert_directory(directory_path, recursive=False):
    """批量转换目录中的所有MHD文件
    
    Args:
        directory_path: 目录路径
        recursive: 是否递归子目录
    """
    directory_path = Path(directory_path)
    
    if not directory_path.exists() or not directory_path.is_dir():
        print(f"❌ 错误：目录不存在: {directory_path}")
        return
    
    # 查找所有MHD文件
    if recursive:
        mhd_files = list(directory_path.rglob('*.mhd'))
    else:
        mhd_files = list(directory_path.glob('*.mhd'))
    
    if not mhd_files:
        print(f"❌ 未找到MHD文件: {directory_path}")
        return
    
    print(f"\n🔍 找到 {len(mhd_files)} 个MHD文件")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for i, mhd_file in enumerate(mhd_files, 1):
        print(f"\n[{i}/{len(mhd_files)}] 处理: {mhd_file.name}")
        print("-" * 60)
        
        if convert_single_file(mhd_file):
            success_count += 1
        else:
            fail_count += 1
    
    print("=" * 60)
    print(f"\n✅ 转换完成！")
    print(f"   成功: {success_count} 个")
    print(f"   失败: {fail_count} 个")


def main():
    """主函数"""
    print("=" * 60)
    print("  MHD格式 → NRRD格式 转换工具")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\n用法:")
        print("  1. 转换单个文件:")
        print("     python convert_mhd_to_nrrd.py input.mhd")
        print("     python convert_mhd_to_nrrd.py input.mhd output.nrrd")
        print()
        print("  2. 批量转换目录:")
        print("     python convert_mhd_to_nrrd.py /path/to/folder/")
        print("     python convert_mhd_to_nrrd.py /path/to/folder/ --recursive")
        print()
        print("示例:")
        print("  python convert_mhd_to_nrrd.py patient001.mhd")
        print("  python convert_mhd_to_nrrd.py data/")
        print()
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # 检查是否是目录
    if os.path.isdir(input_path):
        recursive = '--recursive' in sys.argv or '-r' in sys.argv
        convert_directory(input_path, recursive)
    else:
        # 单个文件转换
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        
        if convert_single_file(input_path, output_path):
            print("✅ 转换成功！现在您可以上传NRRD文件到TiCNet系统了。")
        else:
            print("❌ 转换失败！请检查文件路径和格式。")
            sys.exit(1)


if __name__ == '__main__':
    main()

