import pandas as pd
import numpy as np
import os
import re
from typing import List, Tuple, Dict, Any
import logging

class AnnotationHandler:
    """处理LUNA16注解数据的类"""
    
    def __init__(self, annotations_path: str = None, seriesuids_path: str = None):
        self.logger = self._setup_logger()
        
        # 获取项目根目录（annotation_handler.py所在目录的上一级）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # 设置默认路径（使用绝对路径）
        if annotations_path is None:
            annotations_path = os.path.join(project_root, "annotations", "annotations.csv")
        if seriesuids_path is None:
            seriesuids_path = os.path.join(project_root, "annotations", "seriesuids.csv")
            
        self.annotations_path = annotations_path
        self.seriesuids_path = seriesuids_path
        
        self.logger.info(f"标注文件路径: {self.annotations_path}")
        self.logger.info(f"SeriesUID文件路径: {self.seriesuids_path}")
        
        # 加载注解数据
        self.annotations_df = None
        self.seriesuids_list = None
        self._load_annotations()
    
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('AnnotationHandler')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_annotations(self):
        """加载注解文件"""
        try:
            if os.path.exists(self.annotations_path):
                self.annotations_df = pd.read_csv(self.annotations_path)
                self.logger.info(f"成功加载annotations文件: {len(self.annotations_df)} 条记录")
            else:
                self.logger.warning(f"未找到annotations文件: {self.annotations_path}")
                
            if os.path.exists(self.seriesuids_path):
                self.seriesuids_list = pd.read_csv(self.seriesuids_path, header=None)[0].tolist()
                self.logger.info(f"成功加载seriesuids文件: {len(self.seriesuids_list)} 个序列")
            else:
                self.logger.warning(f"未找到seriesuids文件: {self.seriesuids_path}")
                
        except Exception as e:
            self.logger.error(f"加载注解文件失败: {str(e)}")
    
    def extract_seriesuid_from_path(self, file_path: str) -> str:
        """从文件路径中提取seriesuid"""
        # 方法1: 从文件名中提取（如果文件名就是seriesuid）
        filename = os.path.basename(file_path)
        filename_without_ext = os.path.splitext(filename)[0]
        
        # 检查是否是LUNA16的seriesuid格式
        luna16_pattern = r'1\.3\.6\.1\.4\.1\.14519\.5\.2\.1\.6279\.6001\.\d+'
        
        if re.match(luna16_pattern, filename_without_ext):
            return filename_without_ext
        
        # 方法2: 从路径中提取（如果在目录名中）
        path_parts = file_path.split(os.sep)
        for part in path_parts:
            if re.match(luna16_pattern, part):
                return part
        
        # 方法3: 尝试从文件名中提取（去掉可能的前缀/后缀）
        for part in filename_without_ext.split('_'):
            if re.match(luna16_pattern, part):
                return part
        
        self.logger.warning(f"无法从路径中提取seriesuid: {file_path}")
        return None
    
    def get_annotations_for_seriesuid(self, seriesuid: str) -> List[Dict[str, float]]:
        """获取指定seriesuid的所有注解"""
        if self.annotations_df is None:
            return []
        
        # 筛选出该seriesuid的注解
        series_annotations = self.annotations_df[
            self.annotations_df['seriesuid'] == seriesuid
        ]
        
        annotations = []
        for _, row in series_annotations.iterrows():
            annotation = {
                'coordX': float(row['coordX']),
                'coordY': float(row['coordY']), 
                'coordZ': float(row['coordZ']),
                'diameter_mm': float(row['diameter_mm'])
            }
            annotations.append(annotation)
        
        self.logger.info(f"找到seriesuid {seriesuid} 的 {len(annotations)} 个注解")
        return annotations
    
    def convert_world_to_voxel_coords(self, world_coords: List[Dict], 
                                    spacing: Tuple[float, float, float],
                                    origin: Tuple[float, float, float]) -> List[Dict]:
        """将世界坐标转换为体素坐标"""
        voxel_coords = []
        
        self.logger.info(f"坐标转换参数:")
        self.logger.info(f"  Origin:  {origin}")
        self.logger.info(f"  Spacing: {spacing}")
        
        for i, coord in enumerate(world_coords):
            self.logger.info(f"  结节 {i+1} 世界坐标: ({coord['coordX']:.2f}, {coord['coordY']:.2f}, {coord['coordZ']:.2f})")
            
            # 世界坐标到体素坐标的转换
            # voxel = (world - origin) / spacing
            voxel_x = (coord['coordX'] - origin[0]) / spacing[0]
            voxel_y = (coord['coordY'] - origin[1]) / spacing[1]
            voxel_z = (coord['coordZ'] - origin[2]) / spacing[2]
            
            self.logger.info(f"  转换后体素坐标: ({voxel_x:.2f}, {voxel_y:.2f}, {voxel_z:.2f})")
            
            # 计算体素尺寸的半径
            radius_x = (coord['diameter_mm'] / 2.0) / spacing[0]
            radius_y = (coord['diameter_mm'] / 2.0) / spacing[1]
            radius_z = (coord['diameter_mm'] / 2.0) / spacing[2]
            
            voxel_coord = {
                'voxel_x': voxel_x,
                'voxel_y': voxel_y,
                'voxel_z': voxel_z,
                'radius_x': radius_x,
                'radius_y': radius_y,
                'radius_z': radius_z,
                'diameter_mm': coord['diameter_mm']
            }
            voxel_coords.append(voxel_coord)
        
        return voxel_coords
    
    def create_truth_boxes_and_labels(self, annotations: List[Dict], 
                                     image_shape: Tuple[int, int, int]) -> Tuple[List, List]:
        """创建truth_boxes和truth_labels用于模型输入
        
        Args:
            annotations: 体素坐标的注解列表
            image_shape: 图像尺寸 (depth, height, width) 或 (z, y, x)
        """
        if not annotations:
            # 没有注解时返回空列表
            return [], []
        
        truth_boxes = []
        truth_labels = []
        
        self.logger.info(f"图像尺寸 (image_shape): {image_shape}")
        
        for i, annotation in enumerate(annotations):
            # 获取体素坐标
            x, y, z = annotation['voxel_x'], annotation['voxel_y'], annotation['voxel_z']
            rx, ry, rz = annotation['radius_x'], annotation['radius_y'], annotation['radius_z']
            
            self.logger.info(f"注解 {i+1}: 体素坐标=({x:.2f}, {y:.2f}, {z:.2f}), 半径=({rx:.2f}, {ry:.2f}, {rz:.2f})")
            
            # 检查坐标是否在图像范围内
            # image_shape的格式取决于输入，需要判断
            # SimpleITK: (width, height, depth) -> (x, y, z)
            # NumPy: (depth, height, width) -> (z, y, x)
            
            # 先尝试NumPy格式 (z, y, x)
            in_bounds_numpy = (0 <= x < image_shape[2] and 
                              0 <= y < image_shape[1] and 
                              0 <= z < image_shape[0])
            
            # 再尝试SimpleITK格式 (x, y, z)
            in_bounds_sitk = (0 <= x < image_shape[0] and 
                             0 <= y < image_shape[1] and 
                             0 <= z < image_shape[2])
            
            # 根据哪种格式合理来判断
            if in_bounds_numpy:
                self.logger.info(f"   ✅ 坐标在范围内 (NumPy格式)")
                # 创建边界框 [x1, y1, z1, x2, y2, z2]
                x1 = max(0, x - rx)
                y1 = max(0, y - ry)
                z1 = max(0, z - rz)
                x2 = min(image_shape[2], x + rx)
                y2 = min(image_shape[1], y + ry)
                z2 = min(image_shape[0], z + rz)
                
                truth_boxes.append([x1, y1, z1, x2, y2, z2])
                truth_labels.append(1)
            elif in_bounds_sitk:
                self.logger.info(f"   ✅ 坐标在范围内 (SimpleITK格式)")
                # 创建边界框 [x1, y1, z1, x2, y2, z2]
                x1 = max(0, x - rx)
                y1 = max(0, y - ry)
                z1 = max(0, z - rz)
                x2 = min(image_shape[0], x + rx)
                y2 = min(image_shape[1], y + ry)
                z2 = min(image_shape[2], z + rz)
                
                truth_boxes.append([x1, y1, z1, x2, y2, z2])
                truth_labels.append(1)
            else:
                self.logger.warning(f"   ❌ 坐标超出范围！")
                self.logger.warning(f"      x={x:.2f}, y={y:.2f}, z={z:.2f}")
                self.logger.warning(f"      image_shape={image_shape}")
        
        return truth_boxes, truth_labels
    
    def get_truth_data_for_image(self, file_path: str, 
                                spacing: Tuple[float, float, float],
                                origin: Tuple[float, float, float],
                                image_shape: Tuple[int, int, int],
                                meta_info: dict = None) -> Tuple[List, List]:
        """为指定图像获取truth数据"""
        try:
            # 检查是否是分割文件（_seg后缀）
            if '_seg' in os.path.basename(file_path).lower():
                self.logger.warning(f"检测到分割文件（_seg），跳过LUNA16标注加载")
                self.logger.warning(f"分割文件的origin通常被重置，无法使用原始标注")
                return [], []
            
            # 检查origin是否合理（LUNA16原始数据的origin通常是负数且较大）
            # 如果origin接近(0,0,0)，很可能是处理过的图像或.npy文件
            if abs(origin[0]) < 10 and abs(origin[1]) < 10 and abs(origin[2]) < 10:
                self.logger.warning(f"Origin接近(0,0,0)，这可能不是原始LUNA16图像")
                self.logger.warning(f"Origin: {origin}，无法使用LUNA16标注")
                self.logger.info(f"提示：LUNA16原始图像的origin通常是较大的负数，如(-375, -242, -347)")
                self.logger.info(f"提示：请使用原始NRRD或MHD格式的CT文件")
                return [], []
            
            # 提取seriesuid
            seriesuid = self.extract_seriesuid_from_path(file_path)
            if not seriesuid:
                self.logger.warning(f"无法提取seriesuid，使用空的truth数据")
                return [], []
            
            # 获取注解
            world_annotations = self.get_annotations_for_seriesuid(seriesuid)
            if not world_annotations:
                self.logger.info(f"seriesuid {seriesuid} 没有注解，使用空的truth数据")
                return [], []
            
            # 转换为体素坐标
            voxel_annotations = self.convert_world_to_voxel_coords(
                world_annotations, spacing, origin
            )
            
            # 创建truth数据
            truth_boxes, truth_labels = self.create_truth_boxes_and_labels(
                voxel_annotations, image_shape
            )
            
            self.logger.info(f"为seriesuid {seriesuid} 创建了 {len(truth_boxes)} 个truth boxes")
            return truth_boxes, truth_labels
            
        except Exception as e:
            self.logger.error(f"获取truth数据失败: {str(e)}")
            return [], [] 