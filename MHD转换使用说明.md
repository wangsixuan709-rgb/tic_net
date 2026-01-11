# 🔄 MHD格式转换为NRRD - 简单方案

## ✅ 推荐方案：本地转换

与其在系统中处理MHD的两个文件（.mhd + .raw），**更简单的方法是在本地先转换为NRRD格式**！

---

## 🚀 快速使用

### 1. 转换单个文件

```bash
python convert_mhd_to_nrrd.py patient001.mhd
```

**输出：** 
- `patient001.nrrd` （同目录下）

### 2. 指定输出路径

```bash
python convert_mhd_to_nrrd.py input/patient001.mhd output/patient001.nrrd
```

### 3. 批量转换整个目录

```bash
python convert_mhd_to_nrrd.py data/mhd_files/
```

**批量转换所有子目录：**
```bash
python convert_mhd_to_nrrd.py data/mhd_files/ --recursive
```

---

## 📋 转换示例

### 示例1：单个文件

```bash
$ python convert_mhd_to_nrrd.py 1.3.6.1.4.1.14519.5.2.1.6279.6001.149463915556499304732434215056.mhd

============================================================
  MHD格式 → NRRD格式 转换工具
============================================================

📄 读取MHD文件: 1.3.6.1.4.1.14519.5.2.1.6279.6001.149463915556499304732434215056.mhd
   ✓ 图像尺寸: (512, 512, 133)
   ✓ 体素间距: (0.703125, 0.703125, 2.5)
   ✓ 原点坐标: (-175.0, -242.5, -347.5)

💾 保存NRRD文件: 1.3.6.1.4.1.14519.5.2.1.6279.6001.149463915556499304732434215056.nrrd
   ✓ 文件大小: 67.89 MB
   ✓ 转换成功！

✅ 转换成功！现在您可以上传NRRD文件到TiCNet系统了。
```

### 示例2：批量转换

```bash
$ python convert_mhd_to_nrrd.py /home/yangao/LUNG/data/

🔍 找到 5 个MHD文件
============================================================

[1/5] 处理: patient001.mhd
------------------------------------------------------------
📄 读取MHD文件: patient001.mhd
   ✓ 图像尺寸: (512, 512, 120)
   ✓ 转换成功！

[2/5] 处理: patient002.mhd
------------------------------------------------------------
...

============================================================
✅ 转换完成！
   成功: 5 个
   失败: 0 个
```

---

## 🎯 为什么这个方案更好？

### ❌ 之前的方案（复杂）
1. 用户需要同时上传 `.mhd` + `.raw` 两个文件
2. 前端需要支持多文件上传
3. 后端需要处理文件配对
4. 容易出错（忘记上传.raw文件）

### ✅ 现在的方案（简单）
1. 用户在本地运行一行命令转换
2. 只需上传单个`.nrrd`文件
3. 系统直接支持NRRD格式
4. 简单、快速、不易出错

---

## 📊 格式对比

| 特性 | MHD格式 | NRRD格式 |
|------|---------|----------|
| 文件数量 | 2个（.mhd + .raw） | 1个（.nrrd） |
| 上传难度 | 需要同时上传两个文件 | 只需上传一个文件 |
| 数据完整性 | 容易丢失.raw文件 | 所有数据在一个文件中 |
| 系统支持 | 需要特殊处理 | 原生支持 |
| 推荐程度 | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 💡 工作流程

### 完整流程：

```
步骤1: 本地转换
   patient001.mhd + patient001.raw
             ↓
   python convert_mhd_to_nrrd.py patient001.mhd
             ↓
   patient001.nrrd  ← 单个文件

步骤2: 上传到TiCNet
   访问 http://localhost:5000
   上传 patient001.nrrd
   
步骤3: 查看检测结果
   系统自动处理，显示结节检测结果
```

---

## ⚙️ 技术细节

### 转换过程：

