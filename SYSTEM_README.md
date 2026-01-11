# TiCNet 肺结节检测系统使用说明

## 系统介绍

TiCNet 肺结节检测系统是一个基于深度学习的医学影像分析工具，专门用于CT图像中的肺结节自动检测。该系统结合了Transformer和卷积神经网络的优势，能够高精度地识别和定位肺结节。

## 主要功能

- **高精度检测**: 基于LUNA16数据集验证，平均检测精度达到95.37%
- **3D图像分析**: 支持完整的3D CT图像处理和分析
- **多格式支持**: 支持MetaImage、NIfTI、NRRD、DICOM等医学图像格式
- **智能可视化**: 自动生成检测结果的多角度可视化图像
- **Web界面**: 提供友好的Web界面，易于使用
- **历史记录**: 保存和管理检测历史记录

## 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web前端界面   │────│   Flask应用     │────│   模型推理引擎   │
│   (HTML/CSS/JS) │    │   (app.py)      │    │   (TiCNet模型)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │                   │
            ┌───────▼────────┐ ┌────────▼────────┐
            │  结果可视化模块  │ │   图像处理模块   │
            │ (visualization) │ │   (preprocessing)│
            └────────────────┘ └─────────────────┘
```

## 快速开始

### 1. 环境要求

- Python 3.7+
- PyTorch 1.8+
- CUDA 11.0+ (可选，用于GPU加速)

### 2. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装额外的医学图像处理库
pip install SimpleITK opencv-python

# 安装NRRD文件支持（可选但推荐）
pip install pynrrd
```

### 3. 启动系统

```bash
# 方法1: 使用启动脚本（推荐）
python run_system.py

# 方法2: 直接运行Flask应用
python app.py

# 方法3: 指定参数启动
python run_system.py --host 0.0.0.0 --port 8080 --debug
```

### 4. 访问系统

打开浏览器访问：`http://localhost:5000`

## 使用指南

### 文件上传

1. 点击"选择CT图像文件"按钮
2. 选择支持的医学图像文件：
   - MetaImage格式 (.mhd + .raw文件)
   - NIfTI格式 (.nii, .nii.gz)
   - NRRD格式 (.nrrd, .nhdr)
   - DICOM格式 (.dcm)
   - 常规图像格式 (.png, .jpg) - 用于演示
3. 点击"开始智能检测"按钮

### 结果查看

检测完成后，系统会自动跳转到结果页面，显示：

- **检测统计**: 总结节数量、置信度分布
- **可视化图像**: 原始切片、叠加结果、汇总分析
- **详细列表**: 每个检测结节的具体信息
- **医学建议**: 专业的使用建议和注意事项

### 历史记录

在"历史记录"页面可以：
- 查看所有检测记录
- 重新查看检测结果
- 下载检测报告

### NRRD文件支持

系统对NRRD (Nearly Raw Raster Data) 格式提供完整支持：

#### 支持的NRRD格式
- `.nrrd` - 标准NRRD文件
- `.nhdr` - NRRD头文件（带外部数据文件）

#### NRRD文件处理特性
- **自动格式检测**: 系统会自动识别NRRD文件的编码和压缩方式
- **多维度支持**: 支持3D和4D NRRD数据，自动处理维度转换
- **双引擎读取**: 
  - 主要使用SimpleITK读取（稳定性好）
  - 备用pynrrd读取（兼容性好）
- **元数据保留**: 保持spacing、origin等关键医学信息

#### 测试NRRD文件
```bash
# 测试NRRD文件是否能正确读取
python test_nrrd.py your_file.nrrd
```

## 系统配置

### 模型配置 (config.py)

```python
# 网络配置
net_config = {
    'anchors': [...],
    'crop_size': [128, 128, 128],
    'num_class': 2,
    'hidden_dim': 64,
    # ...更多配置
}

# 推理配置
inference_config = {
    'min_confidence': 0.3,
    'nms_threshold': 0.1,
    'max_detections': 100
}
```

### 系统配置 (system/config.py)

