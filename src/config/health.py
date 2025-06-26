"""
Health check utilities for the Flashcard Generator application.
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import httpx


class HealthChecker:
    """Health check manager for the application."""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_check = datetime.now()
        self.check_count = 0
        
    async def check_application_health(self) -> Dict[str, Any]:
        """Comprehensive application health check."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - self.start_time,
            "checks": {}
        }
        
        try:
            # Basic application health
            health_status["checks"]["app"] = await self._check_app_basics()
            
            # External dependencies health
            health_status["checks"]["openrouter"] = await self._check_openrouter_connectivity()
            
            # System resources
            health_status["checks"]["resources"] = await self._check_system_resources()
            
            # Overall status determination
            failed_checks = [name for name, check in health_status["checks"].items() 
                           if not check.get("healthy", False)]
            
            if failed_checks:
                health_status["status"] = "degraded"
                health_status["failed_checks"] = failed_checks
                
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            logging.error(f"Health check failed: {e}")
        
        self.last_check = datetime.now()
        self.check_count += 1
        
        return health_status
    
    async def _check_app_basics(self) -> Dict[str, Any]:
        """Check basic application functionality."""
        try:
            # 获取动态模型数量
            from model_manager import model_manager
            models = await model_manager.get_all_models()
            
            return {
                "healthy": True,
                "models_count": len(models),
                "check_time": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "check_time": datetime.now().isoformat()
            }
    
    async def _check_openrouter_connectivity(self) -> Dict[str, Any]:
        """Check OpenRouter API connectivity (without making actual calls)."""
        try:
            # Simple connectivity test to OpenRouter
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.head("https://openrouter.ai")
                
                return {
                    "healthy": response.status_code < 500,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds() if response.elapsed else 0,
                    "check_time": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "check_time": datetime.now().isoformat()
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources."""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "healthy": cpu_percent < 90 and memory.percent < 90 and disk.percent < 90,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "check_time": datetime.now().isoformat()
            }
        except ImportError:
            # psutil not available, basic check
            return {
                "healthy": True,
                "note": "System resource monitoring not available (psutil not installed)",
                "check_time": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "check_time": datetime.now().isoformat()
            }
    
    def get_readiness_status(self) -> Dict[str, Any]:
        """Check if the application is ready to serve requests."""
        return {
            "ready": True,
            "timestamp": datetime.now().isoformat(),
            "check_count": self.check_count,
            "last_check": self.last_check.isoformat() if self.last_check else None
        }
    
    def get_liveness_status(self) -> Dict[str, Any]:
        """Check if the application is alive and running."""
        return {
            "alive": True,
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - self.start_time,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat()
        }


# Metrics collection
class MetricsCollector:
    """Simple metrics collector for monitoring."""
    
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "response_time_sum": 0.0,
            "response_time_count": 0,
            "flashcards_generated": 0,
            "api_errors": {},
            "model_usage": {}
        }
    
    def record_request(self, success: bool, response_time: float, 
                      model_name: Optional[str] = None, error_code: Optional[str] = None):
        """Record request metrics."""
        self.metrics["requests_total"] += 1
        
        if success:
            self.metrics["requests_successful"] += 1
        else:
            self.metrics["requests_failed"] += 1
            if error_code:
                self.metrics["api_errors"][error_code] = self.metrics["api_errors"].get(error_code, 0) + 1
        
        self.metrics["response_time_sum"] += response_time
        self.metrics["response_time_count"] += 1
        
        if model_name:
            self.metrics["model_usage"][model_name] = self.metrics["model_usage"].get(model_name, 0) + 1
    
    def record_flashcards_generated(self, count: int):
        """Record number of flashcards generated."""
        self.metrics["flashcards_generated"] += count
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        avg_response_time = (
            self.metrics["response_time_sum"] / self.metrics["response_time_count"]
            if self.metrics["response_time_count"] > 0 else 0
        )
        
        return {
            **self.metrics,
            "avg_response_time": avg_response_time,
            "success_rate": (
                self.metrics["requests_successful"] / self.metrics["requests_total"] 
                if self.metrics["requests_total"] > 0 else 0
            ),
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.__init__()


# Global instances
health_checker = HealthChecker()
metrics_collector = MetricsCollector()