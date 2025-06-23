#!/bin/bash
# AI Flashcard Generator - 传统部署管理脚本
# 用于管理现有的systemd服务部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 发现现有部署
discover_deployment() {
    log_info "正在排查现有部署..."
    
    echo "=== 服务状态检查 ==="
    
    # 检查AI flashcard相关服务
    if systemctl list-units --type=service | grep -i flashcard; then
        log_success "发现flashcard相关服务:"
        systemctl list-units --type=service | grep -i flashcard
    else
        log_warning "未发现flashcard相关服务"
    fi
    
    echo ""
    echo "=== Gunicorn进程检查 ==="
    
    # 检查Gunicorn进程
    if pgrep -f gunicorn > /dev/null; then
        log_success "发现Gunicorn进程:"
        ps aux | grep gunicorn | grep -v grep
    else
        log_warning "未发现Gunicorn进程"
    fi
    
    echo ""
    echo "=== Nginx状态检查 ==="
    
    # 检查Nginx状态
    if systemctl is-active nginx > /dev/null 2>&1; then
        log_success "Nginx服务运行中"
        systemctl status nginx --no-pager -l
    else
        log_warning "Nginx服务未运行"
    fi
    
    echo ""
    echo "=== 端口占用检查 ==="
    
    # 检查常用端口
    log_info "检查端口占用情况:"
    netstat -tlnp | grep -E ':80|:443|:8000|:8080|:5000' || echo "未发现相关端口占用"
    
    echo ""
    echo "=== 日志文件检查 ==="
    
    # 检查日志文件
    log_info "查找日志文件:"
    find /var/log -name "*flashcard*" -o -name "*gunicorn*" 2>/dev/null || echo "未发现相关日志文件"
    
    echo ""
    echo "=== 配置文件查找 ==="
    
    # 查找配置文件
    log_info "查找配置文件:"
    find /etc -name "*flashcard*" 2>/dev/null || echo "未发现/etc下的配置文件"
    find /etc/systemd/system -name "*flashcard*" 2>/dev/null || echo "未发现systemd服务文件"
    find /etc/nginx -name "*flashcard*" 2>/dev/null || echo "未发现nginx配置文件"
    
    echo ""
    echo "=== 应用目录查找 ==="
    
    # 查找应用目录
    log_info "查找应用目录:"
    find /home -maxdepth 3 -name "*flashcard*" -type d 2>/dev/null || echo "未发现home目录下的应用"
    find /opt -maxdepth 2 -name "*flashcard*" -type d 2>/dev/null || echo "未发现opt目录下的应用"
    find /var/www -maxdepth 2 -name "*flashcard*" -type d 2>/dev/null || echo "未发现www目录下的应用"
}

# 显示当前状态
show_status() {
    log_info "显示当前服务状态..."
    
    echo "=== AI Flashcard 服务状态 ==="
    
    # 检查ai_flashcard服务
    if systemctl list-units --full -t service --no-page | grep -q ai_flashcard; then
        echo "🔍 ai_flashcard 服务状态:"
        sudo systemctl status ai_flashcard --no-pager -l
    else
        log_warning "ai_flashcard 服务未找到"
    fi
    
    echo ""
    echo "=== Nginx 状态 ==="
    sudo systemctl status nginx --no-pager -l
    
    echo ""
    echo "=== 最近的错误日志 ==="
    if [ -f /var/log/gunicorn/ai_flashcard-error.log ]; then
        echo "🔍 Gunicorn 错误日志 (最后10行):"
        sudo tail -10 /var/log/gunicorn/ai_flashcard-error.log
    else
        log_warning "Gunicorn错误日志文件不存在"
    fi
    
    echo ""
    echo "=== 端口监听状态 ==="
    netstat -tlnp | grep -E ':80|:443|:8000|:8080|:5000'
}

# 启动服务
start_services() {
    log_info "启动AI Flashcard服务..."
    
    # 启动ai_flashcard服务
    if systemctl list-units --full -t service --no-page | grep -q ai_flashcard; then
        log_info "启动 ai_flashcard 服务..."
        sudo systemctl start ai_flashcard
        
        # 等待服务启动
        sleep 5
        
        if sudo systemctl is-active ai_flashcard > /dev/null; then
            log_success "ai_flashcard 服务启动成功"
        else
            log_error "ai_flashcard 服务启动失败"
            sudo systemctl status ai_flashcard --no-pager -l
        fi
    else
        log_error "未找到 ai_flashcard 服务"
    fi
    
    # 启动nginx
    log_info "启动 Nginx 服务..."
    sudo systemctl start nginx
    
    if sudo systemctl is-active nginx > /dev/null; then
        log_success "Nginx 服务启动成功"
    else
        log_error "Nginx 服务启动失败"
        sudo systemctl status nginx --no-pager -l
    fi
}

