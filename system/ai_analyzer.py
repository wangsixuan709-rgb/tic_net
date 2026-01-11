#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI驱动的检测结果分析模块
使用DeepSeek模型生成智能医学分析报告
"""

import os
import logging
from typing import Dict, List, Any
import json

class AIAnalyzer:
    """使用DeepSeek进行智能分析的类"""
    
    def __init__(self, api_key: str = None):
        self.logger = self._setup_logger()
        
        # API配置
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY', '')
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"
        
        # 检查API密钥
        if not self.api_key:
            self.logger.warning("未配置DeepSeek API密钥，AI分析功能将不可用")
            self.enabled = False
        else:
            self.enabled = True
            self.logger.info("AI分析器初始化成功")
    
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('AIAnalyzer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def generate_analysis(self, detection_results: Dict) -> Dict[str, Any]:
        """
        生成智能医学分析报告
        
        Args:
            detection_results: 检测结果字典，包含detections和statistics
            
        Returns:
            包含AI分析结果的字典
        """
        if not self.enabled:
            return {
                'success': False,
                'message': '未配置API密钥，AI分析不可用',
                'analysis': self._generate_fallback_analysis(detection_results)
            }
        
        try:
            self.logger.info("正在生成AI分析报告...")
            
            # 构建提示词
            prompt = self._build_prompt(detection_results)
            
            # 调用DeepSeek API
            analysis_text = self._call_deepseek_api(prompt)
            
            if analysis_text:
                return {
                    'success': True,
                    'analysis': analysis_text,
                    'ai_model': self.model
                }
            else:
                return {
                    'success': False,
                    'message': 'API调用失败',
                    'analysis': self._generate_fallback_analysis(detection_results)
                }
                
        except Exception as e:
            self.logger.error(f"AI分析生成失败: {str(e)}")
            return {
                'success': False,
                'message': f'生成失败: {str(e)}',
                'analysis': self._generate_fallback_analysis(detection_results)
            }
    
    def _build_prompt(self, results: Dict) -> str:
        """构建DeepSeek的提示词"""
        
        detections = results.get('detections', [])
        stats = results.get('statistics', {})
        meta_info = results.get('meta_info', {})
        
        # 整理检测数据
        total_count = stats.get('total_detections', 0)
        high_conf = stats.get('high_confidence_count', 0)
        medium_conf = stats.get('medium_confidence_count', 0)
        avg_conf = stats.get('average_confidence', 0)
        avg_volume = stats.get('average_volume', 0)
        
        # 获取top检测结果
        top_detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)[:5]
        
        detection_details = []
        for i, det in enumerate(top_detections, 1):
            bbox = det['bbox']
            detection_details.append(
                f"结节{i}: 置信度{det['confidence']:.2f}, "
                f"位置({bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}), "
                f"体积{det['volume']:.1f}mm³"
            )
        
        prompt = f"""你是一位专业的肺部影像科医生，请根据以下TiCNet AI系统的肺结节检测结果，生成一份专业的医学分析报告。

【检测数据】
- 检测结节总数: {total_count}个
- 高置信度结节(≥0.7): {high_conf}个
- 中等置信度结节(0.4-0.7): {medium_conf}个
- 平均置信度: {avg_conf:.3f}
- 平均结节体积: {avg_volume:.1f} mm³
- 图像尺寸: {meta_info.get('original_shape', 'N/A')}

【主要检测结果】
{chr(10).join(detection_details)}

【报告要求】
请以专业医学术语撰写分析报告，包含以下部分：

1. **检测结果总览** (2-3句话概述)
2. **结节特征分析** (分析结节大小、位置分布、数量特点)
3. **风险评估** (根据置信度和体积评估风险等级)
4. **临床建议** (3-4条具体建议，包括：复查频率、进一步检查、注意事项等)

要求：
- 使用专业但易懂的医学语言
- 客观、准确、负责任
- 明确说明这是AI辅助诊断，需医生确认
- 每部分用简短段落，便于阅读
- 总字数控制在300-500字

