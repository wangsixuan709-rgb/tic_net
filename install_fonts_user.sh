#!/bin/bash
# 安装中文字体到用户目录（不需要sudo权限）

echo "======================================================================"
echo "安装中文字体到用户目录"
echo "======================================================================"
echo ""

# 创建用户字体目录
FONT_DIR="$HOME/.fonts"
mkdir -p "$FONT_DIR"

echo "📁 字体安装目录: $FONT_DIR"
echo ""

# 检查是否已有文泉驿字体
if fc-list | grep -i "WenQuanYi" > /dev/null 2>&1; then
    echo "✅ 系统已安装文泉驿字体"
else
    echo "📦 下载文泉驿微米黑字体..."
    echo ""
    
    cd /tmp
    
    # 下载文泉驿微米黑
    if [ ! -f "wqy-microhei.ttc" ]; then
        wget -q --show-progress https://github.com/anthonyfok/fonts-wqy-microhei/raw/master/wqy-microhei.ttc \
            -O wqy-microhei.ttc 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "✅ 下载成功"
            cp wqy-microhei.ttc "$FONT_DIR/"
            echo "✅ 字体已安装到 $FONT_DIR/wqy-microhei.ttc"
        else
            echo "❌ 下载失败，尝试备用源..."
            
            # 备用下载地址
            wget -q --show-progress https://sourceforge.net/projects/wqy/files/wqy-microhei/0.2.0-beta/wqy-microhei-0.2.0-beta.tar.gz \
                -O wqy-microhei.tar.gz 2>/dev/null
            
            if [ $? -eq 0 ]; then
                tar -xzf wqy-microhei.tar.gz
                cp wqy-microhei/wqy-microhei.ttc "$FONT_DIR/"
                echo "✅ 字体已安装"
                rm -rf wqy-microhei wqy-microhei.tar.gz
            else
                echo "❌ 无法下载字体文件"
                echo ""
                echo "请手动安装字体，命令如下："
                echo "  sudo apt-get install fonts-wqy-microhei"
                exit 1
            fi
        fi
    fi
fi

echo ""
echo "🔄 刷新字体缓存..."
fc-cache -fv > /dev/null 2>&1

echo "🔄 清除matplotlib缓存..."
rm -rf ~/.cache/matplotlib ~/.matplotlib 2>/dev/null

echo ""
echo "======================================================================"
echo "✅ 字体安装完成！"
echo "======================================================================"
echo ""
echo "验证安装:"
echo "  $ python check_chinese_fonts.py"
echo ""

