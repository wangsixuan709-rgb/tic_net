#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试上传.npy文件的脚本
"""

import sys
import os
import numpy as np

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from system.model_inference import ModelInference
from system.config import SystemConfig

def test_npy_file(npy_file_path):
    """测试.npy文件的处理"""
    print(f"\n{'='*60}")
    print(f"测试文件: {os.path.basename(npy_file_path)}")
    print(f"{'='*60}")
    
    # 检查文件是否存在
    if not os.path.exists(npy_file_path):
        print(f"❌ 文件不存在: {npy_file_path}")
        return False
    
    # 检查相关元数据文件
    base_path = npy_file_path.replace('.npy', '')
    required_files = [
        npy_file_path,
        base_path + '_origin.npy',
        base_path + '_spacing.npy',
        base_path + '_ebox.npy',
        base_path + '_bboxes.npy'
    ]
    
    print("\n检查文件完整性:")
    all_exist = True
    for f in required_files:
        exists = os.path.exists(f)
        status = "✅" if exists else "❌"
        print(f"{status} {os.path.basename(f)}")
        if not exists and f != (base_path + '_bboxes.npy'):
            # bboxes可选
            if not f.endswith('_bboxes.npy'):
                all_exist = False
    
    if not all_exist:
        print("\n⚠️  缺少必要的元数据文件")
        print("预处理的.npy文件需要配套的 _origin.npy, _spacing.npy, _ebox.npy 文件")
        return False
    
    # 加载文件并显示信息
    print("\n文件信息:")
    data = np.load(npy_file_path)
    print(f"主文件形状: {data.shape}")
    print(f"数据类型: {data.dtype}")
    print(f"数值范围: [{data.min()}, {data.max()}]")
    
    origin = np.load(base_path + '_origin.npy')
    spacing = np.load(base_path + '_spacing.npy')
    ebox = np.load(base_path + '_ebox.npy')
    
    print(f"Origin: {origin}")
    print(f"Spacing: {spacing}")
    print(f"Ebox: {ebox}")
    
    if os.path.exists(base_path + '_bboxes.npy'):
        bboxes = np.load(base_path + '_bboxes.npy')
        print(f"标注框数量: {len(bboxes)}")
        print(f"标注框:\n{bboxes}")
    
    # 尝试使用系统处理
    print("\n开始系统处理测试...")
    try:
        config = SystemConfig()
        model_inference = ModelInference(config)
        
        task_id = "test_" + os.path.basename(npy_file_path).split('.')[0][:20]
        print(f"任务ID: {task_id}")
        
        # 进行推理
        results = model_inference.predict(npy_file_path, task_id)
        
        print("\n✅ 处理成功!")
        print(f"检测到的结节数量: {len(results['detections'])}")
        print(f"推理时间: {results['inference_time']:.2f}秒")
        
        if results['detections']:
            print("\n检测结果:")
            for i, det in enumerate(results['detections'][:5]):  # 只显示前5个
                print(f"  结节 {i+1}:")
                print(f"    置信度: {det['confidence']:.3f}")
                print(f"    体积: {det['volume']:.2f} mm³")
                print(f"    中心: {det.get('center', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # 测试文件路径
    test_file = "/home/yangao/LUNG/SANet/NoduleNet-master/data/LUNA16/intermideate/1.3.6.1.4.1.14519.5.2.1.6279.6001.100225287222365663678666836860.npy"
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    
    success = test_npy_file(test_file)
    
    if success:
        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ 测试失败")
        print("="*60)
        sys.exit(1)

