#!/usr/bin/env python3
"""
简单性能测试 - 测试服务器响应能力
无需API密钥，只测试服务器基础性能
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any

async def test_endpoint_performance(url: str, num_requests: int = 10) -> Dict[str, Any]:
    """测试单个端点的性能"""
    response_times = []
    successful_requests = 0
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        start_time = time.time()
        
        for i in range(num_requests):
            task = asyncio.create_task(make_single_request(session, url))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        for result in results:
            if isinstance(result, dict) and result.get('success'):
                response_times.append(result['response_time'])
                successful_requests += 1
    
    if response_times:
        return {
            'total_requests': num_requests,
            'successful_requests': successful_requests,
            'failed_requests': num_requests - successful_requests,
            'success_rate': successful_requests / num_requests * 100,
            'total_time': total_time,
            'avg_response_time': statistics.mean(response_times),
            'median_response_time': statistics.median(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'requests_per_second': successful_requests / total_time
        }
    else:
        return {
            'total_requests': num_requests,
            'successful_requests': 0,
            'failed_requests': num_requests,
            'success_rate': 0,
            'error': 'All requests failed'
        }

async def make_single_request(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
    """发送单个请求"""
    start_time = time.time()
    
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            await response.text()  # 读取响应内容
            end_time = time.time()
            
            return {
                'success': response.status == 200,
                'status_code': response.status,
                'response_time': (end_time - start_time) * 1000  # 转换为毫秒
            }
    except Exception as e:
        end_time = time.time()
        return {
            'success': False,
            'error': str(e),
            'response_time': (end_time - start_time) * 1000
        }

async def test_api_stress():
    """测试API承压能力"""
    base_url = "http://127.0.0.1:8001"
    
    print("🚀 开始API性能压力测试")
    print("="*50)
    
    # 测试不同的端点
    test_cases = [
        {
            'name': '模型列表端点',
            'url': f'{base_url}/supported_models',
            'requests': 20
        },
        {
            'name': '健康检查端点',
            'url': f'{base_url}/docs',  # FastAPI自动生成的文档端点
            'requests': 15
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        print(f"\n🧪 测试: {test_case['name']}")
        print(f"URL: {test_case['url']}")
        print(f"并发请求数: {test_case['requests']}")
        
        result = await test_endpoint_performance(test_case['url'], test_case['requests'])
        results[test_case['name']] = result
        
        if 'error' not in result:
            print(f"✅ 成功率: {result['success_rate']:.1f}%")
            print(f"📊 平均响应时间: {result['avg_response_time']:.2f}ms")
            print(f"📈 每秒请求数: {result['requests_per_second']:.2f}")
            print(f"⏱️  总耗时: {result['total_time']:.2f}s")
        else:
            print(f"❌ 测试失败: {result['error']}")
    
    return results

async def test_concurrent_load():
    """测试并发负载"""
    print("\n🔥 并发负载测试")
    print("="*50)
    
    base_url = "http://127.0.0.1:8001/supported_models"
    
    # 测试不同的并发级别
    concurrency_levels = [1, 5, 10, 20]
    
    for level in concurrency_levels:
        print(f"\n📊 测试并发级别: {level}")
        
        result = await test_endpoint_performance(base_url, level)
        
        if 'error' not in result:
            print(f"  成功率: {result['success_rate']:.1f}%")
            print(f"  平均响应时间: {result['avg_response_time']:.2f}ms")
            print(f"  QPS: {result['requests_per_second']:.2f}")
            
            # 简单的性能评级
            avg_time = result['avg_response_time']
            if avg_time < 100:
                grade = "🟢 优秀"
            elif avg_time < 500:
                grade = "🟡 良好"
            elif avg_time < 1000:
                grade = "🟠 一般"
            else:
                grade = "🔴 需优化"
            
            print(f"  性能评级: {grade}")
        else:
            print(f"  ❌ 失败: {result['error']}")

async def main():
    """主函数"""
    print("🎯 AI Flashcard Generator 性能测试")
    print("测试服务器基础性能，无需API密钥")
    print("="*60)
    
    # 先检查服务器是否运行
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8001/supported_models", 
                                  timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    print("✅ 服务器运行正常，开始性能测试...")
                else:
                    print(f"❌ 服务器响应异常: {response.status}")
                    return
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        print("请确保服务器在 http://127.0.0.1:8001 运行")
        return
    
    # 执行性能测试
    await test_api_stress()
    await test_concurrent_load()
    
    print("\n🎉 性能测试完成!")
    print("💡 建议: 使用真实API密钥进行完整的端到端测试")

if __name__ == "__main__":
    asyncio.run(main())