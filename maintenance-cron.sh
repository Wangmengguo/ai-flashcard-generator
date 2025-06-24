#!/bin/bash
# 定期维护和清理任务脚本
# 用于设置自动化的Docker清理和系统维护

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 项目配置
PROJECT_DIR="/root/ai-flashcard-generator"
LOG_DIR="/root/maintenance_logs"
BACKUP_DIR="/root/backups"

# 创建必要目录
setup_directories() {
    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"
    log_success "维护目录已创建"
}

# 每日清理任务
daily_cleanup() {
    local log_file="$LOG_DIR/daily_cleanup_$(date +%Y%m%d).log"
    
    {
        echo "=== 每日清理任务开始 $(date) ==="
        
        # 基础Docker清理
        echo "执行Docker基础清理..."
        if [ -f "$PROJECT_DIR/docker-cleanup.sh" ]; then
            cd "$PROJECT_DIR"
            ./docker-cleanup.sh basic
        else
            docker container prune -f
            docker image prune -f
            docker network prune -f
        fi
        
        # 清理旧日志文件（保留7天）
        echo "清理旧维护日志..."
        find "$LOG_DIR" -name "*.log" -mtime +7 -delete
        
        # 检查磁盘空间
        echo "磁盘空间使用情况："
        df -h /
        
        # 检查内存使用
        echo "内存使用情况："
        free -h
        
        echo "=== 每日清理任务完成 $(date) ==="
        echo
        
    } >> "$log_file" 2>&1
    
    echo "每日清理完成，日志: $log_file"
}

# 每周深度清理
weekly_cleanup() {
    local log_file="$LOG_DIR/weekly_cleanup_$(date +%Y%m%d).log"
    
    {
        echo "=== 每周深度清理开始 $(date) ==="
        
        # Docker深度清理
        echo "执行Docker深度清理..."
        if [ -f "$PROJECT_DIR/docker-cleanup.sh" ]; then
            cd "$PROJECT_DIR"
            # 自动确认深度清理
            echo "y" | ./docker-cleanup.sh deep
        else
            docker system prune -a -f
        fi
        
        # 清理构建缓存
        echo "清理构建缓存..."
        docker builder prune -a -f
        
        # 备份重要配置
        echo "备份配置文件..."
        if [ -d "$PROJECT_DIR" ]; then
            backup_name="config_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
            tar -czf "$BACKUP_DIR/$backup_name" \
                "$PROJECT_DIR/.env" \
                "$PROJECT_DIR/docker-compose.yml" \
                "$PROJECT_DIR/unified_index.html" \
                "$PROJECT_DIR/main_refactored.py" \
                2>/dev/null || echo "部分文件备份失败"
            echo "配置备份完成: $backup_name"
        fi
        
        # 清理旧备份（保留30天）
        echo "清理旧备份文件..."
        find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
        
        echo "=== 每周深度清理完成 $(date) ==="
        echo
        
    } >> "$log_file" 2>&1
    
    echo "每周深度清理完成，日志: $log_file"
}

# 健康检查任务
health_check() {
    local log_file="$LOG_DIR/health_check_$(date +%Y%m%d).log"
    
    {
        echo "=== 健康检查开始 $(date) ==="
        
        # 检查应用是否运行
        if [ -d "$PROJECT_DIR" ]; then
            cd "$PROJECT_DIR"
            
            echo "检查容器状态..."
            docker compose ps
            
            echo "检查API健康状态..."
            if curl -f -s http://localhost:8000/health >/dev/null; then
                echo "✅ API健康检查通过"
            else
                echo "❌ API健康检查失败"
                # 尝试重启应用
                echo "尝试重启应用..."
                docker compose restart flashcard-app
                sleep 30
                
                # 再次检查
                if curl -f -s http://localhost:8000/health >/dev/null; then
                    echo "✅ 重启后API恢复正常"
                else
                    echo "❌ 重启后API仍然异常，需要人工介入"
                fi
            fi
            
            echo "检查系统资源..."
            echo "内存使用："
            free -h
            echo "磁盘使用："
            df -h
            echo "Docker资源："
            docker system df
        fi
        
        echo "=== 健康检查完成 $(date) ==="
        echo
        
    } >> "$log_file" 2>&1
    
    echo "健康检查完成，日志: $log_file"
}

