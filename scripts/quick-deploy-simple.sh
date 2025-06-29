#!/bin/bash

# =============================================================================
# AI Flashcard Generator - 快速更新脚本
# 用于快速更新代码，不涉及nginx和SSL配置
# =============================================================================

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
SERVER_IP="198.23.164.200"
SERVER_USER="root"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

main() {
    echo "🚀 快速更新部署..."
    
    # 1. 同步代码
    print_status "同步应用代码..."
    scp main_refactored.py $SERVER_USER@$SERVER_IP:/root/ai-flashcard-generator/src/
    scp unified_index.html $SERVER_USER@$SERVER_IP:/root/ai-flashcard-generator/src/
    
    # 同步可选文件
    [[ -f "prompt_templates.json" ]] && scp prompt_templates.json $SERVER_USER@$SERVER_IP:/root/ai-flashcard-generator/src/
    [[ -f "model_manager.py" ]] && scp model_manager.py $SERVER_USER@$SERVER_IP:/root/ai-flashcard-generator/src/
    [[ -f "local_model_metadata.json" ]] && scp local_model_metadata.json $SERVER_USER@$SERVER_IP:/root/ai-flashcard-generator/src/
    
    # 2. 更新服务器
    print_status "重启应用服务..."
    ssh $SERVER_USER@$SERVER_IP << 'EOF'
        # 更新前端
        cp /root/ai-flashcard-generator/src/unified_index.html /var/www/ai-flashcard-generator/
        sed -i "s|window\.API_BASE_URL = ''|window.API_BASE_URL = '/ai-flashcard-generator/api'|g" /var/www/ai-flashcard-generator/unified_index.html
        chown -R www-data:www-data /var/www/ai-flashcard-generator
        
        # 重启Docker容器
        cd /root/ai-flashcard-generator
        docker build -t ai-flashcard-generator-flashcard-app . >/dev/null 2>&1
        docker stop flashcard-generator-new >/dev/null 2>&1 || true
        docker run -d --name flashcard-generator-new \
          --restart unless-stopped \
          -p 127.0.0.1:8000:8000 \
          --mount type=bind,source=/root/ai-flashcard-generator/src/config,target=/app/config,readonly \
          ai-flashcard-generator-flashcard-app >/dev/null 2>&1
        
        # 清理
        docker container prune -f >/dev/null 2>&1
        
        # 等待启动
        sleep 5
        
        # 验证
        if curl -s http://127.0.0.1:8000/health >/dev/null; then
            echo "✅ 应用重启成功"
        else
            echo "❌ 应用重启失败"
            exit 1
        fi
EOF
    
    # 3. 验证部署
    print_status "验证部署结果..."
    if curl -s "https://explain1thing.top/ai-flashcard-generator/api/health" | grep -q "status"; then
        print_success "✅ 部署验证成功"
    else
        echo "⚠️  外部访问验证失败，但应用可能正常"
    fi
    
    print_success "🎉 快速部署完成！"
    echo "📱 访问: https://explain1thing.top/ai-flashcard-generator"
}

main "$@"