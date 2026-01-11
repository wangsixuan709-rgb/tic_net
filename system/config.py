import os
import torch
from pathlib import Path

class SystemConfig:
    """系统配置类"""
    
    def __init__(self):
        # 基础路径设置
        self.BASE_DIR = Path(__file__).parent.parent
        self.SYSTEM_DIR = self.BASE_DIR / 'system'
        
        # 数据存储路径
        self.UPLOAD_FOLDER = self.BASE_DIR / 'uploads'
        self.RESULTS_FOLDER = self.BASE_DIR / 'system_results'
        self.VISUALIZATION_FOLDER = self.BASE_DIR / 'visualizations'
        self.MODELS_FOLDER = self.BASE_DIR / 'models'
        
        # 创建必要的目录
        self._create_directories()
        
        # 模型配置
        # 优先使用已训练的模型权重
        trained_model_path = self.BASE_DIR / 'results' / 'ticnet' / '2_fold' / 'model' / '100_best.pth'
        fallback_model_path = self.MODELS_FOLDER / 'best_model.pth'
        
        self.MODEL_CONFIG = {
            'model_path': trained_model_path if trained_model_path.exists() else fallback_model_path,
            'config_path': self.BASE_DIR / 'config.py',
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
            'batch_size': 1,
            'num_workers': 2,
            'trained_model_available': trained_model_path.exists()
        }
        
        # 推理配置
        self.INFERENCE_CONFIG = {
            'min_confidence': 0.7,  # 只显示置信度>=0.7的检测框
            'nms_threshold': 0.1,
            'max_detections': 100,
            'crop_size': [128, 128, 128],
            'stride': 4,
            'auto_convert_mhd_to_nrrd': True  # 自动将MHD转换为NRRD
        }
        
        # 可视化配置
        self.VISUALIZATION_CONFIG = {
            'slice_thickness': 1.0,
            'output_format': 'png',
            'colormap': 'hot',
            'alpha': 0.7,
            'save_original': True,
            'save_overlay': True,
            'save_3d_view': True
        }
        
        # Web界面配置
        self.WEB_CONFIG = {
            'max_file_size': 500 * 1024 * 1024,  # 500MB
            'allowed_extensions': {'.mhd', '.nii', '.nii.gz', '.nrrd', '.nhdr', '.dcm', '.npy'},
            'results_per_page': 20,
            'auto_cleanup_days': 30
        }
        
        # 日志配置
        self.LOG_CONFIG = {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': self.BASE_DIR / 'logs' / 'system.log'
        }
        
    def _create_directories(self):
        """创建必要的目录"""
        directories = [
            self.UPLOAD_FOLDER,
            self.RESULTS_FOLDER,
            self.VISUALIZATION_FOLDER,
            self.MODELS_FOLDER,
            self.BASE_DIR / 'logs'
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_model_path(self):
        """获取模型路径"""
        return str(self.MODEL_CONFIG['model_path'])
    
    def get_device(self):
        """获取计算设备"""
        return self.MODEL_CONFIG['device']
    
    def is_cuda_available(self):
        """检查CUDA是否可用"""
        return torch.cuda.is_available()
    
    def get_upload_path(self, filename):
        """获取上传文件的完整路径"""
        return str(self.UPLOAD_FOLDER / filename)
    
    def get_result_path(self, filename):
        """获取结果文件的完整路径"""
        return str(self.RESULTS_FOLDER / filename)
    
    def get_visualization_path(self, filename):
        """获取可视化文件的完整路径"""
        return str(self.VISUALIZATION_FOLDER / filename)
    
    def __str__(self):
        """返回配置信息的字符串表示"""
        return f"""
TiCNet系统配置:
- 基础目录: {self.BASE_DIR}
- 计算设备: {self.MODEL_CONFIG['device']}
- CUDA可用: {self.is_cuda_available()}
- 上传目录: {self.UPLOAD_FOLDER}
- 结果目录: {self.RESULTS_FOLDER}
- 可视化目录: {self.VISUALIZATION_FOLDER}
""" 