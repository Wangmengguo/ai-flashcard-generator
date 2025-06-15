#0.导入

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import logging
import re

# 1.配置

SYSTEM_PROMPT = """
你是一位高阶抽认卡（Flashcards）生成专家，请将用户输入的原始中文文本转化为优质、问题驱动的问答卡片。严格参照下述规范：

1. 【输出语言】仅用中文。
2. 【知识原子化】每段文本≈一个考点，卡片信息应原子化（单一知识点），绝不混合多个独立概念；避免碎片化（不把过小信息单独成卡）。
3. 【问答格式规范】每张卡片用如下形式：
Q: <针对该段核心概念的清晰、独立问题>
A: <精准、完整、简明扼要的答案>
问答对间用“---”分隔，每个问答单独占一行。
4. 【问题类型】优先设为简答题，避免使用“对/错”、“是/否”即可回答的问题。
5. 【高优先级内容】优先抽取（如原文有）：
   - 概念定义与本质
   - 关键步骤、流程、公式
   - 原理或因果关系
   - 分类、对比
   - 典型例子或实际应用场景
   - 常见易错点或高频混淆
6. 【信息筛选与上限】如能抽取高质量卡片≤10张，全输出；如>10张，优先保留信息量最大、代表性最强的前10张（衡量标准为对理解全貌最重要的卡片）。
7. 【表达要求】
   - 回答必须准确、独立、完整且可单独理解。问题和答案不得出现上下文专属代词（如“它”、“其”、“他们”等）。
   - 允许适度同义改写以提升可记忆性，但绝不添加或推断原文未明示的事实或信息。
   - 问答风格统一，保持与示例一致的表达方式，不得出现解释性备注或输出模板外内容。
8. 【质量门槛】如遇信息稀疏或逻辑不清，无法构造高质量问答卡，请直接忽略该段材料，不强行生成低质卡片。
9. 【输出格式】请严格用 markdown 段落，便于后续处理。
10. 【示例】（仅示例格式，实际输出不得包含“示例”字样）：

Q: 光合作用的总体化学反应式是什么？
A: 6 CO₂ + 6 H₂O → C₆H₁₂O₆ + 6 O₂

---
Q: 柏拉图在《理想国》中使用“洞穴寓言”说明了什么哲学观点？
A: 说明感官世界只是表象，真正的知识来自理性对理念（真理）的把握。

---

请按以上全部规范和范例格式，生成最佳问答抽认卡。
"""