```python
# 读取MHD（会自动找到对应的.raw文件）
image = sitk.ReadImage('patient001.mhd')

# 图像对象包含：
# - 图像数据（从.raw读取）
# - spacing（体素间距）
# - origin（原点坐标）
# - direction（方向矩阵）
# - 其他元数据

# 保存为NRRD（所有信息打包到一个文件）
sitk.WriteImage(image, 'patient001.nrrd')
```

### 优势：

- ✅ **无损转换** - 所有信息完整保留
- ✅ **自动处理** - SimpleITK自动找到.raw文件
- ✅ **压缩支持** - NRRD支持gzip压缩
- ✅ **兼容性强** - 广泛支持的医学影像格式

---

## 🔍 常见问题

### Q1: 转换会损失数据吗？

**A:** 不会！转换是完全无损的：
- 图像数据完全一致
- spacing、origin等元数据完全保留
- 只是文件格式改变，内容不变

### Q2: 转换后文件会变大吗？

**A:** 基本一致：
- 未压缩NRRD ≈ MHD+RAW的总大小
- 使用压缩可以减小50-70%

### Q3: 可以批量转换吗？

**A:** 可以！
```bash
# 转换整个目录
python convert_mhd_to_nrrd.py /path/to/folder/

# 包括子目录
python convert_mhd_to_nrrd.py /path/to/folder/ --recursive
```

### Q4: 转换需要多长时间？

**A:** 非常快：
- 典型CT图像（512×512×133）约1-2秒
- 批量转换100个文件约2-3分钟

### Q5: 如果找不到.raw文件怎么办？

**A:** 脚本会显示警告并尝试读取MHD中指定的数据文件：
```
⚠️ 警告：未找到对应的RAW文件
   尝试读取MHD文件中指定的数据文件...
```

有些MHD文件使用`.zraw`或其他格式，SimpleITK会自动处理。

### Q6: 可以反向转换吗（NRRD → MHD）？

**A:** 可以！只需修改脚本或使用：
```python
image = sitk.ReadImage('input.nrrd')
sitk.WriteImage(image, 'output.mhd')
```

---

## 🛠️ 高级用法

### 1. 转换并压缩

```python
import SimpleITK as sitk

image = sitk.ReadImage('input.mhd')
sitk.WriteImage(image, 'output.nrrd', useCompression=True)
```

### 2. 转换为其他格式

```bash
# 转换为NIfTI
python -c "import SimpleITK as sitk; sitk.WriteImage(sitk.ReadImage('input.mhd'), 'output.nii.gz')"

# 转换为MetaImage（不推荐，回到两个文件）
python -c "import SimpleITK as sitk; sitk.WriteImage(sitk.ReadImage('input.nrrd'), 'output.mhd')"
```

### 3. 查看图像信息（不转换）

```python
import SimpleITK as sitk

image = sitk.ReadImage('input.mhd')
print(f"尺寸: {image.GetSize()}")
print(f"间距: {image.GetSpacing()}")
print(f"原点: {image.GetOrigin()}")
print(f"方向: {image.GetDirection()}")
```

---

## 📝 脚本位置

```
TiCNet/
├── convert_mhd_to_nrrd.py  ← 转换脚本
├── run_system.py
├── app.py
└── ...
```

---

## ✅ 总结

**推荐工作流程：**

1. ✅ 使用 `convert_mhd_to_nrrd.py` 在本地转换MHD文件
2. ✅ 上传转换后的`.nrrd`文件到TiCNet系统
3. ✅ 享受简单、快速的检测体验

**不推荐：**
- ❌ 尝试同时上传.mhd和.raw文件（复杂、易出错）
- ❌ 修改系统支持多文件上传（开发成本高、维护复杂）

**一行命令解决所有问题：**
```bash
python convert_mhd_to_nrrd.py your_file.mhd
```

然后上传生成的`.nrrd`文件即可！🎉

---

**开始使用：**
```bash
python convert_mhd_to_nrrd.py --help
```

