#!/bin/bash

# =============================================================================
# AI Flashcard Generator - 快速回滚脚本
# 用于紧急情况下快速回滚到上一个工作版本
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示可用备份
show_backups() {
    print_status "查询可用备份..."
    ssh $SERVER_USER@$SERVER_IP << 'EOF'
        echo "可用备份列表："
        ls -la /root/backup-* 2>/dev/null | head -10 || echo "未找到备份文件"
        
        echo ""
        echo "Docker镜像历史："
        docker images | grep ai-flashcard-generator | head -5 || echo "未找到Docker镜像"
EOF
}

# 回滚到指定备份
rollback_to_backup() {
    local backup_dir="$1"
    
    if [[ -z "$backup_dir" ]]; then
        print_error "请指定备份目录"
        return 1
    fi
    
    print_status "回滚到备份: $backup_dir"
    
    ssh $SERVER_USER@$SERVER_IP << EOF
        BACKUP_DIR="$backup_dir"
        
        if [[ ! -d "\$BACKUP_DIR" ]]; then
            echo "错误：备份目录不存在: \$BACKUP_DIR"
            exit 1
        fi
        
        echo "开始回滚..."
        
        # 停止当前容器
        docker stop flashcard-generator-new 2>/dev/null || true
        
        # 恢复应用文件
        if [[ -d "\$BACKUP_DIR/ai-flashcard-generator" ]]; then
            echo "恢复应用文件..."
            cp -r \$BACKUP_DIR/ai-flashcard-generator/* /var/www/ai-flashcard-generator/
            chown -R www-data:www-data /var/www/ai-flashcard-generator
        fi
        
        # 恢复nginx配置
        if [[ -f "\$BACKUP_DIR/explain1thing_ssl.conf" ]]; then
            echo "恢复nginx配置..."
            cp \$BACKUP_DIR/explain1thing_ssl.conf /etc/nginx/sites-enabled/
            nginx -t && systemctl reload nginx
        fi
        
        echo "回滚完成"
EOF
    
    print_success "回滚操作完成"
}

# 快速回滚（重启到上一个工作版本）
quick_rollback() {
    print_status "执行快速回滚..."
    
    ssh $SERVER_USER@$SERVER_IP << 'EOF'
        # 停止当前容器
        echo "停止当前容器..."
        docker stop flashcard-generator-new 2>/dev/null || true
        
        # 使用备份的unified_index.html
        echo "恢复前端文件..."
        cd /var/www/ai-flashcard-generator
        if [[ -f "unified_index.html.backup-"* ]]; then
            LATEST_BACKUP=$(ls -t unified_index.html.backup-* | head -1)
            cp "$LATEST_BACKUP" unified_index.html
            echo "已恢复前端文件: $LATEST_BACKUP"
        fi
        
        # 重启容器到之前的状态
        echo "重启Docker容器..."
        docker run -d --name flashcard-generator-new \
          --restart unless-stopped \
          -p 127.0.0.1:8000:8000 \
          --mount type=bind,source=/root/ai-flashcard-generator/src/config,target=/app/config,readonly \
          ai-flashcard-generator-flashcard-app 2>/dev/null || {
            echo "使用上一个Docker镜像重启..."
            PREV_IMAGE=$(docker images | grep ai-flashcard-generator | sed -n '2p' | awk '{print $3}')
            if [[ -n "$PREV_IMAGE" ]]; then
                docker run -d --name flashcard-generator-new \
                  --restart unless-stopped \
                  -p 127.0.0.1:8000:8000 \
                  --mount type=bind,source=/root/ai-flashcard-generator/src/config,target=/app/config,readonly \
                  $PREV_IMAGE
            fi
        }
        
        # 清理容器
        docker container prune -f >/dev/null 2>&1
        
        # 重载nginx
        echo "重载nginx配置..."
        nginx -t && systemctl reload nginx
        
        # 等待服务启动
        sleep 10
        
        # 验证服务
        if curl -s http://127.0.0.1:8000/health >/dev/null; then
            echo "✅ 快速回滚成功，服务已恢复"
        else
            echo "❌ 回滚后服务仍异常"
            exit 1
        fi
EOF
    
    print_success "快速回滚完成"
}

# 检查服务状态
check_service_status() {
    print_status "检查服务状态..."
    
    ssh $SERVER_USER@$SERVER_IP << 'EOF'
        echo "=== 服务状态检查 ==="
        
        # Docker状态
        echo "Docker容器："
        docker ps | grep flashcard || echo "未找到运行中的容器"
        
        # 端口状态
        echo "端口监听："
        ss -tlnp | grep :8000 && echo "✓ 8000端口正常" || echo "✗ 8000端口异常"
        ss -tlnp | grep :443 && echo "✓ 443端口正常" || echo "✗ 443端口异常"
        
        # nginx状态
        echo "nginx状态："
        systemctl is-active nginx && echo "✓ nginx正常运行" || echo "✗ nginx异常"
        
        # API测试
        echo "API测试："
        curl -s http://127.0.0.1:8000/health >/dev/null && echo "✓ 本地API正常" || echo "✗ 本地API异常"
        curl -s http://127.0.0.1/ai-flashcard-generator/api/health >/dev/null && echo "✓ 代理API正常" || echo "✗ 代理API异常"
EOF
    
    # 外部访问测试
    if curl -s "https://explain1thing.top/ai-flashcard-generator/api/health" | grep -q "status"; then
        print_success "✓ 外部访问正常"
    else
        print_warning "✗ 外部访问异常"
    fi
}

# 主菜单
show_menu() {
    echo "=============================================="
    echo -e "${BLUE}🔄 AI Flashcard Generator 回滚工具${NC}"
    echo "=============================================="
    echo ""
    echo "选择操作："
    echo "1) 检查服务状态"
    echo "2) 查看可用备份"
    echo "3) 快速回滚（推荐）"
    echo "4) 回滚到指定备份"
    echo "5) 退出"
    echo ""
}

main() {
    if [[ $# -eq 1 && "$1" == "--quick" ]]; then
        quick_rollback
        return 0
    fi
    
    while true; do
        show_menu
        read -p "请选择 (1-5): " choice
        
        case $choice in
            1)
                check_service_status
                echo ""
                ;;
            2)
                show_backups
                echo ""
                ;;
            3)
                echo ""
                read -p "确认执行快速回滚？(y/N): " -n 1 -r
                echo ""
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    quick_rollback
                fi
                echo ""
                ;;
            4)
                echo ""
                read -p "请输入备份目录路径: " backup_path
                if [[ -n "$backup_path" ]]; then
                    rollback_to_backup "$backup_path"
                fi
                echo ""
                ;;
            5)
                echo "退出"
                break
                ;;
            *)
                print_error "无效选择"
                echo ""
                ;;
        esac
    done
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi