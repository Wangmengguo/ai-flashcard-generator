# AI Flashcard Generator MVP

## 🎯 项目概述

AI Flashcard Generator 是一个基于 FastAPI 的智能抽认卡生成系统，专注于将任意中文文本转化为高质量的问答卡片，并支持多种格式导出到主流学习软件（如 Anki、CSV 等）。

### 核心特性
- 🤖 **多AI模型支持**：集成 Gemini、Claude、GPT 等 8+ 主流AI模型
- 📝 **智能文本解析**：高质量中文问答对生成，支持复杂格式容错
- 📤 **多格式导出**：支持 Anki Markdown、制表符分隔、CSV、JSON 等格式
- 🎨 **直观用户界面**：简洁现代的 Web 界面，支持实时编辑和删除
- ☁️ **灵活部署**：支持云端部署和本地开发调试

## 🏗️ 项目结构

```
flashcard_generator_mvp/
├── main.py                 # FastAPI 后端主程序
├── index.html             # 云端部署前端页面
├── local_index.html       # 本地调试前端页面
├── requirements.txt       # Python 依赖包
├── flashcard/            # Python 虚拟环境
├── venv/                 # 备用虚拟环境
└── README.md             # 项目说明文档
```

## ⚡ 快速开始

### 环境要求
- Python 3.8+
- OpenRouter API Key

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd flashcard_generator_mvp
   ```

2. **激活虚拟环境**
   ```bash
   # 使用项目内置环境
   source flashcard/bin/activate  # Linux/Mac
   # 或
   flashcard\Scripts\activate     # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **启动服务**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **访问应用**
   - 本地开发：打开 `local_index.html`
   - 云端部署：访问 `http://your-domain/index.html`

## 🔧 使用说明

### 基本流程
1. 输入 OpenRouter API 密钥
2. 选择合适的 AI 模型（推荐 Gemini 2.5 Flash 性价比最高）
3. 粘贴需要生成卡片的中文文本
4. 点击"生成 Flashcards"
5. 选择导出格式并导入到学习软件

### 支持的AI模型
- **Gemini 2.5 Flash**: 极快速度，高性价比（推荐）
- **Claude 3.7 Sonnet**: 最高质量，适合重要内容
- **GPT-4.1 Mini**: 中庸选择
- **Qwen 3 235B**: 适合中文语境
- 等 8 种模型...

### 导出格式说明
- **Anki Markdown**: 包含牌组和标签信息，可直接导入 Anki
- **Anki 制表符**: 简单的问答对格式，兼容性最好
- **CSV**: 可导入 Excel 或其他数据处理工具
- **JSON**: 程序化处理或自定义导入

## 📈 项目优势与特色

### 技术优势
- **容错解析**: 智能识别多种 Q/A 格式变体
- **模型灵活性**: 支持多种 AI 服务商，避免单点依赖
- **导出丰富**: 专注导出功能，而非内置学习算法
- **部署简单**: 单文件部署，依赖最小化

### 设计理念
本项目的核心理念是**生成即导出**，不追求在 Web 端实现复杂的间隔重复算法，而是专注于：
1. 高质量卡片内容生成
2. 丰富的导出格式支持
3. 与现有学习软件的完美对接
4. 简单高效的用户体验

## 🚀 发展路线图

### Phase 1: 基础设施优化 (优先级: 高)
- [ ] **数据持久化**: 集成 SQLite，支持卡片保存和历史记录
- [ ] **用户系统**: 基础的用户认证和个人卡片库管理
- [ ] **API 规范化**: 实现 RESTful API 设计，支持更多操作
- [ ] **错误处理优化**: 细化异常处理和用户友好的错误信息

### Phase 2: 功能增强 (优先级: 中)
- [ ] **批量处理**: 支持多文件上传和批量生成
- [ ] **内容预处理**: PDF、Word、图片 OCR 等格式支持
- [ ] **模板系统**: 自定义问答生成模板和风格
- [ ] **质量评估**: AI 生成内容的质量评分和筛选

### Phase 3: 集成扩展 (优先级: 中)
- [ ] **更多导出格式**: Quizlet、Memrise、SuperMemo 等平台支持
- [ ] **API 服务化**: 提供开放 API 供第三方应用集成
- [ ] **浏览器插件**: 网页内容一键生成卡片
- [ ] **移动端适配**: 响应式设计优化

### Phase 4: 高级特性 (优先级: 低)
- [ ] **多语言支持**: 英文、日文等其他语言的卡片生成
- [ ] **协作功能**: 卡片分享和社区库
- [ ] **统计分析**: 生成效果分析和使用统计
- [ ] **企业版功能**: 团队管理和批量授权

## 🔧 开发说明

### 代码结构说明
- `index.html` 和 `local_index.html` 存在代码重复是**设计选择**，目的是：
  - 方便本地调试（local版本直接使用localhost）
  - 云端部署配置独立（index版本使用相对路径）
  - 避免复杂的环境配置切换逻辑

### 本地开发
```bash
# 本地开发模式
uvicorn main:app --reload --host 127.0.0.1 --port 8000
# 访问 local_index.html 进行调试
```

### 生产部署
```bash
# 生产环境推荐使用 gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 优先改进领域
1. 数据持久化实现
2. 用户认证系统
3. 新的导出格式支持
4. AI 模型集成优化
5. 前端用户体验改进

## 📄 许可证

[添加您的许可证信息]

## 📞 联系方式

- 问题反馈: [您的联系方式]
- 功能建议: [反馈表单链接]

---

**💡 提示**: 这是一个专注于内容生成和导出的工具，建议与 Anki、Quizlet 等专业记忆软件配合使用，以获得最佳学习效果。
