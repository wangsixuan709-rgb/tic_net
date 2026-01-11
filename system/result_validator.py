import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple, Any
import logging
from .annotation_handler import AnnotationHandler
import os
import matplotlib.patches as patches

class ResultValidator:
    """检测结果验证器，用于对比检测结果与真实标注"""
    
    def __init__(self, annotation_handler: AnnotationHandler = None):
        self.logger = self._setup_logger()
        self.annotation_handler = annotation_handler or AnnotationHandler()
    
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('ResultValidator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def calculate_iou_3d(self, box1: List[float], box2: List[float]) -> float:
        """计算3D IoU (Intersection over Union)"""
        try:
            # box格式: [x1, y1, z1, x2, y2, z2]
            x1_inter = max(box1[0], box2[0])
            y1_inter = max(box1[1], box2[1])
            z1_inter = max(box1[2], box2[2])
            x2_inter = min(box1[3], box2[3])
            y2_inter = min(box1[4], box2[4])
            z2_inter = min(box1[5], box2[5])
            
            # 计算交集体积
            if x2_inter > x1_inter and y2_inter > y1_inter and z2_inter > z1_inter:
                intersection = (x2_inter - x1_inter) * (y2_inter - y1_inter) * (z2_inter - z1_inter)
            else:
                intersection = 0.0
            
            # 计算各自体积
            volume1 = (box1[3] - box1[0]) * (box1[4] - box1[1]) * (box1[5] - box1[2])
            volume2 = (box2[3] - box2[0]) * (box2[4] - box2[1]) * (box2[5] - box2[2])
            
            # 计算并集体积
            union = volume1 + volume2 - intersection
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            self.logger.warning(f"IoU计算失败: {str(e)}")
            return 0.0
    
    def calculate_distance_3d(self, center1: List[float], center2: List[float]) -> float:
        """计算3D欧氏距离"""
        try:
            dx = center1[0] - center2[0]
            dy = center1[1] - center2[1]
            dz = center1[2] - center2[2]
            return np.sqrt(dx*dx + dy*dy + dz*dz)
        except:
            return float('inf')
    
    def validate_detection_results(self, 
                                 image_path: str,
                                 detections: List[Dict],
                                 meta_info: Dict,
                                 iou_threshold: float = 0.3,
                                 distance_threshold: float = 10.0) -> Dict[str, Any]:
        """验证检测结果与真实标注的对比"""
        try:
            self.logger.info(f"正在验证检测结果: {len(detections)} 个检测")
            
            # 获取真实标注
            truth_boxes, truth_labels = self.annotation_handler.get_truth_data_for_image(
                image_path,
                meta_info['spacing'],
                meta_info['origin'], 
                meta_info['original_shape']
            )
            
            self.logger.info(f"真实标注数量: {len(truth_boxes)}")
            
            if not truth_boxes:
                return {
                    'has_ground_truth': False,
                    'message': '该图像没有真实标注，无法进行验证',
                    'detection_count': len(detections),
                    'ground_truth_count': 0
                }
            
            # 转换真实标注为检测格式
            ground_truth = []
            for i, (box, label) in enumerate(zip(truth_boxes, truth_labels)):
                center_x = (box[0] + box[3]) / 2
                center_y = (box[1] + box[4]) / 2  
                center_z = (box[2] + box[5]) / 2
                
                gt = {
                    'bbox': box,
                    'center': [center_x, center_y, center_z],
                    'label': label,
                    'id': i
                }
                ground_truth.append(gt)
            
            # 匹配检测结果与真实标注
            matches = []
            unmatched_detections = list(range(len(detections)))
            unmatched_ground_truth = list(range(len(ground_truth)))
            
            # 为每个检测找到最佳匹配的真实标注
            for det_idx, detection in enumerate(detections):
                best_match = None
                best_score = 0.0
                best_gt_idx = -1
                
                det_center = detection.get('center', [
                    (detection['bbox'][0] + detection['bbox'][3]) / 2,
                    (detection['bbox'][1] + detection['bbox'][4]) / 2,
                    (detection['bbox'][2] + detection['bbox'][5]) / 2
                ])
                
                for gt_idx in unmatched_ground_truth:
                    gt = ground_truth[gt_idx]
                    
                    # 计算IoU
                    iou = self.calculate_iou_3d(detection['bbox'], gt['bbox'])
                    
                    # 计算距离
                    distance = self.calculate_distance_3d(det_center, gt['center'])
                    
                    # 综合评分 (IoU权重更高)
                    score = iou * 0.7 + (1.0 / (1.0 + distance/10.0)) * 0.3
                    
                    if (iou >= iou_threshold or distance <= distance_threshold) and score > best_score:
                        best_score = score
                        best_match = {
                            'detection_idx': det_idx,
                            'ground_truth_idx': gt_idx,
                            'iou': iou,
                            'distance': distance,
                            'score': score,
                            'confidence': detection['confidence']
                        }
                        best_gt_idx = gt_idx
                
                if best_match:
                    matches.append(best_match)
                    if det_idx in unmatched_detections:
                        unmatched_detections.remove(det_idx)
                    if best_gt_idx in unmatched_ground_truth:
                        unmatched_ground_truth.remove(best_gt_idx)
            
            # 计算指标
            true_positives = len(matches)
            false_positives = len(unmatched_detections)
            false_negatives = len(unmatched_ground_truth)
            
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            # 计算平均IoU和距离
            avg_iou = np.mean([m['iou'] for m in matches]) if matches else 0
            avg_distance = np.mean([m['distance'] for m in matches]) if matches else 0
            avg_confidence = np.mean([m['confidence'] for m in matches]) if matches else 0
            
            validation_result = {
                'has_ground_truth': True,
                'detection_count': len(detections),
                'ground_truth_count': len(ground_truth),
                'true_positives': true_positives,
                'false_positives': false_positives,
                'false_negatives': false_negatives,
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'average_iou': avg_iou,
                'average_distance': avg_distance,
                'average_confidence': avg_confidence,
                'matches': matches,
                'unmatched_detections': [detections[i] for i in unmatched_detections],
                'unmatched_ground_truth': [ground_truth[i] for i in unmatched_ground_truth],
                'validation_summary': self._generate_validation_summary(
                    true_positives, false_positives, false_negatives, 
                    precision, recall, f1_score, avg_iou
                )
            }
            
            self.logger.info(f"验证完成: TP={true_positives}, FP={false_positives}, FN={false_negatives}")
            self.logger.info(f"精度={precision:.3f}, 召回率={recall:.3f}, F1={f1_score:.3f}")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"验证失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'has_ground_truth': False,
                'error': str(e),
                'message': '验证过程中出现错误'
            }
    
    def _generate_validation_summary(self, tp: int, fp: int, fn: int, 
                                   precision: float, recall: float, 
                                   f1_score: float, avg_iou: float) -> str:
        """生成验证摘要文字"""
        if tp == 0 and fp == 0 and fn == 0:
            return "没有检测结果和真实标注"
        
        summary_parts = []
        
        # 总体评价
        if f1_score >= 0.8:
            summary_parts.append("🟢 检测效果优秀")
        elif f1_score >= 0.6:
            summary_parts.append("🟡 检测效果良好") 
        elif f1_score >= 0.4:
            summary_parts.append("🟠 检测效果一般")
        else:
            summary_parts.append("🔴 检测效果较差")
        
        # 具体分析
        if precision >= 0.8:
            summary_parts.append("精度高，误报较少")
        elif precision >= 0.5:
            summary_parts.append("精度中等，有一定误报")
        else:
            summary_parts.append("精度较低，误报较多")
        
        if recall >= 0.8:
            summary_parts.append("召回率高，漏检较少")
        elif recall >= 0.5:
            summary_parts.append("召回率中等，有一定漏检")
        else:
            summary_parts.append("召回率较低，漏检较多")
        
        if avg_iou >= 0.5:
            summary_parts.append("定位精确")
        elif avg_iou >= 0.3:
            summary_parts.append("定位基本准确")
        else:
            summary_parts.append("定位精度有待提高")
        
        return "；".join(summary_parts)
    
    def create_comparison_visualization(self, 
                                      image_data: np.ndarray,
                                      detections: List[Dict],
                                      validation_result: Dict,
                                      task_id: str,
                                      save_dir: str) -> str:
        """创建检测结果与真实标注的对比可视化"""
        try:
            if not validation_result.get('has_ground_truth', False):
                return ""
            
            fig = plt.figure(figsize=(20, 12))
            
            # 选择几个代表性切片
            depth = image_data.shape[0]
            slice_indices = [depth // 4, depth // 2, 3 * depth // 4]
            
            # 布局：上行显示检测结果，下行显示对比分析
            gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.2)
            
            # 上行：显示检测结果叠加图
            for i, slice_idx in enumerate(slice_indices):
                ax = fig.add_subplot(gs[0, i])
                ax.imshow(image_data[slice_idx], cmap='gray')
                ax.set_title(f'切片 {slice_idx} - 检测结果对比', fontsize=12)
                ax.axis('off')
                
                # 绘制真实标注（绿色）
                for gt in validation_result.get('unmatched_ground_truth', []):
                    bbox = gt['bbox']
                    if bbox[2] <= slice_idx <= bbox[5]:
                        rect = patches.Rectangle(
                            (bbox[0], bbox[1]), bbox[3] - bbox[0], bbox[4] - bbox[1],
                            linewidth=2, edgecolor='green', facecolor='none', 
                            linestyle='--', label='真实标注(未匹配)'
                        )
                        ax.add_patch(rect)
                
                # 绘制匹配的检测（蓝色）和真实标注（绿色）
                for match in validation_result.get('matches', []):
                    det_idx = match['detection_idx']
                    detection = detections[det_idx]
                    bbox = detection['bbox']
                    
                    if bbox[2] <= slice_idx <= bbox[5]:
                        # 检测框（蓝色）
                        rect = patches.Rectangle(
                            (bbox[0], bbox[1]), bbox[3] - bbox[0], bbox[4] - bbox[1],
                            linewidth=2, edgecolor='blue', facecolor='none'
                        )
                        ax.add_patch(rect)
                        
                        # 添加置信度和IoU
                        ax.text(bbox[0], bbox[1] - 5, 
                               f'检测: {detection["confidence"]:.2f}\nIoU: {match["iou"]:.2f}',
                               color='blue', fontsize=8, fontweight='bold')
                
                # 绘制未匹配的检测（红色）
                for i in range(len(detections)):
                    if i in [m['detection_idx'] for m in validation_result.get('matches', [])]:
                        continue
                    
                    detection = detections[i]
                    bbox = detection['bbox']
                    if bbox[2] <= slice_idx <= bbox[5]:
                        rect = patches.Rectangle(
                            (bbox[0], bbox[1]), bbox[3] - bbox[0], bbox[4] - bbox[1],
                            linewidth=2, edgecolor='red', facecolor='none',
                            linestyle=':'
                        )
                        ax.add_patch(rect)
                        ax.text(bbox[0], bbox[1] - 5, f'误报: {detection["confidence"]:.2f}',
                               color='red', fontsize=8)
            
            # 右侧：验证指标
            ax_metrics = fig.add_subplot(gs[0, 3])
            ax_metrics.axis('off')
            metrics_text = f"""验证结果:
            
真实标注: {validation_result['ground_truth_count']}
检测结果: {validation_result['detection_count']}

正确检测: {validation_result['true_positives']}
误报: {validation_result['false_positives']}  
漏检: {validation_result['false_negatives']}

精度: {validation_result['precision']:.3f}
召回率: {validation_result['recall']:.3f}
F1分数: {validation_result['f1_score']:.3f}

平均IoU: {validation_result['average_iou']:.3f}
平均距离: {validation_result['average_distance']:.1f}

{validation_result['validation_summary']}"""
            
            ax_metrics.text(0.05, 0.95, metrics_text, transform=ax_metrics.transAxes,
                           fontsize=11, verticalalignment='top', fontfamily='monospace')
            
            # 下行：详细分析图表
            # 置信度分布
            ax_conf = fig.add_subplot(gs[1, 0])
            if detections:
                confidences = [d['confidence'] for d in detections]
                ax_conf.hist(confidences, bins=10, alpha=0.7, color='skyblue', edgecolor='black')
                ax_conf.set_title('检测置信度分布')
                ax_conf.set_xlabel('置信度')
                ax_conf.set_ylabel('数量')
            
            # IoU分布（仅匹配的）
            ax_iou = fig.add_subplot(gs[1, 1])
            if validation_result.get('matches'):
                ious = [m['iou'] for m in validation_result['matches']]
                ax_iou.hist(ious, bins=10, alpha=0.7, color='lightgreen', edgecolor='black')
                ax_iou.set_title('IoU分布（匹配检测）')
                ax_iou.set_xlabel('IoU')
                ax_iou.set_ylabel('数量')
            
            # 混淆矩阵风格的总结
            ax_summary = fig.add_subplot(gs[1, 2:])
            categories = ['正确检测', '误报', '漏检']
            values = [validation_result['true_positives'], 
                     validation_result['false_positives'],
                     validation_result['false_negatives']]
            colors = ['green', 'red', 'orange']
            
            bars = ax_summary.bar(categories, values, color=colors, alpha=0.7)
            ax_summary.set_title('检测结果汇总')
            ax_summary.set_ylabel('数量')
            
            # 添加数值标签
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax_summary.text(bar.get_x() + bar.get_width()/2., height,
                               f'{value}', ha='center', va='bottom', fontweight='bold')
            
            plt.suptitle(f'检测结果验证报告 - 任务 {task_id[:8]}', fontsize=16)
            
            # 保存图像
            filename = f"{task_id}_validation.png"
            save_path = os.path.join(save_dir, filename)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return filename
            
        except Exception as e:
            self.logger.error(f"创建对比可视化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return "" 