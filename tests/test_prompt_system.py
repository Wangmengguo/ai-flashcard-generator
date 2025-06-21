"""
AI Flashcard Generator - Prompt系统测试脚本
验证新的模板系统功能
"""

import pytest
import json
from prompt_manager import PromptManager, PromptTemplate, CustomPromptTemplate

def test_prompt_template_creation():
    """测试PromptTemplate创建和验证"""
    print("测试 PromptTemplate 创建...")
    
    # 正常创建
    template = PromptTemplate(
        name="测试模板",
        description="这是一个测试模板",
        max_cards=10,
        system_prompt="你是一个测试专家，生成{max_cards}张卡片。",
        user_prompt_template="请处理以下内容：\n\n{text}",
        priority_keywords=["测试", "验证"],
        question_types=["概念类", "应用类"]
    )
    
    assert template.name == "测试模板"
    assert template.max_cards == 10
    
    # 测试格式化
    formatted_system = template.format_system_prompt()
    assert "10张卡片" in formatted_system
    
    formatted_user = template.format_user_prompt("测试文本")
    assert "测试文本" in formatted_user
    
    print("✓ PromptTemplate 创建和格式化测试通过")

def test_prompt_template_validation():
    """测试PromptTemplate参数验证"""
    print("测试 PromptTemplate 参数验证...")
    
    # 测试无效的max_cards
    try:
        PromptTemplate(
            name="测试",
            description="测试",
            max_cards=0,  # 无效值
            system_prompt="测试",
            user_prompt_template="测试{text}"
        )
        assert False, "应该抛出ValueError"
    except ValueError:
        pass
    
    # 测试缺少{text}占位符
    try:
        PromptTemplate(
            name="测试",
            description="测试", 
            max_cards=5,
            system_prompt="测试",
            user_prompt_template="没有占位符"  # 缺少{text}
        )
        assert False, "应该抛出ValueError"
    except ValueError:
        pass
    
    print("✓ PromptTemplate 参数验证测试通过")

def test_custom_prompt_template():
    """测试CustomPromptTemplate Pydantic模型"""
    print("测试 CustomPromptTemplate...")
    
    # 正常创建
    custom = CustomPromptTemplate(
        name="自定义模板",
        description="这是自定义模板",
        max_cards=8,
        system_prompt="自定义系统提示",
        user_prompt_template="处理：{text}",
        priority_keywords=["关键词1", "关键词2"]
    )
    
    # 转换为PromptTemplate
    template = custom.to_prompt_template()
    assert isinstance(template, PromptTemplate)
    assert template.name == "自定义模板"
    
    # 测试验证失败的情况
    try:
        CustomPromptTemplate(
            name="",  # 空名称
            description="测试",
            system_prompt="测试",
            user_prompt_template="测试{text}"
        )
        assert False, "应该抛出验证错误"
    except:
        pass
    
    print("✓ CustomPromptTemplate 测试通过")

