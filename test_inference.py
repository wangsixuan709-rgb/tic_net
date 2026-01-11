#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模型推理功能
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

def test_model_inference():
    """测试模型推理功能"""
    print("=" * 60)
    print("TiCNet 模型推理测试")
    print("=" * 60)
    
    try:
        # 初始化配置和推理引擎
        config = SystemConfig()
        print(f"设备: {config.get_device()}")
        
        # 初始化模型推理
        print("正在初始化模型推理引擎...")
        inference = ModelInference(config)
        print("✅ 模型推理引擎初始化成功")
        
        # 创建测试数据
        print("\n正在创建测试数据...")
        
        # 创建一个模拟的图像文件路径（使用LUNA16格式的seriesuid）
        test_seriesuid = "1.3.6.1.4.1.14519.5.2.1.6279.6001.100225287222365663678666836860"
        test_image_path = f"test_data/{test_seriesuid}.nrrd"
        
        # 创建模拟的图像数据
        test_image = np.random.randint(0, 255, (64, 128, 128), dtype=np.int16)
        
        # 保存为临时文件（如果需要的话）
        test_dir = Path("test_data")
        test_dir.mkdir(exist_ok=True)
        
        print(f"测试图像路径: {test_image_path}")
        print(f"测试图像形状: {test_image.shape}")
        
        # 模拟meta_info
        meta_info = {
            'spacing': (1.0, 1.0, 1.0),
            'origin': (0.0, 0.0, 0.0),
            'original_shape': test_image.shape,
            'dtype': str(test_image.dtype)
        }
        
        # 测试注解处理器
        print("\n测试注解处理...")
        seriesuid = inference.annotation_handler.extract_seriesuid_from_path(test_image_path)
        print(f"提取的seriesuid: {seriesuid}")
        
        if seriesuid:
            annotations = inference.annotation_handler.get_annotations_for_seriesuid(seriesuid)
            print(f"找到的注解数量: {len(annotations)}")
            
            truth_boxes, truth_labels = inference.annotation_handler.get_truth_data_for_image(
                test_image_path, 
                meta_info['spacing'], 
                meta_info['origin'], 
                meta_info['original_shape']
            )
            print(f"Truth boxes数量: {len(truth_boxes)}")
            print(f"Truth labels数量: {len(truth_labels)}")
        
        print("\n✅ 注解处理测试完成")
        
        # 测试模型推理（使用模拟数据）
        print("\n测试模型推理...")
        
        # 创建模拟的图像张量
        image_tensor = torch.from_numpy(test_image.astype(np.float32))
        image_tensor = image_tensor.unsqueeze(0).unsqueeze(0)  # 添加batch和channel维度
        image_tensor = image_tensor.to(inference.device)
        
        print(f"输入张量形状: {image_tensor.shape}")
        
        # 测试模型forward调用
        try:
            inference.model.set_mode('eval')
            
            # 创建空的truth数据用于测试
            truth_boxes_list = [torch.zeros((0, 6), dtype=torch.float32, device=inference.device)]
            truth_labels_list = [torch.zeros((0,), dtype=torch.long, device=inference.device)]
            
            print("正在调用模型...")
            with torch.no_grad():
                inference.model.forward(image_tensor, truth_boxes_list, truth_labels_list)
            
            print("✅ 模型forward调用成功")
            
            # 检查模型输出
            if hasattr(inference.model, 'rpn_proposals'):
                print(f"RPN proposals: {inference.model.rpn_proposals.shape if inference.model.rpn_proposals is not None else 'None'}")
            if hasattr(inference.model, 'detections'):
                print(f"Detections: {inference.model.detections.shape if inference.model.detections is not None else 'None'}")
            if hasattr(inference.model, 'ensemble_proposals'):
                print(f"Ensemble proposals: {inference.model.ensemble_proposals.shape if inference.model.ensemble_proposals is not None else 'None'}")
            
        except Exception as e:
            print(f"❌ 模型推理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n✅ 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_model_inference()
    if success:
        print("\n🎉 推理系统测试成功！")
        sys.exit(0)
    else:
        print("\n💥 推理系统测试失败！")
        sys.exit(1) 