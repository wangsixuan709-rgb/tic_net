#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新功能：置信度阈值和报告生成
"""

import os
import sys
import json

def test_config_update():
    """测试配置更新"""
    print("=" * 60)
    print("测试1: 检查置信度阈值配置")
    print("=" * 60)
    
    try:
        from system.config import SystemConfig
        config = SystemConfig()
        
        threshold = config.INFERENCE_CONFIG['min_confidence']
        print(f"✅ 当前置信度阈值: {threshold}")
        
        if threshold == 0.7:
            print("✅ 阈值已正确更新为0.7")
            return True
        else:
            print(f"❌ 阈值为{threshold}，预期为0.7")
            return False
            
    except Exception as e:
        print(f"❌ 配置检查失败: {str(e)}")
        return False

def test_report_generator_import():
    """测试报告生成器导入"""
    print("\n" + "=" * 60)
    print("测试2: 检查报告生成模块")
    print("=" * 60)
    
    try:
        from system.report_generator import ReportGenerator
        print("✅ ReportGenerator模块导入成功")
        
        # 检查reportlab依赖
        try:
            import reportlab
            print(f"✅ reportlab已安装 (版本: {reportlab.Version})")
            return True
        except ImportError:
            print("⚠️  reportlab未安装")
            print("   请运行: pip install reportlab")
            return False
            
    except Exception as e:
        print(f"❌ 模块导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_visualization_filtering():
    """测试可视化过滤逻辑"""
    print("\n" + "=" * 60)
    print("测试3: 检查可视化过滤逻辑")
    print("=" * 60)
    
    try:
        # 读取visualization.py源码检查过滤逻辑
        with open('system/visualization.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含置信度过滤代码
        if "detection['confidence'] >= 0.7" in content:
            print("✅ 可视化代码包含置信度过滤逻辑")
            
            # 统计出现次数
            count = content.count("detection['confidence'] >= 0.7")
            print(f"✅ 在{count}处添加了置信度过滤（预期3处）")
            
            if count >= 3:
                return True
            else:
                print("⚠️  过滤逻辑可能不完整")
                return False
        else:
            print("❌ 未找到置信度过滤代码")
            return False
            
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        return False

def test_flask_routes():
    """测试Flask路由"""
    print("\n" + "=" * 60)
    print("测试4: 检查Flask路由")
    print("=" * 60)
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        routes = [
            'generate_report',
            'api_generate_report',
            'download_report'
        ]
        
        all_found = True
        for route in routes:
            if f"def {route}" in content:
                print(f"✅ 路由函数 {route} 已添加")
            else:
                print(f"❌ 路由函数 {route} 未找到")
                all_found = False
        
        # 检查ReportGenerator导入
        if 'from system.report_generator import ReportGenerator' in content:
            print("✅ ReportGenerator已导入")
        else:
            print("❌ ReportGenerator未导入")
            all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        return False

def test_frontend_button():
    """测试前端按钮"""
    print("\n" + "=" * 60)
    print("测试5: 检查前端生成报告按钮")
    print("=" * 60)
    
    try:
        with open('templates/results.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = {
            '生成报告按钮': 'generateReportBtn',
            '按钮点击事件': "('#generateReportBtn').click",
            '报告生成请求': '/generate_report/'
        }
        
        all_found = True
        for name, pattern in checks.items():
            if pattern in content:
                print(f"✅ {name} 已添加")
            else:
                print(f"❌ {name} 未找到")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        return False

def test_requirements():
    """测试依赖文件"""
    print("\n" + "=" * 60)
    print("测试6: 检查requirements.txt")
    print("=" * 60)
    
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'reportlab' in content:
            print("✅ reportlab已添加到requirements.txt")
            return True
        else:
            print("❌ reportlab未添加到requirements.txt")
            return False
            
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "TiCNet 新功能测试" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    tests = [
        ("置信度阈值配置", test_config_update),
        ("报告生成模块", test_report_generator_import),
        ("可视化过滤", test_visualization_filtering),
        ("Flask路由", test_flask_routes),
        ("前端按钮", test_frontend_button),
        ("依赖文件", test_requirements)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name}测试异常: {str(e)}")
            results.append((name, False))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print("\n" + "-" * 60)
    print(f"总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！新功能已成功集成。")
        print("\n下一步操作：")
        print("1. 安装reportlab: pip install reportlab")
        print("2. 启动系统: python run_system.py")
        print("3. 进行检测并测试报告生成功能")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息。")
        return 1

if __name__ == '__main__':
    sys.exit(main())

