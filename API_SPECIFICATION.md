# API规范文档 - AI Flashcard Generator

## 概述

AI Flashcard Generator 提供一套基于 FastAPI 的 RESTful API，用于将中文文本转换为高质量的问答卡片。该 API 通过 OpenRouter 集成多个 AI 模型，支持智能文本解析和结构化输出。

**基础信息：**
- API版本：v1
- 协议：HTTP/HTTPS
- 内容类型：application/json
- 编码：UTF-8

## API端点总览

| 端点 | 方法 | 描述 |
|------|------|------|
| `/supported_models` | GET | 获取支持的AI模型列表 |
| `/generate_flashcards/` | POST | 生成问答卡片 |

## 通用响应格式

### 成功响应
```json
{
  "data": "具体数据内容",
  "success": true
}
```

### 错误响应
```json
{
  "detail": {
    "success": false,
    "error_code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

## 1. 获取支持的模型列表

**端点：** `GET /supported_models`

**描述：** 返回当前支持的所有AI模型及其配置信息。

### 请求示例

```bash
curl -X GET "http://127.0.0.1:8000/supported_models" \
  -H "Content-Type: application/json"
```

### 响应示例

```json
{
  "default_model_id": "google/gemini-2.5-flash-preview",
  "models": {
    "google/gemini-2.5-flash-preview": {
      "name": "gemini-2.5-flash-preview",
      "description": "Created Apr 17, 2025; $0.15/M input tokens; $0.60/M output tokens",
      "max_tokens": 1048576,
      "suggested_use": "极快的模型，生成质量也不错"
    },
    "google/gemini-2.5-flash-preview-05-20": {
      "name": "gemini-2.5-flash-preview-05-20",
      "description": "Created May 20, 2025; $0.15/M input tokens; $0.60/M output tokens",
      "max_tokens": 1048576,
      "suggested_use": "极快的模型(0520)，生成质量也不错"
    },
    "google/gemini-2.5-pro-preview": {
      "name": "gemini-2.5-pro-preview",
      "description": "Created May 7, 2025; $1.25/M input tokens; $10/M output tokens",
      "max_tokens": 1048576,
      "suggested_use": "PRO模型，生成质量更好"
    },
    "anthropic/claude-3.7-sonnet": {
      "name": "anthropic/claude-3.7-sonnet",
      "description": "Created Feb 24, 2025; $3/M input tokens; $15/M output tokens",
      "max_tokens": 200000,
      "suggested_use": "唯一真神，富哥甄选"
    },
    "anthropic/claude-sonnet-4": {
      "name": "anthropic/claude-sonnet-4",
      "description": "Created May 22, 2025; $3/M input tokens; $15/M output tokens",
      "max_tokens": 200000,
      "suggested_use": "最新版Claude，与3.7差距不大，尝鲜可用"
    },
    "anthropic/claude-3-haiku": {
      "name": "Claude 3 Haiku",
      "description": "Created Mar 13, 2024; $0.25/M input tokens; $1.25/M output tokens",
      "max_tokens": 200000,
      "suggested_use": "适合一般文本处理，可能要抽卡"
    },
    "qwen/qwen3-235b-a22b": {
      "name": "qwen3 235b a22b",
      "description": "Created Apr 28, 2025; $0.14/M input tokens; $0.60/M output tokens",
      "max_tokens": 40960,
      "suggested_use": "思考模型，适合中国宝宝体质"
    },
    "x-ai/grok-3-mini-beta": {
      "name": "x-ai/grok-3-mini-beta",
      "description": "Created Apr 9, 2025; $0.30/M input tokens; $0.50/M output tokens",
      "max_tokens": 131072,
      "suggested_use": "马斯克产，价格不错，回答简短"
    },
    "openai/gpt-4.1-mini": {
      "name": "openai/gpt-4.1-mini",
      "description": "Created Apr 14, 2025; $0.40/M input tokens; $1.60/M output tokens",
      "max_tokens": 1047576,
      "suggested_use": "Sam Altman产，没啥优势，就是中庸"
    }
  }
}
```

### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `default_model_id` | string | 默认推荐使用的模型ID |
| `models` | object | 模型配置对象 |
| `models.{model_id}` | object | 具体模型配置 |
| `models.{model_id}.name` | string | 模型显示名称 |
| `models.{model_id}.description` | string | 模型详细描述，包含定价信息 |
| `models.{model_id}.max_tokens` | integer | 模型支持的最大token数 |
| `models.{model_id}.suggested_use` | string | 使用建议 |

## 2. 生成问答卡片

**端点：** `POST /generate_flashcards/`

**描述：** 基于输入的中文文本生成结构化的问答卡片。

### 请求格式

#### 请求头
```
Content-Type: application/json
```

#### 请求体

```json
{
  "text": "需要生成问答卡片的文本内容",
  "api_key": "OpenRouter API密钥",
  "model_name": "使用的AI模型名称"
}
```

#### 请求字段说明

| 字段 | 类型 | 必填 | 描述 | 验证规则 |
|------|------|------|------|----------|
| `text` | string | 是 | 需要处理的中文文本 | 长度1-10000字符，不能为空字符串 |
| `api_key` | string | 是 | OpenRouter API密钥 | 格式必须为 `sk-or-` 开头 |
| `model_name` | string | 是 | AI模型标识符 | 必须是支持的模型列表中的一个 |

### 请求示例

```bash
curl -X POST "http://127.0.0.1:8000/generate_flashcards/" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "光合作用是植物、藻类和某些细菌利用光能，将二氧化碳和水转化为有机物，并释放氧气的过程。这个过程包括光反应和暗反应两个阶段。光反应发生在叶绿体的类囊体膜上，需要光照，产生ATP和NADPH。暗反应发生在叶绿体基质中，不直接需要光照，利用ATP和NADPH固定CO2形成葡萄糖。",
    "api_key": "sk-or-v1-abc123def456ghi789jkl...",
    "model_name": "google/gemini-2.5-flash-preview"
  }'
