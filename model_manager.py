"""
AI Flashcard Generator - 模型管理器
负责动态模型发现、元数据管理和API数据融合
"""

import json
import os
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import httpx

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelMetadata:
    """模型元数据结构"""
    suggested_use: str
    local_notes: str = ""
    quality_rating: int = 0  # 1-5 星级评分
    cost_efficiency: int = 0  # 1-5 性价比评分
    preferred_for: List[str] = None
    status: str = "new"  # new, verified, testing, deprecated
    last_updated: str = ""
    added_by: str = "system"
    test_results: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.preferred_for is None:
            self.preferred_for = []
        if self.test_results is None:
            self.test_results = {}
        if not self.last_updated:
            self.last_updated = datetime.now().strftime("%Y-%m-%d")

@dataclass 
class OpenRouterModel:
    """OpenRouter API返回的模型信息"""
    id: str
    name: str
    description: str = ""
    pricing: Dict[str, float] = None
    context_length: int = 0
    architecture: Dict[str, Any] = None
    top_provider: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.pricing is None:
            self.pricing = {}
        if self.architecture is None:
            self.architecture = {}
        if self.top_provider is None:
            self.top_provider = {}

@dataclass
class CombinedModelInfo:
    """融合后的模型信息"""
    # OpenRouter API 数据
    id: str
    name: str
    description: str
    pricing: Dict[str, float]
    context_length: int
    architecture: Dict[str, Any]
    
    # 本地元数据
    suggested_use: str
    local_notes: str
    quality_rating: int
    cost_efficiency: int
    preferred_for: List[str]
    status: str
    last_updated: str
    test_results: Dict[str, Any]
    
    # 系统信息
    max_tokens: int = 0  # 为了兼容现有API格式
    
    def to_legacy_format(self) -> Dict[str, Any]:
        """转换为旧版API格式，保持向后兼容"""
        return {
            "name": self.name,
            "description": self.description,
            "max_tokens": self.max_tokens or self.context_length,
            "suggested_use": self.suggested_use,
            # 额外信息
            "pricing": self.pricing,
            "quality_rating": self.quality_rating,
            "cost_efficiency": self.cost_efficiency,
            "preferred_for": self.preferred_for,
            "status": self.status
        }

