#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型输出调试工具
用于检查TiCNet模型的实际输出格式和置信度分布
"""

import sys
import os
import torch
import numpy as np
from pathlib import Path

# 添加项目路径
sys.path.append('.')

from system.config import SystemConfig
from system.model_inference import ModelInference

def debug_model_output(image_path: str):
    """调试模型输出格式"""
    print("=" * 60)
    print("TiCNet 模型输出格式调试")
    print("=" * 60)
    
    try:
        # 初始化推理引擎
        config = SystemConfig()
        inference = ModelInference(config)
        
        print(f"正在处理图像: {image_path}")
        
        # 进行推理
        results = inference.predict(image_path, "debug_task")
        
        print(f"\n检测结果数量: {len(results['detections'])}")
        print(f"推理时间: {results['inference_time']:.2f}秒")
        
        # 分析检测结果
        if results['detections']:
            confidences = [d['confidence'] for d in results['detections']]
            print(f"\n置信度分析:")
            print(f"  最小值: {min(confidences):.4f}")
            print(f"  最大值: {max(confidences):.4f}")
            print(f"  平均值: {np.mean(confidences):.4f}")
            print(f"  标准差: {np.std(confidences):.4f}")
            print(f"  唯一值数量: {len(set([f'{c:.3f}' for c in confidences]))}")
            
            # 检查是否所有置信度都相同
            if len(set([f'{c:.4f}' for c in confidences])) == 1:
                print("  ⚠️  警告: 所有检测的置信度都相同！这可能表示数据解析有误。")
            
            print(f"\n前5个检测详情:")
            for i, det in enumerate(results['detections'][:5]):
                print(f"  检测 {i+1}:")
                print(f"    置信度: {det['confidence']:.6f}")
                print(f"    中心坐标: ({det['center'][0]:.1f}, {det['center'][1]:.1f}, {det['center'][2]:.1f})")
                print(f"    尺寸: ({det['size'][0]:.1f}, {det['size'][1]:.1f}, {det['size'][2]:.1f})")
                print(f"    来源: {det.get('source', 'unknown')}")
        
        # 检查模型的原始输出
        print(f"\n模型信息:")
        print(f"  设备: {inference.device}")
        print(f"  模型模式: {inference.model.mode}")
        print(f"  使用RCNN: {getattr(inference.model, 'use_rcnn', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 调试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) != 2:
        print("用法: python debug_model_output.py <图像文件路径>")
        print("示例: python debug_model_output.py test.nrrd")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"❌ 文件不存在: {image_path}")
        sys.exit(1)
    
    success = debug_model_output(image_path)
    
    if success:
        print("\n✅ 模型输出调试完成！")
        sys.exit(0)
    else:
        print("\n❌ 模型输出调试失败！")
        sys.exit(1)

if __name__ == '__main__':
    main() 