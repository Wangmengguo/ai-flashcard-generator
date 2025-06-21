#!/usr/bin/env python3
"""
端到端API测试脚本 - 使用真实API密钥
测试所有新功能和模板系统
"""

import asyncio
import httpx
import json
import time
from typing import Dict, List, Any

class E2EAPITester:
    def __init__(self, api_key: str, base_url: str = "http://127.0.0.1:8001"):
        self.api_key = api_key
        self.base_url = base_url
        self.test_results = []
        
    async def test_template_system(self, template_name: str, test_text: str, max_cards: int = 5) -> Dict[str, Any]:
        """测试特定模板和卡片数量配置"""
        print(f"\n🧪 测试模板: {template_name} (max_cards: {max_cards})")
        
        payload = {
            "text": test_text,
            "api_key": self.api_key,
            "model_name": "google/gemini-2.5-flash-preview",
            "template_id": template_name,
            "max_cards": max_cards
        }
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/generate_flashcards/",
                    json=payload
                )
                
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                cards_count = len(result.get('flashcards', []))
                
                test_result = {
                    'template': template_name,
                    'max_cards_requested': max_cards,
                    'cards_generated': cards_count,
                    'response_time': response_time,
                    'status': 'success',
                    'token_usage': result.get('token_usage', {}),
                    'processing_info': result.get('processing_info', {})
                }
                
                print(f"✅ 成功 - 生成 {cards_count} 张卡片，耗时 {response_time:.2f}s")
                if result.get('flashcards'):
                    print(f"   示例: {result['flashcards'][0]['q'][:50]}...")
                    
            else:
                test_result = {
                    'template': template_name,
                    'max_cards_requested': max_cards,
                    'status': 'error',
                    'error': response.json(),
                    'response_time': response_time
                }
                print(f"❌ 失败 - 状态码: {response.status_code}")
                print(f"   错误: {response.json()}")
                
        except Exception as e:
            test_result = {
                'template': template_name,
                'max_cards_requested': max_cards,
                'status': 'exception',
                'error': str(e),
                'response_time': time.time() - start_time
            }
            print(f"💥 异常 - {str(e)}")
            
        self.test_results.append(test_result)
        return test_result
    
    async def test_all_templates(self):
        """测试所有预设模板"""
        print("🚀 开始测试所有模板系统...")
        
        test_cases = [
            {
                'template': 'academic',
                'text': '深度学习是机器学习的一个子领域，它基于人工神经网络的学习和改进。深度学习模型由多个处理层组成，能够学习数据的多层次表示。这种方法在图像识别、自然语言处理和语音识别等领域取得了突破性进展。',
                'max_cards': 8
            },
            {
                'template': 'exam',
                'text': '牛顿第二定律：物体的加速度与作用力成正比，与物体质量成反比。公式为F=ma，其中F是力，m是质量，a是加速度。这个定律是经典力学的基础，解释了力、质量和运动之间的关系。',
                'max_cards': 6
            },
            {
                'template': 'language',
                'text': 'Machine learning is a subset of artificial intelligence that focuses on the development of algorithms and statistical models that enable computers to perform tasks without explicit instructions.',
                'max_cards': 10
            },
            {
                'template': 'technical',
                'text': 'FastAPI是一个现代、快速的Python Web框架，用于构建API。它基于标准Python类型提示，具有自动交互式文档生成、数据验证、序列化等功能。支持异步操作，性能接近NodeJS和Go。',
                'max_cards': 7
            },
            {
                'template': 'general',
                'text': '可持续发展是指满足当前需求而不损害后代满足其需求能力的发展模式。它包括经济可持续性、环境可持续性和社会可持续性三个维度，是21世纪全球发展的重要理念。',
                'max_cards': 5
            }
        ]
        
        for test_case in test_cases:
            await self.test_template_system(
                test_case['template'],
                test_case['text'],
                test_case['max_cards']
            )
            await asyncio.sleep(1)  # 避免请求过于频繁
    
    async def test_edge_cases(self):
        """测试边界情况"""
        print("\n🔬 测试边界情况...")
        
        edge_cases = [
            {
                'name': '最小卡片数量',
                'template': 'general',
                'text': '测试文本内容',
                'max_cards': 1
            },
            {
                'name': '最大卡片数量',
                'template': 'language',
                'text': '这是一个很长的测试文本，包含多个概念和知识点。我们要测试系统在处理大量卡片生成请求时的表现。人工智能技术正在快速发展，深度学习、机器学习、自然语言处理等领域都有重大突破。',
                'max_cards': 50
            },
            {
                'name': '空文本处理',
                'template': 'general',
                'text': '',
                'max_cards': 5
            },
            {
                'name': '超长文本',
                'template': 'academic',
                'text': '人工智能' * 1000,  # 创建一个很长的文本
                'max_cards': 10
            }
        ]
        
        for case in edge_cases:
            print(f"\n测试案例: {case['name']}")
            await self.test_template_system(
                case['template'],
                case['text'],
                case['max_cards']
            )
            await asyncio.sleep(1)
    
    async def test_invalid_parameters(self):
        """测试无效参数处理"""
        print("\n🚨 测试无效参数处理...")
        
        invalid_cases = [
            {
                'name': '无效模板名',
                'payload': {
                    "text": "测试文本",
                    "api_key": self.api_key,
                    "model_name": "google/gemini-2.5-flash-preview",
                    "template_id": "invalid_template",
                    "max_cards": 5
                }
            },
            {
                'name': '超出范围的卡片数量',
                'payload': {
                    "text": "测试文本",
                    "api_key": self.api_key,
                    "model_name": "google/gemini-2.5-flash-preview",
                    "template_id": "general",
                    "max_cards": 100  # 超过最大限制
                }
            },
            {
                'name': '无效模型名',
                'payload': {
                    "text": "测试文本",
                    "api_key": self.api_key,
                    "model_name": "invalid/model",
                    "template_id": "general",
                    "max_cards": 5
                }
            }
        ]
        
        for case in invalid_cases:
            print(f"\n测试案例: {case['name']}")
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.base_url}/generate_flashcards/",
                        json=case['payload']
                    )
                
                print(f"状态码: {response.status_code}")
                if response.status_code != 200:
                    print(f"✅ 正确处理错误: {response.json()}")
                else:
                    print(f"⚠️  意外成功: {response.json()}")
                    
            except Exception as e:
                print(f"💥 异常: {str(e)}")
            
            await asyncio.sleep(1)
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 测试报告")
        print("="*60)
        
        successful_tests = [r for r in self.test_results if r['status'] == 'success']
        failed_tests = [r for r in self.test_results if r['status'] != 'success']
        
        print(f"总测试数: {len(self.test_results)}")
        print(f"成功: {len(successful_tests)}")
        print(f"失败: {len(failed_tests)}")
        print(f"成功率: {len(successful_tests)/len(self.test_results)*100:.1f}%")
        
        if successful_tests:
            avg_response_time = sum(r['response_time'] for r in successful_tests) / len(successful_tests)
            print(f"平均响应时间: {avg_response_time:.2f}s")
            
            total_cards = sum(r.get('cards_generated', 0) for r in successful_tests)
            print(f"总生成卡片数: {total_cards}")
            
            # 按模板统计
            print("\n📋 按模板统计:")
            template_stats = {}
            for result in successful_tests:
                template = result['template']
                if template not in template_stats:
                    template_stats[template] = {'count': 0, 'avg_time': 0, 'total_cards': 0}
                template_stats[template]['count'] += 1
                template_stats[template]['avg_time'] += result['response_time']
                template_stats[template]['total_cards'] += result.get('cards_generated', 0)
            
            for template, stats in template_stats.items():
                avg_time = stats['avg_time'] / stats['count']
                print(f"  {template}: {stats['count']}次测试, 平均{avg_time:.2f}s, 共{stats['total_cards']}张卡片")
        
        if failed_tests:
            print("\n❌ 失败测试详情:")
            for test in failed_tests:
                print(f"  模板: {test['template']}, 错误: {test.get('error', 'Unknown')}")
        
        # 保存详细结果到文件
        with open('e2e_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        print(f"\n📄 详细结果已保存到: e2e_test_results.json")

async def main():
    """主测试函数"""
    import sys
    
    print("🚀 AI Flashcard Generator 端到端测试")
    
    # 从命令行参数或环境变量获取API密钥
    api_key = None
    if len(sys.argv) > 1:
        api_key = sys.argv[1].strip()
    
    if not api_key:
        print("❌ 请提供API密钥作为命令行参数")
        print("用法: python test_e2e_with_api.py YOUR_API_KEY")
        return
    
    # 确认服务器运行状态
    print("\n🔍 检查服务器状态...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8001/supported_models")
            if response.status_code == 200:
                print("✅ 服务器运行正常")
            else:
                print(f"❌ 服务器响应异常: {response.status_code}")
                return
    except Exception as e:
        print(f"❌ 无法连接服务器: {e}")
        return
    
    # 创建测试器实例
    tester = E2EAPITester(api_key)
    
    # 执行测试
    await tester.test_all_templates()
    await tester.test_edge_cases()
    await tester.test_invalid_parameters()
    
    # 生成报告
    tester.generate_report()

if __name__ == "__main__":
    asyncio.run(main())