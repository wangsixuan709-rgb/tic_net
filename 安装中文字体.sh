#!/bin/bash
# 自动安装中文字体脚本

echo "======================================================================"
echo "TiCNet 中文字体安装脚本"
echo "======================================================================"
echo ""

# 检测操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "❌ 无法检测操作系统"
    exit 1
fi

echo "检测到操作系统: $OS"
echo ""

# 根据不同操作系统安装字体
case $OS in
    ubuntu|debian)
        echo "📦 安装中文字体 (Ubuntu/Debian)..."
        echo ""
        echo "将安装以下字体包:"
        echo "  • fonts-wqy-microhei (文泉驿微米黑)"
        echo "  • fonts-wqy-zenhei (文泉驿正黑)"  
        echo "  • fonts-noto-cjk (思源黑体)"
        echo ""
        read -p "是否继续? (y/n) " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo apt-get update
            sudo apt-get install -y fonts-wqy-microhei fonts-wqy-zenhei fonts-noto-cjk
            
            if [ $? -eq 0 ]; then
                echo "✅ 字体安装成功"
            else
                echo "❌ 字体安装失败"
                exit 1
            fi
        else
            echo "取消安装"
            exit 0
        fi
        ;;
        
    centos|rhel|fedora)
        echo "📦 安装中文字体 (CentOS/RHEL/Fedora)..."
        echo ""
        echo "将安装以下字体包:"
        echo "  • wqy-microhei-fonts"
        echo "  • wqy-zenhei-fonts"
        echo "  • google-noto-sans-cjk-fonts"
        echo ""
        read -p "是否继续? (y/n) " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo yum install -y wqy-microhei-fonts wqy-zenhei-fonts google-noto-sans-cjk-fonts
            
            if [ $? -eq 0 ]; then
                echo "✅ 字体安装成功"
            else
                echo "❌ 字体安装失败"
                exit 1
            fi
        else
            echo "取消安装"
            exit 0
        fi
        ;;
        
    *)
        echo "⚠️  未识别的操作系统: $OS"
        echo ""
        echo "请手动安装中文字体:"
        echo "  1. 下载字体文件 (.ttf 或 .otf)"
        echo "  2. 复制到 ~/.fonts/ 目录"
        echo "  3. 运行: fc-cache -fv"
        exit 1
        ;;
esac

# 刷新字体缓存
echo ""
echo "🔄 刷新字体缓存..."
fc-cache -fv > /dev/null 2>&1

# 清除matplotlib缓存
echo "🔄 清除matplotlib缓存..."
rm -rf ~/.cache/matplotlib ~/.matplotlib 2>/dev/null

echo ""
echo "======================================================================"
echo "✅ 字体安装完成！"
echo "======================================================================"
echo ""
echo "下一步:"
echo "  1. 运行字体检测: python check_chinese_fonts.py"
echo "  2. 重启TiCNet系统: python run_system.py"
echo ""

