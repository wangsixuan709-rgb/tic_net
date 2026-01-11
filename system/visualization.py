import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import SimpleITK as sitk
import cv2
import os
import logging
from typing import Dict, List, Tuple, Any
import traceback
from PIL import Image

class ResultVisualizer:
    """检测结果可视化类"""
    
    def __init__(self, config):
        self.config = config
        self.logger = self._setup_logger()
        
        # 设置matplotlib参数 - 使用英文显示
        self.use_chinese = False  # 强制使用英文，避免字体问题
        
        try:
            # 使用标准英文字体
            plt.rcParams['font.family'] = 'DejaVu Sans'
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'Arial', 'sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['figure.dpi'] = 100
            plt.rcParams['savefig.dpi'] = 150
            plt.rcParams['font.size'] = 10
            
            self.logger.info("Using English display to avoid font issues")
            
        except Exception as e:
            self.logger.warning(f"Font setup failed: {str(e)}")
        
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('ResultVisualizer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def create_preview(self, image_path: str, task_id: str) -> str:
        """创建上传文件的预览图像
        
        Args:
            image_path: 图像文件路径
            task_id: 任务ID
            
        Returns:
            预览图像的文件名
        """
        try:
            self.logger.info(f"正在为任务 {task_id} 创建预览图像")
            
            # 读取图像
            image_data = self._load_image(image_path)
            depth, height, width = image_data.shape
            
            # 选择代表性的切片（均匀分布）
            num_slices = min(9, depth)  # 最多显示9个切片
            indices = np.linspace(0, depth - 1, num_slices, dtype=int)
            
            # 创建网格布局
            cols = 3
            rows = (num_slices + cols - 1) // cols
            
            fig, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows))
            
            # 确保axes是可迭代的
            if num_slices == 1:
                axes = [axes]
            elif rows == 1:
                axes = [axes] if not hasattr(axes, '__iter__') else list(axes)
            else:
                axes = axes.flatten()
            
            # 显示每个切片
            for i, idx in enumerate(indices):
                if i < len(axes):
                    axes[i].imshow(image_data[idx], cmap='gray')
                    if self.use_chinese:
                        title = f'切片 {idx}/{depth-1} ({idx/depth*100:.1f}%)'
                    else:
                        title = f'Slice {idx}/{depth-1} ({idx/depth*100:.1f}%)'
                    axes[i].set_title(title, fontsize=12)
                    axes[i].axis('off')
            
            # 隐藏多余的子图
            for i in range(num_slices, len(axes)):
                axes[i].axis('off')
            
            # 添加总标题
            if self.use_chinese:
                main_title = f'CT图像预览 - 形状: {depth}×{height}×{width}'
            else:
                main_title = f'CT Image Preview - Shape: {depth}×{height}×{width}'
            fig.suptitle(main_title, fontsize=16, fontweight='bold')
            
            plt.tight_layout()
            
            # 保存预览图像
            filename = f"{task_id}_preview.png"
            save_path = os.path.join(self.config.VISUALIZATION_FOLDER, filename)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"预览图像创建成功: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"创建预览图像失败: {str(e)}")
            traceback.print_exc()
            return ""
    
    def create_visualizations(self, image_path: str, results: Dict, task_id: str, ground_truth_boxes: List = None) -> Dict[str, str]:
        """创建检测结果的可视化图像"""
        try:
            self.logger.info(f"正在为任务 {task_id} 创建可视化结果")
            
            if ground_truth_boxes is None:
                ground_truth_boxes = []
            
            visualization_paths = {}
            
            # 读取原始图像
            image_data = self._load_image(image_path)
            detections = results['detections']
            
            # 创建不同类型的可视化
            if self.config.VISUALIZATION_CONFIG['save_original']:
                original_path = self._create_original_slices(
                    image_data, task_id, detections, ground_truth_boxes
                )
                visualization_paths['original_slices'] = original_path
            
            if self.config.VISUALIZATION_CONFIG['save_overlay']:
                overlay_path = self._create_overlay_visualization(
                    image_data, task_id, detections
                )
                visualization_paths['overlay'] = overlay_path
            
            if self.config.VISUALIZATION_CONFIG['save_3d_view']:
                summary_path = self._create_detection_summary(
                    image_data, task_id, detections, ground_truth_boxes
                )
                visualization_paths['summary'] = summary_path
            
            self.logger.info(f"可视化结果创建完成，任务ID: {task_id}")
            return visualization_paths
            
        except Exception as e:
            self.logger.error(f"创建可视化结果失败: {str(e)}")
            traceback.print_exc()
            return {}
    
    def _load_image(self, image_path: str) -> np.ndarray:
        """加载医学图像"""
        try:
            self.logger.info(f"正在加载图像: {image_path}")
            
            if image_path.endswith('.mhd'):
                image = sitk.ReadImage(image_path)
                image_array = sitk.GetArrayFromImage(image)
            elif image_path.endswith(('.nii', '.nii.gz')):
                image = sitk.ReadImage(image_path)
                image_array = sitk.GetArrayFromImage(image)
            elif image_path.endswith(('.nrrd', '.nhdr')):
                # NRRD格式处理
                try:
                    image = sitk.ReadImage(image_path)
                    image_array = sitk.GetArrayFromImage(image)
                    self.logger.info(f"NRRD图像加载成功，形状: {image_array.shape}")
                except Exception as e:
                    self.logger.warning(f"SimpleITK加载NRRD失败，尝试pynrrd: {str(e)}")
                    import nrrd
                    image_array, header = nrrd.read(image_path)
                    self.logger.info(f"pynrrd加载成功，形状: {image_array.shape}")
            elif image_path.endswith('.dcm'):
                image = sitk.ReadImage(image_path)
                image_array = sitk.GetArrayFromImage(image)
            elif image_path.endswith('.npy'):
                # NumPy格式
                self.logger.info("加载NumPy文件...")
                image_array = np.load(image_path)
                
                # 确保是3D数组
                if len(image_array.shape) == 2:
                    image_array = image_array[np.newaxis, ...]
                elif len(image_array.shape) == 4:
                    if image_array.shape[0] == 1:
                        image_array = np.squeeze(image_array, axis=0)
                    elif image_array.shape[3] == 1:
                        image_array = np.squeeze(image_array, axis=3)
                
                self.logger.info(f"NumPy数组加载成功，形状: {image_array.shape}")
            else:
                # 对于其他格式
                img = Image.open(image_path).convert('L')
                image_array = np.array(img)
                if len(image_array.shape) == 2:
                    image_array = image_array[np.newaxis, ...]
            
            self.logger.info(f"原始图像形状: {image_array.shape}, 数据类型: {image_array.dtype}")
            self.logger.info(f"数值范围: [{image_array.min():.2f}, {image_array.max():.2f}]")
            
            # 归一化到0-255
            image_array = self._normalize_for_display(image_array)
            self.logger.info(f"归一化后形状: {image_array.shape}, 数值范围: [{image_array.min()}, {image_array.max()}]")
            
            return image_array
            
        except Exception as e:
            self.logger.error(f"加载图像失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _normalize_for_display(self, image: np.ndarray) -> np.ndarray:
        """将图像归一化到0-255范围用于显示"""
        # 移除异常值
        p1, p99 = np.percentile(image, [1, 99])
        image = np.clip(image, p1, p99)
        
        # 归一化到0-255
        image = (image - image.min()) / (image.max() - image.min() + 1e-8)
        image = (image * 255).astype(np.uint8)
        
        return image
    
    def _create_original_slices(self, image: np.ndarray, task_id: str, detections: List[Dict], ground_truth_boxes: List = None) -> str:
        """创建原始图像切片的可视化"""
        try:
            if ground_truth_boxes is None:
                ground_truth_boxes = []
                
            depth, height, width = image.shape
            
            # 选择有检测结果或ground truth的关键切片
            key_slices = []
            
            # 从检测结果收集切片
            for detection in detections:
                bbox = detection['bbox']
                center_z = int((bbox[2] + bbox[5]) / 2)
                if 0 <= center_z < depth:
                    key_slices.append(center_z)
            
            # 从ground truth收集切片
            for gt_box in ground_truth_boxes:
                center_z = int((gt_box[2] + gt_box[5]) / 2)
                if 0 <= center_z < depth:
                    key_slices.append(center_z)
            
            # 如果没有检测结果和ground truth，均匀选择切片
            if not key_slices:
                key_slices = [depth // 5, 2*depth // 5, 3*depth // 5, 4*depth // 5]
            
            # 去重并排序
            key_slices = sorted(list(set(key_slices)))
            key_slices = key_slices[:9]  # 最多显示9个切片
            
            # 创建图像网格
            n_slices = len(key_slices)
            cols = min(3, n_slices)
            rows = (n_slices + cols - 1) // cols
            
            fig, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows))
            if n_slices == 1:
                axes = [axes]
            elif rows == 1:
                axes = axes if isinstance(axes, list) or hasattr(axes, '__iter__') else [axes]
            else:
                axes = axes.flatten()
            
            for i, slice_idx in enumerate(key_slices):
                if i < len(axes):
                    axes[i].imshow(image[slice_idx], cmap='gray')
                    if self.use_chinese:
                        axes[i].set_title(f'切片 {slice_idx}')
                    else:
                        axes[i].set_title(f'Slice {slice_idx}')
                    axes[i].axis('off')
                    
                    # 在该切片上绘制ground truth框（绿色）
                    for gt_box in ground_truth_boxes:
                        if gt_box[2] <= slice_idx <= gt_box[5]:  # GT框包含当前切片
                            rect = patches.Rectangle(
                                (gt_box[0], gt_box[1]), 
                                gt_box[3] - gt_box[0], 
                                gt_box[4] - gt_box[1],
                                linewidth=2, 
                                edgecolor='green', 
                                facecolor='none',
                                linestyle='--'
                            )
                            axes[i].add_patch(rect)
                            
                            # 添加GT标签
                            axes[i].text(
                                gt_box[0], gt_box[1] - 15, 
                                'GT',
                                color='green', fontsize=10, fontweight='bold',
                                bbox=dict(boxstyle='round,pad=0.3', facecolor='green', alpha=0.3)
                            )
                    
                    # 在该切片上绘制检测框（红色，只显示置信度>=0.7的）
                    for detection in detections:
                        if detection['confidence'] >= 0.7:  # 只显示高置信度检测框
                            bbox = detection['bbox']
                            if bbox[2] <= slice_idx <= bbox[5]:  # 检测框包含当前切片
                                rect = patches.Rectangle(
                                    (bbox[0], bbox[1]), 
                                    bbox[3] - bbox[0], 
                                    bbox[4] - bbox[1],
                                    linewidth=2, 
                                    edgecolor='red', 
                                    facecolor='none'
                                )
                                axes[i].add_patch(rect)
                                
                                # 添加置信度标签
                                axes[i].text(
                                    bbox[0], bbox[1] - 5, 
                                    f'{detection["confidence"]:.2f}',
                                    color='red', fontsize=10, fontweight='bold',
                                    bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.3)
                                )
            
            # 隐藏多余的子图
            for i in range(n_slices, len(axes)):
                axes[i].axis('off')
            
            plt.tight_layout()
            
            # 保存图像
            filename = f"{task_id}_original_slices.png"
            save_path = os.path.join(self.config.VISUALIZATION_FOLDER, filename)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return filename
            
        except Exception as e:
            self.logger.error(f"创建原始切片可视化失败: {str(e)}")
            return ""
    
    def _create_overlay_visualization(self, image: np.ndarray, task_id: str, detections: List[Dict]) -> str:
        """创建检测结果叠加可视化"""
        try:
            depth, height, width = image.shape
            
            # 创建检测热图
            heatmap = np.zeros_like(image, dtype=np.float32)
            
            for detection in detections:
                bbox = detection['bbox']
                confidence = detection['confidence']
                
                # 确保坐标在有效范围内
                z1, y1, x1 = max(0, int(bbox[2])), max(0, int(bbox[1])), max(0, int(bbox[0]))
                z2, y2, x2 = min(depth, int(bbox[5])), min(height, int(bbox[4])), min(width, int(bbox[3]))
                
                # 在检测区域填充置信度值
                heatmap[z1:z2, y1:y2, x1:x2] = np.maximum(
                    heatmap[z1:z2, y1:y2, x1:x2], confidence
                )
            
            # 选择最具代表性的切片
            if detections:
                # 选择包含最多检测结果的切片
                slice_scores = np.sum(heatmap, axis=(1, 2))
                best_slice = np.argmax(slice_scores)
            else:
                best_slice = depth // 2
            
            # 创建叠加图像
            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
            
            # 原始图像
            ax1.imshow(image[best_slice], cmap='gray')
            ax1.set_title('原始图像' if self.use_chinese else 'Original Image')
            ax1.axis('off')
            
            # 检测热图
            ax2.imshow(heatmap[best_slice], cmap='hot', alpha=0.8)
            ax2.set_title('检测热图' if self.use_chinese else 'Detection Heatmap')
            ax2.axis('off')
            
            # 叠加图像
            ax3.imshow(image[best_slice], cmap='gray')
            ax3.imshow(heatmap[best_slice], cmap='hot', alpha=0.5)
            ax3.set_title('叠加结果' if self.use_chinese else 'Overlay Result')
            ax3.axis('off')
            
            # 添加检测框（只显示置信度>=0.7的）
            for detection in detections:
                if detection['confidence'] >= 0.7:  # 只显示高置信度检测框
                    bbox = detection['bbox']
                    if bbox[2] <= best_slice <= bbox[5]:
                        for ax in [ax1, ax3]:
                            rect = patches.Rectangle(
                                (bbox[0], bbox[1]), 
                                bbox[3] - bbox[0], 
                                bbox[4] - bbox[1],
                                linewidth=2, 
                                edgecolor='yellow', 
                                facecolor='none'
                            )
                            ax.add_patch(rect)
            
            plt.tight_layout()
            
            # 保存图像
            filename = f"{task_id}_overlay.png"
            save_path = os.path.join(self.config.VISUALIZATION_FOLDER, filename)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return filename
            
        except Exception as e:
            self.logger.error(f"创建叠加可视化失败: {str(e)}")
            return ""
    
    def _create_detection_summary(self, image: np.ndarray, task_id: str, 
                                detections: List[Dict], ground_truth_boxes: List = None) -> str:
        """创建检测结果汇总图 - 显示多个切片"""
        try:
            if ground_truth_boxes is None:
                ground_truth_boxes = []
                
            depth, height, width = image.shape
            
            # 收集关键切片（从检测结果和ground truth）
            key_slices = []
            
            # 从检测结果收集
            for detection in detections:
                if detection['confidence'] >= 0.7:
                    bbox = detection['bbox']
                    center_z = int((bbox[2] + bbox[5]) / 2)
                    if 0 <= center_z < depth:
                        key_slices.append(center_z)
            
            # 从ground truth收集
            for gt_box in ground_truth_boxes:
                center_z = int((gt_box[2] + gt_box[5]) / 2)
                if 0 <= center_z < depth:
                    key_slices.append(center_z)
            
            # 如果切片不足12个，补充均匀分布的切片
            if len(key_slices) < 12:
                uniform_slices = np.linspace(depth//6, depth - depth//6, 12).astype(int)
                key_slices.extend(uniform_slices.tolist())
            
            # 去重并排序，选择12个最具代表性的切片
            key_slices = sorted(list(set(key_slices)))
            key_slices = key_slices[:12]
            
            # 创建4x3的网格布局
            fig, axes = plt.subplots(3, 4, figsize=(20, 15))
            axes = axes.flatten()
            
            for i, slice_idx in enumerate(key_slices):
                if i < len(axes):
                    axes[i].imshow(image[slice_idx], cmap='gray')
                    
                    # 标题
                    title = f'Slice {slice_idx} ({slice_idx/depth:.0%})' if not self.use_chinese else f'切片 {slice_idx} ({slice_idx/depth:.0%})'
                    axes[i].set_title(title, fontsize=11, pad=5)
                    axes[i].axis('off')
                    
                    # 绘制ground truth框（绿色虚线）
                    for gt_box in ground_truth_boxes:
                        if gt_box[2] <= slice_idx <= gt_box[5]:
                            rect = patches.Rectangle(
                                (gt_box[0], gt_box[1]), 
                                gt_box[3] - gt_box[0], 
                                gt_box[4] - gt_box[1],
                                linewidth=2.5, 
                                edgecolor='lime', 
                                facecolor='none',
                                linestyle='--'
                            )
                            axes[i].add_patch(rect)
                            
                            # GT标签
                            axes[i].text(
                                gt_box[0], gt_box[1] - 8, 
                                'GT',
                                color='lime', fontsize=9, fontweight='bold',
                                bbox=dict(boxstyle='round,pad=0.3', facecolor='lime', alpha=0.4)
                            )
                    
                    # 绘制检测框（红色实线，只显示置信度>=0.7的）
                    for detection in detections:
                        if detection['confidence'] >= 0.7:
                            bbox = detection['bbox']
                            if bbox[2] <= slice_idx <= bbox[5]:
                                rect = patches.Rectangle(
                                    (bbox[0], bbox[1]), 
                                    bbox[3] - bbox[0], 
                                    bbox[4] - bbox[1],
                                    linewidth=2.5, 
                                    edgecolor='red', 
                                    facecolor='none'
                                )
                                axes[i].add_patch(rect)
                                
                                # 置信度标签
                                axes[i].text(
                                    bbox[0], bbox[1] - 8, 
                                    f'{detection["confidence"]:.2f}',
                                    color='red', fontsize=9, fontweight='bold',
                                    bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.4)
                                )
            
            # 隐藏多余的子图
            for i in range(len(key_slices), len(axes)):
                axes[i].axis('off')
            
            # 添加图例
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], color='red', linewidth=2.5, label='检测框 (Pred, conf≥0.7)' if self.use_chinese else 'Detection (Pred, conf≥0.7)')
            ]
            if len(ground_truth_boxes) > 0:
                legend_elements.append(
                    Line2D([0], [0], color='lime', linewidth=2.5, linestyle='--', label='真实标注 (GT)' if self.use_chinese else 'Ground Truth (GT)')
                )
            
            fig.legend(handles=legend_elements, loc='upper center', ncol=2, fontsize=12, 
                      bbox_to_anchor=(0.5, 0.98), frameon=True, fancybox=True, shadow=True)
            
            # 总标题
            if self.use_chinese:
                suptitle = f'TiCNet 肺结节检测结果 - 任务 {task_id[:8]}'
            else:
                suptitle = f'TiCNet Nodule Detection Results - Task {task_id[:8]}'
            plt.suptitle(suptitle, fontsize=16, y=0.995)
            
            plt.tight_layout(rect=[0, 0, 1, 0.96])
            
            # 保存图像
            filename = f"{task_id}_summary.png"
            save_path = os.path.join(self.config.VISUALIZATION_FOLDER, filename)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return filename
            
        except Exception as e:
            self.logger.error(f"创建汇总可视化失败: {str(e)}")
            traceback.print_exc()
            return ""
    
    def _plot_detection_statistics(self, ax, statistics):
        """绘制检测统计图表"""
        if self.use_chinese:
            categories = ['高置信度\n(≥0.7)', '中等置信度\n(0.4-0.7)', '低置信度\n(<0.4)']
            title = '检测结果统计'
            ylabel = '数量'
        else:
            categories = ['High Conf.\n(≥0.7)', 'Medium Conf.\n(0.4-0.7)', 'Low Conf.\n(<0.4)']
            title = 'Detection Statistics'
            ylabel = 'Count'
            
        counts = [
            statistics['high_confidence_count'],
            statistics['medium_confidence_count'],
            statistics['low_confidence_count']
        ]
        colors = ['#2E8B57', '#FFD700', '#FF6347']
        
        bars = ax.bar(categories, counts, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax.set_title(title, fontsize=12, pad=15)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.grid(axis='y', alpha=0.3)
        
        # 添加数值标签
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{count}', ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    def _plot_confidence_distribution(self, ax, detections):
        """绘制置信度分布图"""
        if self.use_chinese:
            no_data_text = '无检测结果'
            title = '置信度分布'
            xlabel = '置信度'
            ylabel = '频次'
            avg_label = f'平均值: {np.mean([d["confidence"] for d in detections]):.3f}' if detections else ''
        else:
            no_data_text = 'No Detections'
            title = 'Confidence Distribution'
            xlabel = 'Confidence'
            ylabel = 'Frequency'
            avg_label = f'Average: {np.mean([d["confidence"] for d in detections]):.3f}' if detections else ''
        
        if not detections:
            ax.text(0.5, 0.5, no_data_text, ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title(title, fontsize=12, pad=15)
            return
        
        confidences = [d['confidence'] for d in detections]
        n, bins, patches = ax.hist(confidences, bins=min(10, len(set(confidences))), 
                                  alpha=0.7, color='skyblue', edgecolor='black', linewidth=0.5)
        ax.set_title(title, fontsize=12, pad=15)
        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.grid(axis='y', alpha=0.3)
        
        # 添加平均值线
        mean_conf = np.mean(confidences)
        ax.axvline(mean_conf, color='red', linestyle='--', linewidth=2,
                  label=avg_label)
        ax.legend(fontsize=10)
        
        # 设置x轴范围
        ax.set_xlim(0, 1)
    
    def _plot_detection_list(self, ax, detections):
        """绘制检测结果列表"""
        ax.axis('off')
        
        if not detections:
            no_data = '无检测结果' if self.use_chinese else 'No Detections'
            ax.text(0.5, 0.5, no_data, ha='center', va='center', transform=ax.transAxes)
            return
        
        # 显示前10个最高置信度的检测
        top_detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)[:10]
        
        if self.use_chinese:
            text_content = "Top 检测结果:\n\n"
            for i, det in enumerate(top_detections, 1):
                bbox = det['bbox']
                text_content += f"{i}. 置信度: {det['confidence']:.3f}\n"
                text_content += f"   位置: ({bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f})\n"
                text_content += f"   体积: {det['volume']:.1f} mm³\n\n"
            title = '检测列表'
        else:
            text_content = "Top Detections:\n\n"
            for i, det in enumerate(top_detections, 1):
                bbox = det['bbox']
                text_content += f"{i}. Confidence: {det['confidence']:.3f}\n"
                text_content += f"   Position: ({bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f})\n"
                text_content += f"   Volume: {det['volume']:.1f} mm³\n\n"
            title = 'Detection List'
        
        ax.text(0.05, 0.95, text_content, transform=ax.transAxes, 
               verticalalignment='top', fontsize=9, fontfamily='monospace')
        ax.set_title(title)
    
    def _plot_3d_overview(self, ax, image, detections):
        """绘制3D概览图"""
        depth, height, width = image.shape
        
        # 创建3个正交切面的投影
        # 轴向投影 (从上往下看)
        sagittal_proj = np.mean(image, axis=2)  # 矢状面投影
        
        im = ax.imshow(sagittal_proj, cmap='gray', aspect='auto')
        if self.use_chinese:
            ax.set_title('矢状面投影 (侧视图)')
            ax.set_xlabel('Y轴')
            ax.set_ylabel('Z轴')
        else:
            ax.set_title('Sagittal Projection (Side View)')
            ax.set_xlabel('Y Axis')
            ax.set_ylabel('Z Axis')
        
        # 在投影上标记检测结果
        for detection in detections:
            bbox = detection['bbox']
            center_y = (bbox[1] + bbox[4]) / 2
            center_z = (bbox[2] + bbox[5]) / 2
            
            ax.plot(center_y, center_z, 'ro', markersize=6, alpha=0.8)
            ax.text(center_y + 5, center_z, f'{detection["confidence"]:.2f}',
                   color='red', fontsize=8)
    
    def _plot_volume_distribution(self, ax, detections):
        """绘制体积分布图"""
        if not detections:
            no_data = '无检测结果' if self.use_chinese else 'No Detections'
            title = '体积分布' if self.use_chinese else 'Volume Distribution'
            ax.text(0.5, 0.5, no_data, ha='center', va='center', transform=ax.transAxes)
            ax.set_title(title)
            return
        
        volumes = [d['volume'] for d in detections if d['volume'] > 0]
        if not volumes:
            no_data = '无有效体积数据' if self.use_chinese else 'No Valid Volume Data'
            title = '体积分布' if self.use_chinese else 'Volume Distribution'
            ax.text(0.5, 0.5, no_data, ha='center', va='center', transform=ax.transAxes)
            ax.set_title(title)
            return
        
        ax.hist(volumes, bins=min(10, len(volumes)), alpha=0.7, color='lightgreen', edgecolor='black')
        
        if self.use_chinese:
            ax.set_title('结节体积分布')
            ax.set_xlabel('体积 (mm³)')
            ax.set_ylabel('频次')
            label = f'平均体积: {np.mean(volumes):.1f} mm³'
        else:
            ax.set_title('Nodule Volume Distribution')
            ax.set_xlabel('Volume (mm³)')
            ax.set_ylabel('Frequency')
            label = f'Average: {np.mean(volumes):.1f} mm³'
        
        # 添加统计信息
        ax.axvline(np.mean(volumes), color='red', linestyle='--', label=label)
        ax.legend() 