# 安装cron任务
install_cron_jobs() {
    log_info "安装定期维护任务..."
    
    # 备份现有crontab
    crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
    
    # 创建临时cron文件
    local temp_cron="/tmp/maintenance_cron"
    
    # 保留现有的cron任务（除了我们的维护任务）
    crontab -l 2>/dev/null | grep -v "maintenance-cron.sh" > "$temp_cron" || true
    
    # 添加新的维护任务
    cat >> "$temp_cron" << EOF

# AI Flashcard Generator 维护任务
# 每日2点执行基础清理
0 2 * * * $PROJECT_DIR/maintenance-cron.sh daily >> $LOG_DIR/cron.log 2>&1

# 每周日4点执行深度清理
0 4 * * 0 $PROJECT_DIR/maintenance-cron.sh weekly >> $LOG_DIR/cron.log 2>&1

# 每小时执行健康检查
0 * * * * $PROJECT_DIR/maintenance-cron.sh health >> $LOG_DIR/cron.log 2>&1

EOF
    
    # 安装新的crontab
    crontab "$temp_cron"
    rm "$temp_cron"
    
    log_success "定期维护任务已安装"
    echo
    echo "已设置的定期任务："
    echo "📅 每日 2:00  - 基础清理（Docker清理、日志清理）"
    echo "🧹 每周日 4:00 - 深度清理（镜像清理、配置备份）"
    echo "💓 每小时     - 健康检查（API状态、资源监控）"
    echo
    echo "查看cron任务: crontab -l"
    echo "查看执行日志: tail -f $LOG_DIR/cron.log"
}

# 卸载cron任务
uninstall_cron_jobs() {
    log_info "卸载定期维护任务..."
    
    # 备份现有crontab
    crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
    
    # 移除我们的维护任务
    crontab -l 2>/dev/null | grep -v "maintenance-cron.sh" | crontab -
    
    log_success "定期维护任务已卸载"
}

# 显示当前状态
show_status() {
    echo "=== 维护系统状态 ==="
    echo
    echo "📁 项目目录: $PROJECT_DIR"
    echo "📝 日志目录: $LOG_DIR"
    echo "💾 备份目录: $BACKUP_DIR"
    echo
    
    echo "📅 当前Cron任务:"
    crontab -l 2>/dev/null | grep -E "(maintenance-cron|#.*maintenance)" || echo "  未设置维护任务"
    echo
    
    echo "📊 磁盘使用情况:"
    df -h / | tail -1
    echo
    
    echo "🧠 内存使用情况:"
    free -h | head -2
    echo
    
    echo "🐳 Docker资源使用:"
    docker system df 2>/dev/null || echo "  Docker未运行"
    echo
    
    echo "📜 最近日志文件:"
    if [ -d "$LOG_DIR" ]; then
        ls -la "$LOG_DIR" | tail -5
    else
        echo "  无日志文件"
    fi
    echo
}

# 显示帮助信息
show_help() {
    echo "定期维护和清理任务管理工具"
    echo
    echo "用法: $0 [命令]"
    echo
    echo "命令:"
    echo "  daily        执行每日清理任务"
    echo "  weekly       执行每周深度清理"
    echo "  health       执行健康检查"
    echo "  install      安装定期任务到crontab"
    echo "  uninstall    从crontab卸载定期任务"
    echo "  status       显示维护系统状态"
    echo "  help         显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 install       # 设置自动维护"
    echo "  $0 daily         # 手动执行日常清理"
    echo "  $0 status        # 查看系统状态"
    echo
    echo "自动任务时间表:"
    echo "  每日 2:00   - 基础清理"
    echo "  每周日 4:00 - 深度清理"
    echo "  每小时      - 健康检查"
    echo
}

# 主函数
main() {
    case "${1:-}" in
        "daily")
            setup_directories
            daily_cleanup
            ;;
        "weekly")
            setup_directories
            weekly_cleanup
            ;;
        "health")
            setup_directories
            health_check
            ;;
        "install")
            setup_directories
            install_cron_jobs
            ;;
        "uninstall")
            uninstall_cron_jobs
            ;;
        "status")
            show_status
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        "")
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"