class ModelManager:
    """模型管理器 - 负责动态模型发现和元数据管理"""
    
    def __init__(self, 
                 metadata_file: str = "local_model_metadata.json",
                 cache_file: str = "openrouter_cache.json",
                 cache_ttl: int = 3600):  # 1小时缓存
        self.metadata_file = metadata_file
        self.cache_file = cache_file
        self.cache_ttl = cache_ttl
        
        # 加载本地元数据
        self.local_metadata: Dict[str, ModelMetadata] = self._load_local_metadata()
        
        # OpenRouter API缓存
        self.api_cache: Dict[str, Any] = self._load_api_cache()
        
        logger.info(f"ModelManager initialized with {len(self.local_metadata)} local models")
    
    def _load_local_metadata(self) -> Dict[str, ModelMetadata]:
        """加载本地模型元数据"""
        try:
            if not os.path.exists(self.metadata_file):
                logger.warning(f"Metadata file {self.metadata_file} not found, creating empty metadata")
                return {}
            
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = {}
            for model_id, meta_dict in data.items():
                try:
                    metadata[model_id] = ModelMetadata(**meta_dict)
                except Exception as e:
                    logger.error(f"Failed to load metadata for {model_id}: {e}")
            
            logger.info(f"Loaded {len(metadata)} model metadata entries")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to load metadata file: {e}")
            return {}
    
    def _save_local_metadata(self) -> bool:
        """保存本地模型元数据"""
        try:
            # 转换为可序列化的字典
            data = {}
            for model_id, metadata in self.local_metadata.items():
                data[model_id] = asdict(metadata)
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(data)} model metadata entries")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save metadata file: {e}")
            return False
    
    def _load_api_cache(self) -> Dict[str, Any]:
        """加载OpenRouter API缓存"""
        try:
            if not os.path.exists(self.cache_file):
                return {"models": [], "timestamp": 0}
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to load API cache: {e}")
            return {"models": [], "timestamp": 0}
    
    def _save_api_cache(self, models: List[Dict]) -> bool:
        """保存OpenRouter API缓存"""
        try:
            cache_data = {
                "models": models,
                "timestamp": time.time()
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Cached {len(models)} models from OpenRouter API")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save API cache: {e}")
            return False
    
    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if not self.api_cache or "timestamp" not in self.api_cache:
            return False
        
        cache_age = time.time() - self.api_cache["timestamp"]
        return cache_age < self.cache_ttl
    
    async def fetch_openrouter_models(self) -> List[OpenRouterModel]:
        """从OpenRouter API获取模型列表"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get("https://openrouter.ai/api/v1/models")
                response.raise_for_status()
                
                data = response.json()
                models = []
                
                for model_data in data.get("data", []):
                    try:
                        # 只保留文本生成模型
                        if self._is_text_generation_model(model_data):
                            model = OpenRouterModel(
                                id=model_data.get("id", ""),
                                name=model_data.get("name", ""),
                                description=model_data.get("description", ""),
                                pricing=model_data.get("pricing", {}),
                                context_length=model_data.get("context_length", 0),
                                architecture=model_data.get("architecture", {}),
                                top_provider=model_data.get("top_provider", {})
                            )
                            models.append(model)
                    except Exception as e:
                        logger.warning(f"Failed to parse model {model_data.get('id', 'unknown')}: {e}")
                
                # 缓存结果
                self._save_api_cache([asdict(model) for model in models])
                logger.info(f"Fetched {len(models)} text generation models from OpenRouter")
                
                return models
                
        except Exception as e:
            logger.error(f"Failed to fetch models from OpenRouter: {e}")
            return []
    
    def _is_text_generation_model(self, model_data: Dict) -> bool:
        """判断是否为文本生成模型"""
        model_id = model_data.get("id", "").lower()
        
        # 排除非文本模型
        exclude_keywords = [
            "dall-e", "stable-diffusion", "midjourney", "runway",
            "whisper", "tts", "voice", "speech",
            "vision", "image", "video", "audio"
        ]
        
        for keyword in exclude_keywords:
            if keyword in model_id:
                return False
        
        # 只包含已知的文本生成模型提供商
        include_providers = [
            "openai", "anthropic", "google", "meta", "qwen", 
            "deepseek", "x-ai", "mistral", "cohere", "ai21"
        ]
        
        for provider in include_providers:
            if model_id.startswith(provider + "/"):
                return True
        
        return False
    
    async def get_all_models(self, force_refresh: bool = False) -> Dict[str, CombinedModelInfo]:
        """获取所有模型（API数据 + 本地元数据）"""
        
        # 获取OpenRouter模型数据
        if force_refresh or not self._is_cache_valid():
            api_models = await self.fetch_openrouter_models()
            self.api_cache = {
                "models": [asdict(model) for model in api_models],
                "timestamp": time.time()
            }
        else:
            # 使用缓存数据
            api_models = [OpenRouterModel(**model_data) for model_data in self.api_cache.get("models", [])]
            logger.info(f"Using cached OpenRouter models ({len(api_models)} models)")
        
        # 融合API数据和本地元数据
        combined_models = {}
        
        # 处理API返回的模型
        for api_model in api_models:
            metadata = self.local_metadata.get(api_model.id)
            
            if metadata is None:
                # 新发现的模型，创建默认元数据
                metadata = ModelMetadata(
                    suggested_use="新发现模型，等待人工评估",
                    local_notes=f"从OpenRouter API自动发现于 {datetime.now().strftime('%Y-%m-%d')}",
                    status="new",
                    added_by="system"
                )
                self.local_metadata[api_model.id] = metadata
                logger.info(f"New model discovered: {api_model.id}")
            
            # 创建融合模型信息
            combined_model = CombinedModelInfo(
                id=api_model.id,
                name=api_model.name,
                description=api_model.description,
                pricing=api_model.pricing,
                context_length=api_model.context_length,
                architecture=api_model.architecture,
                suggested_use=metadata.suggested_use,
                local_notes=metadata.local_notes,
                quality_rating=metadata.quality_rating,
                cost_efficiency=metadata.cost_efficiency,
                preferred_for=metadata.preferred_for,
                status=metadata.status,
                last_updated=metadata.last_updated,
                test_results=metadata.test_results,
                max_tokens=api_model.context_length  # 兼容旧格式
            )
            
            combined_models[api_model.id] = combined_model
        
        # 检查本地元数据中是否有API中不存在的模型（可能已下线）
        for model_id, metadata in self.local_metadata.items():
            if model_id not in combined_models and metadata.status != "deprecated":
                logger.warning(f"Model {model_id} not found in OpenRouter API, marking as deprecated")
                metadata.status = "deprecated"
                metadata.last_updated = datetime.now().strftime("%Y-%m-%d")
        
        # 保存更新的元数据
        self._save_local_metadata()
        
        logger.info(f"Combined {len(combined_models)} models with metadata")
        return combined_models
    
    def update_model_metadata(self, model_id: str, metadata: Dict[str, Any]) -> bool:
        """更新模型元数据"""
        try:
            if model_id in self.local_metadata:
                current_metadata = self.local_metadata[model_id]
                
                # 更新允许的字段
                for field in ["suggested_use", "local_notes", "quality_rating", 
                             "cost_efficiency", "preferred_for", "status"]:
                    if field in metadata:
                        setattr(current_metadata, field, metadata[field])
                
                current_metadata.last_updated = datetime.now().strftime("%Y-%m-%d")
                
                # 保存到文件
                if self._save_local_metadata():
                    logger.info(f"Updated metadata for model: {model_id}")
                    return True
            else:
                logger.error(f"Model {model_id} not found in local metadata")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update metadata for {model_id}: {e}")
            return False
    
    def get_supported_models_legacy_format(self) -> Dict[str, Dict[str, Any]]:
        """获取旧版格式的模型列表，用于向后兼容"""
        import asyncio
        
        # 如果在异步上下文中，直接获取；否则创建新的事件循环
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 在已有事件循环中，需要创建任务
                future = asyncio.create_task(self.get_all_models())
                # 这里我们使用缓存数据，避免在同步函数中等待异步操作
                combined_models = self._get_models_from_cache()
            else:
                combined_models = loop.run_until_complete(self.get_all_models())
        except RuntimeError:
            # 没有事件循环，创建新的
            combined_models = asyncio.run(self.get_all_models())
        
        # 转换为旧版格式
        legacy_models = {}
        for model_id, model_info in combined_models.items():
            if model_info.status != "deprecated":  # 过滤掉已下线的模型
                legacy_models[model_id] = model_info.to_legacy_format()
        
        return legacy_models
    
    def _get_models_from_cache(self) -> Dict[str, CombinedModelInfo]:
        """从缓存获取模型（同步版本）"""
        if not self._is_cache_valid():
            # 缓存无效，返回基于本地元数据的基础模型列表
            logger.warning("API cache invalid, using local metadata only")
            combined_models = {}
            
            for model_id, metadata in self.local_metadata.items():
                if metadata.status != "deprecated":
                    combined_model = CombinedModelInfo(
                        id=model_id,
                        name=model_id.split("/")[-1] if "/" in model_id else model_id,
                        description="缓存数据不可用，显示基础信息",
                        pricing={},
                        context_length=0,
                        architecture={},
                        suggested_use=metadata.suggested_use,
                        local_notes=metadata.local_notes,
                        quality_rating=metadata.quality_rating,
                        cost_efficiency=metadata.cost_efficiency,
                        preferred_for=metadata.preferred_for,
                        status=metadata.status,
                        last_updated=metadata.last_updated,
                        test_results=metadata.test_results
                    )
                    combined_models[model_id] = combined_model
            
            return combined_models
        
        # 使用缓存数据
        api_models = [OpenRouterModel(**model_data) for model_data in self.api_cache.get("models", [])]
        combined_models = {}
        
        for api_model in api_models:
            metadata = self.local_metadata.get(api_model.id)
            if metadata and metadata.status != "deprecated":
                combined_model = CombinedModelInfo(
                    id=api_model.id,
                    name=api_model.name,
                    description=api_model.description,
                    pricing=api_model.pricing,
                    context_length=api_model.context_length,
                    architecture=api_model.architecture,
                    suggested_use=metadata.suggested_use,
                    local_notes=metadata.local_notes,
                    quality_rating=metadata.quality_rating,
                    cost_efficiency=metadata.cost_efficiency,
                    preferred_for=metadata.preferred_for,
                    status=metadata.status,
                    last_updated=metadata.last_updated,
                    test_results=metadata.test_results,
                    max_tokens=api_model.context_length
                )
                combined_models[api_model.id] = combined_model
        
        return combined_models
    
    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态信息"""
        cache_age = time.time() - self.api_cache.get("timestamp", 0)
        
        new_models = sum(1 for meta in self.local_metadata.values() if meta.status == "new")
        deprecated_models = sum(1 for meta in self.local_metadata.values() if meta.status == "deprecated")
        verified_models = sum(1 for meta in self.local_metadata.values() if meta.status == "verified")
        
        return {
            "last_sync": datetime.fromtimestamp(self.api_cache.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S") if self.api_cache.get("timestamp") else "从未同步",
            "cache_age_hours": round(cache_age / 3600, 1),
            "cache_valid": self._is_cache_valid(),
            "total_models": len(self.local_metadata),
            "new_models": new_models,
            "verified_models": verified_models,
            "deprecated_models": deprecated_models,
            "api_models_cached": len(self.api_cache.get("models", []))
        }

# 全局实例
model_manager = ModelManager()