# 停止服务
stop_services() {
    log_info "停止AI Flashcard服务..."
    
    # 停止ai_flashcard服务
    if systemctl list-units --full -t service --no-page | grep -q ai_flashcard; then
        log_info "停止 ai_flashcard 服务..."
        sudo systemctl stop ai_flashcard
        log_success "ai_flashcard 服务已停止"
    else
        log_warning "ai_flashcard 服务未运行"
    fi
    
    # 询问是否停止nginx
    read -p "是否也停止 Nginx 服务? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl stop nginx
        log_success "Nginx 服务已停止"
    fi
}

# 重启服务
restart_services() {
    log_info "重启AI Flashcard服务..."
    
    # 重启ai_flashcard服务
    if systemctl list-units --full -t service --no-page | grep -q ai_flashcard; then
        log_info "重启 ai_flashcard 服务..."
        sudo systemctl restart ai_flashcard
        
        # 等待服务重启
        sleep 5
        
        if sudo systemctl is-active ai_flashcard > /dev/null; then
            log_success "ai_flashcard 服务重启成功"
        else
            log_error "ai_flashcard 服务重启失败"
            sudo systemctl status ai_flashcard --no-pager -l
        fi
    else
        log_error "未找到 ai_flashcard 服务"
    fi
    
    # 重启nginx
    log_info "重启 Nginx 服务..."
    
    # 先检查配置
    if sudo nginx -t; then
        sudo systemctl restart nginx
        log_success "Nginx 服务重启成功"
    else
        log_error "Nginx 配置有误，无法重启"
    fi
}

