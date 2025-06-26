#!/bin/bash
# 在云端服务器上执行的更新脚本

set -e

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

echo "=== 开始云端部署更新 ==="

# 检查当前目录
if [ ! -f "main_refactored.py" ]; then
    log_error "请在项目根目录中运行此脚本"
    exit 1
fi

# 备份当前状态
log_info "创建部署前备份..."
backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"
cp .env "$backup_dir/" 2>/dev/null || true
cp docker-compose.yml "$backup_dir/" 2>/dev/null || true
log_success "备份已创建: $backup_dir"

# 拉取最新代码
log_info "拉取最新代码..."
git pull origin main

# 显示最新更改
log_info "最新更改内容："
git log --oneline -3

# 检查重要文件
if [ ! -f "unified_index.html" ]; then
    log_error "关键文件 unified_index.html 丢失"
    exit 1
fi

# 重新构建和部署
log_info "重新构建Docker镜像..."
docker compose build --no-cache

log_info "重启应用服务..."
docker compose down
docker compose up -d

# 等待服务启动
log_info "等待服务启动（30秒）..."
sleep 30

# 验证部署
log_info "验证部署状态..."

# 检查容器状态
if docker compose ps | grep -q "Up"; then
    log_success "容器运行正常"
else
    log_error "容器启动失败"
    docker compose logs
    exit 1
fi

# 检查API响应
if curl -f -s http://localhost:8000/health > /dev/null; then
    log_success "API健康检查通过"
else
    log_warning "API健康检查失败"
fi

# 检查支持的模型
if curl -f -s http://localhost:8000/supported_models > /dev/null; then
    log_success "模型接口正常"
else
    log_warning "模型接口异常"
fi

echo
log_success "🎉 部署更新完成！"
echo
echo "=== 访问信息 ==="
echo "🌐 应用地址: http://198.23.164.200:8000"
echo "🌙 新功能: 夜间模式已启用"
echo
echo "=== 验证步骤 ==="
echo "1. 访问应用检查基本功能"
echo "2. 测试夜间模式切换（右上角按钮或设置面板）"
echo "3. 确认所有现有功能正常"
echo
echo "=== 管理命令 ==="
echo "📊 查看状态: docker compose ps"
echo "📜 查看日志: docker compose logs -f flashcard-app"
echo "🔄 重启应用: docker compose restart flashcard-app"
echo

# 运行部署检查脚本（如果存在）
if [ -f "deployment-check.py" ]; then
    log_info "运行部署验证..."
    python3 deployment-check.py http://localhost:8000 || log_warning "部署验证有警告，请手动检查"
fi

