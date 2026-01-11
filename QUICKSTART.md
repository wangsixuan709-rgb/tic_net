# TiCNet 肺结节检测系统 - 快速开始

## 🚀 一键启动

### Windows用户
```bash
# 双击运行 (推荐简化启动)
start_system.bat
```

### Linux/Mac用户
```bash
# 方法1: 简化启动 (推荐)
python run_system_simple.py

# 方法2: 完整检查启动
python run_system.py
```

### 🔧 如果遇到依赖检测问题

有时系统可能错误报告某些包缺失，即使它们已经安装。请使用简化启动脚本：
```bash
python run_system_simple.py
```

## 📋 使用步骤

1. **启动系统** - 运行上述命令
2. **打开浏览器** - 访问 `http://localhost:5000`
3. **上传CT图像** - 选择 .mhd, .nii, .nrrd, .dcm 或 .png 文件
4. **等待检测** - 系统自动分析（约2-5分钟）
5. **查看结果** - 浏览检测结果和可视化图像

## 🔧 环境要求

- Python 3.7+
- PyTorch 1.8+
- 8GB+ 内存
- GPU推荐（可选）

## 📁 支持的文件格式

- ✅ MetaImage (.mhd + .raw)
- ✅ NIfTI (.nii, .nii.gz)  
- ✅ NRRD (.nrrd, .nhdr)
- ✅ DICOM (.dcm)
- ✅ 图像文件 (.png, .jpg) - 演示用

## ⚠️ 重要提醒

**本系统仅供科研和教育用途，不能作为医学诊断依据！**

## 📖 详细文档

更多信息请参考：[SYSTEM_README.md](SYSTEM_README.md) 