SUPPORTED_MODELS = {
    "google/gemini-2.5-flash-preview":{
        "name": "gemini-2.5-flash-preview",
        "description": "Created Apr 17, 2025; $0.15/M input tokens; $0.60/M output tokens",
        "max_tokens": 1048576,
        "suggested_use": "极快的模型，生成质量也不错",
    },
    "google/gemini-2.5-flash-preview-05-20":{
        "name": "gemini-2.5-flash-preview-05-20",
        "description": "Created May 20, 2025; $0.15/M input tokens; $0.60/M output tokens",
        "max_tokens": 1048576,
        "suggested_use": "极快的模型(0520)，生成质量也不错",
    },
    "google/gemini-2.5-pro-preview":{
        "name": "gemini-2.5-pro-preview",
        "description": "Created May 7, 2025; $1.25/M input tokens; $10/M output tokens",
        "max_tokens": 1048576,
        "suggested_use": "PRO模型，生成质量更好",
    },
    "anthropic/claude-3.7-sonnet":{
        "name":"anthropic/claude-3.7-sonnet",
        "description":"Created Feb 24, 2025; $3/M input tokens; $15/M output tokens",
        "max_tokens": 200000,
        "suggested_use": "唯一真神，富哥甄选",
    },
    "anthropic/claude-sonnet-4":{
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
    "x-ai/grok-3-mini-beta":{
        "name":"x-ai/grok-3-mini-beta",
        "description":"Created Apr 9, 2025; $0.30/M input tokens; $0.50/M output tokens",
        "max_tokens": 131072,
        "suggested_use": "马斯克产，价格不错，回答简短",
    },
    "openai/gpt-4.1-mini":{
        "name":"openai/gpt-4.1-mini",
        "description":"Created Apr 14, 2025; $0.40/M input tokens; $1.60/M output tokens",
        "max_tokens": 1047576,
        "suggested_use": "Sam Altman产，没啥优势，就是中庸",
    }
}

# 默认模型
DEFAULT_MODEL_ID = "google/gemini-2.5-flash-preview"

# 错误处理
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

# 2. 定义数据模型
class FlashcardRequest(BaseModel):
    text: str
    api_key: str
    model_name: str 

class FlashcardPair(BaseModel):
    q: str
    a: str

class FlashcardResponse(BaseModel):
    flashcards: list[FlashcardPair]
    error: str | None = None

# 3. 核心功能

# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# 辅助函数: 解析LLM输出（部分容错，支持Q/A格式变体）
def parse_llm_output(llm_output: str) -> list[FlashcardPair]:
    flashcards = []
    # 1. 标准化Q/A标记的多种写法
    # 支持Q:, q:, Q： 中文冒号等
    pattern_q = re.compile(r'^[\s\-]*[Qq][：:]?\s*', re.MULTILINE)
    pattern_a = re.compile(r'^[\s\-]*[Aa][：:]?\s*', re.MULTILINE)
    
    # 2. 按 "---" 分割成原始卡片文本块
    # 使用 re.split 可以更灵活地处理分隔符周围的空白
    raw_cards = re.split(r'\s*\n-{3,}\n\s*', llm_output.strip())   # 兼容 ---、——— 等分隔形式
    
    for card_text in raw_cards:
        card_text = card_text.strip()
        if not card_text:
            continue
        
        # 提取Q/A内容
        lines = card_text.splitlines()

        question_text = None
        answer_lines = []

        # 状态机
        current_state = 'finding_q' 
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped: # 空行
                continue
            
            is_q_line = pattern_q.match(line_stripped)
            is_a_line = pattern_a.match(line_stripped)
            
            # 检查Q
            if current_state == 'finding_q':
                if is_q_line:
                    question_text = pattern_q.sub('', line_stripped).strip()
                    current_state = 'finding_a' # 找到了Q，接下来找A
            
            elif current_state == 'finding_a':
                if is_a_line:
                    possible_answer_part = pattern_a.sub('', line_stripped).strip()
                    if possible_answer_part:
                        answer_lines.append(possible_answer_part)
                    current_state = 'collecting_a' # 开始收集答案行
                elif is_q_line:
                    # 如果在找A的时候又遇到了Q, 说明上一个Q可能没有A
                    # 可以选择记录一个只有问题没有答案的卡片，或者忽略
                    logging.error(f"Found Q without A: {question_text}")
                    question_text = pattern_q.sub('', line_stripped).strip() # 开始新的Q
                    answer_lines = [] # 重置答案
                    # current_state 保持 'finding_a' 或者根据逻辑决定是否回到 'finding_q'
                # else: 继续寻找A标记
            
            elif current_state == 'collecting_a':
                if is_q_line:
                    # 找到新的问题Q
                    # 先保存之前的卡片
                    if question_text and answer_lines:
                        flashcards.append(FlashcardPair(q=question_text,a="\n".join(answer_lines).strip()))

                    # 开始新的卡片
                    question_text = pattern_q.sub('',line_stripped).strip()
                    answer_lines = []
                    current_state = 'finding_a'
                elif is_a_line:
                    # 再次出现独立的A，报错
                    if question_text and answer_lines:
                        flashcards.append(FlashcardPair(q=question_text,a="\n".join(answer_lines).strip()))
                    # 开始新的卡片，但这个A没有Q，所以可能要忽略或记录错误
                    logging.error(f"Found A without Q or unexpected A: {line_stripped}")
                    question_text = None # 重置
                    answer_lines = []
                    possible_answer_part = pattern_a.sub('', line_stripped).strip()
                    if possible_answer_part:
                         logging.info(f"Treating stray A as start of new answer for a potential next Q or orphan A.")
                         # 这个逻辑比较复杂，简单起见，可以先忽略这种孤立的A
                         pass 
                    current_state = 'finding_q' # 回到寻找Q的状态
                
                else: # 不是新的Q，也不是新的A，都算作当前答案的一部分
                    answer_lines.append(line_stripped.strip()) # 保留原始缩进（如果需要）或 .strip()
        
                # 处理最后一个卡片块结束后可能未保存的卡片
        if question_text and answer_lines and current_state == 'collecting_a':
            flashcards.append(FlashcardPair(q=question_text, a="\n".join(answer_lines).strip()))
        elif question_text and not answer_lines and current_state == 'finding_a':
            # 可以选择记录一个只有问题没有答案的卡片
            logging.error(f"Found Q without A at end of block: {question_text}")
            pass

        # 后处理：去除可能因为解析逻辑产生的只有问题或只有答案的空卡片
        # （上述逻辑已尽量避免，但可以再加一层保险）
        flashcards = [card for card in flashcards if card.q and card.a]

    return flashcards

# 调用 OpenRouter API 生成 Flashcards
async def generate_flashcards_from_llm(
        text_to_process: str, 
        user_api_key: str, 
        model_name: str
) -> list[FlashcardPair]:
    """调用 OpenRouter API 生成 Flashcards"""
    
        
    # 验证模型是否支持
    if model_name not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模型。当前仅支持: {list(SUPPORTED_MODELS.keys())}"
        )
    
    # 其余代码保持不变，但使用传入的 model_name
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请为以下文本生成Flashcards：\n\n{text_to_process}"}
        ]
    }

    # OpenRouter API 配置
    headers = {
        "Authorization": f"Bearer {user_api_key}",
        "Content-Type": "application/json",
    }
    
    # 日志记录
    logging.info(f"调用OpenRouter模型: {model_name}")

    # 发送请求到 OpenRouter
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()  # 检查HTTP错误
            
            # 解析响应
            data = response.json()
            
            # ==== LLM输出解析和容错 ====
            llm_output = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not llm_output or not isinstance(llm_output, str):
                logging.error(f"OpenRouter输出为空或格式异常, 原始返回: {data}")
                raise HTTPException(status_code=500, detail="模型未返回有效内容。")
            
            # 解析
            flashcards = parse_llm_output(llm_output)
            # 容错: 若未能解析出任何卡片，也给予用户提示
            if not flashcards:
                # 可以在API返回debug字段，附带原始LLM输出
                logging.warning(f"LLM输出未能解析出有效问答对，原始输出：{llm_output[:200]}")
                raise HTTPException(
                    status_code=500, 
                    detail="生成内容未能解析成有效的问答卡片（可能原文太短，或LLM未遵守格式）。",
                    headers={"x-llm-output": llm_output[:500]}
                )     
            return flashcards
        
        except httpx.HTTPStatusError as e:
            # 细化处理各个常见OpenRouter错误码
            code = e.response.status_code
            msg, codename = OPENROUTER_ERROR_MAP.get(code, ("调用模型服务时出现未知错误", "UNKNOWN"))
            logging.error(f"OpenRouter返回错误: {code} {msg} | {e.response.text}")
            raise HTTPException(
                status_code=code,
                detail={
                    "success": False,
                    "error_code": codename,
                    "message": msg
                }
            )

        except httpx.RequestError as e:
            # 网络等异常
            logging.error(f"请求OpenRouter失败: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail={
                    "success": False,
                    "error_code": "CONNECTION_ERROR",
                    "message": "无法连接到模型服务，请检查网络。"
                }
            )
        except Exception as e:
            # 兜底异常
            logging.error(f"未知错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error_code": "INTERNAL_ERROR",
                    "message": f"生成Flashcards时发生未知错误: {str(e)}"
                }
            )

