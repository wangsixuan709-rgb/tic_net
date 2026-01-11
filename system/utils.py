import numpy as np
import torch
import SimpleITK as sitk
from typing import Tuple, Dict, Any
import os

def normalize(img: np.ndarray) -> np.ndarray:
    """图像归一化函数"""
    maximum = img.max()
    minimum = img.min()
    
    # 0 ~ 1
    img = (img - minimum) / max(1, (maximum - minimum))
    
    # -1 ~ 1
    img = img * 2 - 1
    return img

def convert_mhd_to_nrrd(mhd_path: str) -> str:
    """将MHD文件转换为NRRD格式
    
    Args:
        mhd_path: MHD文件路径
        
    Returns:
        转换后的NRRD文件路径
    """
    print(f"正在将MHD转换为NRRD: {mhd_path}")
    
    # 读取MHD文件
    image = sitk.ReadImage(mhd_path)
    
    # 生成NRRD文件路径（与MHD文件同目录）
    nrrd_path = mhd_path.rsplit('.', 1)[0] + '_converted.nrrd'
    
    # 保存为NRRD格式
    sitk.WriteImage(image, nrrd_path)
    
    print(f"✅ 转换完成: {nrrd_path}")
    return nrrd_path

def load_medical_image(image_path: str, auto_convert_to_nrrd: bool = False) -> Tuple[np.ndarray, Dict[str, Any]]:
    """加载医学图像
    
    Args:
        image_path: 图像文件路径
        auto_convert_to_nrrd: 是否自动将MHD转换为NRRD（默认False）
        
    Returns:
        (image_array, meta_info): 图像数组和元数据
    """
    # 如果是MHD文件且需要转换
    if image_path.endswith('.mhd') and auto_convert_to_nrrd:
        print("检测到MHD文件，自动转换为NRRD格式...")
        nrrd_path = convert_mhd_to_nrrd(image_path)
        image_path = nrrd_path  # 使用转换后的NRRD文件
        print(f"使用转换后的文件: {image_path}")
    
    if image_path.endswith('.mhd'):
        # MetaImage格式
        image = sitk.ReadImage(image_path)
        image_array = sitk.GetArrayFromImage(image)
        spacing = image.GetSpacing()
        origin = image.GetOrigin()
        direction = image.GetDirection()
    elif image_path.endswith(('.nii', '.nii.gz')):
        # NIfTI格式
        image = sitk.ReadImage(image_path)
        image_array = sitk.GetArrayFromImage(image)
        spacing = image.GetSpacing()
        origin = image.GetOrigin()
        direction = image.GetDirection()
    elif image_path.endswith(('.nrrd', '.nhdr')):
        # NRRD格式 (Nearly Raw Raster Data)
        try:
            image = sitk.ReadImage(image_path)
            image_array = sitk.GetArrayFromImage(image)
            spacing = image.GetSpacing()
            origin = image.GetOrigin()
            direction = image.GetDirection()
            
            # 处理NRRD特殊情况
            # 某些NRRD文件可能有不同的数据类型或维度顺序
            if len(image_array.shape) == 4 and image_array.shape[3] == 1:
                # 移除单一维度
                image_array = np.squeeze(image_array, axis=3)
            elif len(image_array.shape) == 4 and image_array.shape[0] == 1:
                # 移除第一个单一维度
                image_array = np.squeeze(image_array, axis=0)
                
        except Exception as e:
            print(f"警告: NRRD文件读取遇到问题，尝试使用备用方法: {str(e)}")
            # 尝试使用其他方法读取NRRD
            try:
                import nrrd
                image_array, header = nrrd.read(image_path)
                # 从header中提取spacing信息
                spacing = tuple(header.get('space directions', [1.0, 1.0, 1.0]))
                origin = tuple(header.get('space origin', [0.0, 0.0, 0.0]))
                direction = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
            except ImportError:
                print("提示: 如需更好的NRRD支持，请安装 pynrrd: pip install pynrrd")
                raise Exception("无法读取NRRD文件，请检查文件格式或安装pynrrd包")
    elif image_path.endswith('.dcm'):
        # DICOM格式
        image = sitk.ReadImage(image_path)
        image_array = sitk.GetArrayFromImage(image)
        spacing = image.GetSpacing()
        origin = image.GetOrigin()
        direction = image.GetDirection()
    elif image_path.endswith('.npy'):
        # NumPy格式 - 简单支持
        print("加载NumPy文件...")
        image_array = np.load(image_path)
        
        print(f"原始数组形状: {image_array.shape}, 数据类型: {image_array.dtype}")
        
        # 检查数组维度
        if len(image_array.shape) == 2:
            # 2D图像，添加深度维度
            print(f"检测到2D图像，添加深度维度...")
            image_array = image_array[np.newaxis, ...]
        elif len(image_array.shape) == 4:
            # 4D数组，尝试移除多余维度
            if image_array.shape[0] == 1:
                image_array = np.squeeze(image_array, axis=0)
            elif image_array.shape[3] == 1:
                image_array = np.squeeze(image_array, axis=3)
        
        if len(image_array.shape) != 3:
            raise ValueError(
                f"不支持的数组维度: {image_array.shape}\n"
                f"期望3D数组格式: (depth, height, width)"
            )
        
        # 使用默认spacing和origin（.npy文件通常没有这些信息）
        spacing = (1.0, 1.0, 1.0)
        origin = (0.0, 0.0, 0.0)
        direction = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
        
        print(f"NumPy数组形状: {image_array.shape}, 数据类型: {image_array.dtype}")
        print(f"数值范围: [{image_array.min():.2f}, {image_array.max():.2f}]")
        print("⚠️ 使用默认spacing=(1,1,1)和origin=(0,0,0)")
        print("   提示: .npy文件缺少空间信息，无法显示真实标注框")
    else:
        # 其他格式，使用PIL加载
        from PIL import Image
        img = Image.open(image_path).convert('L')
        image_array = np.array(img)
        if len(image_array.shape) == 2:
            # 为2D图像添加深度维度
            image_array = image_array[np.newaxis, ...]
        spacing = (1.0, 1.0, 1.0)
        origin = (0.0, 0.0, 0.0)
        direction = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    
    meta_info = {
        'spacing': spacing,
        'origin': origin,
        'direction': direction,
        'original_shape': image_array.shape,
        'dtype': str(image_array.dtype)
    }
    
    return image_array, meta_info

