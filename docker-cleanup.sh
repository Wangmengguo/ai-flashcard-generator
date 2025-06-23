#!/bin/bash
# Docker 资源清理维护脚本
# 用于释放Docker占用的磁盘空间和内存

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

# 显示Docker资源使用情况
show_docker_usage() {
    echo "=== Docker 资源使用情况 ==="
    docker system df
    echo
    
    echo "=== 详细资源分析 ==="
    docker system df -v | head -20
    echo
}

# 基础清理 - 安全的清理操作
basic_cleanup() {
    log_info "执行基础清理..."
    
    # 清理停止的容器
    log_info "清理停止的容器..."
    STOPPED_CONTAINERS=$(docker container ls -aq --filter "status=exited")
    if [ -n "$STOPPED_CONTAINERS" ]; then
        docker container rm $STOPPED_CONTAINERS
        log_success "已清理停止的容器"
    else
        log_info "没有停止的容器需要清理"
    fi
    
    # 清理悬空镜像
    log_info "清理悬空镜像..."
    DANGLING_IMAGES=$(docker images -f "dangling=true" -q)
    if [ -n "$DANGLING_IMAGES" ]; then
        docker rmi $DANGLING_IMAGES
        log_success "已清理悬空镜像"
    else
        log_info "没有悬空镜像需要清理"
    fi
    
    # 清理未使用的网络
    log_info "清理未使用的网络..."
    docker network prune -f
    
    log_success "基础清理完成"
}

# 深度清理 - 包括未使用的镜像
deep_cleanup() {
    log_info "执行深度清理..."
    
    # 先执行基础清理
    basic_cleanup
    
    # 清理未使用的镜像
    log_warning "清理所有未使用的镜像（这将删除所有不被容器使用的镜像）"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker image prune -a -f
        log_success "已清理未使用的镜像"
    else
        log_info "跳过镜像清理"
    fi
    
    # 清理未使用的数据卷
    log_info "清理未使用的数据卷..."
    docker volume prune -f
    
    log_success "深度清理完成"
}

# 构建缓存清理
cache_cleanup() {
    log_info "清理构建缓存..."
    
    echo "构建缓存使用情况："
    docker system df | grep "Build Cache" || echo "没有构建缓存数据"
    echo
    
    # 清理旧的构建缓存（保留最近24小时的）
    log_info "清理24小时前的构建缓存..."
    docker builder prune -f --filter until=24h
    
    # 选择性清理所有构建缓存
    log_warning "是否清理所有构建缓存？（会影响下次构建速度）"
    read -p "(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker builder prune -a -f
        log_success "所有构建缓存已清理"
    else
        log_info "保留构建缓存"
    fi
    
    log_success "缓存清理完成"
}

# 一键清理所有资源
nuclear_cleanup() {
    log_error "⚠️  核心清理模式 - 将清理所有Docker资源"
    log_warning "这将删除："
    echo "  - 所有停止的容器"
    echo "  - 所有未使用的镜像"
    echo "  - 所有未使用的网络"
    echo "  - 所有未使用的数据卷"
    echo "  - 所有构建缓存"
    echo
    log_error "请确保没有重要数据存储在Docker中！"
    
    read -p "确定要继续吗？输入 'YES' 确认: " -r
    if [[ $REPLY == "YES" ]]; then
        log_info "执行核心清理..."
        docker system prune -a -f --volumes
        log_success "核心清理完成"
    else
        log_info "取消核心清理"
        exit 0
    fi
}

# 显示帮助信息
show_help() {
    echo "Docker 资源清理工具"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  basic     基础清理（停止的容器、悬空镜像、未使用的网络）"
    echo "  deep      深度清理（包括未使用的镜像和数据卷）"
    echo "  cache     清理构建缓存"
    echo "  nuclear   核心清理（删除所有Docker资源）⚠️"
    echo "  status    显示Docker资源使用情况"
    echo "  help      显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 basic          # 日常维护清理"
    echo "  $0 deep           # 深度清理释放更多空间"
    echo "  $0 status         # 查看资源使用"
    echo
}

# 生成清理报告
generate_cleanup_report() {
    local before_file="/tmp/docker_before_cleanup"
    local after_file="/tmp/docker_after_cleanup"
    
    # 保存清理前状态
    docker system df > "$before_file" 2>/dev/null || true
    
    # 执行清理操作
    case "${1:-basic}" in
        "basic")
            basic_cleanup
            ;;
        "deep")
            deep_cleanup
            ;;
        "cache")
            cache_cleanup
            ;;
        *)
            basic_cleanup
            ;;
    esac
    
    # 保存清理后状态
    docker system df > "$after_file" 2>/dev/null || true
    
    # 显示对比报告
    echo
    echo "=== 清理报告 ==="
    echo "清理前："
    cat "$before_file" 2>/dev/null || echo "无法获取清理前状态"
    echo
    echo "清理后："
    cat "$after_file" 2>/dev/null || echo "无法获取清理后状态"
    echo
    
    # 清理临时文件
    rm -f "$before_file" "$after_file"
}

# 主函数
main() {
    echo "=== Docker 资源清理工具 ==="
    echo "当前时间: $(date)"
    echo
    
    # 检查Docker是否运行
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker未运行或无访问权限"
        exit 1
    fi
    
    # 显示当前资源使用
    show_docker_usage
    
    case "${1:-}" in
        "basic")
            generate_cleanup_report "basic"
            ;;
        "deep")
            generate_cleanup_report "deep"
            ;;
        "cache")
            cache_cleanup
            ;;
        "nuclear")
            nuclear_cleanup
            ;;
        "status")
            show_docker_usage
            exit 0
            ;;
        "help"|"-h"|"--help")
            show_help
            exit 0
            ;;
        "")
            log_info "使用基础清理模式（默认）"
            generate_cleanup_report "basic"
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
    
    echo
    log_success "清理操作完成！"
    echo
    echo "=== 建议 ==="
    echo "🔄 定期运行: $0 basic"
    echo "🧹 深度清理: $0 deep (每周)"
    echo "📊 监控状态: $0 status"
    echo
}

# 执行主函数
main "$@"