# AI智能分析功能配置指南

## 🤖 功能简介

系统集成了**DeepSeek大模型**，可以根据检测结果自动生成专业的医学分析报告，包括：
- ✅ 检测结果总览
- ✅ 结节特征分析  
- ✅ 风险评估
- ✅ 临床建议

---

## 📋 前置要求

### 1. 安装依赖
```bash
pip install openai>=1.0.0
```

### 2. 获取DeepSeek API密钥

1. 访问 DeepSeek 官网：https://platform.deepseek.com/
2. 注册账号并登录
3. 进入 API Keys 页面
4. 创建新的API密钥并复制保存

---

## ⚙️ 配置方法

### 方法1：环境变量（推荐）

#### Linux/Mac
```bash
# 编辑 ~/.bashrc 或 ~/.zshrc
export DEEPSEEK_API_KEY="your_api_key_here"

# 使配置生效
source ~/.bashrc
```

#### Windows
```powershell
# PowerShell
$env:DEEPSEEK_API_KEY = "your_api_key_here"

# 或在系统环境变量中设置
```

### 方法2：.env文件

1. 复制模板文件：
```bash
cp .env.template .env
```

2. 编辑 `.env` 文件：
```bash
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

3. 安装python-dotenv（如果使用.env文件）：
```bash
pip install python-dotenv
```

4. 在 `app.py` 开头添加：
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 🚀 使用方法

### 启动系统
```bash
# 确保已配置API密钥
echo $DEEPSEEK_API_KEY  # 检查是否已设置

# 启动系统
conda activate projectwcsnet
python run_system.py
```

### 生成报告
1. 进行CT图像检测
2. 点击"生成报告"按钮
3. 系统会自动调用DeepSeek生成AI分析
4. 下载PDF报告查看AI分析结果

---

## 📊 AI分析示例

### 输入数据
- 检测结节总数：6个
- 高置信度结节：3个
- 平均置信度：0.722
- 平均体积：4797 mm³

### AI输出示例
```
**检测结果总览**

本次胸部CT扫描检测到6个肺结节，其中3个为高置信度结节（置信度≥0.7）。
整体检测置信度较高，平均达到0.722，提示这些结节具有较为典型的影像学特征。

**结节特征分析**

检测到的结节平均体积为4797mm³，属于较大结节范畴。高置信度结节占比50%，
说明部分结节的影像学征象明确，需要重点关注...

**风险评估**

风险等级：中等-较高

根据检测结果，存在3个高置信度结节，结合较大的平均体积，建议进一步进行
专业医学评估...

**临床建议**

1. 建议1-3个月内进行胸部CT复查，密切观察结节变化
2. 考虑进行增强CT或PET-CT检查以进一步明确性质
3. 必要时可进行穿刺活检或由胸外科会诊
4. 如有胸痛、咳嗽等症状应及时就诊
```

---

## 🛠️ 功能特性

### ✨ 智能特性
- 🤖 DeepSeek-V3大模型驱动
- 📊 自动分析检测数据
- 🎯 风险等级评估
- 💡 个性化临床建议
- 🔄 自动降级机制（API不可用时）

### 📋 降级方案
如果API不可用或未配置密钥，系统会自动使用**规则基础的分析**：
- ✅ 基于检测数据生成结构化报告
- ✅ 风险等级评估
- ✅ 标准化临床建议
- ⚠️ 不包含深度AI分析

---

## 🔍 测试连接

### 方法1：Python测试
```python
from system.ai_analyzer import AIAnalyzer

# 初始化分析器
analyzer = AIAnalyzer()

# 测试连接
if analyzer.test_connection():
    print("✅ DeepSeek API连接成功")
else:
    print("❌ API连接失败")
```

### 方法2：命令行测试
```bash
python << EOF
from system.ai_analyzer import AIAnalyzer
analyzer = AIAnalyzer()
print("API启用状态:", analyzer.enabled)
EOF
```

---

## ⚠️ 注意事项

### API使用
- 💰 DeepSeek API为付费服务，请注意用量
- 🔐 妥善保管API密钥，不要提交到代码仓库
- 🌐 需要网络连接才能使用AI分析
- ⏱️ 生成报告时间会增加3-10秒

### 安全建议
1. ✅ 使用环境变量而非硬编码API密钥
2. ✅ 将 `.env` 添加到 `.gitignore`
3. ✅ 定期更换API密钥
4. ✅ 监控API使用量

---

## 🔧 故障排除

### 问题1：API密钥无效
**错误信息：** `Authentication failed`

**解决方案：**
1. 检查API密钥是否正确
2. 确认密钥未过期
3. 在DeepSeek平台检查密钥状态

### 问题2：网络连接失败
**错误信息：** `Connection timeout`

**解决方案：**
1. 检查网络连接
2. 确认可以访问 api.deepseek.com
3. 检查防火墙设置

### 问题3：导入openai失败
**错误信息：** `No module named 'openai'`

**解决方案：**
```bash
pip install openai>=1.0.0
```

### 问题4：未生成AI分析
**现象：** PDF中只有基础分析

**检查步骤：**
1. 确认API密钥已配置
2. 查看系统日志：`tail -f logs/system.log`
3. 检查网络连接
4. 验证API额度未用完

---

## 📊 API用量估算

### 单次报告
- **输入tokens**: 约300-500
- **输出tokens**: 约500-800
- **总计**: 约800-1300 tokens
- **费用**: 约￥0.001-0.002（参考价格）

### 月度估算
假设每天生成10份报告：
- 每月tokens: 约39,000
- 每月费用: 约￥0.05-0.10

---

## 🎯 高级配置

### 自定义提示词
修改 `system/ai_analyzer.py` 中的 `_build_prompt` 方法：

```python
def _build_prompt(self, results: Dict) -> str:
    # 自定义您的提示词模板
    prompt = f"""自定义提示词..."""
    return prompt
```

### 调整AI参数
修改 `_call_deepseek_api` 方法中的参数：

```python
response = client.chat.completions.create(
    model=self.model,
    messages=[...],
    temperature=0.7,  # 调整创造性 (0.0-1.0)
    max_tokens=1500   # 调整输出长度
)
```

---

## 📝 .gitignore配置

确保您的 `.gitignore` 包含：
```
.env
*.env
.env.local
.env.*.local
```

---

## 🔄 更新日志

**v1.0** (2025-10-22)
- ✅ 集成DeepSeek AI分析
- ✅ 自动生成医学分析报告
- ✅ 支持降级方案
- ✅ 完整的错误处理

---

## 📞 技术支持

### DeepSeek官方
- 文档：https://platform.deepseek.com/docs
- 社区：https://discord.gg/deepseek
- 邮箱：support@deepseek.com

### 问题反馈
如有问题，请查看：
- 系统日志：`logs/system.log`
- API文档：https://platform.deepseek.com/api-docs

---

## 📚 相关资源

- [DeepSeek官网](https://www.deepseek.com/)
- [API文档](https://platform.deepseek.com/docs)
- [定价说明](https://platform.deepseek.com/pricing)
- [Python SDK](https://github.com/openai/openai-python)

---

**配置完成后，重启Flask应用即可使用AI分析功能！** 🎉