def pad_image(image: np.ndarray, target_size: Tuple[int, int, int]) -> np.ndarray:
    """将图像填充到目标尺寸"""
    current_shape = image.shape
    
    # 计算需要填充的大小
    pad_z = max(0, target_size[0] - current_shape[0])
    pad_y = max(0, target_size[1] - current_shape[1])
    pad_x = max(0, target_size[2] - current_shape[2])
    
    # 对称填充
    pad_z_before = pad_z // 2
    pad_z_after = pad_z - pad_z_before
    pad_y_before = pad_y // 2
    pad_y_after = pad_y - pad_y_before
    pad_x_before = pad_x // 2
    pad_x_after = pad_x - pad_x_before
    
    padded_image = np.pad(
        image,
        ((pad_z_before, pad_z_after), 
         (pad_y_before, pad_y_after), 
         (pad_x_before, pad_x_after)),
        mode='constant',
        constant_values=-1
    )
    
    return padded_image

def crop_image(image: np.ndarray, target_size: Tuple[int, int, int]) -> np.ndarray:
    """将图像裁剪到目标尺寸"""
    current_shape = image.shape
    
    # 计算裁剪的起始位置（中心裁剪）
    start_z = max(0, (current_shape[0] - target_size[0]) // 2)
    start_y = max(0, (current_shape[1] - target_size[1]) // 2)
    start_x = max(0, (current_shape[2] - target_size[2]) // 2)
    
    end_z = start_z + target_size[0]
    end_y = start_y + target_size[1]
    end_x = start_x + target_size[2]
    
    cropped_image = image[start_z:end_z, start_y:end_y, start_x:end_x]
    
    return cropped_image

def resize_image(image: np.ndarray, target_size: Tuple[int, int, int]) -> np.ndarray:
    """调整图像尺寸"""
    from scipy import ndimage
    
    current_shape = image.shape
    zoom_factors = [target_size[i] / current_shape[i] for i in range(3)]
    
    resized_image = ndimage.zoom(image, zoom_factors, order=1)
    
    return resized_image

def preprocess_for_model(image: np.ndarray, target_size: Tuple[int, int, int] = (128, 128, 128)) -> torch.Tensor:
    """为模型预处理图像"""
    # 归一化
    image = normalize(image)
    
    # 调整尺寸
    if image.shape != target_size:
        # 先填充后裁剪的策略
        max_dim = max(max(image.shape), max(target_size))
        temp_size = (max_dim, max_dim, max_dim)
        
        # 如果图像小于目标尺寸，先填充
        if any(image.shape[i] < temp_size[i] for i in range(3)):
            image = pad_image(image, temp_size)
        
        # 如果图像大于目标尺寸，再裁剪/调整
        if any(image.shape[i] > target_size[i] for i in range(3)):
            image = resize_image(image, target_size)
    
    # 转换为PyTorch张量
    image_tensor = torch.from_numpy(image.astype(np.float32))
    image_tensor = image_tensor.unsqueeze(0).unsqueeze(0)  # 添加batch和channel维度
    
    return image_tensor

def calculate_volume(bbox: list, spacing: Tuple[float, float, float]) -> float:
    """计算结节体积（以mm³为单位）"""
    try:
        # bbox格式: [x1, y1, z1, x2, y2, z2]
        width = abs(bbox[3] - bbox[0]) * spacing[0]
        height = abs(bbox[4] - bbox[1]) * spacing[1] 
        depth = abs(bbox[5] - bbox[2]) * spacing[2]
        volume = width * height * depth
        return float(volume)
    except:
        return 0.0

def apply_window_level(image: np.ndarray, window_center: float = -600, window_width: float = 1500) -> np.ndarray:
    """应用窗宽窗位调整（用于CT图像显示）"""
    min_value = window_center - window_width / 2
    max_value = window_center + window_width / 2
    
    # 应用窗宽窗位
    image = np.clip(image, min_value, max_value)
    
    # 归一化到0-255
    image = ((image - min_value) / (max_value - min_value) * 255).astype(np.uint8)
    
    return image 