请直接输出报告内容，不要有多余的说明。"""

        return prompt
    
    def _call_deepseek_api(self, prompt: str) -> str:
        """调用DeepSeek API"""
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            self.logger.info("正在调用DeepSeek API...")
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位经验丰富的肺部影像科医生，擅长分析肺结节检测结果并提供专业医学建议。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            analysis = response.choices[0].message.content
            self.logger.info("AI分析生成成功")
            
            return analysis
            
        except ImportError:
            self.logger.error("未安装openai库，请运行: pip install openai")
            return ""
        except Exception as e:
            self.logger.error(f"DeepSeek API调用失败: {str(e)}")
            return ""
    
    def _generate_fallback_analysis(self, results: Dict) -> str:
        """生成降级分析报告（当AI不可用时）"""
        
        stats = results.get('statistics', {})
        detections = results.get('detections', [])
        
        total = stats.get('total_detections', 0)
        high_conf = stats.get('high_confidence_count', 0)
        medium_conf = stats.get('medium_confidence_count', 0)
        avg_conf = stats.get('average_confidence', 0)
        avg_volume = stats.get('average_volume', 0)
        
        # 风险评估
        if high_conf >= 3:
            risk_level = "较高"
            risk_desc = "检测到多个高置信度结节，建议尽快进行进一步检查"
        elif high_conf >= 1:
            risk_level = "中等"
            risk_desc = "检测到高置信度结节，建议定期随访观察"
        elif total >= 1:
            risk_level = "较低"
            risk_desc = "检测到结节但置信度中等，建议常规随访"
        else:
            risk_level = "低"
            risk_desc = "未检测到明显结节征象"
        
        report = f"""【检测结果总览】

本次CT扫描共检测到{total}个可疑结节，其中高置信度结节{high_conf}个，中等置信度结节{medium_conf}个。平均检测置信度为{avg_conf:.2f}，平均结节体积为{avg_volume:.1f}mm³。

【结节特征分析】

"""
        
        if total > 0:
            # 体积分析
            if avg_volume < 300:
                size_cat = "微小结节"
            elif avg_volume < 1000:
                size_cat = "小结节"
            else:
                size_cat = "较大结节"
            
            report += f"""检测到的结节以{size_cat}为主（平均{avg_volume:.1f}mm³）。"""
            
            if high_conf > 0:
                report += f"""系统识别出{high_conf}个高置信度结节，这些结节的影像学特征较为典型，需要重点关注。"""
            
            if medium_conf > 0:
                report += f"""另有{medium_conf}个中等置信度结节，可能需要结合临床病史进一步判断。"""
        else:
            report += "本次扫描未发现明显的肺结节征象。图像质量良好，肺野清晰。"
        
        report += f"""

【风险评估】

风险等级：{risk_level}

{risk_desc}。

【临床建议】

"""
        
        if high_conf >= 3:
            report += """1. 建议1-3个月内进行胸部CT复查，密切观察结节变化
2. 考虑进行PET-CT或增强CT检查以进一步明确性质
3. 必要时可进行穿刺活检或手术切除
4. 建议由胸外科或呼吸科专家会诊"""
        elif high_conf >= 1:
            report += """1. 建议3-6个月内进行胸部CT复查
2. 观察结节大小、形态、密度变化
3. 如有胸痛、咳嗽、咯血等症状应及时就诊
4. 定期随访，必要时进一步检查"""
        elif total >= 1:
            report += """1. 建议6-12个月进行胸部CT复查
2. 保持健康生活方式，戒烟限酒
3. 如出现不适症状及时就诊
4. 定期体检，动态观察"""
        else:
            report += """1. 建议每年进行一次胸部CT体检
2. 保持健康生活方式
3. 如有高危因素（吸烟、家族史等）应缩短随访间隔
4. 如出现呼吸道症状及时就诊"""
        
        report += """

【重要提示】

本报告由AI系统自动生成，仅供临床参考。最终诊断需要由专业医生结合患者病史、体征及其他检查综合判断。请勿自行用药，如有疑问请及时咨询专业医生。"""
        
        return report
    
    def test_connection(self) -> bool:
        """测试API连接"""
        if not self.enabled:
            return False
        
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            # 发送测试请求
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "测试连接"}],
                max_tokens=10
            )
            
            self.logger.info("DeepSeek API连接测试成功")
            return True
            
        except Exception as e:
            self.logger.error(f"API连接测试失败: {str(e)}")
            return False

