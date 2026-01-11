#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TiCNet 肺结节检测系统 - 简化启动脚本
跳过复杂的依赖检查，直接启动系统
"""

import os
import sys
import argparse
from pathlib import Path

def create_directories():
    """创建必要的目录"""
    directories = [
        'uploads',
        'system_results', 
        'visualizations',
        'models',
        'logs'
    ]
    
    print("创建系统目录:")
    for directory in directories:
        path = Path(directory)
        path.mkdir(exist_ok=True)
        print(f"✅ {directory}/")

def main():
    parser = argparse.ArgumentParser(description='TiCNet 肺结节检测系统')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=5000, help='服务器端口')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    print("🫁 TiCNet 肺结节检测系统")
    print("   Transformer in Convolutional Neural Network")
    print("   for Pulmonary Nodule Detection on CT Images")
    print("")
    
    # 创建目录
    create_directories()
    
    # 检查模型权重
    print("\n检查模型权重:")
    try:
        from system.config import SystemConfig
        config = SystemConfig()
        model_path = config.get_model_path()
        
        if os.path.exists(model_path):
            file_size = os.path.getsize(model_path) / (1024*1024)
            print(f"✅ 找到训练好的模型权重: {model_path}")
            print(f"   文件大小: {file_size:.1f} MB")
            
            # 检查是否是训练权重
            if 'results/ticnet' in str(model_path):
                print(f"   🎯 使用已训练的模型权重 - 检测结果将更加准确")
            else:
                print(f"   📦 使用自定义模型权重")
        else:
            print(f"⚠️  未找到模型权重: {model_path}")
            print("   系统将使用随机初始化权重运行（仅用于演示）")
            print("   运行 'python check_model_weights.py' 查看可用的权重文件")
            
    except Exception as e:
        print(f"❌ 检查模型权重时出错: {str(e)}")
        print("   可能需要检查配置文件")
    
    # 启动Web服务
    print("\n" + "=" * 60)
    print("启动Web服务器")
    print("=" * 60)
    print(f"服务器地址: http://{args.host}:{args.port}")
    print("按 Ctrl+C 停止服务器")
    print("")
    
    try:
        # 导入并启动Flask应用
        from app import app
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True
        )
    except ImportError as e:
        print(f"\n❌ 导入失败: {str(e)}")
        print("请确保已安装所需的Python包:")
        print("pip install flask torch numpy matplotlib pillow SimpleITK opencv-python scipy pandas")
        print("\n如需NRRD文件支持，另外安装:")
        print("pip install pynrrd")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 感谢使用 TiCNet 肺结节检测系统！")
    except Exception as e:
        print(f"\n❌ 启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main() 