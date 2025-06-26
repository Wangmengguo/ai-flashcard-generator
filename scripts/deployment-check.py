#!/usr/bin/env python3
"""
快速部署验证脚本
用于验证AI Flashcard Generator的部署状态和功能
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, List, Optional
from pathlib import Path

class DeploymentChecker:
    """部署状态检查器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.results: List[Dict] = []
        
    def log_result(self, check_name: str, status: str, message: str, details: Optional[Dict] = None):
        """记录检查结果"""
        result = {
            "check": check_name,
            "status": status,  # "pass", "fail", "warning"
            "message": message,
            "timestamp": time.time(),
            "details": details or {}
        }
        self.results.append(result)
        
        # 实时显示结果
        emoji = "✅" if status == "pass" else "❌" if status == "fail" else "⚠️"
        print(f"{emoji} {check_name}: {message}")
        
    async def check_basic_connectivity(self):
        """检查基础连接性"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/", timeout=10) as response:
                    if response.status == 200:
                        self.log_result(
                            "基础连接", "pass", 
                            f"应用可访问 (HTTP {response.status})",
                            {"status_code": response.status, "url": self.base_url}
                        )
                    else:
                        self.log_result(
                            "基础连接", "fail",
                            f"应用返回错误状态码: {response.status}"
                        )
        except Exception as e:
            self.log_result(
                "基础连接", "fail",
                f"无法连接到应用: {str(e)}"
            )
    
    async def check_health_endpoint(self):
        """检查健康检查端点"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=10) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        self.log_result(
                            "健康检查", "pass",
                            "健康检查端点正常",
                            health_data
                        )
                    else:
                        self.log_result(
                            "健康检查", "fail",
                            f"健康检查返回状态码: {response.status}"
                        )
        except Exception as e:
            self.log_result(
                "健康检查", "fail",
                f"健康检查端点异常: {str(e)}"
            )
    
    async def check_supported_models(self):
        """检查支持的模型列表"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/supported_models", timeout=10) as response:
                    if response.status == 200:
                        models = await response.json()
                        if isinstance(models, list) and len(models) > 0:
                            self.log_result(
                                "模型列表", "pass",
                                f"成功获取 {len(models)} 个支持的模型",
                                {"model_count": len(models), "models": models[:3]}  # 只显示前3个
                            )
                        else:
                            self.log_result(
                                "模型列表", "warning",
                                "模型列表为空"
                            )
                    else:
                        self.log_result(
                            "模型列表", "fail",
                            f"模型接口返回状态码: {response.status}"
                        )
        except Exception as e:
            self.log_result(
                "模型列表", "fail",
                f"模型接口异常: {str(e)}"
            )
    
    async def check_generate_endpoint(self):
        """检查生成接口功能"""
        test_data = {
            "text": "这是一个测试文本，用于验证闪卡生成功能。",
            "model": "google/gemini-2.5-flash-preview",
            "card_count": 2
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/generate", 
                    json=test_data,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("cards") and len(result["cards"]) > 0:
                            self.log_result(
                                "生成功能", "pass",
                                f"成功生成 {len(result['cards'])} 张卡片",
                                {"card_count": len(result["cards"]), "model": result.get("model")}
                            )
                        else:
                            self.log_result(
                                "生成功能", "warning",
                                "生成接口响应但未返回卡片"
                            )
                    elif response.status == 400:
                        error_data = await response.json()
                        self.log_result(
                            "生成功能", "warning",
                            f"请求参数错误: {error_data.get('detail', '未知错误')}"
                        )
                    elif response.status == 401:
                        self.log_result(
                            "生成功能", "fail",
                            "API密钥未配置或无效 - 请检查OPENROUTER_API_KEY"
                        )
                    else:
                        self.log_result(
                            "生成功能", "fail",
                            f"生成接口返回状态码: {response.status}"
                        )
        except asyncio.TimeoutError:
            self.log_result(
                "生成功能", "fail",
                "生成接口超时 (>30秒)"
            )
        except Exception as e:
            self.log_result(
                "生成功能", "fail",
                f"生成接口异常: {str(e)}"
            )
    
    async def check_metrics_endpoint(self):
        """检查监控指标端点"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/metrics", timeout=10) as response:
                    if response.status == 200:
                        metrics_data = await response.text()
                        if "requests_total" in metrics_data:
                            self.log_result(
                                "监控指标", "pass",
                                "Prometheus指标端点正常"
                            )
                        else:
                            self.log_result(
                                "监控指标", "warning",
                                "指标端点可访问但数据异常"
                            )
                    else:
                        self.log_result(
                            "监控指标", "warning",
                            f"指标端点返回状态码: {response.status}"
                        )
        except Exception as e:
            self.log_result(
                "监控指标", "warning",
                f"指标端点异常: {str(e)}"
            )
    
    def check_environment_config(self):
        """检查环境配置"""
        env_file = Path(".env")
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查关键配置项
                required_vars = [
                    "OPENROUTER_API_KEY",
                    "ENVIRONMENT", 
                    "PORT",
                    "CORS_ORIGINS"
                ]
                
                missing_vars = []
                for var in required_vars:
                    if var not in content or f"{var}=" not in content:
                        missing_vars.append(var)
                
                if not missing_vars:
                    self.log_result(
                        "环境配置", "pass",
                        "环境变量配置完整"
                    )
                else:
                    self.log_result(
                        "环境配置", "warning",
                        f"缺少环境变量: {', '.join(missing_vars)}"
                    )
                    
                # 检查API密钥是否设置
                if "OPENROUTER_API_KEY=" in content:
                    # 查找API密钥行
                    for line in content.split('\n'):
                        if line.startswith("OPENROUTER_API_KEY="):
                            key_value = line.split('=', 1)[1].strip()
                            if not key_value or key_value in ["your-openrouter-api-key", "your-openrouter-api-key-here"]:
                                self.log_result(
                                    "API密钥配置", "fail",
                                    "OPENROUTER_API_KEY未设置或使用默认值"
                                )
                            else:
                                self.log_result(
                                    "API密钥配置", "pass",
                                    "OPENROUTER_API_KEY已配置"
                                )
                            break
                        
            except Exception as e:
                self.log_result(
                    "环境配置", "fail",
                    f"读取环境配置文件失败: {str(e)}"
                )
        else:
            self.log_result(
                "环境配置", "fail",
                ".env文件不存在"
            )
    
    def check_docker_status(self):
        """检查Docker容器状态"""
        try:
            import subprocess
            
            # 检查docker-compose是否运行
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                try:
                    containers = json.loads(result.stdout) if result.stdout.strip() else []
                    if not isinstance(containers, list):
                        containers = [containers]
                    
                    running_containers = [c for c in containers if c.get("State") == "running"]
                    
                    if running_containers:
                        self.log_result(
                            "Docker状态", "pass",
                            f"发现 {len(running_containers)} 个运行中的容器",
                            {"containers": [c.get("Name", "unknown") for c in running_containers]}
                        )
                    else:
                        self.log_result(
                            "Docker状态", "warning",
                            "未发现运行中的容器"
                        )
                except json.JSONDecodeError:
                    self.log_result(
                        "Docker状态", "warning",
                        "无法解析docker-compose状态"
                    )
            else:
                self.log_result(
                    "Docker状态", "warning",
                    "docker-compose命令执行失败"
                )
                
        except subprocess.TimeoutExpired:
            self.log_result(
                "Docker状态", "warning",
                "Docker命令超时"
            )
        except FileNotFoundError:
            self.log_result(
                "Docker状态", "warning",
                "docker-compose命令未找到"
            )
        except Exception as e:
            self.log_result(
                "Docker状态", "warning",
                f"检查Docker状态异常: {str(e)}"
            )
    
    async def run_all_checks(self):
        """运行所有检查"""
        print("🔍 开始部署验证检查...\n")
        
        # 环境检查 (同步)
        self.check_environment_config()
        self.check_docker_status()
        
        print()  # 空行分隔
        
        # 网络检查 (异步)
        await self.check_basic_connectivity()
        await self.check_health_endpoint()
        await self.check_supported_models()
        await self.check_metrics_endpoint()
        
        print()  # 空行分隔
        
        # 功能检查 (异步)
        await self.check_generate_endpoint()
        
        print("\n" + "="*60)
        self.print_summary()
    
    def print_summary(self):
        """打印检查结果摘要"""
        print("📊 部署验证结果摘要")
        print("="*60)
        
        passed = [r for r in self.results if r["status"] == "pass"]
        failed = [r for r in self.results if r["status"] == "fail"]
        warnings = [r for r in self.results if r["status"] == "warning"]
        
        print(f"✅ 通过: {len(passed)}")
        print(f"❌ 失败: {len(failed)}")
        print(f"⚠️  警告: {len(warnings)}")
        
        if failed:
            print(f"\n🚨 需要修复的问题:")
            for result in failed:
                print(f"   • {result['check']}: {result['message']}")
        
        if warnings:
            print(f"\n⚠️  需要注意的问题:")
            for result in warnings:
                print(f"   • {result['check']}: {result['message']}")
        
        print("\n" + "="*60)
        
        if not failed:
            if not warnings:
                print("🎉 所有检查都通过了! 部署状态良好.")
            else:
                print("✅ 核心功能正常, 但有一些警告需要关注.")
        else:
            print("🚨 发现严重问题, 请修复后重新检查.")
            
        # 保存详细结果到文件
        self.save_results()
    
    def save_results(self):
        """保存检查结果到文件"""
        results_file = Path("deployment-check-results.json")
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": time.time(),
                    "base_url": self.base_url,
                    "summary": {
                        "total": len(self.results),
                        "passed": len([r for r in self.results if r["status"] == "pass"]),
                        "failed": len([r for r in self.results if r["status"] == "fail"]),
                        "warnings": len([r for r in self.results if r["status"] == "warning"])
                    },
                    "results": self.results
                }, f, indent=2, ensure_ascii=False)
            print(f"\n📄 详细结果已保存到: {results_file}")
        except Exception as e:
            print(f"\n⚠️  无法保存结果文件: {str(e)}")

async def main():
    """主函数"""
    # 支持命令行参数指定URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    checker = DeploymentChecker(base_url)
    await checker.run_all_checks()
    
    # 根据结果设置退出码
    failed_count = len([r for r in checker.results if r["status"] == "fail"])
    sys.exit(1 if failed_count > 0 else 0)

if __name__ == "__main__":
    asyncio.run(main())