from flask import Flask, render_template, request, jsonify, send_file, url_for
import os
import json
import uuid
import numpy as np
from werkzeug.utils import secure_filename
import torch
from datetime import datetime
import traceback

from system.model_inference import ModelInference
from system.visualization import ResultVisualizer
from system.config import SystemConfig
from system.result_validator import ResultValidator
from system.report_generator import ReportGenerator
from system.ai_analyzer import AIAnalyzer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ticnet-system-2024'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['JSON_AS_ASCII'] = False  # 支持中文JSON响应

# 初始化系统组件
config = SystemConfig()
model_inference = ModelInference(config)
visualizer = ResultVisualizer(config)
validator = ResultValidator(model_inference.annotation_handler)
report_generator = ReportGenerator(config)
ai_analyzer = AIAnalyzer()

# 确保上传和结果目录存在
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.RESULTS_FOLDER, exist_ok=True)
os.makedirs(config.VISUALIZATION_FOLDER, exist_ok=True)

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/preview', methods=['POST'])
def preview_file():
    """预览上传的文件（支持多文件上传，特别是MHD格式）"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        files = request.files.getlist('file')
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        # 生成唯一的任务ID
        task_id = str(uuid.uuid4())
        
        # 保存所有上传的文件
        saved_files = []
        main_file_path = None
        raw_file_path = None
        
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(config.UPLOAD_FOLDER, f"{task_id}_{filename}")
                file.save(file_path)
                saved_files.append(filename)
                
                # 找到主文件（非.raw文件）
                if not filename.endswith('.raw') and allowed_file(filename):
                    main_file_path = file_path
                    main_filename = filename
                elif filename.endswith('.raw'):
                    raw_file_path = file_path
        
        # 如果是MHD文件，需要修改其中的ElementDataFile路径
        if main_file_path and main_file_path.endswith('.mhd') and raw_file_path:
            print(f"检测到MHD+RAW文件组合，修复MHD文件中的路径引用...")
            try:
                with open(main_file_path, 'r') as f:
                    mhd_content = f.read()
                
                # 提取原始raw文件名
                import re
                match = re.search(r'ElementDataFile\s*=\s*(.+)', mhd_content)
                if match:
                    original_raw_name = match.group(1).strip()
                    new_raw_name = os.path.basename(raw_file_path)
                    
                    # 替换为带task_id的文件名
                    mhd_content = mhd_content.replace(
                        f'ElementDataFile = {original_raw_name}',
                        f'ElementDataFile = {new_raw_name}'
                    )
                    
                    # 写回文件
                    with open(main_file_path, 'w') as f:
                        f.write(mhd_content)
                    
                    print(f"✓ 已更新MHD文件: {original_raw_name} → {new_raw_name}")
            except Exception as e:
                print(f"⚠️ 修改MHD文件失败: {str(e)}")
        
        if not main_file_path:
            return jsonify({'success': False, 'error': '未找到有效的主文件'})
        
        print(f"保存的文件: {saved_files}")
        print(f"主文件: {main_filename}")
        
        # 生成预览图像
        preview_path = visualizer.create_preview(main_file_path, task_id)
        
        if preview_path:
            return jsonify({
                'success': True,
                'task_id': task_id,
                'preview_path': preview_path,
                'filename': main_filename,
                'all_files': saved_files
            })
        else:
            return jsonify({'success': False, 'error': '无法生成预览图像'})
            
    except Exception as e:
        print(f"预览错误: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'预览失败: {str(e)}'})

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传和模型推理（支持多文件上传，特别是MHD格式）"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        files = request.files.getlist('file')
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        # 生成唯一的任务ID
        task_id = str(uuid.uuid4())
        
        # 保存所有上传的文件
        saved_files = []
        main_file_path = None
        main_filename = None
        raw_file_path = None
        
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(config.UPLOAD_FOLDER, f"{task_id}_{filename}")
                file.save(file_path)
                saved_files.append(filename)
                
                # 找到主文件（非.raw文件）
                if not filename.endswith('.raw') and allowed_file(filename):
                    main_file_path = file_path
                    main_filename = filename
                elif filename.endswith('.raw'):
                    raw_file_path = file_path
        
        # 如果是MHD文件，需要修改其中的ElementDataFile路径
        if main_file_path and main_file_path.endswith('.mhd') and raw_file_path:
            print(f"检测到MHD+RAW文件组合，修复MHD文件中的路径引用...")
            try:
                with open(main_file_path, 'r') as f:
                    mhd_content = f.read()
                
                # 提取原始raw文件名
                import re
                match = re.search(r'ElementDataFile\s*=\s*(.+)', mhd_content)
                if match:
                    original_raw_name = match.group(1).strip()
                    new_raw_name = os.path.basename(raw_file_path)
                    
                    # 替换为带task_id的文件名
                    mhd_content = mhd_content.replace(
                        f'ElementDataFile = {original_raw_name}',
                        f'ElementDataFile = {new_raw_name}'
                    )
                    
                    # 写回文件
                    with open(main_file_path, 'w') as f:
                        f.write(mhd_content)
                    
                    print(f"✓ 已更新MHD文件: {original_raw_name} → {new_raw_name}")
            except Exception as e:
                print(f"⚠️ 修改MHD文件失败: {str(e)}")
        
        if not main_file_path:
            return jsonify({'success': False, 'error': '未找到有效的主文件'})
        
        print(f"保存的文件: {saved_files}")
        print(f"主文件: {main_filename}")
        print(f"开始处理: {main_file_path}")
        
        # 进行模型推理
        results = model_inference.predict(main_file_path, task_id)
        
        # 进行结果验证
        validation_result = validator.validate_detection_results(
            main_file_path, results['detections'], results['meta_info']
        )
        
        # 生成可视化结果（传递ground truth数据）
        ground_truth_boxes = []
        if validation_result.get('has_ground_truth', False):
            # 从annotation_handler获取ground truth
            truth_boxes, truth_labels = model_inference.annotation_handler.get_truth_data_for_image(
                main_file_path, 
                results['meta_info']['spacing'],
                results['meta_info']['origin'], 
                results['meta_info']['original_shape']
            )
            ground_truth_boxes = truth_boxes
        
        visualization_paths = visualizer.create_visualizations(
            main_file_path, results, task_id, ground_truth_boxes=ground_truth_boxes
        )
        
        # 如果有真实标注，创建对比可视化
        if validation_result.get('has_ground_truth', False):
            image_data = visualizer._load_image(main_file_path)
            comparison_viz = validator.create_comparison_visualization(
                image_data, results['detections'], validation_result, 
                task_id, config.VISUALIZATION_FOLDER
            )
            if comparison_viz:
                visualization_paths['validation'] = comparison_viz
        
        # 保存结果到JSON文件
        result_data = {
            'task_id': task_id,
            'filename': main_filename,
            'timestamp': datetime.now().isoformat(),
            'detections': results['detections'],
            'statistics': results['statistics'],
            'meta_info': results['meta_info'],
            'visualization_paths': visualization_paths,  # 修正变量名
            'validation_result': validation_result
        }
        
        result_file = os.path.join(config.RESULTS_FOLDER, f"{task_id}_results.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'filename': main_filename,
            'detections': results['detections'],
            'statistics': results['statistics'],
            'visualization_paths': visualization_paths  # 修正变量名
        })
            
    except Exception as e:
        print(f"错误: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'处理失败: {str(e)}'})

@app.route('/results/<task_id>')
def view_results(task_id):
    """查看检测结果页面"""
    try:
        result_file = os.path.join(config.RESULTS_FOLDER, f"{task_id}_results.json")
        if not os.path.exists(result_file):
            return render_template('error.html', message='未找到结果文件')
        
        with open(result_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        return render_template('results.html', results=results)
    
    except Exception as e:
        return render_template('error.html', message=f'加载结果失败: {str(e)}')

@app.route('/api/results/<task_id>')
def get_results_api(task_id):
    """获取检测结果的API接口"""
    try:
        result_file = os.path.join(config.RESULTS_FOLDER, f"{task_id}_results.json")
        if not os.path.exists(result_file):
            return jsonify({'success': False, 'error': '未找到结果'})
        
        with open(result_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        return jsonify({'success': True, 'data': results})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/visualization/<path:filename>')
def serve_visualization(filename):
    """提供可视化图像文件"""
    return send_file(os.path.join(config.VISUALIZATION_FOLDER, filename))

@app.route('/history')
def history():
    """查看历史检测记录"""
    try:
        history_data = []
        for filename in os.listdir(config.RESULTS_FOLDER):
            if filename.endswith('_results.json'):
                file_path = os.path.join(config.RESULTS_FOLDER, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    history_data.append({
                        'task_id': data['task_id'],
                        'filename': data['filename'],
                        'timestamp': data['timestamp'],
                        'num_detections': len(data['detections'])
                    })
        
        # 按时间排序
        history_data.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return render_template('history.html', history=history_data)
    
    except Exception as e:
        return render_template('error.html', message=f'加载历史记录失败: {str(e)}')

@app.route('/about')
def about():
    """关于页面"""
    model_info = {
        'name': 'TiCNet',
        'description': 'Transformer in Convolutional Neural Network for Pulmonary Nodule Detection',
        'version': '1.0',
        'paper': 'TiCNet: Transformer in Convolutional Neural Network for Pulmonary Nodule Detection on CT Images',
        'authors': 'Ma, Ling and Li, Gen and Feng, Xingyu and Fan, Qiliang and Liu, Lizhi'
    }
    return render_template('about.html', model_info=model_info)

@app.route('/report/<task_id>')
def view_report(task_id):
    """查看在线报告（网页版）"""
    try:
        # 加载检测结果
        result_file = os.path.join(config.RESULTS_FOLDER, f"{task_id}_results.json")
        
        if not os.path.exists(result_file):
            return render_template('error.html', message=f'未找到任务 {task_id} 的检测结果')
        
        with open(result_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # 准备可视化文件信息
        viz_files = {
            'summary': f"{task_id}_summary.png",
            'original_slices': f"{task_id}_original_slices.png",
            'overlay': f"{task_id}_overlay.png"
        }
        
        # 检查文件是否存在
        for key, filename in viz_files.items():
            if not os.path.exists(os.path.join(config.VISUALIZATION_FOLDER, filename)):
                viz_files[key] = None
        
        # 准备文件信息
        file_info = {
            'filename': results.get('filename', 'Unknown'),
            'task_id': task_id
        }
        
        # 渲染报告页面
        return render_template('report.html',
                             results=results,
                             file_info=file_info,
                             stats=results.get('statistics', {}),
                             detections=results.get('detections', []),
                             viz_files=viz_files)
    
    except Exception as e:
        print(f"加载报告错误: {str(e)}")
        traceback.print_exc()
        return render_template('error.html', message=f'加载报告失败: {str(e)}')

@app.route('/api/ai_analysis/<task_id>')
def get_ai_analysis(task_id):
    """获取AI智能分析（API接口）"""
    try:
        # 加载检测结果
        result_file = os.path.join(config.RESULTS_FOLDER, f"{task_id}_results.json")
        
        if not os.path.exists(result_file):
            return jsonify({
                'success': False,
                'error': '未找到检测结果'
            }), 404
        
        with open(result_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # 调用AI分析器生成分析
        analysis_result = ai_analyzer.generate_analysis(results)
        
        return jsonify(analysis_result)
    
    except Exception as e:
        print(f"AI分析错误: {str(e)}")
        traceback.print_exc()
        
        # 返回降级分析
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            fallback_text = ai_analyzer._generate_fallback_analysis(results)
            return jsonify({
                'success': False,
                'analysis': fallback_text,
                'error': str(e)
            })
        except:
            return jsonify({
                'success': False,
                'error': '生成分析失败',
                'analysis': '暂无分析内容'
            }), 500

@app.route('/generate_report/<task_id>')
def generate_report(task_id):
    """生成PDF报告（下载）"""
    try:
        # 生成PDF报告
        report_path = report_generator.generate_report(task_id)
        
        # 返回PDF文件
        return send_file(
            report_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"TiCNet_Report_{task_id[:8]}.pdf"
        )
        
    except Exception as e:
        print(f"生成报告错误: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'生成报告失败: {str(e)}'}), 500

@app.route('/api/generate_report/<task_id>', methods=['POST'])
def api_generate_report(task_id):
    """生成报告的API接口（异步）"""
    try:
        # 生成报告
        report_path = report_generator.generate_report(task_id)
        
        # 返回报告文件名
        report_filename = os.path.basename(report_path)
        
        return jsonify({
            'success': True,
            'report_filename': report_filename,
            'message': '报告生成成功'
        })
        
    except Exception as e:
        print(f"生成报告错误: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'生成报告失败: {str(e)}'}), 500

@app.route('/download_report/<filename>')
def download_report(filename):
    """下载报告文件"""
    try:
        report_path = os.path.join(config.RESULTS_FOLDER, filename)
        if not os.path.exists(report_path):
            return jsonify({'success': False, 'error': '报告文件不存在'}), 404
        
        return send_file(
            report_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"下载报告错误: {str(e)}")
        return jsonify({'success': False, 'error': f'下载失败: {str(e)}'}), 500

@app.route('/api/delete/<task_id>', methods=['DELETE'])
def delete_record(task_id):
    """删除单个检测记录及其相关文件"""
    try:
        deleted_files = []
        
        # 1. 删除结果JSON文件
        result_file = os.path.join(config.RESULTS_FOLDER, f"{task_id}_results.json")
        if os.path.exists(result_file):
            os.remove(result_file)
            deleted_files.append('results.json')
        
        # 2. 删除PDF报告
        report_file = os.path.join(config.RESULTS_FOLDER, f"{task_id}_report.pdf")
        if os.path.exists(report_file):
            os.remove(report_file)
            deleted_files.append('report.pdf')
        
        # 3. 删除可视化图像
        viz_patterns = [
            f"{task_id}_preview.png",
            f"{task_id}_summary.png",
            f"{task_id}_overlay.png",
            f"{task_id}_original_slices.png",
            f"{task_id}_validation.png"
        ]
        
        for pattern in viz_patterns:
            viz_file = os.path.join(config.VISUALIZATION_FOLDER, pattern)
            if os.path.exists(viz_file):
                os.remove(viz_file)
                deleted_files.append(pattern)
        
        # 4. 删除上传的原始文件
        for filename in os.listdir(config.UPLOAD_FOLDER):
            if filename.startswith(task_id):
                upload_file = os.path.join(config.UPLOAD_FOLDER, filename)
                os.remove(upload_file)
                deleted_files.append(filename)
        
        return jsonify({
            'success': True,
            'message': '记录已删除',
            'deleted_files': deleted_files
        })
        
    except Exception as e:
        print(f"删除记录错误: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'删除失败: {str(e)}'}), 500

@app.route('/api/delete_batch', methods=['POST'])
def delete_batch():
    """批量删除检测记录"""
    try:
        task_ids = request.json.get('task_ids', [])
        
        if not task_ids:
            return jsonify({'success': False, 'error': '未提供要删除的记录'}), 400
        
        deleted_count = 0
        failed_count = 0
        
        for task_id in task_ids:
            try:
                # 删除结果JSON
                result_file = os.path.join(config.RESULTS_FOLDER, f"{task_id}_results.json")
                if os.path.exists(result_file):
                    os.remove(result_file)
                
                # 删除PDF报告
                report_file = os.path.join(config.RESULTS_FOLDER, f"{task_id}_report.pdf")
                if os.path.exists(report_file):
                    os.remove(report_file)
                
                # 删除可视化图像
                for filename in os.listdir(config.VISUALIZATION_FOLDER):
                    if filename.startswith(task_id):
                        os.remove(os.path.join(config.VISUALIZATION_FOLDER, filename))
                
                # 删除上传文件
                for filename in os.listdir(config.UPLOAD_FOLDER):
                    if filename.startswith(task_id):
                        os.remove(os.path.join(config.UPLOAD_FOLDER, filename))
                
                deleted_count += 1
                
            except Exception as e:
                print(f"删除任务 {task_id} 失败: {str(e)}")
                failed_count += 1
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'failed_count': failed_count,
            'message': f'成功删除 {deleted_count} 条记录'
        })
        
    except Exception as e:
        print(f"批量删除错误: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'批量删除失败: {str(e)}'}), 500

@app.route('/api/clear_all', methods=['POST'])
def clear_all():
    """清空所有检测记录"""
    try:
        deleted_count = 0
        
        # 清空results文件夹
        for filename in os.listdir(config.RESULTS_FOLDER):
            if filename.endswith('_results.json') or filename.endswith('_report.pdf'):
                os.remove(os.path.join(config.RESULTS_FOLDER, filename))
                deleted_count += 1
        
        # 清空visualizations文件夹
        for filename in os.listdir(config.VISUALIZATION_FOLDER):
            if filename.endswith('.png'):
                os.remove(os.path.join(config.VISUALIZATION_FOLDER, filename))
        
        # 清空uploads文件夹
        for filename in os.listdir(config.UPLOAD_FOLDER):
            os.remove(os.path.join(config.UPLOAD_FOLDER, filename))
        
        return jsonify({
            'success': True,
            'message': f'已清空所有记录 (共{deleted_count}条)'
        })
        
    except Exception as e:
        print(f"清空记录错误: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'清空失败: {str(e)}'}), 500

def allowed_file(filename):
    """检查文件类型是否允许"""
    ALLOWED_EXTENSIONS = {'mhd', 'nii', 'nii.gz', 'nrrd', 'nhdr', 'dcm', 'npy', 'png', 'jpg', 'jpeg', 'raw'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS or \
           filename.lower().endswith('.nii.gz')

@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'error': '文件太大，请上传小于500MB的文件'})

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'success': False, 'error': '服务器内部错误'})

if __name__ == '__main__':
    print("启动TiCNet肺结节检测系统...")
    print(f"上传目录: {config.UPLOAD_FOLDER}")
    print(f"结果目录: {config.RESULTS_FOLDER}")
    print(f"可视化目录: {config.VISUALIZATION_FOLDER}")
    
    app.run(host='0.0.0.0', port=5000, debug=True) 