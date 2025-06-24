#!/bin/bash
# AI Flashcard Generator - 云端部署更新脚本
# 用于将最新的代码更改（包括夜间模式）部署到云端服务器

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

# 服务器信息
SERVER_IP="198.23.164.200"
PROJECT_DIR="/root/ai-flashcard-generator"
APP_URL="http://198.23.164.200:8000"

echo "=== AI Flashcard Generator - 云端部署更新 ==="
echo "目标服务器: $SERVER_IP"
echo "更新内容: 夜间模式功能 + README更新"
echo

# 检查SSH连接
check_ssh_connection() {
    log_info "检查SSH连接到服务器..."
    
    if ! command -v ssh &> /dev/null; then
        log_error "SSH命令未找到，请安装SSH客户端"
        exit 1
    fi
    
    log_success "SSH检查完成"
}

# 显示更新命令
show_update_commands() {
    echo
    log_info "请在服务器上执行以下命令："
    echo
    echo "# 1. SSH连接到服务器"
    echo "ssh root@$SERVER_IP"
    echo
    echo "# 2. 进入项目目录"
    echo "cd $PROJECT_DIR"
    echo
    echo "# 3. 拉取最新代码"
    echo "git pull origin main"
    echo
    echo "# 4. 查看更新内容"
    echo "git log --oneline -3"
    echo
    echo "# 5. 使用快速部署脚本更新"
    echo "./quick-deploy.sh"
    echo
    echo "# 或者手动更新："
    echo "# docker compose build --no-cache"
    echo "# docker compose down"
    echo "# docker compose up -d"
    echo
    echo "# 6. 验证部署"
    echo "python3 deployment-check.py http://localhost:8000"
    echo
    echo "# 7. 检查容器状态"
    echo "docker compose ps"
    echo "docker compose logs -f flashcard-app"
    echo
}

# 生成远程执行脚本
generate_remote_script() {
    log_info "生成远程执行脚本..."
    
    cat > remote-update.sh << 'EOF'
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

EOF
    
    chmod +x remote-update.sh
    log_success "远程执行脚本已生成: remote-update.sh"
}

# 显示使用SSH密钥的建议
show_ssh_tips() {
    echo
    log_info "SSH连接提示："
    echo "1. 如果使用密钥认证："
    echo "   ssh -i /path/to/private-key root@$SERVER_IP"
    echo
    echo "2. 如果服务器使用非标准端口："
    echo "   ssh -p 2222 root@$SERVER_IP"
    echo
    echo "3. 传输更新脚本到服务器："
    echo "   scp remote-update.sh root@$SERVER_IP:$PROJECT_DIR/"
    echo
    echo "4. 在服务器上执行："
    echo "   cd $PROJECT_DIR && ./remote-update.sh"
    echo
}

# 验证更新是否成功
verify_update() {
    echo
    log_info "更新完成后，请验证以下内容："
    echo
    echo "✅ 应用可正常访问: $APP_URL"
    echo "✅ 夜间模式功能可用（右上角切换按钮）"
    echo "✅ 设置面板中有主题选择选项"
    echo "✅ 主题切换保存到本地存储"
    echo "✅ 所有现有功能正常（卡片生成、导出等）"
    echo
    echo "🌙 夜间模式测试："
    echo "1. 点击右上角圆形按钮，应该循环切换三种主题"
    echo "2. 进入设置面板，应该看到主题选择下拉菜单"
    echo "3. 选择不同主题，界面应该立即切换"
    echo "4. 刷新页面，主题设置应该保持"
    echo
}

# 主函数
main() {
    check_ssh_connection
    generate_remote_script
    show_update_commands
    show_ssh_tips
    verify_update
    
    echo
    log_success "🚀 更新准备完成！"
    echo
    log_warning "请按照上述步骤在服务器上执行更新"
    echo
}

# 执行主函数
main