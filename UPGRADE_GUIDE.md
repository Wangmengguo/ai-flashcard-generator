# AI Flashcard Generator - Prompt系统重构升级指南

## 概述

本次重构为AI Flashcard Generator引入了灵活的Prompt模板系统，支持多种预设模板和完全自定义的提示词配置。

## 主要特性

### 1. 多种预设模板
- **学术研究模板 (academic)**: 适用于学术论文、研究报告
- **考试备考模板 (exam)**: 适用于各类考试复习材料
- **语言学习模板 (language)**: 适用于外语学习内容
- **技术文档模板 (technical)**: 适用于技术文档、编程教程
- **通用模板 (general)**: 默认模板，适用于一般性文本

### 2. 灵活配置选项
- 可调整最大卡片数量 (1-50张)
- 支持优先关键词设置
- 支持附加指令定制
- 完全自定义系统和用户提示词

### 3. 智能模板推荐
- 基于内容关键词匹配度推荐最适合的模板
- 模板验证API帮助选择最佳配置

## 文件结构

```
flashcard_generator_mvp/
├── main_refactored.py      # 重构后的主应用文件
├── prompt_manager.py       # 提示词模板管理系统
├── prompt_templates.json   # 预设模板配置文件
├── examples.py            # 使用示例代码
├── UPGRADE_GUIDE.md       # 本升级指南
├── main_backup.py         # 原版本备份
└── ...
```

## API变更

### 新增请求参数

`FlashcardRequest` 模型新增以下可选参数：

```python
{
    "text": "必填：待处理文本",
    "api_key": "必填：OpenRouter API密钥", 
    "model_name": "必填：AI模型名称",
    
    # 新增可选参数
    "template_id": "可选：模板ID（academic/exam/language/technical/general）",
    "max_cards": "可选：最大卡片数量（1-50）",
    "custom_system_prompt": "可选：自定义系统提示词",
    "custom_user_prompt": "可选：自定义用户提示词",
    "priority_keywords": "可选：优先关键词列表",
    "additional_instructions": "可选：附加指令（最长500字符）"
}
```

### 新增响应字段

`FlashcardResponse` 模型新增以下字段：

```python
{
    "flashcards": "生成的卡片列表",
    "error": "错误信息（如有）",
    
    # 新增字段
    "template_used": "使用的模板ID",
    "cards_generated": "实际生成的卡片数量",
    "processing_info": "处理信息和统计数据"
}
```

### 新增API端点

1. **获取模板列表**
   ```
   GET /templates
   ```

2. **验证模板匹配度**
   ```
   GET /templates/{template_id}/validate?text={text}
   ```

3. **添加自定义模板**
   ```
   POST /templates/{template_id}
   ```

4. **删除模板**
   ```
   DELETE /templates/{template_id}
   ```

## 使用示例

### 1. 基础使用（向后兼容）

```python
# 旧版本API调用方式仍然完全支持
request = {
    "text": "光合作用是植物将光能转化为化学能的过程...",
    "api_key": "your-api-key",
    "model_name": "google/gemini-2.5-flash-preview"
}
```

### 2. 使用预设模板

```python
# 使用学术模板，生成更多卡片
request = {
    "text": "机器学习的基本概念和应用...",
    "api_key": "your-api-key", 
    "model_name": "anthropic/claude-3.7-sonnet",
    "template_id": "academic",
    "max_cards": 15
}
```

### 3. 自定义配置

```python
# 使用考试模板并添加特殊要求
request = {
    "text": "中国近现代史重要事件...",
    "api_key": "your-api-key",
    "model_name": "google/gemini-2.5-pro-preview", 
    "template_id": "exam",
    "priority_keywords": ["时间", "人物", "事件"],
    "additional_instructions": "重点关注时间和因果关系"
}
```

### 4. 完全自定义提示词

```python
# 使用完全自定义的提示词
request = {
    "text": "待处理的文本内容...",
    "api_key": "your-api-key",
    "model_name": "qwen/qwen3-235b-a22b",
    "custom_system_prompt": "你的自定义系统提示词...",
    "custom_user_prompt": "请处理以下内容：\n\n{text}"
}
```

## 部署指南

### 1. 安装依赖

确保安装了新的依赖：

```bash
pip install pydantic[email] fastapi uvicorn httpx
```

### 2. 启动新版本

```bash
# 使用重构版本
uvicorn main_refactored:app --reload --host 127.0.0.1 --port 8000

# 或者用于生产环境
gunicorn main_refactored:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3. 测试API

```bash
# 检查API状态
curl http://127.0.0.1:8000/

# 获取支持的模型
curl http://127.0.0.1:8000/supported_models

# 获取可用模板
curl http://127.0.0.1:8000/templates
```

### 4. 运行示例

```bash
# 运行所有使用示例（需要有效的API密钥）
python examples.py
```

## 配置文件说明

### prompt_templates.json 结构

```json
{
  "templates": {
    "template_id": {
      "name": "模板显示名称",
      "description": "模板描述",
      "max_cards": 10,
      "system_prompt": "系统提示词模板，支持{max_cards}占位符",
      "user_prompt_template": "用户提示词模板，必须包含{text}占位符",
      "priority_keywords": ["关键词1", "关键词2"],
      "question_types": ["问题类型1", "问题类型2"]
    }
  },
  "default_template": "general"
}
```

### 自定义模板添加

```python
custom_template = {
    "name": "医学学习", 
    "description": "适用于医学知识学习",
    "max_cards": 8,
    "system_prompt": "你是医学教育专家...",
    "user_prompt_template": "请处理医学内容：\n\n{text}",
    "priority_keywords": ["症状", "诊断", "治疗"],
    "question_types": ["症状识别", "诊断方法", "治疗方案"]
}

# 通过API添加
POST /templates/medical
Content-Type: application/json
{custom_template}
```

## 性能优化

1. **缓存系统**: 支持基于内容和配置的智能缓存
2. **异步处理**: 完全异步的API调用和响应处理
3. **错误处理**: 增强的错误处理和用户友好的错误信息
4. **参数验证**: 使用Pydantic进行严格的输入验证

## 向后兼容性

- **100%向后兼容**: 所有现有的API调用方式无需修改
- **渐进式升级**: 可以逐步采用新功能，无需一次性重构
- **配置迁移**: 原有的硬编码配置自动作为默认模板使用

## 故障排除

### 常见问题

1. **模板不存在错误**
   ```
   解决：检查template_id是否正确，或使用GET /templates查看可用模板
   ```

2. **自定义提示词格式错误**
   ```
   解决：确保user_prompt_template包含{text}占位符
   ```

3. **参数验证失败**
   ```
   解决：检查max_cards范围（1-50），additional_instructions长度限制等
   ```

### 日志和监控

- 所有操作都有详细的日志记录
- 处理信息包含在响应的processing_info字段中
- 支持性能指标监控和缓存命中率统计

## 未来扩展

本架构为未来扩展奠定了良好基础：

1. **更多预设模板**: 可轻松添加新的专业领域模板
2. **动态模板生成**: 基于用户使用模式自动生成推荐模板
3. **A/B测试支持**: 支持不同模板效果的对比测试
4. **用户模板库**: 支持用户分享和使用社区模板
5. **智能推荐系统**: 基于内容分析自动推荐最佳模板和参数

## 技术支持

如有问题或建议，请参考：
- 示例代码：`examples.py`
- 源码注释：详细的代码注释和类型提示
- 日志文件：应用运行时的详细日志输出