```python
class SystemConfig:
    def __init__(self):
        # 路径配置
        self.UPLOAD_FOLDER = './uploads'
        self.RESULTS_FOLDER = './system_results'
        
        # 模型配置
        self.MODEL_CONFIG = {
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
            'batch_size': 1
        }
        
        # 可视化配置
        self.VISUALIZATION_CONFIG = {
            'save_original': True,
            'save_overlay': True,
            'save_3d_view': True
        }
```

## API接口

### 上传检测接口

```http
POST /upload
Content-Type: multipart/form-data

参数:
- file: 图像文件

响应:
{
    "success": true,
    "task_id": "uuid",
    "results": {...}
}
```

### 结果查询接口

```http
GET /api/results/{task_id}

响应:
{
    "success": true,
    "data": {
        "detections": [...],
        "statistics": {...},
        "visualization_paths": {...}
    }
}
```

## 目录结构

```
TiCNet/
├── app.py                 # Flask主应用
├── run_system.py          # 系统启动脚本
├── config.py              # 原始TiCNet配置
├── SYSTEM_README.md       # 系统说明文档
├── system/                # 系统模块
│   ├── __init__.py
│   ├── config.py          # 系统配置
│   ├── model_inference.py # 模型推理
│   ├── visualization.py   # 结果可视化
│   └── utils.py           # 工具函数
├── templates/             # Web模板
│   ├── base.html
│   ├── index.html
│   ├── results.html
│   ├── history.html
│   ├── about.html
│   └── error.html
├── net/                   # TiCNet网络模型
├── uploads/               # 上传文件目录
├── system_results/        # 检测结果目录
├── visualizations/        # 可视化图像目录
├── models/                # 模型权重目录
└── logs/                  # 日志目录
```

## 性能指标

基于LUNA16数据集10折交叉验证结果：

| FP/Scan | 敏感度 (%) |
|---------|-----------|
| 0.125   | 79.55     |
| 0.25    | 85.42     |
| 0.5     | 89.09     |
| 1       | 92.22     |
| 2       | 95.37     |
| 4       | 96.52     |
| 8       | 96.95     |

## 注意事项

### 重要声明

⚠️ **本系统仅供科研和教育用途，不能作为最终诊断依据！**

- 检测结果需要专业医生进行临床判断
- 系统输出仅供参考，不能替代医学专业判断
- 建议结合患者病史、临床症状等综合评估

### 数据安全

- 上传的图像仅用于检测分析
- 不会保存或泄露患者隐私信息
- 建议在使用前对敏感数据进行脱敏处理
- 定期清理临时文件和检测记录

### 系统限制

- 文件大小限制：500MB
- 支持的图像格式有限
- 处理时间取决于图像大小和硬件配置
- GPU推荐但非必需（CPU也可运行）

## 故障排除

### 常见问题

1. **模型加载失败**
   - 检查模型权重文件是否存在于 `models/` 目录
   - 确认PyTorch版本兼容性
   - 查看错误日志获取详细信息

2. **图像上传失败**
   - 检查文件格式是否支持
   - 确认文件大小未超过限制
   - 验证图像文件完整性

3. **推理速度慢**
   - 使用GPU加速 (需要CUDA支持)
   - 降低图像分辨率
   - 调整batch_size参数

4. **可视化错误**
   - 检查matplotlib字体配置
   - 确认图像处理库版本
   - 查看系统内存使用情况

### 日志查看

```bash
# 查看系统日志
tail -f logs/system.log

# 查看Flask应用日志
python run_system.py --debug
```

## 更新记录

- **v1.0.0** (2024-09): 初始版本发布
  - 完整的Web界面
  - TiCNet模型集成
  - 可视化功能
  - 历史记录管理

## 技术支持

如有技术问题，请参考：

1. 原始TiCNet论文和代码库
2. PyTorch官方文档
3. SimpleITK用户指南
4. Flask应用开发文档

## 许可证

本系统基于原始TiCNet项目开发，遵循相应的开源许可证。仅供学术研究和教育用途。 