def test_prompt_manager():
    """测试PromptManager功能"""
    print("测试 PromptManager...")
    
    # 创建临时配置文件
    test_config = {
        "templates": {
            "test1": {
                "name": "测试模板1",
                "description": "第一个测试模板",
                "max_cards": 5,
                "system_prompt": "测试系统提示{max_cards}",
                "user_prompt_template": "处理：{text}",
                "priority_keywords": ["测试"],
                "question_types": ["测试类"]
            },
            "test2": {
                "name": "测试模板2", 
                "description": "第二个测试模板",
                "max_cards": 8,
                "system_prompt": "另一个系统提示",
                "user_prompt_template": "分析：{text}",
                "priority_keywords": ["分析"],
                "question_types": ["分析类"]
            }
        },
        "default_template": "test1"
    }
    
    # 保存测试配置
    with open("test_templates.json", "w", encoding="utf-8") as f:
        json.dump(test_config, f, ensure_ascii=False, indent=2)
    
    # 创建PromptManager实例
    manager = PromptManager("test_templates.json")
    
    # 测试模板加载
    assert len(manager.templates) == 2
    assert "test1" in manager.templates
    assert "test2" in manager.templates
    
    # 测试获取模板
    template1 = manager.get_template("test1")
    assert template1 is not None
    assert template1.name == "测试模板1"
    
    # 测试默认模板
    default_template = manager.get_default_template()
    assert default_template.name == "测试模板1"
    
    # 测试列出模板
    template_list = manager.list_templates()
    assert len(template_list) == 2
    assert "test1" in template_list
    
    # 测试添加自定义模板
    custom_template = CustomPromptTemplate(
        name="动态模板",
        description="动态添加的模板",
        system_prompt="动态系统提示",
        user_prompt_template="动态处理：{text}"
    )
    
    success = manager.add_custom_template("dynamic", custom_template)
    assert success == True
    assert len(manager.templates) == 3
    
    # 测试模板验证
    validation_result = manager.validate_template_requirements("test1", "这是测试文本")
    assert validation_result['valid'] == True
    assert validation_result['template_name'] == "测试模板1"
    
    # 清理测试文件
    import os
    os.remove("test_templates.json")
    
    print("✓ PromptManager 功能测试通过")

def test_template_formatting():
    """测试模板格式化功能"""
    print("测试模板格式化...")
    
    template = PromptTemplate(
        name="格式化测试",
        description="测试格式化功能",
        max_cards=12,
        system_prompt="生成{max_cards}张卡片，{additional_instructions}",
        user_prompt_template="处理文本({max_cards}张)：\n{text}\n附加要求：{additional_instructions}",
        priority_keywords=["格式化"]
    )
    
    # 测试系统提示词格式化
    formatted_system = template.format_system_prompt(additional_instructions="重点关注概念")
    assert "生成12张卡片" in formatted_system
    assert "重点关注概念" in formatted_system
    
    # 测试用户提示词格式化
    formatted_user = template.format_user_prompt(
        "这是测试文本",
        additional_instructions="注意细节"
    )
    assert "这是测试文本" in formatted_user
    assert "处理文本(12张)" in formatted_user
    assert "注意细节" in formatted_user
    
    print("✓ 模板格式化测试通过")

def test_error_handling():
    """测试错误处理"""
    print("测试错误处理...")
    
    manager = PromptManager("nonexistent_file.json")
    
    # 应该创建默认模板
    assert len(manager.templates) >= 1
    assert manager.get_default_template() is not None
    
    # 测试获取不存在的模板
    non_template = manager.get_template("nonexistent")
    assert non_template is None
    
    # 测试删除默认模板（应该失败）
    success = manager.remove_template(manager.default_template_key)
    assert success == False
    
    print("✓ 错误处理测试通过")

def test_template_matching():
    """测试模板匹配功能"""
    print("测试模板匹配...")
    
    # 创建测试管理器
    manager = PromptManager()
    
    # 测试学术内容匹配
    academic_text = "机器学习是人工智能的重要分支，包括监督学习、无监督学习等方法。"
    validation = manager.validate_template_requirements("academic", academic_text)
    
    assert validation['valid'] == True
    assert validation['match_score'] >= 0  # 匹配度应该大于等于0
    
    # 测试短文本
    short_text = "短文本"
    validation = manager.validate_template_requirements("academic", short_text)
    assert validation['valid'] == False
    assert validation['reason'] == "Text too short"
    
    print("✓ 模板匹配测试通过")

def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("AI Flashcard Generator - Prompt系统测试")
    print("=" * 50)
    
    try:
        test_prompt_template_creation()
        test_prompt_template_validation()
        test_custom_prompt_template()
        test_prompt_manager()
        test_template_formatting()
        test_error_handling()
        test_template_matching()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试通过！")
        print("Prompt模板系统功能正常")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()