# 查看日志
view_logs() {
    echo "=== 可用的日志文件 ==="
    
    # 列出所有相关日志
    log_files=(
        "/var/log/gunicorn/ai_flashcard-error.log"
        "/var/log/gunicorn/ai_flashcard-access.log"
        "/var/log/nginx/error.log"
        "/var/log/nginx/access.log"
        "/var/log/syslog"
    )
    
    existing_logs=()
    for log_file in "${log_files[@]}"; do
        if [ -f "$log_file" ]; then
            existing_logs+=("$log_file")
            echo "✅ $log_file"
        else
            echo "❌ $log_file (不存在)"
        fi
    done
    
    if [ ${#existing_logs[@]} -eq 0 ]; then
        log_error "未找到任何日志文件"
        return
    fi
    
    echo ""
    echo "选择要查看的日志文件:"
    for i in "${!existing_logs[@]}"; do
        echo "$((i+1)). ${existing_logs[$i]}"
    done
    echo "$((${#existing_logs[@]}+1)). 实时查看所有错误日志"
    echo "$((${#existing_logs[@]}+2)). 返回主菜单"
    
    read -p "请选择 (1-$((${#existing_logs[@]}+2))): " choice
    
    if [ "$choice" -eq "$((${#existing_logs[@]}+1))" ]; then
        log_info "实时查看错误日志 (按Ctrl+C退出)..."
        sudo tail -f /var/log/gunicorn/ai_flashcard-error.log /var/log/nginx/error.log 2>/dev/null
    elif [ "$choice" -eq "$((${#existing_logs[@]}+2))" ]; then
        return
    elif [ "$choice" -ge 1 ] && [ "$choice" -le "${#existing_logs[@]}" ]; then
        selected_log="${existing_logs[$((choice-1))]}"
        log_info "查看 $selected_log (最后50行)..."
        sudo tail -50 "$selected_log"
        echo ""
        read -p "是否实时查看此日志? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "实时查看 $selected_log (按Ctrl+C退出)..."
            sudo tail -f "$selected_log"
        fi
    else
        log_error "无效选择"
    fi
}

# 检查配置
check_config() {
    log_info "检查配置文件..."
    
    echo "=== Nginx 配置检查 ==="
    if sudo nginx -t; then
        log_success "Nginx 配置正确"
    else
        log_error "Nginx 配置有误"
    fi
    
    echo ""
    echo "=== Systemd 服务配置 ==="
    if systemctl list-units --full -t service --no-page | grep -q ai_flashcard; then
        log_info "ai_flashcard 服务配置:"
        sudo systemctl cat ai_flashcard
    else
        log_warning "未找到 ai_flashcard 服务配置"
    fi
    
    echo ""
    echo "=== 进程检查 ==="
    if pgrep -f gunicorn > /dev/null; then
        log_info "Gunicorn 进程:"
        ps aux | grep gunicorn | grep -v grep
    else
        log_warning "未发现 Gunicorn 进程"
    fi
}

# 应用测试
test_application() {
    log_info "测试应用访问..."
    
    # 获取服务器IP
    SERVER_IP=$(curl -s ifconfig.me || echo "localhost")
    
    echo "=== 本地测试 ==="
    
    # 测试本地端口
    local_ports=(8000 8080 5000)
    for port in "${local_ports[@]}"; do
        if curl -s --connect-timeout 5 "http://localhost:$port" > /dev/null; then
            log_success "端口 $port 响应正常"
            echo "  测试URL: http://localhost:$port"
        else
            log_warning "端口 $port 无响应"
        fi
    done
    
    echo ""
    echo "=== 外部访问测试 ==="
    
    # 测试HTTP
    if curl -s --connect-timeout 5 "http://$SERVER_IP" > /dev/null; then
        log_success "HTTP访问正常"
        echo "  访问地址: http://$SERVER_IP"
    else
        log_warning "HTTP访问失败"
    fi
    
    # 测试HTTPS
    if curl -s --connect-timeout 5 "https://$SERVER_IP" > /dev/null; then
        log_success "HTTPS访问正常"
        echo "  访问地址: https://$SERVER_IP"
    else
        log_warning "HTTPS访问失败"
    fi
    
    echo ""
    echo "=== API端点测试 ==="
    
    # 常见API端点
    api_endpoints=(
        "/api/health"
        "/health"
        "/status"
        "/api/models"
        "/supported_models"
    )
    
    for endpoint in "${api_endpoints[@]}"; do
        if curl -s --connect-timeout 5 "http://localhost:8000$endpoint" > /dev/null; then
            log_success "API端点 $endpoint 响应正常"
        elif curl -s --connect-timeout 5 "http://localhost:5000$endpoint" > /dev/null; then
            log_success "API端点 $endpoint 在端口5000响应正常"
        else
            log_warning "API端点 $endpoint 无响应"
        fi
    done
}

# 创建备份
create_backup() {
    log_info "创建当前部署备份..."
    
    BACKUP_DIR="$HOME/legacy-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份systemd服务文件
    if [ -f /etc/systemd/system/ai_flashcard.service ]; then
        sudo cp /etc/systemd/system/ai_flashcard.service "$BACKUP_DIR/"
        log_success "备份systemd服务文件"
    fi
    
    # 备份nginx配置
    if [ -d /etc/nginx/sites-available ]; then
        sudo cp -r /etc/nginx/sites-available "$BACKUP_DIR/nginx-sites-available"
        log_success "备份nginx配置"
    fi
    
    # 备份日志
    if [ -d /var/log/gunicorn ]; then
        sudo cp -r /var/log/gunicorn "$BACKUP_DIR/"
        log_success "备份gunicorn日志"
    fi
    
    # 查找并备份应用代码
    app_dirs=(
        "/home/*/flashcard*"
        "/opt/flashcard*"
        "/var/www/flashcard*"
    )
    
    for pattern in "${app_dirs[@]}"; do
        for dir in $pattern; do
            if [ -d "$dir" ]; then
                cp -r "$dir" "$BACKUP_DIR/"
                log_success "备份应用目录: $dir"
            fi
        done
    done
    
    # 设置权限
    sudo chown -R $USER:$USER "$BACKUP_DIR"
    
    log_success "备份完成: $BACKUP_DIR"
    
    # 创建备份说明
    cat > "$BACKUP_DIR/README.md" << EOF
# 传统部署备份

备份时间: $(date)
备份内容:
- systemd服务文件
- nginx配置文件
- gunicorn日志
- 应用代码目录

## 恢复指令:
sudo cp ai_flashcard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai_flashcard
sudo cp -r nginx-sites-available/* /etc/nginx/sites-available/
sudo nginx -t && sudo systemctl reload nginx
EOF
    
    echo "备份说明文件已创建: $BACKUP_DIR/README.md"
}

# 主菜单
show_menu() {
    clear
    echo "=== AI Flashcard Generator - 传统部署管理工具 ==="
    echo ""
    echo "1. 🔍 发现现有部署"
    echo "2. 📊 显示服务状态"
    echo "3. ▶️  启动所有服务"
    echo "4. ⏹️  停止所有服务"
    echo "5. 🔄 重启所有服务"
    echo "6. 📝 查看日志"
    echo "7. ⚙️  检查配置"
    echo "8. 🧪 测试应用访问"
    echo "9. 💾 创建备份"
    echo "10. ❌ 退出"
    echo ""
}

# 主函数
main() {
    while true; do
        show_menu
        read -p "请选择操作 (1-10): " choice
        
        case $choice in
            1)
                discover_deployment
                read -p "按Enter继续..."
                ;;
            2)
                show_status
                read -p "按Enter继续..."
                ;;
            3)
                start_services
                read -p "按Enter继续..."
                ;;
            4)
                stop_services
                read -p "按Enter继续..."
                ;;
            5)
                restart_services
                read -p "按Enter继续..."
                ;;
            6)
                view_logs
                ;;
            7)
                check_config
                read -p "按Enter继续..."
                ;;
            8)
                test_application
                read -p "按Enter继续..."
                ;;
            9)
                create_backup
                read -p "按Enter继续..."
                ;;
            10)
                log_info "退出管理工具"
                exit 0
                ;;
            *)
                log_error "无效选择，请输入1-10"
                sleep 2
                ;;
        esac
    done
}

# 检查是否有sudo权限
if ! sudo -n true 2>/dev/null; then
    log_warning "此脚本需要sudo权限来管理系统服务"
    echo "请确保您可以使用sudo命令"
fi

# 运行主程序
main "$@"