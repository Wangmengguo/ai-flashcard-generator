#!/bin/bash
"""
Docker容器健康检查脚本
用于Docker容器内部的健康检查
"""

set -e

# 配置
HEALTH_CHECK_URL="http://localhost:8000/supported_models"
TIMEOUT=10
MAX_RETRIES=3

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查基础依赖
check_dependencies() {
    if ! command -v curl &> /dev/null; then
        log_error "curl command not found"
        return 1
    fi
    return 0
}

# 检查端口是否监听
check_port() {
    local port=${1:-8000}
    if netstat -tuln 2>/dev/null | grep -q ":${port} "; then
        log_info "Port ${port} is listening"
        return 0
    else
        log_error "Port ${port} is not listening"
        return 1
    fi
}

# 检查进程是否运行
check_process() {
    if pgrep -f "uvicorn\|gunicorn" > /dev/null; then
        log_info "Application process is running"
        return 0
    else
        log_error "Application process not found"
        return 1
    fi
}

# 检查HTTP响应
check_http_response() {
    local url=$1
    local expected_status=${2:-200}
    
    for i in $(seq 1 $MAX_RETRIES); do
        log_info "Attempting HTTP check ($i/$MAX_RETRIES): $url"
        
        if curl -f -s --max-time $TIMEOUT "$url" > /dev/null; then
            log_info "HTTP check passed"
            return 0
        else
            log_warn "HTTP check failed (attempt $i/$MAX_RETRIES)"
            if [ $i -lt $MAX_RETRIES ]; then
                sleep 2
            fi
        fi
    done
    
    log_error "HTTP check failed after $MAX_RETRIES attempts"
    return 1
}

# 检查应用特定的健康状态
check_app_health() {
    # 检查支持的模型接口 (这个接口不需要API密钥)
    if curl -f -s --max-time $TIMEOUT "$HEALTH_CHECK_URL" | grep -q "google/gemini"; then
        log_info "Application health check passed"
        return 0
    else
        log_error "Application health check failed"
        return 1
    fi
}

# 检查内存使用
check_memory() {
    local memory_limit_mb=${MEMORY_LIMIT_MB:-2048}  # 默认2GB限制
    
    if command -v free &> /dev/null; then
        local memory_used_mb=$(free -m | awk 'NR==2{printf "%.0f", $3}')
        local memory_percent=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
        
        log_info "Memory usage: ${memory_used_mb}MB (${memory_percent}%)"
        
        if [ "$memory_percent" -gt 90 ]; then
            log_warn "High memory usage: ${memory_percent}%"
        fi
    else
        log_warn "Cannot check memory usage - 'free' command not available"
    fi
}

# 检查磁盘空间
check_disk_space() {
    local min_free_mb=${MIN_FREE_SPACE_MB:-1024}  # 默认最少1GB空闲空间
    
    if command -v df &> /dev/null; then
        local free_space_mb=$(df /app 2>/dev/null | awk 'NR==2 {print int($4/1024)}' || echo "0")
        
        log_info "Free disk space: ${free_space_mb}MB"
        
        if [ "$free_space_mb" -lt "$min_free_mb" ]; then
            log_warn "Low disk space: ${free_space_mb}MB (minimum: ${min_free_mb}MB)"
        fi
    else
        log_warn "Cannot check disk space - 'df' command not available"
    fi
}

# 主健康检查函数
main_health_check() {
    local exit_code=0
    
    log_info "Starting container health check..."
    
    # 基础检查
    if ! check_dependencies; then
        exit_code=1
    fi
    
    if ! check_process; then
        exit_code=1
    fi
    
    if ! check_port 8000; then
        exit_code=1
    fi
    
    # HTTP检查
    if ! check_http_response "http://localhost:8000/"; then
        exit_code=1
    fi
    
    # 应用健康检查
    if ! check_app_health; then
        exit_code=1
    fi
    
    # 资源检查 (警告不影响退出码)
    check_memory
    check_disk_space
    
    # 总结
    if [ $exit_code -eq 0 ]; then
        log_info "All health checks passed ✅"
    else
        log_error "Some health checks failed ❌"
    fi
    
    return $exit_code
}

# 快速检查模式 (仅检查HTTP响应)
quick_check() {
    if curl -f -s --max-time 5 "$HEALTH_CHECK_URL" > /dev/null; then
        echo "healthy"
        return 0
    else
        echo "unhealthy"
        return 1
    fi
}

# 命令行参数处理
case "${1:-full}" in
    "quick"|"fast")
        quick_check
        ;;
    "full"|"")
        main_health_check
        ;;
    *)
        echo "Usage: $0 [quick|full]"
        echo "  quick: Fast HTTP-only check"
        echo "  full:  Complete health check (default)"
        exit 1
        ;;
esac