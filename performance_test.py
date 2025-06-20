#!/usr/bin/env python3
"""
AI Flashcard Generator 性能测试框架
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict, Any
import argparse
import logging
from datetime import datetime
import csv
import sys

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceTest:
    def __init__(self, base_url: str = "http://127.0.0.1:8001"):
        self.base_url = base_url
        self.test_results = []
        
    async def make_request(self, session: aiohttp.ClientSession, payload: Dict[str, Any]) -> Dict[str, Any]:
        """发送单个请求并测量响应时间"""
        start_time = time.time()
        
        try:
            async with session.post(
                f"{self.base_url}/generate_flashcards/",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                
                data = await response.json()
                
                return {
                    "status_code": response.status,
                    "response_time_ms": response_time,
                    "success": response.status == 200,
                    "flashcards_count": len(data.get("flashcards", [])),
                    "has_error": bool(data.get("error")),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            end_time = time.time()
            return {
                "status_code": 0,
                "response_time_ms": (end_time - start_time) * 1000,
                "success": False,
                "flashcards_count": 0,
                "has_error": True,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def concurrent_test(self, 
                            concurrent_users: int,
                            requests_per_user: int,
                            test_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """并发测试"""
        logger.info(f"开始并发测试: {concurrent_users} 并发用户, 每用户 {requests_per_user} 请求")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for user_id in range(concurrent_users):
                for req_id in range(requests_per_user):
                    # 为每个请求添加唯一标识
                    payload = test_payload.copy()
                    payload["text"] = f"{payload['text']} [User{user_id}-Req{req_id}]"
                    
                    task = self.make_request(session, payload)
                    tasks.append(task)
            
            # 同时执行所有请求
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    processed_results.append({
                        "status_code": 0,
                        "response_time_ms": 0,
                        "success": False,
                        "flashcards_count": 0,
                        "has_error": True,
                        "error": str(result),
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    processed_results.append(result)
            
            return processed_results

    async def load_test(self, 
                       duration_seconds: int,
                       requests_per_second: int,
                       test_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """负载测试 - 在指定时间内以固定速率发送请求"""
        logger.info(f"开始负载测试: {duration_seconds}秒, {requests_per_second} RPS")
        
        results = []
        start_time = time.time()
        request_count = 0
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration_seconds:
                batch_start = time.time()
                
                # 计算这一秒应该发送的请求数
                tasks = []
                for _ in range(requests_per_second):
                    payload = test_payload.copy()
                    payload["text"] = f"{payload['text']} [LoadTest-{request_count}]"
                    task = self.make_request(session, payload)
                    tasks.append(task)
                    request_count += 1
                
                # 执行这一批请求
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 处理结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        results.append({
                            "status_code": 0,
                            "response_time_ms": 0,
                            "success": False,
                            "flashcards_count": 0,
                            "has_error": True,
                            "error": str(result),
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        results.append(result)
                
                # 控制请求速率
                batch_duration = time.time() - batch_start
                if batch_duration < 1.0:
                    await asyncio.sleep(1.0 - batch_duration)
        
        logger.info(f"负载测试完成，共发送 {len(results)} 个请求")
        return results

    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析测试结果"""
        if not results:
            return {"error": "没有测试结果"}
        
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        response_times = [r["response_time_ms"] for r in successful_results]
        
        analysis = {
            "total_requests": len(results),
            "successful_requests": len(successful_results),
            "failed_requests": len(failed_results),
            "success_rate_percent": (len(successful_results) / len(results)) * 100,
            
            "response_time_stats": {
                "min_ms": min(response_times) if response_times else 0,
                "max_ms": max(response_times) if response_times else 0,
                "avg_ms": statistics.mean(response_times) if response_times else 0,
                "median_ms": statistics.median(response_times) if response_times else 0,
                "p95_ms": self._percentile(response_times, 0.95) if response_times else 0,
                "p99_ms": self._percentile(response_times, 0.99) if response_times else 0,
            },
            
            "flashcards_stats": {
                "total_flashcards": sum(r["flashcards_count"] for r in successful_results),
                "avg_flashcards_per_request": (
                    statistics.mean([r["flashcards_count"] for r in successful_results])
                    if successful_results else 0
                )
            },
            
            "error_analysis": {
                "timeout_errors": len([r for r in failed_results if "timeout" in r.get("error", "").lower()]),
                "connection_errors": len([r for r in failed_results if "connection" in r.get("error", "").lower()]),
                "server_errors": len([r for r in failed_results if r.get("status_code", 0) >= 500]),
                "client_errors": len([r for r in failed_results if 400 <= r.get("status_code", 0) < 500]),
            }
        }
        
        return analysis
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def save_results(self, results: List[Dict[str, Any]], analysis: Dict[str, Any], filename: str):
        """保存测试结果到文件"""
        # 保存详细结果
        with open(f"{filename}_detailed.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # 保存分析结果
        with open(f"{filename}_analysis.json", "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        # 保存CSV格式
        if results:
            with open(f"{filename}_results.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
        
        logger.info(f"测试结果已保存到: {filename}_*.json 和 {filename}_results.csv")

    def print_analysis(self, analysis: Dict[str, Any]):
        """打印分析结果"""
        print("\n" + "="*60)
        print("性能测试结果分析")
        print("="*60)
        
        print(f"总请求数: {analysis['total_requests']}")
        print(f"成功请求数: {analysis['successful_requests']}")
        print(f"失败请求数: {analysis['failed_requests']}")
        print(f"成功率: {analysis['success_rate_percent']:.2f}%")
        
        print("\n响应时间统计 (毫秒):")
        stats = analysis['response_time_stats']
        print(f"  最小值: {stats['min_ms']:.2f}")
        print(f"  最大值: {stats['max_ms']:.2f}")
        print(f"  平均值: {stats['avg_ms']:.2f}")
        print(f"  中位数: {stats['median_ms']:.2f}")
        print(f"  95百分位: {stats['p95_ms']:.2f}")
        print(f"  99百分位: {stats['p99_ms']:.2f}")
        
        print("\n闪卡生成统计:")
        fc_stats = analysis['flashcards_stats']
        print(f"  总闪卡数: {fc_stats['total_flashcards']}")
        print(f"  平均每请求闪卡数: {fc_stats['avg_flashcards_per_request']:.2f}")
        
        print("\n错误分析:")
        err_stats = analysis['error_analysis']
        print(f"  超时错误: {err_stats['timeout_errors']}")
        print(f"  连接错误: {err_stats['connection_errors']}")
        print(f"  服务器错误 (5xx): {err_stats['server_errors']}")
        print(f"  客户端错误 (4xx): {err_stats['client_errors']}")

# 测试数据
TEST_PAYLOADS = {
    "small": {
        "text": "Python是一种高级编程语言，具有简洁的语法和强大的功能。",
        "api_key": "sk-or-test-key",
        "model_name": "google/gemini-2.5-flash-preview"
    },
    "medium": {
        "text": """机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习。
        机器学习算法通过训练数据来构建数学模型，以便对新数据做出预测或决策。
        主要的机器学习类型包括监督学习、无监督学习和强化学习。
        监督学习使用标记的训练数据，无监督学习处理未标记的数据，
        而强化学习通过与环境的交互来学习最优行为。""",
        "api_key": "sk-or-test-key", 
        "model_name": "google/gemini-2.5-flash-preview"
    },
    "large": {
        "text": """深度学习是机器学习的一个子领域，它模仿人脑神经网络的工作方式。
        深度学习使用多层神经网络来学习数据的复杂模式和表示。
        卷积神经网络(CNN)特别适用于图像处理任务，如图像识别和计算机视觉。
        循环神经网络(RNN)和长短期记忆网络(LSTM)适用于序列数据处理，如自然语言处理和时间序列预测。
        Transformer架构革命性地改变了自然语言处理领域，产生了BERT、GPT等预训练模型。
        深度学习在图像识别、语音识别、自然语言处理、推荐系统等领域取得了突破性进展。
        然而，深度学习也面临着数据需求大、计算资源消耗高、模型可解释性差等挑战。
        为了解决这些问题，研究人员正在探索更高效的网络架构、训练方法和解释技术。""",
        "api_key": "sk-or-test-key",
        "model_name": "google/gemini-2.5-flash-preview"
    }
}

async def main():
    parser = argparse.ArgumentParser(description="AI Flashcard Generator 性能测试")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="API基础URL")
    parser.add_argument("--test-type", choices=["concurrent", "load", "all"], default="all", help="测试类型")
    parser.add_argument("--concurrent-users", type=int, default=10, help="并发用户数")
    parser.add_argument("--requests-per-user", type=int, default=5, help="每用户请求数")
    parser.add_argument("--load-duration", type=int, default=60, help="负载测试持续时间(秒)")
    parser.add_argument("--requests-per-second", type=int, default=5, help="负载测试每秒请求数")
    parser.add_argument("--payload-size", choices=["small", "medium", "large"], default="medium", help="测试数据大小")
    parser.add_argument("--output", default="performance_test", help="输出文件前缀")
    
    args = parser.parse_args()
    
    # 检查API密钥
    if TEST_PAYLOADS[args.payload_size]["api_key"] == "sk-or-test-key":
        print("警告: 请设置有效的OpenRouter API密钥")
        api_key = input("请输入您的OpenRouter API密钥: ").strip()
        if not api_key:
            print("错误: 未提供API密钥")
            sys.exit(1)
        
        for payload in TEST_PAYLOADS.values():
            payload["api_key"] = api_key
    
    tester = PerformanceTest(args.url)
    test_payload = TEST_PAYLOADS[args.payload_size]
    
    print(f"开始性能测试...")
    print(f"API URL: {args.url}")
    print(f"测试数据大小: {args.payload_size}")
    print(f"测试内容长度: {len(test_payload['text'])} 字符")
    
    all_results = []
    
    if args.test_type in ["concurrent", "all"]:
        print(f"\n执行并发测试...")
        concurrent_results = await tester.concurrent_test(
            args.concurrent_users,
            args.requests_per_user,
            test_payload
        )
        all_results.extend(concurrent_results)
        
        print(f"并发测试完成，共 {len(concurrent_results)} 个请求")
        concurrent_analysis = tester.analyze_results(concurrent_results)
        print("\n并发测试结果:")
        tester.print_analysis(concurrent_analysis)
        tester.save_results(concurrent_results, concurrent_analysis, f"{args.output}_concurrent")
    
    if args.test_type in ["load", "all"]:
        print(f"\n执行负载测试...")
        load_results = await tester.load_test(
            args.load_duration,
            args.requests_per_second,
            test_payload
        )
        all_results.extend(load_results)
        
        print(f"负载测试完成，共 {len(load_results)} 个请求")
        load_analysis = tester.analyze_results(load_results)
        print("\n负载测试结果:")
        tester.print_analysis(load_analysis)
        tester.save_results(load_results, load_analysis, f"{args.output}_load")
    
    if args.test_type == "all" and all_results:
        print(f"\n综合测试结果:")
        combined_analysis = tester.analyze_results(all_results)
        tester.print_analysis(combined_analysis)
        tester.save_results(all_results, combined_analysis, f"{args.output}_combined")

if __name__ == "__main__":
    asyncio.run(main())