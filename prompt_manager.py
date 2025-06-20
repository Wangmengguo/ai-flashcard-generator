"""
Prompt Template Management System
为AI Flashcard Generator提供灵活的提示词模板管理
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PromptTemplate:
    """提示词模板数据类"""
    name: str
    description: str
    max_cards: int
    system_prompt: str
    user_prompt_template: str
    priority_keywords: List[str] = field(default_factory=list)
    question_types: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """验证模板数据的有效性"""
        if self.max_cards < 1 or self.max_cards > 50:
            raise ValueError(f"max_cards must be between 1 and 50, got {self.max_cards}")
        
        if not self.system_prompt.strip():
            raise ValueError("system_prompt cannot be empty")
        
        if not self.user_prompt_template.strip():
            raise ValueError("user_prompt_template cannot be empty")
        
        # 检查用户提示词模板是否包含必要的占位符
        if '{text}' not in self.user_prompt_template:
            raise ValueError("user_prompt_template must contain {text} placeholder")
    
    def format_system_prompt(self, **kwargs) -> str:
        """格式化系统提示词"""
        try:
            # 替换max_cards占位符
            formatted_prompt = self.system_prompt.format(max_cards=self.max_cards, **kwargs)
            return formatted_prompt
        except KeyError as e:
            logger.warning(f"Missing placeholder in system prompt: {e}")
            return self.system_prompt
    
    def format_user_prompt(self, text: str, **kwargs) -> str:
        """格式化用户提示词"""
        try:
            formatted_prompt = self.user_prompt_template.format(
                text=text, 
                max_cards=self.max_cards, 
                **kwargs
            )
            return formatted_prompt
        except KeyError as e:
            logger.warning(f"Missing placeholder in user prompt: {e}")
            return self.user_prompt_template.format(text=text, max_cards=self.max_cards)


class CustomPromptTemplate(BaseModel):
    """自定义提示词模板的Pydantic模型"""
    name: str = Field(..., min_length=1, max_length=50, description="模板名称")
    description: str = Field(..., min_length=1, max_length=200, description="模板描述")
    max_cards: int = Field(default=10, ge=1, le=50, description="最大卡片数量")
    system_prompt: str = Field(..., min_length=10, description="系统提示词")
    user_prompt_template: str = Field(..., min_length=10, description="用户提示词模板")
    priority_keywords: List[str] = Field(default_factory=list, description="优先关键词")
    question_types: List[str] = Field(default_factory=list, description="问题类型")
    
    @validator('user_prompt_template')
    def validate_user_prompt_template(cls, v):
        if '{text}' not in v:
            raise ValueError('user_prompt_template must contain {text} placeholder')
        return v
    
    def to_prompt_template(self) -> PromptTemplate:
        """转换为PromptTemplate对象"""
        return PromptTemplate(
            name=self.name,
            description=self.description,
            max_cards=self.max_cards,
            system_prompt=self.system_prompt,
            user_prompt_template=self.user_prompt_template,
            priority_keywords=self.priority_keywords,
            question_types=self.question_types
        )


class PromptManager:
    """提示词模板管理器"""
    
    def __init__(self, config_path: str = "prompt_templates.json"):
        self.config_path = config_path
        self.templates: Dict[str, PromptTemplate] = {}
        self.default_template_key = "general"
        self._load_templates()
    
    def _load_templates(self):
        """从配置文件加载模板"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file {self.config_path} not found, using default template")
                self._create_default_template()
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 加载预设模板
            templates_config = config.get('templates', {})
            for template_id, template_data in templates_config.items():
                try:
                    template = PromptTemplate(**template_data)
                    self.templates[template_id] = template
                    logger.info(f"Loaded template: {template_id}")
                except Exception as e:
                    logger.error(f"Failed to load template {template_id}: {e}")
            
            # 设置默认模板
            self.default_template_key = config.get('default_template', 'general')
            
            if not self.templates:
                logger.warning("No valid templates loaded, creating default template")
                self._create_default_template()
                
        except Exception as e:
            logger.error(f"Failed to load templates config: {e}")
            self._create_default_template()
    
    def _create_default_template(self):
        """创建默认模板"""
        default_template = PromptTemplate(
            name="通用模板",
            description="适用于一般性文本内容的默认模板",
            max_cards=10,
            system_prompt="""你是一位高阶抽认卡（Flashcards）生成专家，请将用户输入的原始中文文本转化为优质、问题驱动的问答卡片。严格参照下述规范：

1. 【输出语言】仅用中文。
2. 【知识原子化】每段文本≈一个考点，卡片信息应原子化（单一知识点），绝不混合多个独立概念。
3. 【问答格式规范】每张卡片用如下形式：
Q: <针对该段核心概念的清晰、独立问题>
A: <精准、完整、简明扼要的答案>
问答对间用"---"分隔。
4. 【卡片数量】生成{max_cards}张以内的高质量卡片。
5. 【质量门槛】如遇信息稀疏或逻辑不清，无法构造高质量问答卡，请直接忽略该段材料。

请按以上规范生成问答抽认卡。""",
            user_prompt_template="请为以下文本生成Flashcards（最多{max_cards}张）：\n\n{text}",
            priority_keywords=["定义", "概念", "原理", "方法"],
            question_types=["定义类", "原理类", "方法类", "应用类"]
        )
        self.templates['general'] = default_template
        self.default_template_key = 'general'
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """获取指定模板"""
        return self.templates.get(template_id)
    
    def get_default_template(self) -> PromptTemplate:
        """获取默认模板"""
        return self.templates.get(self.default_template_key, list(self.templates.values())[0])
    
    def list_templates(self) -> Dict[str, Dict[str, Any]]:
        """列出所有可用模板"""
        return {
            template_id: {
                'name': template.name,
                'description': template.description,
                'max_cards': template.max_cards,
                'question_types': template.question_types
            }
            for template_id, template in self.templates.items()
        }
    
    def add_custom_template(self, template_id: str, custom_template: CustomPromptTemplate) -> bool:
        """添加自定义模板"""
        try:
            if template_id in self.templates:
                logger.warning(f"Template {template_id} already exists, will be overwritten")
            
            prompt_template = custom_template.to_prompt_template()
            self.templates[template_id] = prompt_template
            logger.info(f"Added custom template: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add custom template {template_id}: {e}")
            return False
    
    def remove_template(self, template_id: str) -> bool:
        """移除模板"""
        if template_id == self.default_template_key:
            logger.error("Cannot remove default template")
            return False
        
        if template_id in self.templates:
            del self.templates[template_id]
            logger.info(f"Removed template: {template_id}")
            return True
        
        return False
    
    def update_template_config(self, template_id: str, **kwargs) -> bool:
        """更新模板配置"""
        if template_id not in self.templates:
            logger.error(f"Template {template_id} not found")
            return False
        
        try:
            template = self.templates[template_id]
            
            # 更新允许的字段
            if 'max_cards' in kwargs:
                max_cards = kwargs['max_cards']
                if 1 <= max_cards <= 50:
                    template.max_cards = max_cards
                else:
                    raise ValueError(f"max_cards must be between 1 and 50")
            
            if 'priority_keywords' in kwargs:
                template.priority_keywords = kwargs['priority_keywords']
            
            if 'question_types' in kwargs:
                template.question_types = kwargs['question_types']
            
            logger.info(f"Updated template {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update template {template_id}: {e}")
            return False
    
    def save_templates(self, output_path: Optional[str] = None) -> bool:
        """保存模板到文件"""
        save_path = output_path or self.config_path
        
        try:
            config = {
                'templates': {},
                'default_template': self.default_template_key
            }
            
            for template_id, template in self.templates.items():
                config['templates'][template_id] = {
                    'name': template.name,
                    'description': template.description,
                    'max_cards': template.max_cards,
                    'system_prompt': template.system_prompt,
                    'user_prompt_template': template.user_prompt_template,
                    'priority_keywords': template.priority_keywords,
                    'question_types': template.question_types
                }
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Templates saved to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")
            return False
    
    def validate_template_requirements(self, template_id: str, text: str) -> Dict[str, Any]:
        """验证模板要求和文本匹配度"""
        template = self.get_template(template_id)
        if not template:
            return {'valid': False, 'reason': 'Template not found'}
        
        # 基本验证
        if len(text.strip()) < 10:
            return {'valid': False, 'reason': 'Text too short'}
        
        # 关键词匹配度分析
        text_lower = text.lower()
        keyword_matches = [
            keyword for keyword in template.priority_keywords 
            if keyword.lower() in text_lower
        ]
        
        match_score = len(keyword_matches) / max(len(template.priority_keywords), 1)
        
        return {
            'valid': True,
            'template_name': template.name,
            'max_cards': template.max_cards,
            'keyword_matches': keyword_matches,
            'match_score': match_score,
            'recommended': match_score > 0.3,
            'question_types': template.question_types
        }


# 全局实例
prompt_manager = PromptManager()