```

### 成功响应

#### 响应格式
```json
{
  "flashcards": [
    {
      "q": "问题内容",
      "a": "答案内容"
    }
  ],
  "error": null
}
```

#### 响应示例
```json
{
  "flashcards": [
    {
      "q": "光合作用的总体化学反应式是什么？",
      "a": "6 CO₂ + 6 H₂O → C₆H₁₂O₆ + 6 O₂"
    },
    {
      "q": "光合作用包括哪两个主要阶段？",
      "a": "光反应和暗反应两个阶段"
    },
    {
      "q": "光反应发生在叶绿体的哪个部位？",
      "a": "叶绿体的类囊体膜上"
    },
    {
      "q": "暗反应的主要功能是什么？",
      "a": "利用ATP和NADPH固定CO2形成葡萄糖"
    }
  ],
  "error": null
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `flashcards` | array | 生成的问答卡片数组 |
| `flashcards[].q` | string | 问题内容 |
| `flashcards[].a` | string | 答案内容 |
| `error` | string\|null | 错误信息，成功时为null |

### 错误响应

#### 输入验证错误
```json
{
  "flashcards": [],
  "error": "输入文本不能为空"
}
```

#### OpenRouter API错误
```json
{
  "detail": {
    "success": false,
    "error_code": "UNAUTHORIZED",
    "message": "API密钥无效或未授权，请检查API Key配置。"
  }
}
```

#### 模型不支持错误
```json
{
  "detail": "不支持的模型。当前仅支持: ['google/gemini-2.5-flash-preview', 'anthropic/claude-3.7-sonnet', ...]"
}
```

## 错误码标准化

### HTTP状态码

| 状态码 | 含义 | 对应场景 |
|--------|------|----------|
| 200 | 成功 | 请求处理成功 |
| 400 | 请求错误 | 请求参数有误、模型不支持等 |
| 401 | 未授权 | API密钥无效或未授权 |
| 402 | 需要付费 | 账户或API密钥额度不足 |
| 403 | 禁止访问 | 请求被禁止，内容不符合规范 |
| 408 | 请求超时 | 请求处理超时 |
| 429 | 请求过频 | 请求频率过高，触发限流 |
| 500 | 服务器错误 | 内部处理错误 |
| 502 | 网关错误 | 上游模型服务不可用 |
| 503 | 服务不可用 | 无可用模型提供者 |

### 自定义错误码

| 错误码 | 描述 | HTTP状态码 |
|--------|------|------------|
| `BAD_REQUEST` | 请求参数有误 | 400 |
| `UNAUTHORIZED` | API密钥无效或未授权 | 401 |
| `PAYMENT_REQUIRED` | 账户或API密钥额度不足 | 402 |
| `FORBIDDEN` | 请求被禁止 | 403 |
| `TIMEOUT` | 请求超时 | 408 |
| `RATE_LIMITED` | 请求过于频繁 | 429 |
| `INTERNAL_ERROR` | 服务器内部错误 | 500 |
| `BAD_GATEWAY` | 模型服务临时不可用 | 502 |
| `SERVICE_UNAVAILABLE` | 无可用模型提供者 | 503 |
| `CONNECTION_ERROR` | 网络连接错误 | 503 |

## 请求验证规则

### 文本输入验证
- **最小长度：** 1字符
- **最大长度：** 10,000字符
- **内容检查：** 不能为纯空格字符串
- **编码：** 必须为UTF-8

### API密钥验证
- **格式：** 必须以 `sk-or-` 开头
- **长度：** 通常为64位字符串
- **字符集：** 字母数字和特殊字符

### 模型名称验证
- **有效性：** 必须在支持的模型列表中
- **格式：** 遵循 `provider/model-name` 格式

## 智能解析机制

### LLM输出解析

API实现了强大的LLM输出解析器，支持多种格式变体：

#### 支持的问答格式
- `Q: 问题内容` / `A: 答案内容`
- `q: 问题内容` / `a: 答案内容`
- `Q： 问题内容` / `A： 答案内容` (中文冒号)
- 带前导空格或横线的格式

#### 分隔符支持
- `---` (标准分隔符)
- `----` 或更多横线
- 周围允许空白字符

#### 容错机制
- 自动忽略格式不正确的卡片
- 智能处理多行答案
- 状态机解析确保稳定性
- 详细的错误日志记录

### 质量控制

#### 输出质量标准
- 每个问答对必须有完整的问题和答案
- 问题应该清晰、独立、可理解
- 答案应该准确、完整、简明扼要
- 避免上下文依赖的代词

#### 数量控制
- 最优输出：≤10张高质量卡片
- 超量处理：优先保留信息量最大的前10张
- 最小输出：至少1张有效卡片

## 集成指南

### 前端集成示例

#### JavaScript/Fetch
```javascript
async function generateFlashcards(text, apiKey, modelName) {
  try {
    const response = await fetch('http://127.0.0.1:8000/generate_flashcards/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text,
        api_key: apiKey,
        model_name: modelName
      })
    });

    const data = await response.json();
    
    if (!response.ok) {
      const errorMsg = data.detail?.message || data.detail || '生成失败';
      throw new Error(errorMsg);
    }

    if (data.error) {
      throw new Error(data.error);
    }

    return data.flashcards;
  } catch (error) {
    console.error('API调用失败:', error);
    throw error;
  }
}
```

#### Python/requests
```python
import requests
import json

def generate_flashcards(text: str, api_key: str, model_name: str):
    url = "http://127.0.0.1:8000/generate_flashcards/"
    payload = {
        "text": text,
        "api_key": api_key,
        "model_name": model_name
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("error"):
            raise Exception(data["error"])
            
        return data["flashcards"]
    
    except requests.exceptions.HTTPError as e:
        error_data = response.json()
        error_msg = error_data.get("detail", {}).get("message", str(e))
        raise Exception(f"API错误: {error_msg}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络错误: {str(e)}")
```

### 错误处理最佳实践

#### 前端错误处理
```javascript
function handleApiError(error, response) {
  if (response?.status === 401) {
    return "API密钥无效，请检查配置";
  } else if (response?.status === 402) {
    return "账户余额不足，请充值";
  } else if (response?.status === 429) {
    return "请求过于频繁，请稍后重试";
  } else if (response?.status >= 500) {
    return "服务暂时不可用，请稍后重试";
  } else {
    return error.message || "未知错误";
  }
}
```

#### 重试机制
```javascript
async function generateWithRetry(text, apiKey, modelName, maxRetries = 3) {
  let lastError;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await generateFlashcards(text, apiKey, modelName);
    } catch (error) {
      lastError = error;
      
      // 只对特定错误进行重试
      if (error.message.includes('SERVICE_UNAVAILABLE') || 
          error.message.includes('TIMEOUT')) {
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        continue;
      } else {
        break;
      }
    }
  }
  
  throw lastError;
}
```

## 未来API扩展规范

### 计划新增端点

#### 1. 批量处理端点
```
POST /generate_flashcards/batch
```
- 支持多个文本同时处理
- 返回批量处理结果
- 支持进度查询

#### 2. 导出格式端点
```
POST /export/{format}
```
- 支持Anki、CSV、JSON等格式
- 自定义导出配置
- 支持批量导出

#### 3. 模型性能统计
```
GET /models/stats
```
- 返回各模型使用统计
- 响应时间分析
- 成功率统计

### 版本控制策略

#### URL版本控制
- 现有API：`/v1/generate_flashcards/`
- 新版本：`/v2/generate_flashcards/`

#### 向后兼容性
- 保持现有端点至少6个月
- 提供迁移指南
- 废弃通知机制

### 扩展字段预留

#### 请求字段扩展
```json
{
  "text": "文本内容",
  "api_key": "API密钥", 
  "model_name": "模型名称",
  "options": {
    "max_cards": 10,
    "difficulty_level": "medium",
    "question_types": ["short_answer", "multiple_choice"],
    "language": "zh-CN"
  }
}
```

#### 响应字段扩展
```json
{
  "flashcards": [...],
  "error": null,
  "metadata": {
    "processing_time": 2.5,
    "model_version": "gemini-2.5-flash-preview",
    "token_usage": {
      "input_tokens": 150,
      "output_tokens": 300
    },
    "quality_score": 0.95
  }
}
```

## 安全考虑

### API密钥安全
- **存储：** 建议使用环境变量或安全配置文件
- **传输：** 仅通过HTTPS传输
- **日志：** 避免在日志中记录完整密钥

### 输入验证
- **XSS防护：** 对所有输入进行HTML转义
- **注入防护：** 验证输入格式和长度
- **内容过滤：** 检查敏感或不当内容

### 速率限制
- **用户级限制：** 基于API密钥限流
- **IP级限制：** 防止恶意请求
- **全局限制：** 保护服务稳定性

## 性能优化

### 请求优化
- **批量处理：** 合并多个小请求
- **缓存机制：** 相同输入返回缓存结果
- **异步处理：** 长时间任务异步处理

### 响应优化
- **压缩：** 启用Gzip压缩
- **CDN：** 静态资源CDN加速
- **连接池：** 复用HTTP连接

## 支持与维护

### 技术支持
- **文档更新：** 定期更新API文档
- **示例代码：** 提供多语言示例
- **社区支持：** 建立开发者社区

### 监控与日志
- **API监控：** 实时监控API可用性
- **性能监控：** 跟踪响应时间和成功率
- **错误跟踪：** 详细记录和分析错误

---

**文档版本：** 1.0  
**最后更新：** 2025-06-20  
**维护团队：** AI Flashcard Generator Development Team