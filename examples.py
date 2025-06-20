"""
AI Flashcard Generator - 使用示例
展示如何使用新的Prompt模板系统
"""

import asyncio
import httpx
import json

# API基础URL
BASE_URL = "http://127.0.0.1:8000"

# 示例API密钥（请替换为实际的OpenRouter API密钥）
API_KEY = "your-openrouter-api-key"

async def example_basic_usage():
    """基础使用示例 - 使用默认模板"""
    print("=== 基础使用示例 ===")
    
    data = {
        "text": """
        光合作用是植物、藻类和某些细菌利用阳光、二氧化碳和水来制造葡萄糖和氧气的过程。
        这个过程发生在植物的叶绿体中，主要包含光反应和暗反应两个阶段。
        光反应阶段在类囊体膜上进行，将光能转化为化学能（ATP和NADPH）。
        暗反应阶段在叶绿体基质中进行，利用ATP和NADPH将CO2固定成有机物。
        """,
        "api_key": API_KEY,
        "model_name": "google/gemini-2.5-flash-preview"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/generate_flashcards/", json=data)
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"使用模板: {result.get('template_used', 'unknown')}")
        print(f"生成卡片数: {result.get('cards_generated', 0)}")
        print("\n生成的卡片:")
        for i, card in enumerate(result.get('flashcards', []), 1):
            print(f"{i}. Q: {card['q']}")
            print(f"   A: {card['a']}\n")

async def example_academic_template():
    """学术模板使用示例"""
    print("=== 学术模板使用示例 ===")
    
    data = {
        "text": """
        机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习和改进性能。
        监督学习是机器学习的一种类型，使用标记的训练数据来训练模型。
        无监督学习则是在没有标记数据的情况下发现数据中的模式。
        深度学习是机器学习的一个子集，使用多层神经网络来模拟人脑的工作方式。
        卷积神经网络（CNN）特别适合图像识别任务，而循环神经网络（RNN）适合序列数据处理。
        """,
        "api_key": API_KEY,
        "model_name": "anthropic/claude-3.7-sonnet",
        "template_id": "academic",
        "max_cards": 12
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/generate_flashcards/", json=data)
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"使用模板: {result.get('template_used', 'unknown')}")
        print(f"生成卡片数: {result.get('cards_generated', 0)}")
        print("\n生成的卡片:")
        for i, card in enumerate(result.get('flashcards', []), 1):
            print(f"{i}. Q: {card['q']}")
            print(f"   A: {card['a']}\n")

async def example_exam_template():
    """考试模板使用示例"""
    print("=== 考试模板使用示例 ===")
    
    data = {
        "text": """
        中华人民共和国成立于1949年10月1日。新中国成立初期面临着经济恢复和建设的艰巨任务。
        第一个五年计划（1953-1957）的重点是发展重工业，建立独立的工业体系。
        改革开放始于1978年，以邓小平为核心的第二代中央领导集体作出了这一重大决策。
        改革开放的总设计师是邓小平，他提出了"一国两制"的构想。
        社会主义市场经济体制的确立是中国改革开放的重大成果。
        """,
        "api_key": API_KEY,
        "model_name": "google/gemini-2.5-pro-preview",
        "template_id": "exam",
        "priority_keywords": ["1949", "五年计划", "改革开放", "邓小平"],
        "additional_instructions": "重点关注时间、人物和重大事件"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/generate_flashcards/", json=data)
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"使用模板: {result.get('template_used', 'unknown')}")
        print(f"生成卡片数: {result.get('cards_generated', 0)}")
        print("\n生成的卡片:")
        for i, card in enumerate(result.get('flashcards', []), 1):
            print(f"{i}. Q: {card['q']}")
            print(f"   A: {card['a']}\n")

async def example_language_template():
    """语言学习模板使用示例"""
    print("=== 语言学习模板使用示例 ===")
    
    data = {
        "text": """
        Hello, my name is John. I am a teacher at the local high school.
        I teach English literature and creative writing classes.
        Every morning, I prepare my lessons carefully and review student homework.
        Teaching is both challenging and rewarding. I enjoy helping students improve their writing skills.
        In my free time, I like to read novels and write short stories.
        """,
        "api_key": API_KEY,
        "model_name": "google/gemini-2.5-flash-preview",
        "template_id": "language",
        "max_cards": 15
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/generate_flashcards/", json=data)
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"使用模板: {result.get('template_used', 'unknown')}")
        print(f"生成卡片数: {result.get('cards_generated', 0)}")
        print("\n生成的卡片:")
        for i, card in enumerate(result.get('flashcards', []), 1):
            print(f"{i}. Q: {card['q']}")
            print(f"   A: {card['a']}\n")

async def example_technical_template():
    """技术文档模板使用示例"""
    print("=== 技术文档模板使用示例 ===")
    
    data = {
        "text": """
        FastAPI是一个现代、快速的Python Web框架，用于构建API。
        它基于标准Python类型提示，具有自动API文档生成功能。
        FastAPI使用Pydantic进行数据验证和序列化，使用Starlette处理HTTP请求。
        异步支持是FastAPI的一个重要特性，允许处理高并发请求。
        中间件系统允许在请求和响应过程中执行自定义逻辑。
        依赖注入系统简化了复杂应用程序的架构设计。
        """,
        "api_key": API_KEY,
        "model_name": "qwen/qwen3-235b-a22b",
        "template_id": "technical",
        "additional_instructions": "注重实际应用和代码示例"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/generate_flashcards/", json=data)
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"使用模板: {result.get('template_used', 'unknown')}")
        print(f"生成卡片数: {result.get('cards_generated', 0)}")
        print("\n生成的卡片:")
        for i, card in enumerate(result.get('flashcards', []), 1):
            print(f"{i}. Q: {card['q']}")
            print(f"   A: {card['a']}\n")

