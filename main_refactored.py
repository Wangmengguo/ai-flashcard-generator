"""
AI Flashcard Generator - 重构版本
支持灵活的Prompt模板系统
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import httpx
import logging
import re
import time
import json
from prompt_manager import prompt_manager, CustomPromptTemplate

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# 支持的模型配置
SUPPORTED_MODELS = {
    "google/gemini-2.5-flash-preview": {
        "name": "gemini-2.5-flash-preview",
        "description": "Created Apr 17, 2025; $0.15/M input tokens; $0.60/M output tokens",
        "max_tokens": 1048576,
        "suggested_use": "极快的模型，生成质量也不错",
    },
    "google/gemini-2.5-flash-preview-05-20": {
        "name": "gemini-2.5-flash-preview-05-20",
        "description": "Created May 20, 2025; $0.15/M input tokens; $0.60/M output tokens",
        "max_tokens": 1048576,
        "suggested_use": "极快的模型(0520)，生成质量也不错",
    },
    "google/gemini-2.5-pro-preview": {
        "name": "gemini-2.5-pro-preview",
        "description": "Created May 7, 2025; $1.25/M input tokens; $10/M output tokens",
        "max_tokens": 1048576,
        "suggested_use": "PRO模型，生成质量更好",
    },
    "anthropic/claude-3.7-sonnet": {
        "name": "anthropic/claude-3.7-sonnet",
        "description": "Created Feb 24, 2025; $3/M input tokens; $15/M output tokens",
        "max_tokens": 200000,
        "suggested_use": "唯一真神，富哥甄选",
    },
    "anthropic/claude-sonnet-4": {
        "name": "anthropic/claude-sonnet-4",
        "description": "Created May 22, 2025; $3/M input tokens; $15/M output tokens",
        "max_tokens": 200000,
        "suggested_use": "最新版Claude，与3.7差距不大，尝鲜可用",
    },
    "anthropic/claude-3-haiku": {
        "name": "Claude 3 Haiku",
        "description": "Created Mar 13, 2024; $0.25/M input tokens; $1.25/M output tokens",
        "max_tokens": 200000,
        "suggested_use": "适合一般文本处理，可能要抽卡",
    },
    "qwen/qwen3-235b-a22b": {
        "name": "qwen3 235b a22b",
        "description": "Created Apr 28, 2025; $0.14/M input tokens; $0.60/M output tokens",
        "max_tokens": 40960,
        "suggested_use": "思考模型，适合中国宝宝体质",
    },
    "x-ai/grok-3-mini-beta": {
        "name": "x-ai/grok-3-mini-beta",
        "description": "Created Apr 9, 2025; $0.30/M input tokens; $0.50/M output tokens",
        "max_tokens": 131072,
        "suggested_use": "马斯克产，价格不错，回答简短",
    },
    "openai/gpt-4.1-mini": {
        "name": "openai/gpt-4.1-mini",
        "description": "Created Apr 14, 2025; $0.40/M input tokens; $1.60/M output tokens",
        "max_tokens": 1047576,
        "suggested_use": "Sam Altman产，没啥优势，就是中庸",
    }
}

DEFAULT_MODEL_ID = "google/gemini-2.5-flash-preview"

# 错误处理映射
OPENROUTER_ERROR_MAP = {
    400: ("请求参数有误，请检查提交内容。", "BAD_REQUEST"),
    401: ("API密钥无效或未授权，请检查API Key配置。", "UNAUTHORIZED"),
    402: ("账户或API密钥额度不足，请充值或更换有效密钥。", "PAYMENT_REQUIRED"),
    403: ("请求被禁止，内容可能不符合规范。", "FORBIDDEN"),
    408: ("请求超时，请稍后重试。", "TIMEOUT"),
    429: ("请求过于频繁，请等待一段时间再试。", "RATE_LIMITED"),
    502: ("模型服务临时不可用，请稍后重试或切换模型。", "BAD_GATEWAY"),
    503: ("无可用模型提供者，请尝试更换API Key或模型。", "SERVICE_UNAVAILABLE"),
}

# 简单缓存系统
response_cache = {}

# 数据模型定义
class FlashcardRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="待处理的文本内容")
    api_key: str = Field(..., min_length=1, description="OpenRouter API密钥")
    model_name: str = Field(..., description="使用的AI模型名称")
    
    # 新增的自定义参数
    template_id: Optional[str] = Field(default=None, description="提示词模板ID")
    max_cards: Optional[int] = Field(default=None, ge=1, le=50, description="最大卡片数量")
    custom_system_prompt: Optional[str] = Field(default=None, description="自定义系统提示词")
    custom_user_prompt: Optional[str] = Field(default=None, description="自定义用户提示词")
    priority_keywords: Optional[List[str]] = Field(default=None, description="优先关键词列表")
    additional_instructions: Optional[str] = Field(default=None, max_length=500, description="附加指令")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "光合作用是植物将光能转化为化学能的过程...",
                "api_key": "your-openrouter-api-key",
                "model_name": "google/gemini-2.5-flash-preview",
                "template_id": "academic",
                "max_cards": 8,
                "priority_keywords": ["光合作用", "叶绿素", "ATP"]
            }
        }
    }

class FlashcardPair(BaseModel):
    q: str
    a: str

class FlashcardResponse(BaseModel):
    flashcards: List[FlashcardPair]
    error: Optional[str] = None
    template_used: Optional[str] = None
    cards_generated: Optional[int] = None
    processing_info: Optional[Dict[str, Any]] = None

class TemplateListResponse(BaseModel):
    templates: Dict[str, Dict[str, Any]]
    default_template: str

class TemplateValidationResponse(BaseModel):
    valid: bool
    template_name: Optional[str] = None
    max_cards: Optional[int] = None
    keyword_matches: Optional[List[str]] = None
    match_score: Optional[float] = None
    recommended: Optional[bool] = None
    question_types: Optional[List[str]] = None
    reason: Optional[str] = None

# 核心功能函数
def parse_llm_output(llm_output: str) -> List[FlashcardPair]:
    """解析LLM输出为FlashcardPair列表"""
    flashcards = []
    
    # 标准化Q/A标记
    pattern_q = re.compile(r'^[\s\-]*[Qq][：:]?\s*', re.MULTILINE)
    pattern_a = re.compile(r'^[\s\-]*[Aa][：:]?\s*', re.MULTILINE)
    
    # 按分隔符分割
    raw_cards = re.split(r'\s*\n-{3,}\n\s*', llm_output.strip())
    
    for card_text in raw_cards:
        card_text = card_text.strip()
        if not card_text:
            continue
        
        lines = card_text.splitlines()
        question_text = None
        answer_lines = []
        current_state = 'finding_q'
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            is_q_line = pattern_q.match(line_stripped)
            is_a_line = pattern_a.match(line_stripped)
            
            if current_state == 'finding_q':
                if is_q_line:
                    question_text = pattern_q.sub('', line_stripped).strip()
                    current_state = 'finding_a'
            elif current_state == 'finding_a':
                if is_a_line:
                    possible_answer_part = pattern_a.sub('', line_stripped).strip()
                    if possible_answer_part:
                        answer_lines.append(possible_answer_part)
                    current_state = 'collecting_a'
                elif is_q_line:
                    logger.error(f"Found Q without A: {question_text}")
                    question_text = pattern_q.sub('', line_stripped).strip()
                    answer_lines = []
            elif current_state == 'collecting_a':
                if is_q_line:
                    if question_text and answer_lines:
                        flashcards.append(FlashcardPair(q=question_text, a="\n".join(answer_lines).strip()))
                    question_text = pattern_q.sub('', line_stripped).strip()
                    answer_lines = []
                    current_state = 'finding_a'
                elif is_a_line:
                    if question_text and answer_lines:
                        flashcards.append(FlashcardPair(q=question_text, a="\n".join(answer_lines).strip()))
                    logger.error(f"Found A without Q: {line_stripped}")
                    question_text = None
                    answer_lines = []
                    current_state = 'finding_q'
                else:
                    answer_lines.append(line_stripped)
        
        # 处理最后一个卡片
        if question_text and answer_lines and current_state == 'collecting_a':
            flashcards.append(FlashcardPair(q=question_text, a="\n".join(answer_lines).strip()))
    
    # 过滤空卡片
    flashcards = [card for card in flashcards if card.q and card.a]
    return flashcards

async def generate_flashcards_from_llm(
    text_to_process: str,
    user_api_key: str,
    model_name: str,
    template_id: Optional[str] = None,
    max_cards: Optional[int] = None,
    custom_system_prompt: Optional[str] = None,
    custom_user_prompt: Optional[str] = None,
    additional_instructions: Optional[str] = None,
    use_cache: bool = True
) -> tuple[List[FlashcardPair], Dict[str, Any]]:
    """调用 OpenRouter API 生成 Flashcards（支持模板系统和缓存）"""
    
    # 确定使用的模板和提示词
    processing_info = {}
    
    if custom_system_prompt and custom_user_prompt:
        # 使用完全自定义的提示词
        system_prompt = custom_system_prompt
        user_prompt = custom_user_prompt.format(text=text_to_process)
        processing_info['prompt_source'] = 'custom'
        processing_info['template_used'] = 'custom'
    else:
        # 使用模板系统
        if template_id:
            template = prompt_manager.get_template(template_id)
            if not template:
                raise HTTPException(
                    status_code=400,
                    detail=f"模板 {template_id} 不存在"
                )
        else:
            template = prompt_manager.get_default_template()
            template_id = 'default'
        
        # 处理max_cards参数
        if max_cards:
            template.max_cards = max_cards
        
        # 格式化提示词
        format_kwargs = {}
        if additional_instructions:
            format_kwargs['additional_instructions'] = additional_instructions
            
        system_prompt = template.format_system_prompt(**format_kwargs)
        user_prompt = template.format_user_prompt(text_to_process, **format_kwargs)
        
        # 如果有额外指令，添加到系统提示词
        if additional_instructions:
            system_prompt += f"\n\n【额外要求】{additional_instructions}"
        
        processing_info['prompt_source'] = 'template'
        processing_info['template_used'] = template_id
        processing_info['template_name'] = template.name
        processing_info['max_cards'] = template.max_cards
    
    # 生成缓存键
    if use_cache:
        cache_content = f"{model_name}:{system_prompt[:100]}:{hash(text_to_process)}"
        cache_key = str(hash(cache_content))
        if cache_key in response_cache:
            cache_entry = response_cache[cache_key]
            if time.time() - cache_entry['timestamp'] < 3600:  # 1小时过期
                logger.info(f"Cache hit for key: {cache_key[:8]}...")
                return cache_entry['flashcards'], cache_entry['processing_info']
    
    # 验证模型是否支持
    if model_name not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模型。当前仅支持: {list(SUPPORTED_MODELS.keys())}"
        )
    
    # 构建API请求
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    # OpenRouter API 配置
    headers = {
        "Authorization": f"Bearer {user_api_key}",
        "Content-Type": "application/json",
    }
    
    # 日志记录
    logger.info(f"调用OpenRouter模型: {model_name}, 模板: {processing_info.get('template_used', 'unknown')}")

    # 发送请求到 OpenRouter
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            # 解析响应
            data = response.json()
            
            # LLM输出解析
            llm_output = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not llm_output or not isinstance(llm_output, str):
                logger.error(f"OpenRouter输出为空或格式异常, 原始返回: {data}")
                raise HTTPException(status_code=500, detail="模型未返回有效内容。")
            
            # 解析卡片
            flashcards = parse_llm_output(llm_output)
            if not flashcards:
                logger.warning(f"LLM输出未能解析出有效问答对，原始输出：{llm_output[:200]}")
                raise HTTPException(
                    status_code=500,
                    detail="生成内容未能解析成有效的问答卡片（可能原文太短，或LLM未遵守格式）。",
                    headers={"x-llm-output": llm_output[:500]}
                )
            
            # 更新处理信息
            processing_info['cards_generated'] = len(flashcards)
            processing_info['model_used'] = model_name
            processing_info['raw_output_length'] = len(llm_output)
            
            # 缓存结果
            if use_cache:
                response_cache[cache_key] = {
                    'flashcards': flashcards,
                    'processing_info': processing_info,
                    'timestamp': time.time()
                }
                logger.info(f"Cached response for key: {cache_key[:8]}...")
                
            return flashcards, processing_info
            
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            msg, codename = OPENROUTER_ERROR_MAP.get(code, ("调用模型服务时出现未知错误", "UNKNOWN"))
            logger.error(f"OpenRouter返回错误: {code} {msg} | {e.response.text}")
            raise HTTPException(
                status_code=code,
                detail={
                    "success": False,
                    "error_code": codename,
                    "message": msg
                }
            )
        except httpx.RequestError as e:
            logger.error(f"请求OpenRouter失败: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail={
                    "success": False,
                    "error_code": "CONNECTION_ERROR",
                    "message": "无法连接到模型服务，请检查网络。"
                }
            )
        except Exception as e:
            logger.error(f"未知错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error_code": "INTERNAL_ERROR",
                    "message": f"生成Flashcards时发生未知错误: {str(e)}"
                }
            )

# FastAPI 应用初始化
app = FastAPI(
    title="AI Flashcard Generator",
    description="AI驱动的智能抽认卡生成器，支持多种提示词模板",
    version="2.0.0"
)

# CORS 设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务 - 解决前端访问问题
app.mount("/static", StaticFiles(directory="."), name="static")

# 导入FileResponse
from fastapi.responses import FileResponse

# 为方便访问，在根路径提供前端文件
@app.get("/unified")
async def get_unified_interface():
    """提供统一界面的便捷访问"""
    return FileResponse("unified_index.html")

@app.get("/test")
async def get_test_interface():
    """提供测试界面的便捷访问"""
    return FileResponse("unified_index.html")

@app.get("/quality")
async def get_quality_guide():
    """提供质量测试指南"""
    return FileResponse("frontend/tools/quality_test_guide.html")

# API端点定义

@app.get("/")
async def root():
    """根端点，返回前端页面"""
    return FileResponse("unified_index.html")

@app.get("/api")
async def api_info():
    """API信息端点"""
    return {
        "message": "AI Flashcard Generator API",
        "version": "2.0.0",
        "features": [
            "多种预设模板",
            "自定义提示词",
            "灵活参数配置",
            "智能内容解析"
        ]
    }

@app.get("/supported_models")
async def get_supported_models():
    """返回支持的模型列表"""
    if DEFAULT_MODEL_ID not in SUPPORTED_MODELS:
        logger.warning(f"Default model ID '{DEFAULT_MODEL_ID}' not found in SUPPORTED_MODELS")
        actual_default_id = next(iter(SUPPORTED_MODELS)) if SUPPORTED_MODELS else None
    else:
        actual_default_id = DEFAULT_MODEL_ID
    
    return {
        "default_model_id": actual_default_id,
        "models": SUPPORTED_MODELS
    }

@app.get("/templates", response_model=TemplateListResponse)
async def get_templates():
    """获取所有可用的模板"""
    templates = prompt_manager.list_templates()
    return TemplateListResponse(
        templates=templates,
        default_template=prompt_manager.default_template_key
    )

@app.get("/templates/{template_id}/validate", response_model=TemplateValidationResponse)
async def validate_template(template_id: str, text: str):
    """验证模板与文本的匹配度"""
    validation_result = prompt_manager.validate_template_requirements(template_id, text)
    return TemplateValidationResponse(**validation_result)

@app.post("/templates/{template_id}")
async def add_custom_template(template_id: str, custom_template: CustomPromptTemplate):
    """添加自定义模板"""
    success = prompt_manager.add_custom_template(template_id, custom_template)
    if success:
        return {"message": f"模板 {template_id} 添加成功"}
    else:
        raise HTTPException(status_code=400, detail="添加模板失败")

@app.delete("/templates/{template_id}")
async def remove_template(template_id: str):
    """删除模板"""
    success = prompt_manager.remove_template(template_id)
    if success:
        return {"message": f"模板 {template_id} 删除成功"}
    else:
        raise HTTPException(status_code=400, detail="删除模板失败")

@app.post("/generate_flashcards/", response_model=FlashcardResponse)
async def create_flashcards(request: FlashcardRequest):
    """生成Flashcards的主要端点"""
    
    # 基本输入验证
    if not request.text.strip():
        return FlashcardResponse(flashcards=[], error="输入文本不能为空")
    
    if not request.api_key.strip():
        return FlashcardResponse(flashcards=[], error="API密钥不能为空")
    
    # 文本长度限制
    MAX_TEXT_LENGTH = 10000
    if len(request.text) > MAX_TEXT_LENGTH:
        return FlashcardResponse(
            flashcards=[],
            error=f"文本太长，请保持在{MAX_TEXT_LENGTH}字符以内"
        )
    
    try:
        # 调用LLM生成Flashcards
        generated_cards, processing_info = await generate_flashcards_from_llm(
            text_to_process=request.text,
            user_api_key=request.api_key,
            model_name=request.model_name,
            template_id=request.template_id,
            max_cards=request.max_cards,
            custom_system_prompt=request.custom_system_prompt,
            custom_user_prompt=request.custom_user_prompt,
            additional_instructions=request.additional_instructions
        )
        
        if not generated_cards:
            return FlashcardResponse(
                flashcards=[],
                error="未能生成任何有效的Flashcards"
            )
        
        return FlashcardResponse(
            flashcards=generated_cards,
            template_used=processing_info.get('template_used'),
            cards_generated=len(generated_cards),
            processing_info=processing_info
        )
    
    except HTTPException as e:
        # 重新抛出HTTP异常
        raise e
    except Exception as e:
        # 处理其他未预期的错误
        logger.error(f"处理请求时发生未知错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)