# 4.FastAPI 应用设置
app = FastAPI()
# CORS 设置
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#5.工具性端点（如获取模型列表）
@app.get("/supported_models")
async def get_supported_models():
    if DEFAULT_MODEL_ID not in SUPPORTED_MODELS:
        # 一个小小的健壮性检查，如果默认ID不在支持列表里，可以打个日志或者选第一个作为默认
        logging.warning(f"Default model ID '{DEFAULT_MODEL_ID}' not found in SUPPORTED_MODELS. Falling back to the first available model.")
        first_available_model = next(iter(SUPPORTED_MODELS)) if SUPPORTED_MODELS else None
        actual_default_id = first_available_model
    else:
        actual_default_id = DEFAULT_MODEL_ID
    """返回支持的模型列表"""
    
    return {
         "default_model_id": actual_default_id,
        "models": SUPPORTED_MODELS
    }

# 6. 主要的API端点
@app.post("/generate_flashcards/", response_model=FlashcardResponse)
async def create_flashcards(request: FlashcardRequest):
    """生成Flashcards的主要端点"""
    
    # 基本输入验证
    if not request.text.strip():
        return FlashcardResponse(flashcards=[], error="输入文本不能为空")
    
    if not request.api_key.strip():
        return FlashcardResponse(flashcards=[], error="API密钥不能为空")
    
    # 文本长度限制（可选）
    MAX_TEXT_LENGTH = 10000
    if len(request.text) > MAX_TEXT_LENGTH:
        return FlashcardResponse(
            flashcards=[],
            error=f"文本太长，请保持在{MAX_TEXT_LENGTH}字符以内"
        )
    
    try:
        # 调用LLM生成Flashcards
        generated_cards = await generate_flashcards_from_llm(
            request.text,
            request.api_key,
            request.model_name
        )
        
        if not generated_cards:
            return FlashcardResponse(
                flashcards=[],
                error="未能生成任何有效的Flashcards"
            )
        
        return FlashcardResponse(flashcards=generated_cards)
    
    except HTTPException as e:
        # 重新抛出HTTP异常
        raise e
    except Exception as e:
        # 处理其他未预期的错误
        raise HTTPException(status_code=500, detail=str(e))