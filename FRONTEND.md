# AI Flashcard Generator - 前端文件使用指南

本指南详细说明项目中各个前端文件的用途、配置和使用方法。

## 📁 文件概览

| 文件名 | 用途 | 推荐场景 | API端口 |
|--------|------|----------|---------|
| `unified_index.html` | 🚀 生产级主界面 | 生产部署、完整功能体验 | 自动检测 |
| `index.html` | ☁️ 云端部署版本 | 云服务器、CDN分发 | 相对路径 |
| `local_index.html` | 🔧 本地开发版本 | 开发调试、快速验证 | :8000 |
| `frontend/tools/quality_assessment_tool.html` | 📊 质量评估工具 | 质量测试、性能评估 | 独立工具 |
| `frontend/tools/quality_test_guide.html` | 📋 测试指导文档 | 测试培训、质量保证 | 指导文档 |

## 🚀 unified_index.html - 生产级主界面

### 特点
- **最全面的功能集**：包含所有高级特性
- **智能环境检测**：自动识别本地/云端/文件访问环境
- **响应式设计**：支持桌面和移动设备
- **专业UI设计**：现代化界面，用户体验优秀

### 核心功能
- ✅ 多模板系统（Academic/Exam/Language/Technical/General/Custom）
- ✅ 智能参数配置（卡片数量滑块、自定义Prompt）
- ✅ 批量文本处理
- ✅ 历史记录管理
- ✅ 多格式导出（Anki Markdown/Tab/CSV/JSON）
- ✅ 实时API状态检测

### API配置
```javascript
// 自动环境检测逻辑
if (location.protocol === 'file:') {
    window.API_BASE_URL = 'http://127.0.0.1:8000';  // 文件访问
} else if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
    window.API_BASE_URL = '';  // 本地HTTP服务
} else {
    window.API_BASE_URL = '';  // 生产环境
}
```

### 使用场景
1. **生产环境部署** - 直接部署到服务器根目录
2. **本地完整测试** - 开发环境完整功能验证
3. **演示展示** - 客户演示或产品展示

### 启动方法
```bash
# 方法1：本地API + 文件访问
uvicorn main:app --reload --port 8000
# 然后直接双击打开unified_index.html

# 方法2：完整HTTP服务
uvicorn main:app --reload --port 8000
python -m http.server 3000
# 访问 http://localhost:3000/unified_index.html

# 方法3：生产部署
# 将文件上传到服务器根目录，通过域名访问
```

## ☁️ index.html - 云端部署版本

### 特点
- **云端优化**：为云服务器环境特别优化
- **相对路径配置**：使用`<base href="/flashcard/">`
- **轻量级设计**：功能精简，加载快速

### 功能特性
- ✅ AI模型选择
- ✅ 智能闪卡生成
- ✅ 多格式导出（Anki Markdown/Tab/CSV/JSON）
- ✅ 卡片删除编辑
- ✅ API密钥本地存储

### API配置
```html
<base href="/flashcard/">
```
所有API请求使用相对路径，依赖base标签设定的基础路径。

### 使用场景
1. **云服务器部署** - 部署在/flashcard/路径下
2. **网站集成** - 作为网站的子模块
3. **CDN分发** - 通过CDN提供服务

### 部署方法
```bash
# 云端部署
mkdir /var/www/html/flashcard
cp index.html /var/www/html/flashcard/
# 确保API服务在正确路径运行

# 本地测试（需要HTTP服务器）
python -m http.server 8080
# 访问 http://localhost:8080/flashcard/index.html
```

## 🔧 local_index.html - 本地开发版本

### 特点
- **开发专用**：针对本地开发环境优化
- **固定端口**：直接连接到localhost:8000
- **简化调试**：减少环境配置复杂性

### 功能特性
- ✅ AI模型选择
- ✅ 闪卡生成与编辑
- ✅ 卡片删除功能
- ✅ Anki格式复制
- ✅ 输入验证

### API配置
```javascript
const response = await fetch('http://127.0.0.1:8000/generate_flashcards/', {
    // 固定使用8000端口
});
```

### 使用场景
1. **快速开发调试**
2. **功能验证测试**
3. **API接口测试**

### 启动方法
```bash
# 启动本地API服务
uvicorn main:app --reload --port 8000

# 直接打开文件
open local_index.html
# 或双击文件打开
```

## 📊 质量评估工具

### quality_assessment_tool.html

专门用于系统性评估闪卡生成质量的工具。

