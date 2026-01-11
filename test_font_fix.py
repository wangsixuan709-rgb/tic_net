#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试字体方框问题修复
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

def test_font_display():
    """测试混合字体显示"""
    print("=" * 70)
    print("测试字体显示修复")
    print("=" * 70)
    
    # 设置字体（模拟系统配置）
    available_fonts = set([f.name for f in fm.fontManager.ttflist])
    
    if 'Droid Sans Fallback' in available_fonts:
        print("\n✅ 找到 Droid Sans Fallback 字体")
        print("📝 使用混合字体策略:")
        print("   - 英文/数字: DejaVu Sans")
        print("   - 中文: Droid Sans Fallback")
        
        # 设置混合字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Droid Sans Fallback', 'Liberation Sans', 'Arial', 'sans-serif']
    else:
        print("\n❌ 未找到 Droid Sans Fallback")
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'sans-serif']
    
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建测试图像
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 测试1: 纯中文
    axes[0, 0].text(0.5, 0.5, 'TiCNet\n肺结节检测系统\n中文显示测试', 
                    ha='center', va='center', fontsize=14)
    axes[0, 0].set_title('测试1: 纯中文')
    axes[0, 0].axis('off')
    
    # 测试2: 中英混合
    axes[0, 1].text(0.5, 0.5, 
                    'CT Image Preview\nCT图像预览\n形状: 133×512×512\nShape: 133×512×512', 
                    ha='center', va='center', fontsize=12)
    axes[0, 1].set_title('测试2: 中英混合')
    axes[0, 1].axis('off')
    
    # 测试3: 数字和符号
    axes[1, 0].text(0.5, 0.5, 
                    '数字: 0123456789\n符号: ()[]{}+-*/=\n置信度: 0.95\nConfidence: 0.95', 
                    ha='center', va='center', fontsize=12)
    axes[1, 0].set_title('测试3: 数字和符号')
    axes[1, 0].axis('off')
    
    # 测试4: 图表标签
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    axes[1, 1].plot(x, y)
    axes[1, 1].set_title('切片 0/132 (0.0%)')
    axes[1, 1].set_xlabel('X轴 (X Axis)')
    axes[1, 1].set_ylabel('Y轴 (Y Axis)')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.suptitle('字体显示测试 - Font Display Test', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    # 保存图像
    output_file = 'font_fix_test.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n✅ 测试图像已生成: {output_file}")
    print("\n请查看图像，检查是否还有方框:")
    print("  1. 如果没有方框 -> 修复成功！")
    print("  2. 如果还有方框 -> 需要安装更好的字体")
    
    print("\n" + "=" * 70)
    print("如果还有方框，请运行以下命令安装字体:")
    print("  sudo apt-get install fonts-wqy-microhei")
    print("或者:")
    print("  ./install_fonts_user.sh")
    print("=" * 70)

if __name__ == '__main__':
    test_font_display()

