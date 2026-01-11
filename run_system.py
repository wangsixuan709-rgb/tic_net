#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TiCNet 肺结节检测系统启动脚本
"""

import os
import sys
import torch
import argparse
from pathlib import Path

def check_environment():
    """检查运行环境"""
    print("=" * 60)
    print("TiCNet 肺结节检测系统环境检查")
    print("=" * 60)
    
    # Python版本检查
    python_version = sys.version_info
    print(f"Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print("❌ 错误: Python版本过低，需要Python 3.7+")
        return False
    else:
        print("✅ Python版本检查通过")
    
    # PyTorch检查
    try:
        print(f"PyTorch 版本: {torch.__version__}")
        print("✅ PyTorch已安装")
    except ImportError:
        print("❌ 错误: PyTorch未安装")
        return False
    
    # CUDA检查
    if torch.cuda.is_available():
        cuda_count = torch.cuda.device_count()
        current_device = torch.cuda.current_device()
        device_name = torch.cuda.get_device_name(current_device)
        print(f"CUDA 可用: 是")
        print(f"GPU 数量: {cuda_count}")
        print(f"当前设备: {device_name}")
        print("✅ GPU支持检查通过")
    else:
        print("⚠️  警告: CUDA不可用，将使用CPU进行推理")
    
    # 依赖包检查
    required_packages = [
        ('flask', 'flask'),
        ('numpy', 'numpy'), 
        ('matplotlib', 'matplotlib'),
        ('pillow', 'PIL'),
        ('simpleitk', 'SimpleITK'),
        ('opencv-python', 'cv2'),
        ('scipy', 'scipy'),
        ('pandas', 'pandas')
    ]
    
    # 可选包检查
    optional_packages = [
        ('pynrrd', 'nrrd', 'NRRD文件支持')
    ]
    
    print("\n检查依赖包:")
    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} (缺失)")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n❌ 缺失依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    # 检查可选包
    print("\n检查可选包:")
    for package_name, import_name, description in optional_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name} ({description})")
        except ImportError:
            print(f"⚠️  {package_name} (可选) - {description}")
            print(f"   安装命令: pip install {package_name}")
    
    # 目录结构检查
    print("\n检查目录结构:")
    required_dirs = ['net', 'system', 'templates', 'config.py']
    for item in required_dirs:
        if os.path.exists(item):
            print(f"✅ {item}")
        else:
            print(f"❌ {item} (缺失)")
            return False
    
    print("\n✅ 环境检查完成")
    return True

def create_directories():
    """创建必要的目录"""
    directories = [
        'uploads',
        'system_results', 
        'visualizations',
        'models',
        'logs'
    ]
    
    print("\n创建系统目录:")
    for directory in directories:
        path = Path(directory)
        path.mkdir(exist_ok=True)
        print(f"✅ {directory}/")

def download_model_weights():
    """下载或检查模型权重"""
    models_dir = Path('models')
    model_path = models_dir / 'best_model.pth'
    
    print("\n检查模型权重:")
    if model_path.exists():
        print(f"✅ 找到模型权重: {model_path}")
        print(f"   文件大小: {model_path.stat().st_size / (1024*1024):.1f} MB")
    else:
        print(f"⚠️  未找到模型权重: {model_path}")
        print("   系统将使用随机初始化权重运行（仅用于演示）")
        print("   如需使用训练好的模型，请将权重文件放置到 models/ 目录")

def main():
    parser = argparse.ArgumentParser(description='TiCNet 肺结节检测系统')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=5000, help='服务器端口')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--skip-check', action='store_true', help='跳过环境检查')
    
    args = parser.parse_args()
    
    print("🫁 TiCNet 肺结节检测系统")
    print("   Transformer in Convolutional Neural Network")
    print("   for Pulmonary Nodule Detection on CT Images")
    print("")
    
    # 环境检查
    if not args.skip_check:
        if not check_environment():
            print("\n❌ 环境检查失败，请解决上述问题后重新运行")
            sys.exit(1)
    
    # 创建目录
    create_directories()
    
    # 检查模型权重
    download_model_weights()
    
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
    except KeyboardInterrupt:
        print("\n\n👋 感谢使用 TiCNet 肺结节检测系统！")
    except Exception as e:
        print(f"\n❌ 启动失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 