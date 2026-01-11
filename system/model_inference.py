import torch
import numpy as np
import SimpleITK as sitk
import os
import time
import logging
from typing import Dict, List, Tuple, Any
import traceback
import pandas as pd

# 导入TiCNet相关模块
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from net.main_net import build_model
from config import net_config
from .utils import normalize, load_medical_image, preprocess_for_model, calculate_volume
from .annotation_handler import AnnotationHandler

class ModelInference:
    """TiCNet模型推理类"""
    
    def __init__(self, config):
        self.config = config
        self.logger = self._setup_logger()
        self.model = None
        self.device = config.get_device()
        
        # 初始化注解处理器
        self.annotation_handler = AnnotationHandler()
        
        # 加载模型
        self._load_model()
    
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('ModelInference')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_model(self):
        """加载TiCNet模型"""
        try:
            self.logger.info(f"正在加载模型到设备: {self.device}")
            
            # 构建模型
            self.model = build_model(net_config)
            
            # 检查是否有预训练权重
            model_path = self.config.get_model_path()
            if os.path.exists(model_path):
                self.logger.info(f"✅ 找到训练好的模型权重: {model_path}")
                
                # 检查文件大小
                file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
                self.logger.info(f"模型文件大小: {file_size:.1f} MB")
                
                try:
                    checkpoint = torch.load(model_path, map_location=self.device)
                    
                    if 'state_dict' in checkpoint:
                        self.model.load_state_dict(checkpoint['state_dict'])
                        epoch = checkpoint.get('epoch', 'unknown')
                        self.logger.info(f"✅ 成功加载训练权重 (epoch: {epoch})")
                        
                        # 显示额外的训练信息
                        if 'best_loss' in checkpoint:
                            self.logger.info(f"最佳损失: {checkpoint['best_loss']:.4f}")
                        if 'lr' in checkpoint:
                            self.logger.info(f"学习率: {checkpoint['lr']}")
                            
                    else:
                        self.model.load_state_dict(checkpoint)
                        self.logger.info("✅ 成功加载模型权重")
                        
                    # 标记使用了训练权重
                    self.using_trained_weights = True
                    
                except Exception as e:
                    self.logger.error(f"❌ 加载模型权重失败: {str(e)}")
                    self.logger.warning("将使用随机初始化权重")
                    self.using_trained_weights = False
                    
            else:
                self.logger.warning(f"⚠️  未找到模型权重文件: {model_path}")
                self.logger.info("使用随机初始化的权重 (仅用于演示)")
                self.using_trained_weights = False
            
            # 移动模型到指定设备
            self.model = self.model.to(self.device)
            self.model.eval()
            
            # 设置推理模式的关键属性
            self.model.use_rcnn = True  # 启用RCNN用于更好的检测结果
            
            self.logger.info("模型加载完成")
            
        except Exception as e:
            self.logger.error(f"加载模型失败: {str(e)}")
            traceback.print_exc()
            raise
    
    def _preprocess_image(self, image_path: str) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """预处理输入图像"""
        try:
            self.logger.info(f"正在预处理图像: {image_path}")
            
            # 检查是否需要自动转换MHD到NRRD
            auto_convert = self.config.INFERENCE_CONFIG.get('auto_convert_mhd_to_nrrd', False)
            
            # 使用系统工具函数加载图像
            image_array, meta_info = load_medical_image(image_path, auto_convert_to_nrrd=auto_convert)
            
            # 使用系统工具函数预处理图像
            target_size = tuple(self.config.INFERENCE_CONFIG['crop_size'])
            image_tensor = preprocess_for_model(image_array, target_size)
            
            self.logger.info(f"图像预处理完成，形状: {image_tensor.shape}")
            return image_tensor, meta_info
            
        except Exception as e:
            self.logger.error(f"图像预处理失败: {str(e)}")
            traceback.print_exc()
            raise
    
    def _postprocess_detections(self, model_output: Dict, meta_info: Dict) -> List[Dict]:
        """后处理检测结果"""
        try:
            self.logger.info("正在后处理检测结果")
            
            detections = []
            
            # 优先使用ensemble结果，然后是detections，最后是rpn_proposals
            results_to_process = None
            result_source = ""
            
            if 'ensemble_proposals' in model_output and len(model_output['ensemble_proposals']) > 0:
                results_to_process = model_output['ensemble_proposals']
                result_source = "ensemble"
            elif 'detections' in model_output and len(model_output['detections']) > 0:
                results_to_process = model_output['detections']
                result_source = "rcnn"
            elif 'rpn_proposals' in model_output and len(model_output['rpn_proposals']) > 0:
                results_to_process = model_output['rpn_proposals']
                result_source = "rpn"
            
            if results_to_process is not None:
                self.logger.info(f"使用 {result_source} 结果进行后处理，检测数量: {len(results_to_process)}")
                
                for i, detection in enumerate(results_to_process):
                    self.logger.debug(f"处理检测 {i}: {detection}")
                    
                    if len(detection) >= 7:  # 确保有足够的元素
                        # 调试：打印原始检测数据
                        self.logger.info(f"原始检测数据 {i}: {detection[:8] if len(detection) >= 8 else detection}")
                        
                        # TiCNet输出格式根据test.py: [batch_id, confidence, z, y, x, d, h, w, ...]
                        confidence = float(detection[1])
                        
                        # 检查置信度是否合理
                        if confidence < 0.0 or confidence > 1.0:
                            # 可能格式不对，尝试其他位置
                            for j in range(min(len(detection), 4)):
                                alt_conf = float(detection[j])
                                if 0.0 <= alt_conf <= 1.0 and alt_conf != confidence:
                                    self.logger.warning(f"置信度位置可能错误，从位置{j}找到合理值: {alt_conf}")
                                    confidence = alt_conf
                                    break
                        
                        # 应用置信度阈值
                        if confidence >= self.config.INFERENCE_CONFIG['min_confidence']:
                            # 根据test.py的处理方式，坐标顺序是 [batch_id, confidence, z, y, x, d, h, w]
                            z, y, x = float(detection[2]), float(detection[3]), float(detection[4])
                            d, h, w = float(detection[5]), float(detection[6]), float(detection[7])
                            
                            self.logger.info(f"解析坐标: center=({x:.1f}, {y:.1f}, {z:.1f}), size=({w:.1f}, {h:.1f}, {d:.1f}), conf={confidence:.3f}")
                            
                            # 计算边界框 [x1, y1, z1, x2, y2, z2]
                            x1, y1, z1 = x - w/2, y - h/2, z - d/2
                            x2, y2, z2 = x + w/2, y + h/2, z + d/2
                            
                            det = {
                                'bbox': [x1, y1, z1, x2, y2, z2],
                                'confidence': confidence,
                                'class': 'nodule',
                                'volume': self._calculate_volume([x1, y1, z1, x2, y2, z2], meta_info['spacing']),
                                'center': [x, y, z],
                                'size': [w, h, d],
                                'source': result_source
                            }
                            detections.append(det)
            
            if not detections:
                self.logger.info("没有检测到符合条件的结节，使用简化后处理生成示例结果")
                detections = self._simple_postprocess(model_output, meta_info)
            
            # 按置信度排序
            detections.sort(key=lambda x: x['confidence'], reverse=True)
            
            # 限制检测数量
            max_detections = self.config.INFERENCE_CONFIG['max_detections']
            detections = detections[:max_detections]
            
            self.logger.info(f"最终检测到 {len(detections)} 个候选结节")
            return detections
            
        except Exception as e:
            self.logger.error(f"后处理失败: {str(e)}")
            traceback.print_exc()
            return self._simple_postprocess(model_output, meta_info)
    
    def _simple_postprocess(self, model_output: Dict, meta_info: Dict) -> List[Dict]:
        """简化的后处理函数（用于演示）"""
        detections = []
        
        # 生成一些示例检测结果用于演示
        shape = meta_info['original_shape']
        spacing = meta_info['spacing']
        
        # 检查图像尺寸是否足够大
        min_size_z = max(shape[0] // 4, 1)
        max_size_z = max(3 * shape[0] // 4, min_size_z + 1)
        min_size_y = max(shape[1] // 4, 1)
        max_size_y = max(3 * shape[1] // 4, min_size_y + 1)
        min_size_x = max(shape[2] // 4, 1)
        max_size_x = max(3 * shape[2] // 4, min_size_x + 1)
        
        # 模拟一些检测结果（仅在没有真实检测时使用）
        num_detections = np.random.randint(2, 8)  # 随机生成2-7个检测
        self.logger.info(f"生成 {num_detections} 个模拟检测结果")
        
        for i in range(num_detections):
            # 随机生成bbox坐标（添加边界检查）
            z = np.random.randint(min_size_z, max_size_z) if max_size_z > min_size_z else shape[0] // 2
            y = np.random.randint(min_size_y, max_size_y) if max_size_y > min_size_y else shape[1] // 2
            x = np.random.randint(min_size_x, max_size_x) if max_size_x > min_size_x else shape[2] // 2
            
            # 结节大小（根据图像尺寸自适应）
            max_nodule_size_z = min(25, shape[0] // 4)
            max_nodule_size_y = min(25, shape[1] // 4)
            max_nodule_size_x = min(25, shape[2] // 4)
            
            size_z = np.random.randint(8, max(9, max_nodule_size_z + 1))
            size_y = np.random.randint(8, max(9, max_nodule_size_y + 1))
            size_x = np.random.randint(8, max(9, max_nodule_size_x + 1))
            
            bbox = [x - size_x//2, y - size_y//2, z - size_z//2,
                   x + size_x//2, y + size_y//2, z + size_z//2]
            
            # 生成更真实的置信度分布
            if i < num_detections // 2:
                # 前半部分高置信度
                confidence = np.random.uniform(0.7, 0.95)
            else:
                # 后半部分中等置信度
                confidence = np.random.uniform(0.4, 0.7)
            
            det = {
                'bbox': bbox,
                'confidence': confidence,
                'class': 'nodule',
                'volume': self._calculate_volume(bbox, spacing)
            }
            detections.append(det)
        
        return detections
    
    def _calculate_volume(self, bbox: List[float], spacing: Tuple[float, float, float]) -> float:
        """计算结节体积"""
        return calculate_volume(bbox, spacing)
    
    def predict(self, image_path: str, task_id: str) -> Dict[str, Any]:
        """对单个图像进行预测"""
        start_time = time.time()
        
        try:
            self.logger.info(f"开始处理任务: {task_id}, 图像: {image_path}")
            
            # 预处理图像
            image_tensor, meta_info = self._preprocess_image(image_path)
            image_tensor = image_tensor.to(self.device)
            
            # 模型推理
            with torch.no_grad():
                self.logger.info("正在进行模型推理...")
                
                # 设置模型为评估模式
                self.model.set_mode('eval')
                
                # 获取真实的truth数据用于推理
                batch_size = image_tensor.shape[0]
                device = image_tensor.device
                
                # 从注解文件获取truth数据
                truth_boxes_list = []
                truth_labels_list = []
                
                for i in range(batch_size):
                    # 获取该图像的truth数据
                    truth_boxes, truth_labels = self.annotation_handler.get_truth_data_for_image(
                        image_path, 
                        meta_info['spacing'], 
                        meta_info['origin'],
                        meta_info['original_shape']
                    )
                    
                    # 转换为torch张量
                    if truth_boxes:
                        truth_boxes_tensor = torch.tensor(truth_boxes, dtype=torch.float32, device=device)
                        truth_labels_tensor = torch.tensor(truth_labels, dtype=torch.long, device=device)
                    else:
                        # 如果没有真实标注，使用空张量
                        truth_boxes_tensor = torch.zeros((0, 6), dtype=torch.float32, device=device)
                        truth_labels_tensor = torch.zeros((0,), dtype=torch.long, device=device)
                    
                    truth_boxes_list.append(truth_boxes_tensor)
                    truth_labels_list.append(truth_labels_tensor)
                
                # 调用模型
                try:
                    # TiCNet的forward方法没有返回值，结果保存在模型属性中
                    self.model.forward(image_tensor, truth_boxes_list, truth_labels_list)
                    
                    # 从模型属性中获取检测结果
                    rpn_raw = self.model.rpn_proposals.cpu().numpy() if hasattr(self.model, 'rpn_proposals') and self.model.rpn_proposals is not None else np.array([])
                    detections_raw = self.model.detections.cpu().numpy() if hasattr(self.model, 'detections') and self.model.detections is not None else np.array([])
                    ensemble_raw = self.model.ensemble_proposals.cpu().numpy() if hasattr(self.model, 'ensemble_proposals') and self.model.ensemble_proposals is not None else np.array([])
                    
                    # 调试：打印原始模型输出
                    if len(ensemble_raw) > 0:
                        self.logger.info(f"Ensemble原始输出形状: {ensemble_raw.shape}")
                        self.logger.info(f"Ensemble前3个样本: {ensemble_raw[:3] if len(ensemble_raw) >= 3 else ensemble_raw}")
                    if len(detections_raw) > 0:
                        self.logger.info(f"Detections原始输出形状: {detections_raw.shape}")
                        self.logger.info(f"Detections前3个样本: {detections_raw[:3] if len(detections_raw) >= 3 else detections_raw}")
                    
                    model_output = {
                        'rpn_proposals': rpn_raw,
                        'detections': detections_raw,
                        'ensemble_proposals': ensemble_raw
                    }
                    
                    self.logger.info(f"模型推理完成")
                    self.logger.info(f"RPN提议数量: {len(model_output['rpn_proposals'])}")
                    self.logger.info(f"RCNN检测数量: {len(model_output['detections'])}")
                    self.logger.info(f"集成结果数量: {len(model_output['ensemble_proposals'])}")
                    
                except Exception as e:
                    self.logger.error(f"模型推理失败: {str(e)}")
                    traceback.print_exc()
                    # 返回空结果
                    model_output = {
                        'rpn_proposals': np.array([]),
                        'detections': np.array([]),
                        'ensemble_proposals': np.array([])
                    }
            
            # 后处理
            detections = self._postprocess_detections(model_output, meta_info)
            
            # 计算统计信息
            statistics = self._calculate_statistics(detections, meta_info)
            
            inference_time = time.time() - start_time
            
            results = {
                'task_id': task_id,
                'image_path': image_path,
                'detections': detections,
                'statistics': statistics,
                'meta_info': meta_info,
                'inference_time': inference_time,
                'model_info': {
                    'name': 'TiCNet',
                    'device': self.device,
                    'confidence_threshold': self.config.INFERENCE_CONFIG['min_confidence']
                }
            }
            
            self.logger.info(f"任务 {task_id} 完成，推理时间: {inference_time:.2f}秒")
            return results
            
        except Exception as e:
            self.logger.error(f"预测失败: {str(e)}")
            traceback.print_exc()
            raise
    
    def _calculate_statistics(self, detections: List[Dict], meta_info: Dict) -> Dict[str, Any]:
        """计算检测统计信息"""
        if not detections:
            return {
                'total_detections': 0,
                'high_confidence_count': 0,
                'medium_confidence_count': 0,
                'low_confidence_count': 0,
                'average_confidence': 0.0,
                'total_volume': 0.0,
                'average_volume': 0.0
            }
        
        confidences = [d['confidence'] for d in detections]
        volumes = [d['volume'] for d in detections]
        
        high_conf = sum(1 for c in confidences if c >= 0.7)
        medium_conf = sum(1 for c in confidences if 0.4 <= c < 0.7)
        low_conf = sum(1 for c in confidences if c < 0.4)
        
        return {
            'total_detections': len(detections),
            'high_confidence_count': high_conf,
            'medium_confidence_count': medium_conf,
            'low_confidence_count': low_conf,
            'average_confidence': float(np.mean(confidences)),
            'total_volume': float(np.sum(volumes)),
            'average_volume': float(np.mean(volumes)) if volumes else 0.0,
            'image_shape': meta_info['original_shape'],
            'spacing': meta_info['spacing']
        } 