#### 功能特性
- ✅ 5维度质量评分（准确性/相关性/清晰性/完整性/实用性）
- ✅ 模板对比分析
- ✅ 测试结果统计
- ✅ 详细问题记录
- ✅ 改进建议跟踪
- ✅ 数据本地存储
- ✅ 报告导出功能

#### 评分标准
- **1分** - 非常差，不可用
- **2分** - 较差，需要重大改进
- **3分** - 一般，基本可用
- **4分** - 较好，符合预期
- **5分** - 非常好，超出预期

#### 使用流程
1. 选择测试模板（Academic/Exam/Language/Technical/General）
2. 在主界面生成闪卡
3. 返回此工具记录评估结果
4. 重复测试所有模板
5. 查看统计报告

### quality_test_guide.html

提供完整的质量测试指导和最佳实践。

#### 内容包含
- ✅ 5种模板测试样本
- ✅ 系统性测试流程
- ✅ 质量评估标准
- ✅ 详细评分表格
- ✅ 最佳实践指导
- ✅ 问题记录模板

## 🔧 API端口配置

### 统一端口配置
为确保一致性，所有文件现在使用**8000端口**作为标准：

```bash
# 标准启动命令
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 端口修改指南
如需修改API端口，需要同步更新以下位置：

1. **unified_index.html**
```javascript
window.API_BASE_URL = 'http://127.0.0.1:8000';  // 修改端口号
```

2. **local_index.html**
```javascript
const response = await fetch('http://127.0.0.1:8000/...');  // 修改端口号
```

3. **index.html**
```javascript
const response = await fetch('http://127.0.0.1:8000/...');  // 修改端口号
```

## 📱 响应式设计

### 支持设备
- **桌面端**：1200px+（完整功能）
- **平板端**：768px-1199px（适配布局）
- **手机端**：<768px（移动优化）

### 最佳浏览器
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## 🛠️ 本地开发建议

### 开发环境设置
```bash
# 1. 启动后端API
uvicorn main:app --reload --port 8000

# 2. 启动前端服务（可选）
python -m http.server 3000

# 3. 选择合适的前端文件
# - 功能测试：unified_index.html
# - 快速调试：local_index.html
# - 云端测试：index.html
```

### 调试技巧
1. **开发者工具**：F12查看网络请求和控制台错误
2. **API测试**：先访问 http://127.0.0.1:8000/docs 验证API
3. **跨域问题**：确保CORS配置正确
4. **缓存清理**：Ctrl+F5强制刷新

## 🚀 生产部署建议

### 云端部署
```bash
# 方案1：Nginx + uWSGI
# 将HTML文件放在/var/www/html/
# API服务运行在后端

# 方案2：Docker容器化
# 使用提供的Dockerfile和docker-compose.yml

# 方案3：CDN + API Gateway
# 静态文件通过CDN分发
# API通过Gateway路由
```

### 性能优化
- **文件压缩**：启用gzip压缩
- **缓存策略**：设置合理的缓存时间
- **CDN加速**：静态资源CDN分发
- **监控告警**：设置性能监控

## 📋 功能对比表

| 功能特性 | unified_index.html | index.html | local_index.html |
|----------|-------------------|------------|------------------|
| 多模板系统 | ✅ | ❌ | ❌ |
| 批量处理 | ✅ | ❌ | ❌ |
| 历史记录 | ✅ | ❌ | ❌ |
| 自定义Prompt | ✅ | ❌ | ❌ |
| 环境自动检测 | ✅ | ❌ | ❌ |
| 响应式设计 | ✅ | ✅ | ✅ |
| 多格式导出 | ✅ | ✅ | ❌ |
| 卡片删除 | ✅ | ✅ | ✅ |
| API密钥存储 | ✅ | ✅ | ✅ |

## 🔍 故障排除

### 常见问题

1. **API连接失败**
   - 检查API服务是否启动
   - 验证端口配置是否正确
   - 确认防火墙设置

2. **跨域错误**
   - 检查CORS配置
   - 使用HTTP服务器而非file://协议

3. **功能异常**
   - 清除浏览器缓存
   - 检查JavaScript控制台错误
   - 验证API密钥有效性

4. **样式显示问题**
   - 确认CSS文件加载正常
   - 检查浏览器兼容性
   - 验证响应式断点

### 支持渠道
- 📧 技术支持：查看项目README.md
- 🐛 问题报告：GitHub Issues
- 📚 文档查阅：项目文档目录

---

**更新日期**：2025-06-21  
**版本**：v1.0.0  
**维护者**：AI Flashcard Generator Team