async def example_custom_template():
    """自定义模板使用示例"""
    print("=== 自定义模板使用示例 ===")
    
    # 首先添加自定义模板
    custom_template = {
        "name": "医学学习",
        "description": "适用于医学知识学习",
        "max_cards": 8,
        "system_prompt": """你是一位医学教育专家，请将医学文本转化为学习卡片。
        重点关注：疾病症状、诊断方法、治疗方案、药物作用机制。
        问答格式：Q: <医学问题> A: <准确答案>
        每张卡片用"---"分隔。生成{max_cards}张以内的卡片。""",
        "user_prompt_template": "请为以下医学内容生成学习卡片：\n\n{text}",
        "priority_keywords": ["症状", "诊断", "治�疗", "药物"],
        "question_types": ["症状识别", "诊断方法", "治疗方案", "药理机制"]
    }
    
    # 添加自定义模板
    async with httpx.AsyncClient() as client:
        template_response = await client.post(
            f"{BASE_URL}/templates/medical",
            json=custom_template
        )
        print(f"添加模板结果: {template_response.json()}")
    
    # 使用自定义模板生成卡片
    data = {
        "text": """
        糖尿病是一组以高血糖为特征的代谢性疾病。
        1型糖尿病由胰岛β细胞破坏导致的绝对胰岛素缺乏引起。
        2型糖尿病由胰岛素抵抗和相对胰岛素分泌不足引起。
        典型症状包括多饮、多尿、多食和体重减轻（三多一少）。
        诊断标准包括空腹血糖≥7.0mmol/L或糖耐量试验2小时血糖≥11.1mmol/L。
        治疗包括饮食控制、运动疗法、药物治疗和血糖监测。
        """,
        "api_key": API_KEY,
        "model_name": "anthropic/claude-3.7-sonnet",
        "template_id": "medical"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/generate_flashcards/", json=data)
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"使用模板: {result.get('template_used', 'unknown')}")
        print(f"生成卡片数: {result.get('cards_generated', 0)}")
        print("\n生成的卡片:")
        for i, card in enumerate(result.get('flashcards', []), 1):
            print(f"{i}. Q: {card['q']}")
            print(f"   A: {card['a']}\n")

async def example_fully_custom_prompts():
    """完全自定义提示词示例"""
    print("=== 完全自定义提示词示例 ===")
    
    data = {
        "text": """
        人工智能的发展历程可以分为几个重要阶段。
        1950年代，艾伦·图灵提出了著名的图灵测试。
        1956年，达特茅斯会议标志着人工智能学科的正式诞生。
        1980年代，专家系统得到了广泛应用。
        21世纪以来，深度学习推动了AI的快速发展。
        """,
        "api_key": API_KEY,
        "model_name": "google/gemini-2.5-flash-preview",
        "custom_system_prompt": """你是一个简洁的问答生成器。
        将文本转化为简单的问答对，每个问答用"---"分隔。
        问题要直接明了，答案要准确简洁。
        格式：Q: 问题 A: 答案""",
        "custom_user_prompt": "请为以下内容生成5个简洁的问答对：\n\n{text}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/generate_flashcards/", json=data)
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"使用模板: {result.get('template_used', 'unknown')}")
        print(f"生成卡片数: {result.get('cards_generated', 0)}")
        print("\n生成的卡片:")
        for i, card in enumerate(result.get('flashcards', []), 1):
            print(f"{i}. Q: {card['q']}")
            print(f"   A: {card['a']}\n")

async def example_get_templates():
    """获取所有模板示例"""
    print("=== 获取所有模板示例 ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/templates")
        result = response.json()
        
        print(f"默认模板: {result['default_template']}")
        print("\n可用模板:")
        for template_id, template_info in result['templates'].items():
            print(f"- {template_id}: {template_info['name']}")
            print(f"  描述: {template_info['description']}")
            print(f"  最大卡片数: {template_info['max_cards']}")
            print(f"  问题类型: {', '.join(template_info.get('question_types', []))}")
            print()

async def example_validate_template():
    """模板验证示例"""
    print("=== 模板验证示例 ===")
    
    text = "机器学习算法包括监督学习、无监督学习和强化学习。"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/templates/academic/validate",
            params={"text": text}
        )
        result = response.json()
        
        print(f"验证结果: {'通过' if result['valid'] else '失败'}")
        print(f"模板名称: {result.get('template_name', 'N/A')}")
        print(f"推荐使用: {'是' if result.get('recommended', False) else '否'}")
        print(f"匹配关键词: {result.get('keyword_matches', [])}")
        print(f"匹配度: {result.get('match_score', 0):.2f}")

async def main():
    """运行所有示例"""
    print("AI Flashcard Generator - 使用示例演示")
    print("=" * 50)
    
    try:
        # 检查API是否可用
        async with httpx.AsyncClient() as client:
            health_response = await client.get(f"{BASE_URL}/")
            print(f"API状态: {health_response.status_code}")
            print(f"API信息: {health_response.json()}")
            print()
        
        # 运行各种示例
        await example_get_templates()
        await example_validate_template()
        await example_basic_usage()
        await example_academic_template()
        await example_exam_template()
        await example_language_template()
        await example_technical_template()
        await example_custom_template()
        await example_fully_custom_prompts()
        
    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保API服务器正在运行：uvicorn main_refactored:app --reload")

if __name__ == "__main__":
    asyncio.run(main())