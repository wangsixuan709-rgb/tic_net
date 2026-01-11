import os
import json
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image as RLImage, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .ai_analyzer import AIAnalyzer

class ReportGenerator:
    """检测结果分析报告生成器"""
    
    def __init__(self, config):
        self.config = config
        self.logger = self._setup_logger()
        
        # 尝试注册中文字体
        self.has_chinese_font = self._register_chinese_fonts()
        
        # 初始化AI分析器
        self.ai_analyzer = AIAnalyzer()
        
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('ReportGenerator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _register_chinese_fonts(self):
        """注册中文字体"""
        try:
            # 尝试常见的中文字体路径
            font_paths = [
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                '/System/Library/Fonts/PingFang.ttc',  # macOS
                'C:\\Windows\\Fonts\\msyh.ttc',  # Windows
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        self.logger.info(f"成功注册中文字体: {font_path}")
                        return True
                    except Exception as e:
                        self.logger.warning(f"注册字体 {font_path} 失败: {str(e)}")
                        continue
            
            self.logger.warning("未找到可用的中文字体，将使用英文报告")
            return False
            
        except Exception as e:
            self.logger.error(f"字体注册失败: {str(e)}")
            return False
    
    def generate_report(self, task_id: str, output_dir: str = None) -> str:
        """生成检测结果分析报告
        
        Args:
            task_id: 任务ID
            output_dir: 输出目录，默认为系统结果目录
            
        Returns:
            生成的PDF报告文件路径
        """
        try:
            self.logger.info(f"开始生成报告，任务ID: {task_id}")
            
            # 加载检测结果
            result_file = os.path.join(self.config.RESULTS_FOLDER, f"{task_id}_results.json")
            if not os.path.exists(result_file):
                raise FileNotFoundError(f"未找到结果文件: {result_file}")
            
            with open(result_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # 设置输出路径
            if output_dir is None:
                output_dir = self.config.RESULTS_FOLDER
            
            output_path = os.path.join(output_dir, f"{task_id}_report.pdf")
            
            # 创建PDF文档
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # 构建报告内容
            story = []
            story.extend(self._create_header(results))
            story.append(Spacer(1, 0.5*cm))
            
            story.extend(self._create_summary_section(results))
            story.append(Spacer(1, 0.3*cm))
            
            story.extend(self._create_ai_analysis_section(results))
            story.append(Spacer(1, 0.3*cm))
            
            story.extend(self._create_statistics_section(results))
            story.append(Spacer(1, 0.3*cm))
            
            story.extend(self._create_detections_section(results))
            story.append(Spacer(1, 0.3*cm))
            
            story.extend(self._create_visualization_section(results))
            story.append(Spacer(1, 0.3*cm))
            
            if results.get('validation', {}).get('has_ground_truth', False):
                story.extend(self._create_validation_section(results))
                story.append(Spacer(1, 0.3*cm))
            
            story.extend(self._create_recommendations_section(results))
            story.append(Spacer(1, 0.3*cm))
            
            story.extend(self._create_footer())
            
            # 生成PDF
            doc.build(story)
            
            self.logger.info(f"报告生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"生成报告失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _get_styles(self):
        """获取样式"""
        styles = getSampleStyleSheet()
        
        if self.has_chinese_font:
            # 中文样式
            styles.add(ParagraphStyle(
                name='ChineseTitle',
                parent=styles['Title'],
                fontName='ChineseFont',
                fontSize=24,
                textColor=colors.HexColor('#1a5490'),
                alignment=TA_CENTER,
                spaceAfter=12
            ))
            
            styles.add(ParagraphStyle(
                name='ChineseHeading',
                parent=styles['Heading1'],
                fontName='ChineseFont',
                fontSize=16,
                textColor=colors.HexColor('#2c5aa0'),
                spaceAfter=6,
                spaceBefore=12
            ))
            
            styles.add(ParagraphStyle(
                name='ChineseBody',
                parent=styles['BodyText'],
                fontName='ChineseFont',
                fontSize=11,
                alignment=TA_JUSTIFY,
                leading=16
            ))
            
            styles.add(ParagraphStyle(
                name='ChineseNormal',
                fontName='ChineseFont',
                fontSize=10,
                leading=14
            ))
        
        return styles
    
    def _create_header(self, results: Dict) -> list:
        """创建报告头部"""
        styles = self._get_styles()
        elements = []
        
        # 标题
        if self.has_chinese_font:
            title = Paragraph("TiCNet 肺结节检测分析报告", styles['ChineseTitle'])
        else:
            title = Paragraph("TiCNet Pulmonary Nodule Detection Report", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*cm))
        
        # 基本信息表格
        timestamp = results.get('timestamp', '')
        if 'T' in timestamp:
            date_str = timestamp.split('T')[0]
            time_str = timestamp.split('T')[1].split('.')[0]
        else:
            date_str = timestamp
            time_str = ''
        
        data = [
            ['文件名 / Filename:', results.get('filename', 'N/A')],
            ['检测时间 / Detection Time:', f"{date_str} {time_str}"],
            ['任务ID / Task ID:', results.get('task_id', 'N/A')[:16]],
            ['模型 / Model:', 'TiCNet (Transformer in CNN)']
        ]
        
        table = Table(data, colWidths=[5*cm, 12*cm])
        font_name = 'ChineseFont' if self.has_chinese_font else 'Helvetica'
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONT', (0, 0), (-1, -1), font_name, 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_summary_section(self, results: Dict) -> list:
        """创建摘要部分"""
        styles = self._get_styles()
        elements = []
        
        stats = results.get('statistics', {})
        
        # 标题
        if self.has_chinese_font:
            elements.append(Paragraph("一、检测结果摘要", styles['ChineseHeading']))
        else:
            elements.append(Paragraph("1. Detection Summary", styles['Heading1']))
        
        elements.append(Spacer(1, 0.2*cm))
        
        # 摘要统计
        data = [
            ['检测结节总数 / Total Detections', str(stats.get('total_detections', 0))],
            ['高置信度结节 / High Confidence (≥0.7)', str(stats.get('high_confidence_count', 0))],
            ['中等置信度结节 / Medium Confidence (0.4-0.7)', str(stats.get('medium_confidence_count', 0))],
            ['低置信度结节 / Low Confidence (<0.4)', str(stats.get('low_confidence_count', 0))],
            ['平均置信度 / Average Confidence', f"{stats.get('average_confidence', 0):.3f}"],
            ['平均体积 / Average Volume', f"{stats.get('average_volume', 0):.1f} mm³"]
        ]
        
        table = Table(data, colWidths=[10*cm, 7*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont' if self.has_chinese_font else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_ai_analysis_section(self, results: Dict) -> list:
        """创建AI智能分析部分"""
        styles = self._get_styles()
        elements = []
        
        # 标题
        if self.has_chinese_font:
            elements.append(Paragraph("二、AI智能分析", styles['ChineseHeading']))
        else:
            elements.append(Paragraph("2. AI Analysis", styles['Heading1']))
        
        elements.append(Spacer(1, 0.2*cm))
        
        try:
            # 调用AI生成分析
            self.logger.info("正在生成AI分析...")
            ai_result = self.ai_analyzer.generate_analysis(results)
            
            analysis_text = ai_result.get('analysis', '')
            
            if ai_result.get('success', False):
                # AI分析成功
                if self.has_chinese_font:
                    header_text = "🤖 以下分析由DeepSeek AI模型生成："
                else:
                    header_text = "🤖 Analysis generated by DeepSeek AI:"
                
                header = Paragraph(header_text, styles['ChineseBody'] if self.has_chinese_font else styles['BodyText'])
                elements.append(header)
                elements.append(Spacer(1, 0.2*cm))
            else:
                # 使用降级分析
                if self.has_chinese_font:
                    header_text = "📋 系统分析报告："
                else:
                    header_text = "📋 System Analysis Report:"
                
                header = Paragraph(header_text, styles['ChineseBody'] if self.has_chinese_font else styles['BodyText'])
                elements.append(header)
                elements.append(Spacer(1, 0.2*cm))
            
            # 将分析文本分段处理
            paragraphs = analysis_text.split('\n')
            current_section = []
            
            for line in paragraphs:
                line = line.strip()
                if not line:
                    # 空行，处理当前累积的段落
                    if current_section:
                        para_text = self._format_text_for_pdf(' '.join(current_section))
                        p = Paragraph(para_text, styles['ChineseBody'] if self.has_chinese_font else styles['BodyText'])
                        elements.append(p)
                        elements.append(Spacer(1, 0.3*cm))
                        current_section = []
                else:
                    # 有内容的行
                    current_section.append(line)
            
            # 处理最后一个段落
            if current_section:
                para_text = self._format_text_for_pdf(' '.join(current_section))
                p = Paragraph(para_text, styles['ChineseBody'] if self.has_chinese_font else styles['BodyText'])
                elements.append(p)
                elements.append(Spacer(1, 0.3*cm))
            
            # 添加AI模型信息（如果成功）
            if ai_result.get('success', False):
                model_info = f"<i>Model: {ai_result.get('ai_model', 'DeepSeek')}</i>"
                model_para = Paragraph(model_info, styles['ChineseBody'] if self.has_chinese_font else styles['BodyText'])
                
                # 添加边框
                info_table = Table([[model_para]], colWidths=[17*cm])
                info_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f8ff')),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#4a90e2')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                
                elements.append(info_table)
                
        except Exception as e:
            self.logger.error(f"生成AI分析失败: {str(e)}")
            # 降级到简单分析
            fallback_text = self.ai_analyzer._generate_fallback_analysis(results)
            
            # 分段处理降级文本
            paragraphs = fallback_text.split('\n')
            current_section = []
            
            for line in paragraphs:
                line = line.strip()
                if not line:
                    if current_section:
                        para_text = self._format_text_for_pdf(' '.join(current_section))
                        p = Paragraph(para_text, styles['ChineseBody'] if self.has_chinese_font else styles['BodyText'])
                        elements.append(p)
                        elements.append(Spacer(1, 0.3*cm))
                        current_section = []
                else:
                    current_section.append(line)
            
            if current_section:
                para_text = self._format_text_for_pdf(' '.join(current_section))
                p = Paragraph(para_text, styles['ChineseBody'] if self.has_chinese_font else styles['BodyText'])
                elements.append(p)
        
        return elements
    
    def _format_text_for_pdf(self, text: str) -> str:
        """格式化文本用于PDF显示，简单转义特殊字符"""
        import re
        
        # 只做基本的特殊字符转义，不处理markdown
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        
        # 处理【标题】使其加粗
        text = re.sub(r'【(.+?)】', r'<b>【\1】</b>', text)
        
        # 处理数字列表，在前面加缩进
        text = re.sub(r'^(\d+)\.\s+', r'  \1. ', text, flags=re.MULTILINE)
        
        return text
    
    def _create_statistics_section(self, results: Dict) -> list:
        """创建统计分析部分"""
        styles = self._get_styles()
        elements = []
        
        stats = results.get('statistics', {})
        
        # 标题
        if self.has_chinese_font:
            elements.append(Paragraph("二、图像与检测参数", styles['ChineseHeading']))
        else:
            elements.append(Paragraph("2. Image and Detection Parameters", styles['Heading1']))
        
        elements.append(Spacer(1, 0.2*cm))
        
        # 图像信息
        image_shape = stats.get('image_shape', [0, 0, 0])
        spacing = stats.get('spacing', [0, 0, 0])
        
        data = [
            ['图像尺寸 / Image Size', f"{image_shape[0]}×{image_shape[1]}×{image_shape[2]}"],
            ['像素间距 / Pixel Spacing', f"{spacing[0]:.2f}×{spacing[1]:.2f}×{spacing[2]:.2f} mm"],
            ['置信度阈值 / Confidence Threshold', '0.70'],
            ['检测算法 / Algorithm', 'TiCNet (Transformer + CNN)'],
            ['推理时间 / Inference Time', f"{results.get('inference_time', 0):.2f} 秒 / seconds"]
        ]
        
        table = Table(data, colWidths=[10*cm, 7*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont' if self.has_chinese_font else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_detections_section(self, results: Dict) -> list:
        """创建详细检测结果部分"""
        styles = self._get_styles()
        elements = []
        
        # 标题
        if self.has_chinese_font:
            elements.append(Paragraph("三、详细检测结果", styles['ChineseHeading']))
        else:
            elements.append(Paragraph("3. Detailed Detection Results", styles['Heading1']))
        
        elements.append(Spacer(1, 0.2*cm))
        
        detections = results.get('detections', [])
        
        if not detections:
            if self.has_chinese_font:
                text = Paragraph("未检测到肺结节。", styles['ChineseBody'] if self.has_chinese_font else styles['BodyText'])
            else:
                text = Paragraph("No pulmonary nodules detected.", styles['BodyText'])
            elements.append(text)
        else:
            # 只显示前20个检测结果
            display_detections = detections[:20]
            
            # 表头
            data = [['序号\nNo.', '置信度\nConf.', '位置 (X, Y, Z)\nPosition', 
                     '大小 (W×H×D)\nSize', '体积 (mm³)\nVolume', '风险\nRisk']]
            
            for i, det in enumerate(display_detections, 1):
                bbox = det['bbox']
                position = f"({bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f})"
                size = f"{bbox[3]-bbox[0]:.0f}×{bbox[4]-bbox[1]:.0f}×{bbox[5]-bbox[2]:.0f}"
                volume = f"{det['volume']:.1f}"
                confidence = f"{det['confidence']:.3f}"
                
                if det['confidence'] >= 0.7:
                    risk = '高 / High'
                elif det['confidence'] >= 0.4:
                    risk = '中 / Med'
                else:
                    risk = '低 / Low'
                
                data.append([str(i), confidence, position, size, volume, risk])
            
            # 创建表格
            col_widths = [1.5*cm, 2*cm, 4*cm, 3.5*cm, 2.5*cm, 2.5*cm]
            table = Table(data, colWidths=col_widths, repeatRows=1)
            
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'ChineseFont' if self.has_chinese_font else 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'ChineseFont' if self.has_chinese_font else 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
            ]))
            
            elements.append(table)
            
            if len(detections) > 20:
                if self.has_chinese_font:
                    note = Paragraph(f"<i>注：共检测到 {len(detections)} 个结节，此处仅显示前20个。</i>", 
                                   styles['ChineseBody'] if self.has_chinese_font else styles['Italic'])
                else:
                    note = Paragraph(f"<i>Note: {len(detections)} nodules detected in total, showing top 20 only.</i>", 
                                   styles['Italic'])
                elements.append(Spacer(1, 0.2*cm))
                elements.append(note)
        
        return elements
    
    def _create_visualization_section(self, results: Dict) -> list:
        """创建可视化结果部分"""
        styles = self._get_styles()
        elements = []
        
        # 标题
        if self.has_chinese_font:
            elements.append(PageBreak())  # 新页面显示图像
            elements.append(Paragraph("四、可视化结果", styles['ChineseHeading']))
        else:
            elements.append(PageBreak())
            elements.append(Paragraph("4. Visualization Results", styles['Heading1']))
        
        elements.append(Spacer(1, 0.2*cm))
        
        viz_paths = results.get('visualization_paths', {})
        
        # 添加汇总图
        if 'summary' in viz_paths:
            summary_path = os.path.join(self.config.VISUALIZATION_FOLDER, viz_paths['summary'])
            if os.path.exists(summary_path):
                try:
                    if self.has_chinese_font:
                        elements.append(Paragraph("检测结果汇总:", styles['ChineseBody']))
                    else:
                        elements.append(Paragraph("Detection Summary:", styles['BodyText']))
                    elements.append(Spacer(1, 0.2*cm))
                    
                    img = RLImage(summary_path, width=16*cm, height=12*cm)
                    elements.append(img)
                    elements.append(Spacer(1, 0.3*cm))
                except Exception as e:
                    self.logger.warning(f"无法添加汇总图: {str(e)}")
        
        # 添加叠加图
        if 'overlay' in viz_paths:
            overlay_path = os.path.join(self.config.VISUALIZATION_FOLDER, viz_paths['overlay'])
            if os.path.exists(overlay_path):
                try:
                    elements.append(PageBreak())
                    if self.has_chinese_font:
                        elements.append(Paragraph("叠加可视化:", styles['ChineseBody']))
                    else:
                        elements.append(Paragraph("Overlay Visualization:", styles['BodyText']))
                    elements.append(Spacer(1, 0.2*cm))
                    
                    img = RLImage(overlay_path, width=16*cm, height=9*cm)
                    elements.append(img)
                    elements.append(Spacer(1, 0.3*cm))
                except Exception as e:
                    self.logger.warning(f"无法添加叠加图: {str(e)}")
        
        # 添加原始切片图
        if 'original_slices' in viz_paths:
            slices_path = os.path.join(self.config.VISUALIZATION_FOLDER, viz_paths['original_slices'])
            if os.path.exists(slices_path):
                try:
                    if self.has_chinese_font:
                        elements.append(Paragraph("原始切片:", styles['ChineseBody']))
                    else:
                        elements.append(Paragraph("Original Slices:", styles['BodyText']))
                    elements.append(Spacer(1, 0.2*cm))
                    
                    img = RLImage(slices_path, width=16*cm, height=10*cm)
                    elements.append(img)
                except Exception as e:
                    self.logger.warning(f"无法添加切片图: {str(e)}")
        
        return elements
    
    def _create_validation_section(self, results: Dict) -> list:
        """创建验证结果部分"""
        styles = self._get_styles()
        elements = []
        
        validation = results.get('validation', {})
        
        # 标题
        elements.append(PageBreak())
        if self.has_chinese_font:
            elements.append(Paragraph("五、检测结果验证", styles['ChineseHeading']))
        else:
            elements.append(Paragraph("5. Validation Results", styles['Heading1']))
        
        elements.append(Spacer(1, 0.2*cm))
        
        # 验证统计
        data = [
            ['正确检测 / True Positives', str(validation.get('true_positives', 0))],
            ['误报 / False Positives', str(validation.get('false_positives', 0))],
            ['漏检 / False Negatives', str(validation.get('false_negatives', 0))],
            ['精度 / Precision', f"{validation.get('precision', 0)*100:.1f}%"],
            ['召回率 / Recall', f"{validation.get('recall', 0)*100:.1f}%"],
            ['F1分数 / F1 Score', f"{validation.get('f1_score', 0):.3f}"],
            ['平均IoU / Average IoU', f"{validation.get('average_iou', 0):.3f}"]
        ]
        
        table = Table(data, colWidths=[10*cm, 7*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont' if self.has_chinese_font else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        
        # 验证总结
        summary = validation.get('validation_summary', '')
        if summary:
            elements.append(Spacer(1, 0.3*cm))
            if self.has_chinese_font:
                elements.append(Paragraph(f"<b>验证总结 / Summary:</b> {summary}", styles['ChineseBody']))
            else:
                elements.append(Paragraph(f"<b>Summary:</b> {summary}", styles['BodyText']))
        
        return elements
    
    def _create_recommendations_section(self, results: Dict) -> list:
        """创建医学建议部分"""
        styles = self._get_styles()
        elements = []
        
        # 标题
        elements.append(PageBreak())
        if self.has_chinese_font:
            elements.append(Paragraph("六、医学建议与注意事项", styles['ChineseHeading']))
        else:
            elements.append(Paragraph("6. Medical Recommendations", styles['Heading1']))
        
        elements.append(Spacer(1, 0.2*cm))
        
        # 建议内容
        if self.has_chinese_font:
            recommendations = [
                "1. <b>本系统仅供辅助诊断使用</b>，不能替代专业医生的临床判断。",
                "2. 对于高置信度检测结果（≥0.7），建议进一步进行专业影像学检查和病理学确认。",
                "3. 建议结合患者病史、临床症状、实验室检查等综合评估。",
                "4. 肺结节的良恶性判定需要专业医生根据多种因素综合判断。",
                "5. 如有疑问或发现可疑征象，请及时咨询专业医生。",
                "6. 建议定期复查，监测结节变化情况。"
            ]
        else:
            recommendations = [
                "1. <b>This system is for auxiliary diagnosis only</b> and cannot replace professional clinical judgment.",
                "2. For high-confidence detections (≥0.7), further professional imaging and pathological confirmation is recommended.",
                "3. Comprehensive evaluation should be combined with patient history, clinical symptoms, and laboratory tests.",
                "4. Determination of benign or malignant nodules requires professional medical judgment based on multiple factors.",
                "5. If you have any questions or find suspicious signs, please consult a professional doctor promptly.",
                "6. Regular follow-up is recommended to monitor nodule changes."
            ]
        
        for rec in recommendations:
            para = Paragraph(rec, styles['ChineseBody'] if self.has_chinese_font else styles['BodyText'])
            elements.append(para)
            elements.append(Spacer(1, 0.2*cm))
        
        # 免责声明
        elements.append(Spacer(1, 0.5*cm))
        if self.has_chinese_font:
            disclaimer = """
            <b>免责声明 / Disclaimer:</b><br/>
            本报告由TiCNet人工智能系统自动生成，仅供医学研究和辅助诊断参考。
            本系统的检测结果可能存在误差，不应作为临床诊断的唯一依据。
            最终诊断结果应由具备资质的专业医生根据完整的临床信息做出。
            """
        else:
            disclaimer = """
            <b>Disclaimer:</b><br/>
            This report is automatically generated by the TiCNet AI system for medical research 
            and auxiliary diagnosis reference only. The detection results may contain errors and 
            should not be used as the sole basis for clinical diagnosis. Final diagnosis should 
            be made by qualified medical professionals based on complete clinical information.
            """
        
        para = Paragraph(disclaimer, styles['ChineseBody'] if self.has_chinese_font else styles['BodyText'])
        
        # 添加边框
        frame_table = Table([[para]], colWidths=[17*cm])
        frame_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3cd')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#ffc107')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(frame_table)
        
        return elements
    
    def _create_footer(self) -> list:
        """创建报告页脚"""
        styles = self._get_styles()
        elements = []
        
        elements.append(Spacer(1, 1*cm))
        
        # 生成时间和系统信息
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if self.has_chinese_font:
            footer_text = f"""
            <para align="center">
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br/>
            <b>TiCNet 肺结节检测系统</b><br/>
            Transformer in Convolutional Neural Network<br/>
            报告生成时间 / Report Generated: {current_time}<br/>
            版本 / Version: 1.0
            </para>
            """
        else:
            footer_text = f"""
            <para align="center">
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br/>
            <b>TiCNet Pulmonary Nodule Detection System</b><br/>
            Transformer in Convolutional Neural Network<br/>
            Report Generated: {current_time}<br/>
            Version: 1.0
            </para>
            """
        
        para = Paragraph(footer_text, styles['ChineseBody'] if self.has_chinese_font else styles['BodyText'])
        elements.append(para)
        
        return elements

